import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import predictFull from '../test/fixtures/predict_full.json';
import eligFull from '../test/fixtures/eligibility_full.json';
import { mockFetch, renderApp } from '../test/helpers';
import type { PredictResponse } from '../api/types';

afterEach(() => vi.unstubAllGlobals());

async function toResults(predict: unknown) {
  mockFetch({ elig: () => eligFull, predict: () => ({ status: 200, body: predict }) });
  const u = userEvent.setup();
  renderApp();
  await screen.findByTestId('panel-fibrosis_final');
  await u.click(screen.getByTestId('submit'));
  await screen.findByText('Ana modüller ve araştırma modülü');
}

describe('sonuç ekranı', () => {
  it('ana modüller üstte, deneyseller ayrı bölümde; olasılık gösterilmez', async () => {
    await toResults(predictFull);
    const exp = screen.getByTestId('experimental-section');
    expect(within(exp).queryByTestId('result-fibrosis_final')).toBeNull();
    expect(within(exp).getByTestId('result-htn_M1')).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/olasılık\s*[:=]\s*\d|probability|%\s?\d+\s*risk/i);
  });

  it('karar metinleri: eşik üstü -> "İleri değerlendirme önerilir"; ABSTAIN -> neden; kanıt ve metrik tablosu', async () => {
    const p = structuredClone(predictFull) as unknown as PredictResponse;
    const fib = p.results.find((r) => r.model_id === 'fibrosis_final')!;
    fib.decision = { ...fib.decision!, research_class: 'ESIK_USTU', label_tr: 'Eşik üstü — araştırma sınıflaması (klinik karar değildir)' };
    await toResults(p);
    const card = screen.getByTestId('result-fibrosis_final');
    expect(within(card).getByTestId('decision')).toHaveTextContent('İleri değerlendirme önerilir');
    expect(within(card).getByTestId('evidence-badges')).toHaveTextContent('İç test');
    expect(within(card).getByTestId('metrics-table')).toHaveTextContent('Precision');
    expect(card).toHaveTextContent('Hedef tanımı: FibroScan');
    const copd = screen.getByTestId('result-copd_S4_DEVICE');
    expect(within(copd).getByTestId('decision')).toHaveTextContent('Karar üretilmedi (ABSTAIN)');
    expect(within(copd).getByTestId('reasons')).toHaveTextContent('eksik zorunlu alan');
  });

  it('hedefi tanımlayan girdi uyarısı (HbA1c) kartta gösterilir', async () => {
    await toResults(predictFull);
    const dm = screen.getByTestId('result-dm_B');
    expect(within(dm).getByTestId('target-warning')).toHaveTextContent('HbA1c');
  });
});
