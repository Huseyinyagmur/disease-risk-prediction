// Phase L madde 5 ek yoklama: profil yükle -> READY -> "Formu temizle"; panelde eski (READY) durumun kalıp kalmadığı.
// Kullanım (app/frontend içinden): node ../../phase_l/scripts/probe_stale.cjs <çıktı_json>
const path = require('node:path'); const fs = require('node:fs');
const { chromium } = require(path.resolve(process.cwd(), 'node_modules/@playwright/test'));
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
  await p.goto('http://127.0.0.1:4173/'); await p.getByTestId('start').click();
  const all = p.getByTestId('select-all'); if ((await all.getAttribute('aria-pressed')) !== 'true') await all.click();
  await p.getByTestId('profile-fibrosis_ready').click();
  await p.locator('[data-testid="panel-fibrosis_final"][data-state="READY"]').waitFor();
  const st = async () => p.locator('[data-testid="panel-fibrosis_final"], [data-testid="panel-osteo_final"]').evaluateAll((els) => els.map((e) => `${e.dataset.testid}=${e.dataset.state}`));
  await p.getByTestId('clear-form').click();
  const out = [];
  for (const ms of [0, 50, 100, 200, 400, 1500]) { await p.waitForTimeout(ms === 0 ? 0 : ms - (out.at(-1)?.t ?? 0)); out.push({ t: ms, s: await st() }); }
  fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 1)); console.log(JSON.stringify(out)); await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
