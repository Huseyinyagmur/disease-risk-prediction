// @screenshots: faz raporu için ekran görüntüleri (sentetik profiller, açık PhysioNet örnek EKG). Phase XLVII: sihirbaz akışı;
// masaüstü (1440), tablet (768) ve mobil (375) genişlikleri. Çıktı: SHOTS_DIR (varsayılan phase_xlvii/screenshots).
import { expect, test, type Page } from '@playwright/test';
import { expectPanel, gotoStep, loadEcgSample, loadProfile, mainNav, openEcg, openForm, runEcg, submit } from './helpers';

const DIR = process.env.SHOTS_DIR ?? '../../phase_xlvii/screenshots';
const shot = (page: Page, name: string, fullPage = true) => page.screenshot({ path: `${DIR}/${name}.png`, fullPage });

test.describe('@screenshots', () => {
  test('masaüstü (1440 px)', async ({ page }) => {
    test.setTimeout(240_000);
    await page.goto('/');
    await expect(page.getByTestId('start')).toBeVisible();
    await shot(page, 'desktop_01_giris');

    await page.getByTestId('start').click();
    await expect(page.getByTestId('analysis-select')).toBeVisible();
    await page.getByTestId('group-deneysel').locator('summary').click();
    await page.getByTestId('select-liver_fibrosis').check();
    await page.getByTestId('select-af').check();
    await page.getByTestId('select-osteoporosis').check();
    await shot(page, 'desktop_02_analiz_secimi');

    await loadProfile(page, 'fibrosis_ready');
    await page.getByTestId('wizard-next').click();
    await expectPanel(page, 'fibrosis_final', 'READY');
    await shot(page, 'desktop_03_temel_bilgiler');

    await gotoStep(page, 'oyku');
    await page.getByTestId('tech-btn-glucocorticoid_ge1month').click();
    await expect(page.getByTestId('tech-glucocorticoid_ge1month')).toContainText('OSQ130');
    await shot(page, 'desktop_04_oyku_teknik_ayrinti');

    await gotoStep(page, 'laboratuvar');
    await page.locator('#f-albumin_gdl').fill('42');
    await expect(page.getByTestId('err-albumin_gdl')).toBeVisible();
    await expectPanel(page, 'fibrosis_final', 'MISSING');
    await shot(page, 'desktop_05_tahlil_birim_hatasi');
    await page.getByTestId('unit-albumin_gdl').selectOption('g/L');
    await expectPanel(page, 'fibrosis_final', 'READY');

    await gotoStep(page, 'review');
    await shot(page, 'desktop_06_kontrol_ve_hesaplama');

    await submit(page);
    await shot(page, 'desktop_07_sonuclar');
    const card = page.getByTestId('result-fibrosis_final');
    await card.getByTestId('metrics').locator('summary').click();
    await card.getByTestId('tech-details').locator('summary').click();
    await card.scrollIntoViewIfNeeded();
    await card.screenshot({ path: `${DIR}/desktop_08_sonuc_karti_ayrintilar.png` });

    await openForm(page);
    await loadProfile(page, 'out_of_scope');
    await expectPanel(page, 'fibrosis_final', 'OUT_OF_SCOPE');
    await shot(page, 'desktop_09_panel_uygun_degil', false);

    await openEcg(page);
    await loadEcgSample(page, '00691');
    await runEcg(page);
    await expect(page.getByTestId('ecg-trace')).toBeVisible();
    await shot(page, 'desktop_10_ekg_af_ornegi');

    await mainNav(page).getByRole('button', { name: 'Model kartları', exact: true }).click();
    await expect(page.getByTestId('card-fibrosis_final')).toBeVisible();
    await shot(page, 'desktop_11_model_kartlari');

    await mainNav(page).getByRole('button', { name: 'Hakkında', exact: true }).click();
    await expect(page.getByTestId('glossary')).toBeVisible();
    await shot(page, 'desktop_12_hakkinda_terimler');
  });

  for (const [tag, width, height] of [['tablet768', 768, 1024], ['mobile375', 375, 812]] as const) {
    test(`${tag} (${width} px)`, async ({ page }) => {
      test.setTimeout(240_000);
      await page.setViewportSize({ width, height });
      await page.goto('/');
      await shot(page, `${tag}_01_giris`);
      await page.getByTestId('start').click();
      await page.getByTestId('select-all').click();
      await shot(page, `${tag}_02_analiz_secimi`);
      await loadProfile(page, 'fibrosis_ready');
      await page.getByTestId('wizard-next').click();
      await expect(page.getByTestId('section-temel')).toBeVisible();
      await expectPanel(page, 'fibrosis_final', 'READY');
      await shot(page, `${tag}_03_temel_bilgiler`);
      await gotoStep(page, 'laboratuvar');
      await shot(page, `${tag}_04_tahlil`);
      await gotoStep(page, 'review');
      await shot(page, `${tag}_05_kontrol`);
      await submit(page);
      await shot(page, `${tag}_06_sonuclar`);
      await openEcg(page);
      await loadEcgSample(page, '00165');
      await runEcg(page);
      await shot(page, `${tag}_07_ekg`);
    });
  }
});
