module.exports = {
  apps: [
    {
      name: 'sidix-brain',
      script: './start_brain.sh',
      cwd: '/opt/sidix',
      interpreter: 'bash',
      env: {
        SIDIX_TYPO_PIPELINE: '1',
        // Sprint 25: Hybrid BM25+Dense retrieval (LIVE 2026-04-28)
        SIDIX_HYBRID_RETRIEVAL: '1',
        // Sprint 27b: MiniLM reranker (~1-2s CPU) replacing BGE-reranker-v2-m3 (22.7s)
        SIDIX_RERANK: '1',
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
