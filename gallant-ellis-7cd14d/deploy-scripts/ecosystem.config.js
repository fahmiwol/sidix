module.exports = {
  apps: [
    {
      name: 'sidix-brain',
      script: './start_brain.sh',
      cwd: '/opt/sidix',
      interpreter: 'bash',
      env: {
        SIDIX_TYPO_PIPELINE: '1',
        // Sprint 25: Hybrid BM25+Dense retrieval (LIVE 2026-04-28, +6.0% Hit@5)
        SIDIX_HYBRID_RETRIEVAL: '1',
        // Sprint 27c: rerank OFF — MiniLM regressed -2% Hit@5 vs hybrid on
        // Indonesian paraphrase queries (English-bias). Note 271 detail.
        // Code/model selection retained for future GPU/quantized rerank iteration.
        SIDIX_RERANK: '0',
        SIDIX_RERANK_MODEL: 'ms-marco-minilm'
      }
    },
    {
      name: 'sidix-ui',
      script: '/usr/bin/serve',
      args: 'dist -p 4000',
      cwd: '/opt/sidix/SIDIX_USER_UI',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'sidix-mcp-prod',
      script: 'node',
      args: './src/index.js',
      cwd: '/opt/sidix/apps/sidix-mcp',
      autorestart: false,
      env: {
        SIDIX_MCP_ENABLED: 'false'
      }
    },
    {
      name: 'sidix-health-prod',
      script: './deploy-scripts/health-check.sh',
      cwd: '/opt/sidix',
      interpreter: 'bash',
      cron_restart: '*/15 * * * *',
      autorestart: false
    }
  ]
};
