// Dört senaryo grubu (ayrı raporlanır): @normal, @eksik, @birim, @kapsam — en az fibrozis ve AF için.
// Tüm girdiler SENTETİKtir; EKG örnekleri açık PhysioNet PTB-XL kayıtlarıdır (geliştirme kümesi).
import { expect, test } from '@playwright/test';
import { expectPanel, gotoStep, loadEcgSample, loadProfile, openEcg, openForm, runEcg, sample, sampleBytes, submit } from './helpers';

test.describe('@normal normal girdi', () => {
  test('fibrozis: çalışabilir profil -> panel Çalışabilir -> sonuç OK, karar ve kanıt gösterilir', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'fibrosis_final', 'READY', 'Hesaplanabilir');
    await submit(page);
    const card = page.getByTestId('result-fibrosis_final');
    await expect(card).toHaveAttribute('data-status', 'OK');
    await expect(card.getByTestId('decision')).toContainText(/Eşik üstü — ileri değerlendirme önerilir|Eşik altı/);
    await expect(card.getByTestId('next-step')).toContainText(/FibroScan|dışlamaz/);
    await expect(card.getByTestId('metrics-table')).toBeHidden(); // varsayılan kapalı
    await card.getByTestId('metrics').locator('summary').click();
    await expect(card.getByTestId('metrics-table')).toContainText('Recall');
    await expect(card).toContainText('Hedef tanımı');
    await expect(page.locator('[data-testid^="result-dm_"]').getByTestId('target-warning')).toContainText('HbA1c');
  });

  test('fibrozis: yalnız "Karaciğer fibrozisi" seçilir -> yalnız gerekli alanlar gönderilir, panel ve sonuç yalnız fibrozis', async ({ page }) => {
    const sent: Record<string, unknown>[] = [];
    page.on('request', (r) => {
      if (r.url().endsWith('/api/predict')) sent.push((JSON.parse(r.postData() ?? '{}') as { fields: Record<string, unknown> }).fields);
    });
    await openForm(page, ['liver_fibrosis']);
    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'fibrosis_final', 'READY', 'Hesaplanabilir');
    await expect(page.locator('[data-testid^="panel-"][data-state]')).toHaveCount(1);
    await expect(page.getByTestId('step-klinik')).toHaveCount(0);
    await submit(page);
    await expect(page.locator('article[data-testid^="result-"]')).toHaveCount(1);
    await expect(page.getByTestId('result-fibrosis_final')).toHaveAttribute('data-status', 'OK');
    expect(sent).toHaveLength(1);
    expect(sent[0].fracture_hip).toBeUndefined();
    expect(sent[0].alt_ul).toBe(48);
  });

  test('AF: PTB-XL AF örneği -> OK, 10 öznitelik, lead II grafiği ve RR takogramı', async ({ page }) => {
    await openEcg(page);
    await loadEcgSample(page, '00691');
    await expect(page.getByTestId('sample-note')).toContainText('SENTETİK');
    await runEcg(page, { expectProgress: true });
    const card = page.getByTestId('result-af_S4_DEVICE');
    await expect(card).toHaveAttribute('data-status', 'OK');
    await expect(page.getByTestId('ecg-features').locator('tbody tr')).toHaveCount(10);
    await expect(page.getByTestId('ecg-trace')).toBeVisible();
    await expect(page.getByTestId('rr-tachogram')).toBeVisible();
    await expect(page.getByTestId('window-info')).toContainText('ilk 10 sn');
  });

  test('AF: PTB-XL sinüs ritmi örneği -> OK', async ({ page }) => {
    await openEcg(page);
    await loadEcgSample(page, '00165');
    await runEcg(page);
    await expect(page.getByTestId('result-af_S4_DEVICE')).toHaveAttribute('data-status', 'OK');
  });

  test('AF: dosyalar sürükle-bırak yerine dosya seçiciyle yüklenir', async ({ page }) => {
    await openEcg(page);
    await page.getByTestId('file-input').setInputFiles([sample('00165_hr.hea'), sample('00165_hr.dat')]);
    await expect(page.getByTestId('file-list')).toContainText('00165_hr.dat');
    await page.getByTestId('ecg-age').fill('45');
    await page.getByTestId('ecg-sex').selectOption('female');
    await runEcg(page);
    await expect(page.getByTestId('result-af_S4_DEVICE')).toHaveAttribute('data-status', 'OK');
  });
});

