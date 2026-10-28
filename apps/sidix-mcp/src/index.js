#!/usr/bin/env node
/**
 * SIDIX Socio Bot MCP Server
 *
 * Core tools:
 *   - sidix_query
 *   - sidix_capture
 *   - sidix_learn_session
 *   - sidix_status
 *
 * Socio tools are defined in social_tools.js
 * and exposed together with core tools.
 */

import fs from 'fs';
import path from 'path';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import {
  getSocialToolDefinitions,
  handleSocialTool,
  isSocialToolName,
} from './social_tools.js';

const BRAIN_QA_URL = process.env.SIDIX_URL || 'http://localhost:8765';
const CORPUS_PATH =
  process.env.SIDIX_CORPUS ||
  path.join(process.env.HOME || process.env.USERPROFILE || '', 'MIGHAN Model', 'brain', 'public');

const server = new Server(
  { name: 'sidix-socio-mcp', version: '1.1.0' },
  { capabilities: { tools: {} } },
);

const CORE_TOOLS = [
  {
    name: 'sidix_query',
    description:
      'Tanya ke SIDIX (agent backend). Cocok untuk pertanyaan proyek, arsitektur, atau topik corpus SIDIX.',
    inputSchema: {
      type: 'object',
      properties: {
        question: { type: 'string', description: 'Pertanyaan ke SIDIX' },
        persona: {
          type: 'string',
          description: 'Persona SIDIX opsional: MIGHAN, TOARD, FACH, HAYFAR, INAN',
          default: 'MIGHAN',
        },
      },
      required: ['question'],
    },
  },
  {
    name: 'sidix_capture',
    description: 'Simpan pengetahuan baru ke corpus SIDIX dan trigger re-index.',
    inputSchema: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'Judul/topik singkat' },
        content: { type: 'string', description: 'Isi markdown' },
        category: {
          type: 'string',
          description: 'Kategori corpus: research_notes | feedback_learning | praxis',
          default: 'research_notes',
        },
      },
      required: ['topic', 'content'],
    },
  },
  {
    name: 'sidix_learn_session',
    description: 'Rekam ringkasan sesi kerja ke corpus SIDIX.',
    inputSchema: {
      type: 'object',
      properties: {
        project: { type: 'string', description: 'Nama proyek' },
        summary: { type: 'string', description: 'Ringkasan sesi' },
        decisions: { type: 'string', description: 'Keputusan penting (opsional)' },
        errors: { type: 'string', description: 'Error dan fix (opsional)' },
      },
      required: ['project', 'summary'],
    },
  },
  {
    name: 'sidix_status',
    description: 'Cek status health SIDIX backend.',
    inputSchema: { type: 'object', properties: {}, required: [] },
  },
];

const SOCIAL_TOOLS = getSocialToolDefinitions();

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [...CORE_TOOLS, ...SOCIAL_TOOLS],
}));

function nextResearchNoteNumber(notesDir) {
  const files = fs
    .readdirSync(notesDir)
    .filter((name) => /^\d+_/.test(name))
    .sort();
  if (files.length === 0) {
    return 1;
  }
  const match = files[files.length - 1].match(/^(\d+)/);
  return match ? Number.parseInt(match[1], 10) + 1 : 1;
}

function slugify(input, maxLen = 50) {
  return String(input || 'untitled')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .slice(0, maxLen);
}

