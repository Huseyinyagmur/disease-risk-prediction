// @screenshots: faz raporu için ekran görüntüleri (sentetik profiller, açık PhysioNet örnek EKG).
import { expect, test } from '@playwright/test';
import { expectPanel, loadEcgSample, loadProfile, openEcg, openForm, runEcg, submit } from './helpers';

const DIR = process.env.SHOTS_DIR ?? '../../phase_xlv/screenshots';
const shot = (name: string) => ({ path: `${DIR}/${name}.png`, fullPage: true });

test.describe('@screenshots', () => {
  test('ekranlar', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('start')).toBeVisible();
    await page.screenshot(shot('01_giris'));

    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'fibrosis_final', 'READY');
    await page.screenshot(shot('02_veri_girisi_fibrozis_calisabilir'));

    await loadProfile(page, 'missing');
    await expectPanel(page, 'fibrosis_final', 'MISSING');
    await page.screenshot({ path: `${DIR}/03_panel_eksik.png` });

    await loadProfile(page, 'out_of_scope');
    await expectPanel(page, 'fibrosis_final', 'OUT_OF_SCOPE');
    await page.screenshot({ path: `${DIR}/04_panel_kapsam_disi.png` });

    await loadProfile(page, 'unit_error');
    await expect(page.getByTestId('err-glucose_serum_mgdl')).toBeVisible();
    await page.getByTestId('section-laboratuvar').scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${DIR}/05_birim_hatasi.png` });

    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'fibrosis_final', 'READY');
    await submit(page);
    await page.screenshot(shot('06_sonuclar'));

    await openEcg(page);
    await loadEcgSample(page, '00691');
    await runEcg(page);
    await expect(page.getByTestId('ecg-trace')).toBeVisible();
    await page.screenshot(shot('07_ekg_af_ornegi'));

    await loadEcgSample(page, '00165');
    await runEcg(page);
    await expect(page.getByTestId('rr-tachogram')).toBeVisible();
    await page.screenshot(shot('08_ekg_sr_ornegi'));

    await page.getByRole('navigation').getByRole('button', { name: 'Model kartları', exact: true }).click();
    await expect(page.getByTestId('card-fibrosis_final')).toBeVisible();
    await page.screenshot(shot('09_model_kartlari'));

    await page.getByRole('navigation').getByRole('button', { name: 'Hakkında', exact: true }).click();
    await expect(page.getByTestId('about-sources')).toBeVisible();
    await page.screenshot(shot('10_hakkinda'));
  });
});
