// Phase L: anlaşılırlık iyileştirmesi — davranış testleri (fixture: gerçek backend /schema; sentetik tahmin yanıtları).
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { AssistantResultLabel } from './api/types';
import { suggestedQuestions } from './components/AssistantPanel';
import eligEmpty from './test/fixtures/eligibility_empty.json';
import eligFull from './test/fixtures/eligibility_full.json';
import predictFull from './test/fixtures/predict_full.json';
import { mockFetch, renderApp, schema } from './test/helpers';

afterEach(() => vi.unstubAllGlobals());

describe('madde 5: canlı panel eski yanıtı göstermez', () => {
  it('"Formu temizle" sonrası, yeni yanıt gelene dek önceki "Hesaplanabilir" durumu görünmez', async () => {
    // dolu girdi → eligFull (fibrozis READY); boş girdi → eligEmpty (hepsi MISSING)
    mockFetch({ elig: (f) => (Object.keys(f).length ? eligFull : eligEmpty) });
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('profile-fibrosis_ready'));
    await waitFor(() => expect(screen.getByTestId('panel-fibrosis_final')).toHaveAttribute('data-state', 'READY'));
    await u.click(screen.getByTestId('clear-form'));
    // debounce (300 ms) dolmadan: eski READY kartı ekranda OLMAMALI
    expect(screen.queryByTestId('panel-fibrosis_final')).toBeNull();
    await waitFor(() => expect(screen.getByTestId('panel-fibrosis_final')).toHaveAttribute('data-state', 'MISSING'));
    expect(screen.getByTestId('panel-osteo_final')).toHaveAttribute('data-state', 'MISSING');
  });

  it('istek başarısız olursa eski durum gösterilmez (yalnız hata)', async () => {
    const { fn } = mockFetch({ elig: () => eligFull });
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('profile-fibrosis_ready'));
    await waitFor(() => expect(screen.getByTestId('panel-fibrosis_final')).toHaveAttribute('data-state', 'READY'));
    const orig = fn.getMockImplementation()!;
    fn.mockImplementation(async (url: string, init?: RequestInit) => {
      if (String(url).endsWith('/eligibility')) throw new TypeError('Failed to fetch');
      return orig(url, init);
    });
    await u.click(screen.getByTestId('clear-form'));
    await screen.findByRole('alert');
    expect(screen.queryByTestId('panel-fibrosis_final')).toBeNull();
  });
});

async function toResults(only3 = false) {
  mockFetch({ elig: () => eligFull, predict: () => ({ status: 200, body: predictFull }) });
  const u = userEvent.setup();
  renderApp();
  if (!only3) await u.click(await screen.findByTestId('select-all'));
  else await screen.findByTestId('analysis-select');
  await u.click(screen.getByTestId('submit'));
  await screen.findByTestId('results-summary');
  return u;
}

describe('madde 6: sonuç özeti şeridi', () => {
  it('9 analiz: durum sayıları sabit sırayla; her öğe karta bağlanır', async () => {
    await toResults();
    expect(screen.getByTestId('summary-line')).toHaveTextContent(
      '9 analiz: 5 eşik altı, 2 sonuç üretilmedi, 1 EKG kaydı bekliyor, 1 uygun değil',
    );
    const item = screen.getByTestId('summary-item-fibrosis_final');
    expect(item).toHaveAttribute('href', '#card-fibrosis_final');
    expect(document.getElementById('card-fibrosis_final')).not.toBeNull();
  });

  it('varsayılan seçimle (3 analiz) özet yalnız seçilenleri sayar', async () => {
    await toResults(true);
    expect(screen.getByTestId('summary-line')).toHaveTextContent('3 analiz: 2 eşik altı, 1 EKG kaydı bekliyor');
  });

  it('kartta sonuç kutusu durum simgesi taşır; ikincil bilgiler kapalı', async () => {
    await toResults();
    const card = screen.getByTestId('result-fibrosis_final');
    expect(card).toHaveAttribute('data-key', 'ESIK_ALTI');
    expect(within(card).getByTestId('decision')).toHaveTextContent('▼');
    for (const id of ['metrics', 'limitations', 'tech-details']) expect((within(card).getByTestId(id) as HTMLDetailsElement).open).toBe(false);
  });
});