test.describe('@eksik eksik girdi', () => {
  test('fibrozis: eksik alanlı profil -> panel "Eksik: …" (laboratuvarlar) -> sonuç ABSTAIN ve neden', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'missing');
    await expectPanel(page, 'fibrosis_final', 'MISSING', /Eksik bilgi: .*ALT.*AST/);
    await submit(page);
    const card = page.getByTestId('result-fibrosis_final');
    await expect(card).toHaveAttribute('data-status', 'ABSTAIN');
    await expect(card.getByTestId('decision')).toContainText('Sonuç üretilmedi');
    await expect(card.getByTestId('reasons')).toContainText('Eksik bilgiler:');
  });

  test('fibrozis: laboratuvarlar tamamlanınca durum Eksik -> Çalışabilir olur', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'fibrosis_final', 'READY');
    await gotoStep(page, 'laboratuvar');
    await page.locator('#f-platelets_k_ul').fill('');
    await expectPanel(page, 'fibrosis_final', 'MISSING', 'Trombosit');
    await page.locator('#f-platelets_k_ul').fill('210');
    await expectPanel(page, 'fibrosis_final', 'READY');
  });

  test('AF: formda panel "Eksik: EKG kaydı" gösterir', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await expectPanel(page, 'af_S4_DEVICE', 'MISSING', 'EKG kaydı');
  });

  test('AF: yalnız .hea yüklenince analiz başlatılamaz', async ({ page }) => {
    await openEcg(page);
    await page.getByTestId('file-input').setInputFiles([sample('00691_hr.hea')]);
    await expect(page.getByText('.dat veya .mat sinyal dosyası yok')).toBeVisible();
    await expect(page.getByTestId('ecg-run')).toBeDisabled();
  });

  test('AF: yaş/cinsiyet yanıtsız -> ABSTAIN (eksik alan)', async ({ page }) => {
    await openEcg(page);
    await loadEcgSample(page, '00691');
    await page.getByTestId('ecg-age').fill('');
    await page.getByTestId('ecg-sex').selectOption('');
    await runEcg(page);
    const card = page.getByTestId('result-af_S4_DEVICE');
    await expect(card).toHaveAttribute('data-status', 'ABSTAIN');
    await expect(card.getByTestId('reasons')).toContainText(/yaş yanıtsız|Biyolojik cinsiyet/);
  });
});