async function sidixReindexFireAndForget() {
  try {
    await fetch(`${BRAIN_QA_URL}/corpus/reindex`, { method: 'POST' });
  } catch (_err) {
    // no-op: backend mungkin sedang restart
  }
}

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const name = req?.params?.name || '';
  const args = req?.params?.arguments || {};

  try {
    if (isSocialToolName(name)) {
      return await handleSocialTool(name, args, BRAIN_QA_URL);
    }

    switch (name) {
      case 'sidix_query': {
        const res = await fetch(`${BRAIN_QA_URL}/agent/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: args.question,
            persona: args.persona || 'MIGHAN',
            corpus_only: false,
          }),
        });
        if (!res.ok) {
          throw new Error(`SIDIX HTTP ${res.status}`);
        }
        const data = await res.json();
        const answer = data.answer || data.reply || '(tanpa isi)';
        const sourceCount = Array.isArray(data.citations) ? data.citations.length : 0;
        return {
          content: [
            {
              type: 'text',
              text: [
                `SIDIX (${args.persona || 'MIGHAN'})`,
                '',
                answer,
                '',
                `Confidence: ${data.confidence || '-'} | Sources: ${sourceCount}`,
              ].join('\n'),
            },
          ],
        };
      }

      case 'sidix_capture': {
        const category = args.category || 'research_notes';
        const notesDir = path.join(CORPUS_PATH, category);
        fs.mkdirSync(notesDir, { recursive: true });

        const today = new Date().toISOString().slice(0, 10);
        const slug = slugify(args.topic, 60);
        const filename =
          category === 'research_notes'
            ? `${nextResearchNoteNumber(notesDir)}_${slug}.md`
            : `${today}_${slug}.md`;
        const filepath = path.join(notesDir, filename);
        const content = `# ${args.topic}\n\n> Captured via SIDIX MCP - ${today}\n\n${args.content}\n`;
        fs.writeFileSync(filepath, content, 'utf8');
        sidixReindexFireAndForget();

        return {
          content: [
            {
              type: 'text',
              text: `Tersimpan: ${category}/${filename}\nRe-index SIDIX berjalan di background.`,
            },
          ],
        };
      }

      case 'sidix_learn_session': {
        const notesDir = path.join(CORPUS_PATH, 'research_notes');
        fs.mkdirSync(notesDir, { recursive: true });
        const today = new Date().toISOString().slice(0, 10);
        const slug = slugify(args.project, 40);
        const filename = `${nextResearchNoteNumber(notesDir)}_sesi_${slug}_${today}.md`;
        const filepath = path.join(notesDir, filename);

        const lines = [
          `# Sesi Kerja: ${args.project} - ${today}`,
          '',
          '> Direkam via SIDIX MCP',
          '',
          '## Ringkasan',
          `${args.summary || ''}`,
          '',
        ];
        if (args.decisions) {
          lines.push('## Keputusan Penting', `${args.decisions}`, '');
        }
        if (args.errors) {
          lines.push('## Error dan Fix', `${args.errors}`, '');
        }

        fs.writeFileSync(filepath, lines.join('\n'), 'utf8');
        sidixReindexFireAndForget();
        return {
          content: [
            {
              type: 'text',
              text: `Sesi direkam: research_notes/${filename}`,
            },
          ],
        };
      }

      case 'sidix_status': {
        try {
          const res = await fetch(`${BRAIN_QA_URL}/health`);
          const data = await res.json();
          return {
            content: [
              {
                type: 'text',
                text: [
                  'SIDIX Status',
                  `Online: ${data.status === 'ok' ? 'Ya' : 'Tidak'}`,
                  `Corpus: ${data.corpus_doc_count ?? '-'} dokumen`,
                  `Model: ${data.model_mode ?? '-'} (ready: ${String(data.model_ready)})`,
                  `Tools: ${data.tools_available ?? '-'}`,
                  `URL: ${BRAIN_QA_URL}`,
                ].join('\n'),
              },
            ],
          };
        } catch (_err) {
          return {
            content: [
              {
                type: 'text',
                text: `SIDIX offline: tidak bisa menghubungi ${BRAIN_QA_URL}`,
              },
            ],
          };
        }
      }

      default:
        throw new Error(`Tool tidak dikenal: ${name}`);
    }
  } catch (err) {
    return {
      content: [{ type: 'text', text: `Error: ${err.message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error(
  `SIDIX Socio MCP running | core=${CORE_TOOLS.length} social=${SOCIAL_TOOLS.length} | ${BRAIN_QA_URL}`,
);
