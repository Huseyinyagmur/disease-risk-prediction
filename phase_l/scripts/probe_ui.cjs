// Phase L: arayüz yoklaması (madde 5: temiz oturum + boş form + tüm analizler seçili; asistan paneli görüntüsü).
// Kullanım (app/frontend içinden):  node ../../phase_l/scripts/probe_ui.cjs <çıktı_klasörü> [before|after]
// Önkoşul: backend 127.0.0.1:8000, vite preview 127.0.0.1:4173. Sentetik/boş girdi; veri saklanmaz.
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require(path.resolve(process.cwd(), 'node_modules/@playwright/test'));

const OUT = path.resolve(process.argv[2]);
const TAG = process.argv[3] ?? 'before';
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const log = {};
  for (const [vp, w, h] of [['desktop', 1440, 900], ['tablet768', 768, 1024]]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, locale: 'tr-TR' }); // yeni bağlam = temiz localStorage
    const page = await ctx.newPage();
    await page.goto('http://127.0.0.1:4173/');
    log[`${vp}_localStorage_keys`] = await page.evaluate(() => Object.keys(localStorage));
    await page.getByTestId('start').click();
    await page.getByTestId('analysis-select').waitFor();
    if (vp === 'desktop') await page.screenshot({ path: `${OUT}/${vp}_p01_ilk_acilis_secim.png`, fullPage: true });
    // Tüm analizleri seç (varsa "Tümü"); boş form.
    const allBtn = page.getByTestId('select-all');
    if ((await allBtn.getAttribute('aria-pressed')) !== 'true') await allBtn.click();
    const states = [];
    for (const ms of [0, 150, 1500]) {
      await page.waitForTimeout(ms);
      const items = await page.locator('[data-testid^="panel-"][data-state]').evaluateAll((els) =>
        els.map((e) => `${e.getAttribute('data-testid').replace('panel-', '')}=${e.getAttribute('data-state')}`));
      states.push({ after_ms: ms, items });
    }
    log[`${vp}_empty_all_selected_panel`] = states;
    await page.screenshot({ path: `${OUT}/${vp}_p02_bos_form_tumu_secili.png`, fullPage: true });
    // Asistan paneli (soru sormadan)
    await page.getByTestId('assistant-open').click();
    await page.getByTestId('assistant-panel').waitFor();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${OUT}/${vp}_p03_asistan_paneli.png`, fullPage: false });
    await ctx.close();
  }
  fs.writeFileSync(`${OUT}/probe_${TAG}.json`, JSON.stringify(log, null, 1));
  console.log(JSON.stringify(log, null, 1));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
