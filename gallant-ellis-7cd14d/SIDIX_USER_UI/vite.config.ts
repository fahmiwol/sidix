import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [tailwindcss()],
    // BRAIN_QA_BASE ditentukan runtime di src/api.ts —
    // local dev = http://localhost:8765, production = same-origin (nginx proxy)
    // Jangan override di sini supaya deteksi hostname berfungsi.
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      // HMR disabled di Firebase AI Studio agar tidak flickering saat agent edit
      hmr: process.env.DISABLE_HMR !== 'true',
    },
  };
});
