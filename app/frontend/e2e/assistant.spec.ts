// Phase XLVIII: açıklama asistanı paneli uçtan uca (gerçek backend + yerel Ollama 127.0.0.1:11434 çalışırken).
// Ollama yoksa (/health > assistant.enabled=false) testler gerekçeyle SKIP olur. Ekran görüntüleri: SHOTS_DIR
// (varsayılan phase_xlviii/screenshots). Profiller sentetiktir.
import { expect, test, type Page, type Request } from '@playwright/test';
import { gotoStep, loadProfile, openForm, submit } from './helpers';

const DIR = process.env.SHOTS_DIR ?? '../../phase_xlviii/screenshots';
const LLM_TIMEOUT = 240_000;

async function assistantEnabled(page: Page): Promise<{ ok: boolean; reason: string }> {
  const r = await page.request.get('/api/health');
  const h = (await r.json()) as { assistant?: { enabled: boolean; reason: string | null } };
  return { ok: !!h.assistant?.enabled, reason: h.assistant?.reason ?? 'BULUNAMADI' };
}

async function openAssistant(page: Page) {
  await page.getByTestId('assistant-open').click();
  await expect(page.getByTestId('assistant-panel')).toBeVisible();
  await expect(page.getByTestId('assistant-local-note')).toContainText('veriler bilgisayarınızdan çıkmaz');
}

