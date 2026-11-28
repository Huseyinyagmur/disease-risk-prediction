// @screenshots: faz raporu için ekran görüntüleri (sentetik profiller, açık PhysioNet örnek EKG). Phase XLVII: sihirbaz akışı;
// masaüstü (1440), tablet (768) ve mobil (375) genişlikleri. Çıktı: SHOTS_DIR (varsayılan phase_l2/results/suite_shots; Phase L'de güncellendi).
import { expect, test, type Page } from '@playwright/test';
import { expectPanel, gotoStep, loadEcgSample, loadProfile, mainNav, openEcg, openForm, runEcg, submit } from './helpers';

const DIR = process.env.SHOTS_DIR ?? '../../phase_l2/results/suite_shots'; // Phase L2
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

  // Phase L: yeni öğeler (varsayılan seçim, özet şeridi, yan asistan paneli, EKG örnek kayıtları ve süre göstergesi).
  test('Phase L ek görüntüler (masaüstü + tablet)', async ({ page }) => {
    test.setTimeout(240_000);
    await page.goto('/');
    await page.getByTestId('start').click();
    await expect(page.getByTestId('selected-count')).toContainText('3 analiz');
    await loadProfile(page, 'fibrosis_ready');
    await page.getByTestId('wizard-next').click();
    await expectPanel(page, 'fibrosis_final', 'READY');
    await gotoStep(page, 'review');
    await shot(page, 'L_desktop_01_kontrol_atlanan_adimlar');
    await submit(page);
    await page.getByTestId('results-summary').screenshot({ path: `${DIR}/L_desktop_02_ozet_seridi.png` });
    await shot(page, 'L_desktop_03_sonuclar_varsayilan_secim');
    await page.getByTestId('assistant-open').click();
    await expect(page.getByTestId('assistant-panel')).toHaveAttribute('data-layout', 'drawer'); // Phase L2: çekmece
    await expect(page.getByTestId('assistant-examples')).toHaveAttribute('data-from-results', 'true');
    await shot(page, 'L_desktop_04_asistan_yan_panel', false);
    await page.getByTestId('assistant-expand').click();
    await shot(page, 'L_desktop_05_asistan_genis', false);
    await page.getByTestId('assistant-close').click();
    // tablet (768): openEcg sayfayı yeniden yüklediği için (oturum yalnız bellekte) sonuçlar EKG'den ÖNCE çekilir
    await page.setViewportSize({ width: 768, height: 1024 });
    await shot(page, 'L_tablet768_01_sonuclar');
    await page.getByTestId('assistant-open').click();
    await expect(page.getByTestId('assistant-panel')).toHaveAttribute('data-layout', 'fullscreen');
    await shot(page, 'L_tablet768_02_asistan_tam_ekran', false);
    await page.getByTestId('assistant-close').click();
    await page.setViewportSize({ width: 1440, height: 900 });
    await openEcg(page);
    await shot(page, 'L_desktop_06_ekg_ornek_kayitlar', false);
    await loadEcgSample(page, '00691');
    await page.getByTestId('ecg-run').click();
    await expect(page.getByTestId('ecg-wait')).toBeVisible();
    await page.getByTestId('ecg-progress').screenshot({ path: `${DIR}/L_desktop_07_ekg_sure_gostergesi.png` });
    await expect(page.getByTestId('result-af_S4_DEVICE')).toBeVisible({ timeout: 90_000 });
    await page.getByTestId('result-af_S4_DEVICE').screenshot({ path: `${DIR}/L_desktop_08_af_karti.png` });

  });
});
