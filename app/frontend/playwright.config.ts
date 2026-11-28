import { defineConfig, devices } from '@playwright/test';

// Önkoşul: backend 127.0.0.1:8000'de çalışıyor olmalı (app/backend/run_server.py). Testler üretim derlemesine karşı koşar: önce
// "npm run build"; vite preview çalışmıyorsa başlatılır.
// Sonuç dosyaları faz klasörüne yazılır (PW_OUT ile değiştirilebilir). AF testleri Octave çalıştırdığı için seri koşar
// (backend aynı anda tek EKG işler).
const OUT = process.env.PW_OUT ?? '../../phase_l/results/playwright';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [
    ['list'],
    ['json', { outputFile: `${OUT}/playwright_results.json` }],
    ['junit', { outputFile: `${OUT}/playwright_junit.xml` }],
  ],
  outputDir: `${OUT}/playwright_artifacts`,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'off',
    screenshot: 'only-on-failure',
    locale: 'tr-TR',
    viewport: { width: 1440, height: 900 },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } }],
  webServer: {
    command: 'npx vite preview --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
