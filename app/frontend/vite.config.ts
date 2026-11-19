/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend (app/backend/run_server.py) yalnız 127.0.0.1'de çalışır. Arayüz isteklerini /api önekiyle aynı kökenden
// gönderir; Vite vekili öneki kaldırıp backend'e iletir (CORS gerekmez). Port HEALTHRISK_API_PORT ile değiştirilebilir.
const apiPort = process.env.HEALTHRISK_API_PORT ?? '8000';
const proxy = {
  '/api': {
    target: `http://127.0.0.1:${apiPort}`,
    changeOrigin: false,
    rewrite: (p: string) => p.replace(/^\/api/, ''),
  },
};

export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true, proxy },
  build: { sourcemap: false },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,
  },
});
