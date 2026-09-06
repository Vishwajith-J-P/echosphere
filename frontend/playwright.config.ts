import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false, timeout: 45000,
  use: { baseURL: 'http://127.0.0.1:3100', headless: true, screenshot: 'only-on-failure' },
  webServer: [
    { command: 'conda run --no-capture-output -n echosphere python tests/browser_server.py', cwd: '../backend', url: 'http://127.0.0.1:8100/api/health/live', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev -- --host 127.0.0.1 --port 3100', url: 'http://127.0.0.1:3100', env: { ECHOSPHERE_API_PROXY: 'http://127.0.0.1:8100' }, reuseExistingServer: false },
  ],
});
