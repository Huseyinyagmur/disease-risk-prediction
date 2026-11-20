// Phase XLVI — Görev 4: app/docs/architecture.md içindeki ```mermaid bloklarını SVG ve PNG'ye çevirir.
// Diyagramlar elle çizilmez; kaynak yalnız architecture.md'dir. Tarayıcı: app/frontend Playwright Chromium'u (yerel, çevrimdışı).
// Kullanım: node phase_xlvi/scripts/render_diagrams.mjs <mermaid.min.js yolu>
// Çıktı: app/docs/img/0N_<ad>.svg ve .png (+ results/diagram_manifest.json: SHA256, mermaid sürümü ve dosya SHA'sı)
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const V2 = resolve(HERE, '..', '..');
const require = createRequire(join(V2, 'app', 'frontend', 'package.json'));
const { chromium } = require('@playwright/test');

const mermaidPath = process.argv[2];
if (!mermaidPath) throw new Error('mermaid.min.js yolu verilmedi');
const mermaidJs = readFileSync(mermaidPath, 'utf8');
const md = readFileSync(join(V2, 'app', 'docs', 'architecture.md'), 'utf8');
const blocks = [...md.matchAll(/```mermaid\n([\s\S]*?)```/g)].map((m) => m[1]);
const names = ['01_components', '02_startup', '03_routing', '04_af_path'];
if (blocks.length !== names.length) throw new Error(`beklenen ${names.length} blok, bulunan ${blocks.length}`);
const out = join(V2, 'app', 'docs', 'img');
mkdirSync(out, { recursive: true });
const sha = (b) => createHash('sha256').update(b).digest('hex');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 2 });
await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#fff"><div id="c"></div></body></html>');
await page.addScriptTag({ content: mermaidJs });
const version = await page.evaluate(() => {
  // eslint-disable-next-line no-undef
  mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'strict', flowchart: { htmlLabels: true }, fontFamily: 'Segoe UI, Arial, sans-serif' });
  // eslint-disable-next-line no-undef
  return mermaid.version ?? 'bilinmiyor';
});
const pkgVersion = JSON.parse(readFileSync(join(dirname(mermaidPath), '..', 'package.json'), 'utf8')).version;
const manifest = { mermaid_version: typeof version === 'string' && version !== 'bilinmiyor' ? version : pkgVersion, mermaid_js_sha256: sha(mermaidJs), source: 'app/docs/architecture.md', files: {} };
for (let i = 0; i < blocks.length; i++) {
  const svg = await page.evaluate(async ([id, code]) => {
    // eslint-disable-next-line no-undef
    const { svg } = await mermaid.render(id, code);
    document.getElementById('c').innerHTML = svg;
    return svg;
  }, [`d${i}`, blocks[i]]);
  const svgPath = join(out, `${names[i]}.svg`);
  writeFileSync(svgPath, svg, 'utf8');
  const el = await page.$('#c svg');
  const pngPath = join(out, `${names[i]}.png`);
  await el.screenshot({ path: pngPath, omitBackground: false });
  manifest.files[names[i]] = { block_sha256: sha(blocks[i]), svg_sha256: sha(readFileSync(svgPath)), png_sha256: sha(readFileSync(pngPath)) };
  console.log('yazıldı', names[i]);
}
await browser.close();
writeFileSync(join(V2, 'phase_xlvi', 'results', 'diagram_manifest.json'), JSON.stringify(manifest, null, 1), 'utf8');