test.describe('@birim birim hatası', () => {
  test('fibrozis: albümin g/L değeri g/dL biriminde -> alan altında aralık hatası; birim g/L seçilince düzelir ve sunucu dönüştürür', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await gotoStep(page, 'laboratuvar');
    await page.locator('#f-albumin_gdl').fill('42');
    await expect(page.getByTestId('err-albumin_gdl')).toContainText('makul aralık dışında');
    await expectPanel(page, 'fibrosis_final', 'MISSING', 'Albümin');
    await page.getByTestId('unit-albumin_gdl').selectOption('g/L');
    await expect(page.getByTestId('err-albumin_gdl')).toBeHidden();
    await expectPanel(page, 'fibrosis_final', 'READY');
    await submit(page);
    await expect(page.getByTestId('unit-notes')).toContainText('Albümin (kan): 42 g/L -> 4.2 g/dL');
    await expect(page.getByTestId('unit-notes')).not.toContainText('albumin_gdl');
    await expect(page.getByTestId('result-fibrosis_final')).toHaveAttribute('data-status', 'OK');
  });

  test('birim hatalı profil: glukoz ve kreatinin alan altı hataları; hesaplama engellenir', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'unit_error');
    await gotoStep(page, 'laboratuvar');
    await expect(page.getByTestId('err-glucose_serum_mgdl')).toContainText('makul aralık dışında [30, 800]');
    await expect(page.getByTestId('err-creatinine_mgdl')).toContainText('makul aralık dışında [0.2, 15]');
    await page.getByTestId('submit').click();
    await expect(page.getByTestId('block-msg')).toContainText('alanda hata');
    await expect(page.getByTestId('error-step-laboratuvar')).toBeVisible();
    await page.getByTestId('unit-glucose_serum_mgdl').selectOption('mmol/L');
    await page.getByTestId('unit-creatinine_mgdl').selectOption('µmol/L');
    await expect(page.getByTestId('err-glucose_serum_mgdl')).toBeHidden();
    await expect(page.getByTestId('err-creatinine_mgdl')).toBeHidden();
  });

  test('AF: 250 Hz başlıklı kayıt -> ABSTAIN ("500 Hz değil")', async ({ page }) => {
    await openEcg(page);
    const hea = sampleBytes('00691_hr.hea').toString('ascii').replace('00691_hr 12 500 5000', '00691_hr 12 250 5000');
    await page.getByTestId('file-input').setInputFiles([
      { name: '00691_hr.hea', mimeType: 'text/plain', buffer: Buffer.from(hea, 'ascii') },
      { name: '00691_hr.dat', mimeType: 'application/octet-stream', buffer: sampleBytes('00691_hr.dat') },
    ]);
    await page.getByTestId('ecg-age').fill('60');
    await page.getByTestId('ecg-sex').selectOption('male');
    await runEcg(page);
    const card = page.getByTestId('result-af_S4_DEVICE');
    await expect(card).toHaveAttribute('data-status', 'ABSTAIN');
    await expect(card.getByTestId('reasons')).toContainText('500 Hz değil');
  });

  test('AF: yaş ay cinsinden girilmiş (720) -> sunucu 422 hatası gösterilir', async ({ page }) => {
    await openEcg(page);
    await loadEcgSample(page, '00165');
    await page.getByTestId('ecg-age').fill('720');
    await page.getByTestId('ecg-run').click();
    await expect(page.getByTestId('ecg-error')).toContainText('HTTP 422');
    await expect(page.getByTestId('ecg-error')).toContainText('makul aralık dışında');
  });
});

test.describe('@kapsam kapsam dışı veri', () => {
  test('fibrozis: gebe kadın profili -> panel Kapsam dışı (gebe) -> sonuç NOT_APPLICABLE', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'out_of_scope');
    await expectPanel(page, 'fibrosis_final', 'OUT_OF_SCOPE', 'gebe');
    await expectPanel(page, 'osteo_final', 'OUT_OF_SCOPE', 'yaş 30');
    await submit(page);
    await expect(page.getByTestId('result-fibrosis_final')).toHaveAttribute('data-status', 'NOT_APPLICABLE');
  });

  test('fibrozis: 19 yaş -> Kapsam dışı (yaş ≥ 20)', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'fibrosis_ready');
    await page.locator('#f-age_years').fill('19');
    await expectPanel(page, 'fibrosis_final', 'OUT_OF_SCOPE', 'yaş 19');
  });

  test('fibrozis: gebelik "bilmiyorum" -> Karar verilemez (ABSTAIN)', async ({ page }) => {
    await openForm(page);
    await loadProfile(page, 'missing');
    await page.locator('#f-pregnant').selectOption('unknown');
    await expectPanel(page, 'fibrosis_final', 'MISSING');
    await expect(page.getByTestId('panel-fibrosis_final')).toContainText('bilmiyorum');
  });

  test('AF: formda yaş 95 -> panel Kapsam dışı', async ({ page }) => {
    await openForm(page);
    await page.locator('#f-age_years').fill('95');
    await expectPanel(page, 'af_S4_DEVICE', 'OUT_OF_SCOPE', '18–89');
  });

  test('AF: EKG ile yaş 95 -> NOT_APPLICABLE', async ({ page }) => {
    await openEcg(page);
    await loadEcgSample(page, '00165');
    await page.getByTestId('ecg-age').fill('95');
    await runEcg(page);
    const card = page.getByTestId('result-af_S4_DEVICE');
    await expect(card).toHaveAttribute('data-status', 'NOT_APPLICABLE');
    await expect(card.getByTestId('reasons')).toContainText('18–89');
  });
});
