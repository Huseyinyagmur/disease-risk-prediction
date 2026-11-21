// Phase XLVIII: açıklama asistanı paneli + Görev 0 sonuç kartı düzeltmeleri.
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PredictResponse } from '../api/types';
import eligFull from '../test/fixtures/eligibility_full.json';
import predictFull from '../test/fixtures/predict_full.json';
import { mockFetch, renderApp, schema } from '../test/helpers';

afterEach(() => vi.unstubAllGlobals());

const tx = schema.ui!.text_tr;
const DISC = schema.disclaimer!;

interface AskCall { question: string; results: unknown[]; raw: string }

function stubAssistant(opts: { enabled?: boolean; reason?: string; answer?: (q: string) => { status: number; body: unknown }; predict?: unknown } = {}) {
  const base = mockFetch({ elig: () => eligFull, predict: () => ({ status: 200, body: opts.predict ?? predictFull }) });
  const inner = base.fn;
  const asks: AskCall[] = [];
  let release: (() => void) | null = null;
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const path = String(url).replace(/^\/api/, '');
    const ok = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
    if (path === '/health') return ok({ status: 'ok', assistant: { enabled: opts.enabled ?? true, reason: opts.reason ?? null } });
    if (path === '/assistant/ask') {
      const raw = String(init?.body);
      const b = JSON.parse(raw) as { question: string; results: unknown[] };
      asks.push({ ...b, raw });
      const r = opts.answer?.(b.question) ?? {
        status: 200,
        body: {
          route: 'llm', llm_used: true, local_model: true, disclaimer: DISC,
          answer: `Eşik üstü, araştırmada sabitlenmiş eşiğe göre bir sınıflamadır [1].\n\n${DISC}`,
          sources: [
            { doc_id: 'int_glossary', title: 'Terim sözlüğü', section: 'Eşik üstü / Eşik altı (ESIK_USTU / ESIK_ALTI)', kind: 'internal', ref: 'app_config.json > ui.glossary_tr' },
            { doc_id: 'mp_test_a1c', title: 'Hemoglobin A1C (HbA1c) Test', section: 'What is it used for?', kind: 'external', url: 'https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/', publisher: 'MedlinePlus' },
          ],
        },
      };
      await new Promise<void>((res) => { release = res; setTimeout(res, 30); });
      return ok(r.body, r.status);
    }
    return inner(url, init);
  });
  vi.stubGlobal('fetch', fn);
  return { asks, calls: base.calls, release: () => release?.() };
}

describe('açıklama asistanı paneli', () => {
  it('her sayfada açılır; yerel model notu, örnek sorular; yanıt + kaynak bağlantıları + uyarı; bekleme göstergesi', async () => {
    const { asks } = stubAssistant();
    const u = userEvent.setup();
    renderApp('home');
    await u.click(await screen.findByTestId('assistant-open'));
    const panel = screen.getByTestId('assistant-panel');
    expect(within(panel).getByTestId('assistant-local-note')).toHaveTextContent('veriler bilgisayarınızdan çıkmaz');
    const ex = await within(panel).findByTestId('assistant-examples');
    for (const q of tx.asst_examples.split('|')) expect(ex).toHaveTextContent(q);
    await u.click(within(ex).getByText('Eşik üstü ne demek?'));
    expect(await within(panel).findByTestId('assistant-waiting')).toHaveTextContent(tx.asst_waiting);
    const bot = await within(panel).findByTestId('assistant-msg-bot');
    expect(bot).toHaveTextContent('araştırmada sabitlenmiş eşiğe');
    expect(bot).toHaveTextContent(DISC);
    const src = within(bot).getByTestId('assistant-sources');
    const link = within(src).getByRole('link');
    expect(link).toHaveAttribute('href', 'https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(src).toHaveTextContent(tx.asst_internal_doc + ': Terim sözlüğü');
    expect(asks[0].question).toBe('Eşik üstü ne demek?');
    expect(asks[0].results).toEqual([]);                       // sonuç yokken etiket gönderilmez
    expect(screen.queryByTestId('assistant-waiting')).toBeNull();
    // başka sayfaya geçince sohbet bellekte kalır (aynı oturum)
    await u.click(screen.getByRole('button', { name: 'Hakkında' }));
    expect(screen.getByTestId('assistant-msg-bot')).toBeInTheDocument();
  });

  it('sonuç etiketleri yalnız kapalı sözlük (hastalık × durum × eksik alan adı) — form değerleri gönderilmez', async () => {
    const { asks } = stubAssistant();
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('select-all'));
    await u.click(screen.getByTestId('submit'));
    await screen.findByTestId('results-filtered');
    await u.click(screen.getByTestId('assistant-open'));
    const panel = screen.getByTestId('assistant-panel');
    expect(within(panel).getByTestId('assistant-with-results')).toBeChecked();
    await u.type(within(panel).getByTestId('assistant-input'), 'Sonuçlarımı açıkla');
    await u.click(within(panel).getByTestId('assistant-send'));
    await within(panel).findByTestId('assistant-msg-bot');
    const b = JSON.parse(asks[0].raw) as Record<string, unknown>;
    expect(Object.keys(b).sort()).toEqual(['question', 'results']);
    const res = b.results as { disease_key: string; outcome: string; missing_fields: string[] }[];
    for (const r of res) {
      expect(Object.keys(r).sort()).toEqual(['disease_key', 'missing_fields', 'outcome']);
      expect(['ESIK_USTU', 'ESIK_ALTI', 'ABSTAIN', 'NOT_APPLICABLE', 'ECG_REQUIRED']).toContain(r.outcome);
      for (const f of r.missing_fields) expect(schema.fields[f]).toBeDefined();
    }
    expect(res.find((r) => r.disease_key === 'af')?.outcome).toBe('ECG_REQUIRED');
    expect(res.find((r) => r.disease_key === 'copd')).toEqual({ disease_key: 'copd', outcome: 'ABSTAIN', missing_fields: ['fev1_pre_ml', 'fvc_pre_ml'] });
    expect(asks[0].raw).not.toMatch(/\d{2,}/);                 // hiçbir sayısal ölçüm değeri yok
    // kutu kaldırılınca etiket gönderilmez
    await u.click(within(panel).getByTestId('assistant-with-results'));
    await u.type(within(panel).getByTestId('assistant-input'), 'Eşik altı ne demek?');
    await u.click(within(panel).getByTestId('assistant-send'));
    await vi.waitFor(() => expect(asks.length).toBe(2));
    expect(asks[1].results).toEqual([]);
  });

  it('Ollama yokken: panel gerekçeyle devre dışı; uygulamanın geri kalanı çalışır', async () => {
    stubAssistant({ enabled: false, reason: 'Ollama çalışmıyor veya erişilemiyor (http://127.0.0.1:11434)' });
    const u = userEvent.setup();
    renderApp('home');
    await u.click(await screen.findByTestId('assistant-open'));
    const dis = await screen.findByTestId('assistant-disabled');
    expect(dis).toHaveTextContent('Ollama çalışmıyor');
    expect(screen.getByTestId('assistant-input')).toBeDisabled();
    expect(screen.queryByTestId('assistant-examples')).toBeNull();
    await u.click(screen.getByTestId('assistant-close'));
    await u.click(screen.getByRole('button', { name: 'Veri girişi' }));
    expect(await screen.findByTestId('analysis-select')).toBeInTheDocument();
  });

  it('503 yanıtında hata mesajı ve devre dışı durum', async () => {
    stubAssistant({ answer: () => ({ status: 503, body: { detail: 'asistan devre dışı: Ollama sohbet isteği başarısız', disclaimer: DISC } }) });
    const u = userEvent.setup();
    renderApp('home');
    await u.click(await screen.findByTestId('assistant-open'));
    await u.click(await screen.findByText('FibroScan nedir?'));
    expect(await screen.findByTestId('assistant-msg-error')).toHaveTextContent('Ollama sohbet isteği başarısız');
    expect(await screen.findByTestId('assistant-disabled')).toBeInTheDocument();
  });

  it('sohbet tarayıcı depolamasına yazılmaz', async () => {
    stubAssistant();
    const set = vi.spyOn(Storage.prototype, 'setItem');
    const u = userEvent.setup();
    renderApp('home');
    await u.click(await screen.findByTestId('assistant-open'));
    await u.click(await screen.findByText('Neden sonuç üretilmedi?'));
    await screen.findByTestId('assistant-msg-bot');
    expect(set).not.toHaveBeenCalled();
    expect(document.cookie).toBe('');
  });
});