describe('madde 2: kanıt düzeyi rozetleri kart verisinden', () => {
  it('osteoporoz: iç test kaydı yok → üstü çizili + görünür not; zamansal ✓', async () => {
    await toResults();
    const card = screen.getByTestId('result-osteo_final');
    expect(within(card).getByTestId('tier-internal_test')).toHaveAttribute('data-has', 'false');
    expect(within(card).getByTestId('tier-temporal')).toHaveAttribute('data-has', 'true');
    expect(within(card).getByTestId('tier-internal_test')).toHaveTextContent(schema.ui!.text_tr.evidence_missing_short); // görünür, üstü çizili değil
    expect(within(card).getByTestId('tier-temporal')).toHaveTextContent('✓');
    expect(within(card).getByTestId('evidence-missing-note')).toHaveTextContent(schema.ui!.text_tr.evidence_missing_note);
  });

  it('AF: iç test ve dış doğrulama yapıldı → ikisi de işaretli; yalnız zamansal üstü çizili', async () => {
    await toResults();
    const card = screen.getByTestId('result-af_S4_DEVICE');
    expect(within(card).getByTestId('tier-internal_test')).toHaveAttribute('data-has', 'true');
    expect(within(card).getByTestId('tier-external')).toHaveAttribute('data-has', 'true');
    expect(within(card).getByTestId('tier-temporal')).toHaveAttribute('data-has', 'false');
  });
});

describe('madde 3: AF ek sınırlılıkları (phase_xxxiii)', () => {
  it('registry sınırlılıklarına ek olarak ritim bazlı yanlış pozitif satırları listelenir', async () => {
    await toResults();
    const lim = within(screen.getByTestId('result-af_S4_DEVICE')).getByTestId('limitations');
    expect(lim).toHaveTextContent('19/62');
    expect(lim).toHaveTextContent('420/651');
    expect(lim.querySelector('summary')).toHaveTextContent(/Sınırlılıklar \(8\)/); // 6 registry + 2 ek
  });
});

describe('madde 7: açıklama asistanı', () => {
  const L = (disease_key: string, outcome: AssistantResultLabel['outcome']): AssistantResultLabel => ({ disease_key, outcome, missing_fields: [] });

  it('örnek sorular yalnız sonuç etiketlerinden; etiket yoksa varsayılan örnekler', () => {
    const s = suggestedQuestions(schema, [L('liver_fibrosis', 'ESIK_USTU'), L('osteoporosis', 'ESIK_ALTI'), L('af', 'ECG_REQUIRED')]);
    expect(s.fromResults).toBe(true);
    expect(s.qs).toEqual([
      'Eşik üstü sonuç ne anlama geliyor?', 'FibroScan nedir?', 'Eşik altı sonuç hastalığı dışlar mı?',
      'Kemik yoğunluğu ölçümü (DXA) nedir?', 'AF analizi için EKG kaydını nasıl yüklerim?',
    ]);
    for (const q of s.qs) expect(q).not.toMatch(/\d{2,}/); // ham değer yok
    const d = suggestedQuestions(schema, []);
    expect(d.fromResults).toBe(false);
    expect(d.qs).toEqual(schema.ui!.text_tr.asst_examples.split('|'));
  });

  // Phase L2: masaüstü yan panel testi kaldırıldı; yerine çekmece + karartma (phase_l2.test.tsx).

  it('tablet/mobil (matchMedia eşleşmez): tam ekran, genişlet düğmesi yok', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('assistant-open'));
    expect(screen.getByTestId('assistant-panel')).toHaveAttribute('data-layout', 'fullscreen');
    expect(screen.queryByTestId('assistant-expand')).toBeNull();
  });
});

describe('madde 4: EKG sayfası', () => {
  it('"Örnek kayıtla dene" başlığı ve açıklamalı iki büyük düğme', async () => {
    mockFetch();
    renderApp('ecg');
    const box = await screen.findByTestId('ecg-samples');
    expect(box).toHaveTextContent('Örnek kayıtla dene');
    expect(within(box).getByTestId('ecg-sample-00691')).toHaveTextContent('AF kaydı');
    expect(within(box).getByTestId('ecg-sample-00165')).toHaveTextContent('Sinüs ritmi kaydı');
  });
});
