module.exports = {
  apps: [
    {
      name: 'sidix-brain',
      script: './start_brain.sh',
      cwd: '/opt/sidix',
      interpreter: 'bash',
      env: {
        SIDIX_TYPO_PIPELINE: '1',
        // Sprint 25 Hybrid Retrieval (2026-04-28) — flip to '1' after index rebuild
        SIDIX_HYBRID_RETRIEVAL: '0',
        SIDIX_RERANK: '0'
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
