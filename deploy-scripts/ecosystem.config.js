module.exports = {
  apps: [
    {
      name: 'sidix-backend-prod',
      script: 'python',
      args: '-m brain_qa serve',
      cwd: './apps/brain_qa',
      interpreter: 'python3',
      env: {
        NODE_ENV: 'production',
        SIDIX_TYPO_PIPELINE: '1',
        BRAIN_QA_PORT: '8765'
      }
    },
    {
      name: 'sidix-mcp-prod',
      script: 'node',
      args: './src/index.js',
      cwd: './apps/sidix-mcp',
      autorestart: false, // Default OFF per user request
      watch: false,
      env: {
        NODE_ENV: 'production',
        SIDIX_MCP_ENABLED: 'false'
      }
    },
    {
      name: 'sidix-dashboard',
      script: 'npm',
      args: 'run start',
      cwd: './jariyah-hub',
      env: {
        NODE_ENV: 'production',
        PORT: '4000'
      }
    },
    {
      name: 'sidix-health',
      script: './deploy-scripts/health-check.sh',
      interpreter: 'bash',
      cron_restart: '*/15 * * * *', // Run every 15 mins
      autorestart: false
    }
  ]
};
