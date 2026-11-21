// @a11y: axe-core denetimi (WCAG 2.0/2.1 A+AA kuralları) ve klavye ile gezinme. Kritik (critical) ve ciddi (serious)
// ihlal 0 olmalı; tüm ihlaller (orta/küçük dahil) AXE_OUT dosyasına yazılır.
import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { gotoStep, loadEcgSample, loadProfile, mainNav, openEcg, runEcg, submit } from './helpers';

const OUT = process.env.AXE_OUT ?? '../../phase_xlvii/results/axe_results.json';
const rows: { screen: string; viewport: string; violations: { id: string; impact: string | null; nodes: number; help: string; targets: string[] }[] }[] = [];

async function audit(page: Page, screen: string) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  const vp = page.viewportSize();
  rows.push({
    screen,
    viewport: `${vp?.width}x${vp?.height}`,
    violations: r.violations.map((v) => ({
      id: v.id, impact: v.impact ?? null, nodes: v.nodes.length, help: v.help, targets: v.nodes.slice(0, 5).map((n) => n.target.join(' ')),
    })),
  });
  const bad = r.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious');
  expect(bad.map((v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(' ')).slice(0, 3).join(' | ')}`), screen).toEqual([]);
}

test.describe('@a11y erişilebilirlik', () => {
  test.afterAll(() => {
    mkdirSync(path.dirname(OUT), { recursive: true });
    const summary = rows.reduce<Record<string, number>>((acc, r) => {
      for (const v of r.violations) acc[v.impact ?? 'unknown'] = (acc[v.impact ?? 'unknown'] ?? 0) + 1;
      return acc;
    }, {});
    writeFileSync(OUT, JSON.stringify({ tool: '@axe-core/playwright 4.11.3', tags: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'], summary, screens: rows }, null, 1));
  });

  for (const [w, h] of [[1440, 900], [375, 812]] as const) {
    test(`axe: tüm ekranlar (${w}px)`, async ({ page }) => {
      test.setTimeout(240_000);
      await page.setViewportSize({ width: w, height: h });
      await page.goto('/');
      await audit(page, 'giris');
      await page.getByTestId('start').click();
      await page.getByTestId('group-deneysel').locator('summary').click();
      await audit(page, 'analiz_secimi');
      await loadProfile(page, 'fibrosis_ready');
      for (const s of ['temel', 'olcumler', 'oyku', 'laboratuvar', 'klinik', 'review']) {
        await gotoStep(page, s);
        if (s === 'oyku') await page.getByTestId('tech-btn-family_hx_diabetes').click();
        if (s === 'laboratuvar') await page.locator('#f-albumin_gdl').fill('42'); // hata durumu da denetlenir
        if (s === 'laboratuvar') await expect(page.getByTestId('err-albumin_gdl')).toBeVisible();
        await audit(page, `form_${s}`);
        if (s === 'laboratuvar') await page.locator('#f-albumin_gdl').fill('4,2');
      }
      await submit(page);
      for (const c of await page.locator('[data-testid^="result-"] [data-testid="metrics"] summary').all()) await c.click();
      await audit(page, 'sonuclar_metrikler_acik');
      await openEcg(page);
      await loadEcgSample(page, '00165');
      await runEcg(page);
      await audit(page, 'ekg_sonuc');
      await mainNav(page).getByRole('button', { name: 'Model kartları', exact: true }).click();
      await audit(page, 'model_kartlari');
      await mainNav(page).getByRole('button', { name: 'Hakkında', exact: true }).click();
      await audit(page, 'hakkinda');
    });
  }

  test('klavye: analiz seçimi → İleri → odak adım başlığında → alan doldurma → Geri; görünür odak', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('start').click();
    await expect(page.getByTestId('analysis-select')).toBeVisible();
    const focused = () => page.evaluate(() => document.activeElement?.getAttribute('data-testid') ?? document.activeElement?.id ?? '');
    const tabTo = async (target: string, max = 60) => {
      for (let i = 0; i < max; i++) {
        if ((await focused()) === target) return;
        await page.keyboard.press('Tab');
      }
      throw new Error(`Tab ile ${target} odaklanamadı (son: ${await focused()})`);
    };
    await tabTo('select-liver_fibrosis');
    await page.keyboard.press('Space');
    await expect(page.getByTestId('select-liver_fibrosis')).toBeChecked();
    // odak halkası görünür (outline veya box-shadow)
    const ring = await page.evaluate(() => {
      const s = getComputedStyle(document.activeElement!);
      return s.outlineStyle !== 'none' || s.boxShadow !== 'none';
    });
    expect(ring).toBe(true);
    await tabTo('wizard-next');
    await page.keyboard.press('Enter');
    await expect(page.getByTestId('step-title')).toBeFocused();
    await expect(page.getByTestId('step-title')).toHaveText(/Temel bilgiler/);
    await tabTo('tech-btn-age_years');
    await page.keyboard.press('Enter');
    await expect(page.getByTestId('tech-age_years')).toBeVisible();
    await page.keyboard.press('Tab');
    expect(await focused()).toBe('f-age_years');
    await page.keyboard.type('58');
    await tabTo('wizard-back');
    await page.keyboard.press('Enter');
    await expect(page.getByTestId('analysis-select')).toBeVisible();
    await tabTo('wizard-next');
    await page.keyboard.press('Enter');
    await expect(page.locator('#f-age_years')).toHaveValue('58');
  });
});
