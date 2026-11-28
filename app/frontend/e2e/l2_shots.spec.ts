// @l2shots: Phase L2 önce/sonra ekran görüntüleri — masaüstü 1440/1920, tablet 768, mobil 390; asistan kapalı/açık/
// genişletilmiş (masaüstü), sonuç ekranı, EKG sayfası. Çıktı: SHOTS_DIR (varsayılan phase_l2/screenshots/after).
// Profiller sentetiktir; EKG örneği açık PhysioNet kaydıdır. Sohbet görüntüsü yalnız 1440'ta ve asistan etkinse alınır.
import { expect, test, type Page } from '@playwright/test';
import { expectPanel, loadEcgSample, loadProfile, openEcg, runEcg, submit } from './helpers';

const DIR = process.env.SHOTS_DIR ?? '../../phase_l2/screenshots/after';
const shot = (page: Page, name: string, fullPage = false) => page.screenshot({ path: `${DIR}/${name}.png`, fullPage });

async function assistantEnabled(page: Page) {
  const r = await page.request.get('/api/health');
  return !!((await r.json()) as { assistant?: { enabled: boolean } }).assistant?.enabled;
}

const SIZES = [['d1440', 1440, 900], ['d1920', 1920, 1080], ['t768', 768, 1024], ['m390', 390, 844]] as const;

test.describe('@l2shots', () => {
  for (const [tag, w, h] of SIZES) {
    test(`${tag} (${w}px)`, async ({ page }) => {
      test.setTimeout(240_000);
      await page.setViewportSize({ width: w, height: h });
      await page.goto('/');
      await page.getByTestId('start').click();
      await expect(page.getByTestId('analysis-select')).toBeVisible();
      await page.waitForTimeout(1200); // boş form: canlı panelin ilk durumu
      await shot(page, `${tag}_01_bos_form_secim`);
      await loadProfile(page, 'missing');
      await page.getByTestId('wizard-next').click();
      await expect(page.getByTestId('section-temel')).toBeVisible();
      await page.waitForTimeout(800);
      await shot(page, `${tag}_02_form_temel_eksik_profil`);
      // asistan açık (form üstünde)
      await page.getByTestId('assistant-open').click();
      await expect(page.getByTestId('assistant-panel')).toBeVisible();
      await page.waitForTimeout(500);
      await shot(page, `${tag}_03_asistan_acik`);
      const expand = page.getByTestId('assistant-expand');
      if (await expand.isVisible()) {
        await expand.click();
        await page.waitForTimeout(300);
        await shot(page, `${tag}_04_asistan_genis`);
        await expand.click();
      }
      if (tag === 'd1440' && (await assistantEnabled(page))) {
        await page.getByTestId('assistant-input').fill('Eşik üstü ne demek?');
        await page.getByTestId('assistant-send').click();
        await expect(page.getByTestId('assistant-msg-bot')).toBeVisible({ timeout: 120_000 });
        await shot(page, `${tag}_05_asistan_sohbet`);
      }
      await page.getByTestId('assistant-close').click();
      // sonuçlar (fibrozis için hazır profil)
      await loadProfileFresh(page);
      await submit(page);
      await shot(page, `${tag}_06_sonuclar`, true);
      // EKG
      await openEcg(page);
      await shot(page, `${tag}_07_ekg_bos`);
      await loadEcgSample(page, '00691');
      await runEcg(page);
      await shot(page, `${tag}_08_ekg_sonuc`, true);
    });
  }
});

async function loadProfileFresh(page: Page) {
  await page.getByRole('navigation', { name: 'Ana gezinme' }).getByRole('button', { name: 'Veri girişi', exact: true }).click();
  await loadProfile(page, 'fibrosis_ready');
  await expectPanel(page, 'fibrosis_final', 'READY');
}
