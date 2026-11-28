// @mobil: yerleşim denetimi — 375 / 768 / 1440 px'te yatay taşma yok; "Sonuçları hesapla" çubuğu hiçbir form alanının
// üstüne binmez (sabit/sticky değil, form sonunda); dokunma hedefleri ekran içinde.
import { expect, test, type Page } from '@playwright/test';
import { gotoStep, loadProfile, mainNav, submit } from './helpers';

const SIZES = [
  [375, 812],
  [768, 1024],
  [1440, 900],
] as const;

async function noHorizontalOverflow(page: Page, where: string) {
  const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth }));
  expect(r.sw, `${where}: scrollWidth ${r.sw} > innerWidth ${r.iw}`).toBeLessThanOrEqual(r.iw);
}

/** Hesapla çubuğu ile her görünür alanın sınır kutuları kesişmemeli; çubuk konumu sabit/sticky olmamalı.
 * Sayfa en alta ve en üste kaydırılarak iki kez ölçülür (sticky çubuk kaydırınca alanların üstüne biner). */
async function barDoesNotOverlap(page: Page, where: string) {
  const bar = page.getByTestId('wizard-bar');
  await expect(bar).toBeVisible();
  const pos = await bar.evaluate((e) => getComputedStyle(e).position);
  expect(pos, where).not.toMatch(/sticky|fixed/);
  for (const y of [0, 1e6]) {
    await page.evaluate((yy) => window.scrollTo(0, yy), y);
    const overlaps = await page.evaluate(() => {
      const b = document.querySelector('[data-testid="wizard-bar"]')!.getBoundingClientRect();
      return [...document.querySelectorAll('[data-testid^="field-"]')]
        .filter((f) => {
          const r = f.getBoundingClientRect();
          return r.width > 0 && !(r.bottom <= b.top || r.top >= b.bottom || r.right <= b.left || r.left >= b.right);
        })
        .map((f) => f.getAttribute('data-testid'));
    });
    expect(overlaps, `${where} (scroll ${y})`).toEqual([]);
  }
  const sub = page.getByTestId('submit');
  if (await sub.count()) {
    const box = (await sub.boundingBox())!;
    const vw = page.viewportSize()!.width;
    expect(box.x >= 0 && box.x + box.width <= vw, `${where}: buton ekran dışında`).toBe(true);
    expect(box.height, `${where}: dokunma hedefi`).toBeGreaterThanOrEqual(32);
  }
}

test.describe('@mobil yerleşim', () => {
  for (const [w, h] of SIZES) {
    test(`${w}px: tüm adımlar, sonuçlar, EKG, kartlar, hakkında`, async ({ page }) => {
      test.setTimeout(180_000);
      await page.setViewportSize({ width: w, height: h });
      await page.goto('/');
      await noHorizontalOverflow(page, `${w} giriş`);
      await page.getByTestId('start').click();
      await expect(page.getByTestId('analysis-select')).toBeVisible();
      await noHorizontalOverflow(page, `${w} seçim`);
      await barDoesNotOverlap(page, `${w} seçim`);
      await page.getByTestId('select-all').click(); // Phase L: varsayılan 3 analiz; tüm adımlar için Tümü
      await loadProfile(page, 'fibrosis_ready');
      for (const s of ['temel', 'olcumler', 'oyku', 'laboratuvar', 'klinik', 'review']) {
        await gotoStep(page, s);
        await noHorizontalOverflow(page, `${w} ${s}`);
        await barDoesNotOverlap(page, `${w} ${s}`);
      }
      await submit(page);
      await noHorizontalOverflow(page, `${w} sonuçlar`);
      for (const name of ['EKG ile AF', 'Model kartları', 'Hakkında']) {
        await mainNav(page).getByRole('button', { name, exact: true }).click();
        await noHorizontalOverflow(page, `${w} ${name}`);
      }
      // Phase L2: asistan — ≥ 1024 px sağ çekmece (karartma; içerik DARALMAZ, en çok 2 sütun), genişletilmiş ortada ≤ 860 px;
      // altında tam ekran
      await mainNav(page).getByRole('button', { name: 'Sonuçlar', exact: true }).click();
      await page.getByTestId('assistant-open').click();
      const panel = page.getByTestId('assistant-panel');
      await expect(panel).toHaveAttribute('data-layout', w >= 1024 ? 'drawer' : 'fullscreen');
      const pb = (await panel.boundingBox())!;
      if (w >= 1024) {
        expect(pb.height).toBeGreaterThanOrEqual(h - 1);
        expect(pb.width).toBeLessThanOrEqual(461);
        await expect(page.getByTestId('assistant-backdrop')).toBeVisible();
        await expect(page.getByTestId('disclaimer')).toBeInViewport();
        await page.getByTestId('assistant-expand').click();
        await expect(panel).toHaveAttribute('data-layout', 'centered');
        const cb = (await panel.boundingBox())!;
        expect(cb.width).toBeLessThanOrEqual(861);
        expect(Math.abs(cb.x + cb.width / 2 - w / 2)).toBeLessThan(2); // ortalanmış
        const bubble = page.getByTestId('assistant-examples');
        expect((await bubble.boundingBox())!.width).toBeLessThanOrEqual(681); // satır uzunluğu ≤ 680 px
        await page.getByTestId('assistant-expand').click();
      } else {
        expect(pb.x).toBe(0);
        expect(Math.round(pb.width)).toBe(w);
      }
      await noHorizontalOverflow(page, `${w} asistan`);
      await page.getByTestId('assistant-close').click();
    });
  }
});