describe('Görev 0 — sonuç kartı düzeltmeleri', () => {
  async function results(p: unknown) {
    stubAssistant({ predict: p });
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('select-all'));
    await u.click(screen.getByTestId('submit'));
    await screen.findByTestId('results-filtered');
  }

  it('AF EKG yüklenmemiş: "EKG kaydı gerekiyor" ve "Ne gerekiyor?"', async () => {
    await results(predictFull);
    const af = screen.getByTestId('result-af_S4_DEVICE');
    expect(within(af).getByTestId('decision')).toHaveTextContent(tx.ecg_required);
    expect(within(af).getByTestId('decision')).not.toHaveTextContent('Bu analiz size uygun değil');
    expect(within(af).getByTestId('reasons')).toHaveTextContent(tx.reasons_needed);
    expect(within(af).getByTestId('reasons')).not.toHaveTextContent('Neden uygun değil?');
    // yaş kapsam dışı (EKG gerekçesi değil) -> mevcut ifade kalır
    const anemia = screen.getByTestId('result-anemia_LR16');
    expect(within(anemia).getByTestId('decision')).toHaveTextContent('Bu analiz size uygun değil');
    expect(within(anemia).getByTestId('reasons')).toHaveTextContent('Neden uygun değil?');
  });

  it('osteoporoz "yapısal boşluk … age_last_period" yalnız Teknik ayrıntı içinde', async () => {
    const p = structuredClone(predictFull) as unknown as PredictResponse;
    const o = p.results.find((r) => r.model_id === 'osteo_final')!;
    o.reasons = ['yapısal boşluk (eğitimdeki tanım, eksik sayılmaz): age_last_period'];
    await results(p);
    const card = screen.getByTestId('result-osteo_final');
    const tech = within(card).getByTestId('tech-details');
    expect(tech).toHaveTextContent('yapısal boşluk');
    const c = card.cloneNode(true) as HTMLElement;
    c.querySelectorAll('[data-testid="tech-details"]').forEach((x) => x.remove());
    expect(c.textContent).not.toContain('yapısal boşluk');
    expect(c.textContent).not.toContain('age_last_period');
  });

  it('karar kutusu tekrar satırı: "Araştırma sınıflamasıdır; klinik karar değildir. Olasılık gösterilmez."', async () => {
    await results(predictFull);
    const fib = screen.getByTestId('result-fibrosis_final');
    expect(within(fib).getByTestId('decision-note')).toHaveTextContent('Araştırma sınıflamasıdır; klinik karar değildir. Olasılık gösterilmez.');
    expect(within(fib).getByTestId('decision')).not.toHaveTextContent('araştırma sınıflaması (klinik karar değildir)');
  });
});