test.describe('açıklama asistanı', () => {
  test.beforeEach(async ({ page }) => {
    const s = await assistantEnabled(page);
    test.skip(!s.ok, `asistan devre dışı: ${s.reason}`);
  });

  test('her sayfada açılır; örnek soru → yerel model yanıtı, kaynak listesi, uyarı; bekleme göstergesi', async ({ page }) => {
    test.setTimeout(LLM_TIMEOUT + 60_000);
    await page.goto('/');
    await openAssistant(page);
    await expect(page.getByTestId('assistant-examples')).toBeVisible();
    await page.screenshot({ path: `${DIR}/desktop_assistant_01_acik.png` });
    await page.getByTestId('assistant-examples').getByText('Eşik üstü ne demek?').click();
    await expect(page.getByTestId('assistant-waiting')).toBeVisible();
    const bot = page.getByTestId('assistant-msg-bot');
    await expect(bot).toBeVisible({ timeout: LLM_TIMEOUT });
    await expect(page.getByTestId('assistant-waiting')).toBeHidden();
    await expect(bot).toContainText('Araştırma prototipidir;');
    await expect(bot.getByTestId('assistant-sources')).toBeVisible();
    await page.screenshot({ path: `${DIR}/desktop_assistant_02_yanit.png` });
    // başka sayfada da açık ve sohbet bellekte
    await page.getByRole('navigation', { name: 'Ana gezinme' }).getByRole('button', { name: 'Model kartları' }).click();
    await expect(page.getByTestId('assistant-msg-bot')).toBeVisible();
    // sayfa yenilenince sohbet silinir
    await page.reload();
    await page.getByTestId('assistant-open').click();
    await expect(page.getByTestId('assistant-msg-bot')).toHaveCount(0);
  });

  test('sonuç ekranından: yalnız etiketler gönderilir (ölçüm değeri yok); acil durum → 112 (LLM yok)', async ({ page }) => {
    test.setTimeout(LLM_TIMEOUT + 90_000);
    await openForm(page, ['liver_fibrosis', 'af', 'osteoporosis']);
    await loadProfile(page, 'fibrosis_ready');
    await gotoStep(page, 'review');
    await submit(page);
    await expect(page.getByTestId('result-af_S4_DEVICE').getByTestId('decision')).toContainText('EKG kaydı gerekiyor');
    await expect(page.getByTestId('result-af_S4_DEVICE').getByTestId('reasons')).toContainText('Ne gerekiyor?');
    await page.getByTestId('result-af_S4_DEVICE').screenshot({ path: `${DIR}/desktop_gorev0_af_ekg_gerekiyor.png` });
    await page.getByTestId('result-fibrosis_final').getByTestId('decision').screenshot({ path: `${DIR}/desktop_gorev0_karar_kutusu.png` });

    const bodies: string[] = [];
    page.on('request', (r: Request) => { if (r.url().endsWith('/api/assistant/ask')) bodies.push(r.postData() ?? ''); });
    await openAssistant(page);
    await expect(page.getByTestId('assistant-with-results')).toBeChecked();
    await page.getByTestId('assistant-input').fill('Sonuçlarımı kısaca açıklar mısın?');
    await page.getByTestId('assistant-send').click();
    await expect(page.getByTestId('assistant-msg-bot')).toBeVisible({ timeout: LLM_TIMEOUT });
    expect(bodies).toHaveLength(1);
    const b = JSON.parse(bodies[0]) as { question: string; results: { disease_key: string; outcome: string; missing_fields: string[] }[] };
    expect(Object.keys(b).sort()).toEqual(['question', 'results']);
    expect(b.results.map((r) => r.disease_key).sort()).toEqual(['af', 'liver_fibrosis', 'osteoporosis']);
    expect(b.results.find((r) => r.disease_key === 'af')?.outcome).toBe('ECG_REQUIRED');
    expect(bodies[0]).not.toMatch(/\d{2,}/);
    await page.screenshot({ path: `${DIR}/desktop_assistant_03_sonuc_etiketleri.png` });

    await page.getByTestId('assistant-input').fill('Göğüs ağrım var');
    await page.getByTestId('assistant-send').click();
    await expect(page.getByTestId('assistant-msg-bot').last()).toContainText("112'yi arayın", { timeout: 15_000 });
    await page.screenshot({ path: `${DIR}/desktop_assistant_04_acil_112.png` });
  });

  test('v3: genel bilgi sorusunda acil kelimesi → en üstte 112 uyarı kutusu + normal yanıt; kişisel ifade → sabit 112', async ({ page }) => {
    test.setTimeout(LLM_TIMEOUT + 60_000);
    await page.goto('/');
    await openAssistant(page);
    await page.getByTestId('assistant-input').fill('Göğüs ağrısı nedir?');
    await page.getByTestId('assistant-send').click();
    const bot = page.getByTestId('assistant-msg-bot');
    await expect(bot).toBeVisible({ timeout: LLM_TIMEOUT });
    const box = bot.getByTestId('assistant-emergency-notice');
    await expect(box).toBeVisible();
    await expect(box).toContainText('112');
    await expect(bot).toContainText('Araştırma prototipidir;');
    await page.screenshot({ path: `${DIR}/desktop_assistant_05_genel_soru_112_kutusu.png` });
    await page.getByTestId('assistant-input').fill('Şu an göğsümde baskı var');
    await page.getByTestId('assistant-send').click();
    const last = page.getByTestId('assistant-msg-bot').last();
    await expect(last).toContainText("112'yi arayın", { timeout: 15_000 });
    await expect(last.getByTestId('assistant-emergency-notice')).toHaveCount(0);
  });

  test('mobil (375 px): panel ekrana sığar, yatay kaydırma yok', async ({ page }) => {
    test.setTimeout(LLM_TIMEOUT + 60_000);
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto('/');
    await openAssistant(page);
    const box = await page.getByTestId('assistant-panel').boundingBox();
    expect(box && box.x >= 0 && box.x + box.width <= 375).toBeTruthy();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.getByTestId('assistant-input').fill('Bana Python kodu yaz');
    await page.getByTestId('assistant-send').click();
    await expect(page.getByTestId('assistant-msg-bot')).toContainText('kapsamım dışında', { timeout: 15_000 });
    await page.screenshot({ path: `${DIR}/mobile375_assistant_kapsam_disi.png` });
  });
});
