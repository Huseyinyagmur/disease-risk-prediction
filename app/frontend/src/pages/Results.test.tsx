import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PredictResponse } from '../api/types';
import eligFull from '../test/fixtures/eligibility_full.json';
import predictFull from '../test/fixtures/predict_full.json';
import { mockFetch, renderApp, schema, selectOnly } from '../test/helpers';

afterEach(() => vi.unstubAllGlobals());

async function toResults(predict: unknown, only?: string[]) {
  const { calls } = mockFetch({ elig: () => eligFull, predict: () => ({ status: 200, body: predict }) });
  const u = userEvent.setup();
  renderApp();
  if (only) await selectOnly(u, only);
  else await u.click(await screen.findByTestId('select-all'));
  await u.click(screen.getByTestId('submit'));
  await screen.findByTestId('results-filtered');
  return { u, calls };
}

const ui = schema.ui!;

/** Kartın görünür metni (teknik ayrıntı ve kapalı açılır bölümler hariç). */
function visibleText(card: HTMLElement): string {
  const c = card.cloneNode(true) as HTMLElement;
  c.querySelectorAll('details').forEach((d) => {
    if (!(d as HTMLDetailsElement).open) d.querySelectorAll(':scope > :not(summary)').forEach((x) => x.remove());
  });
  c.querySelectorAll('[data-testid="tech-details"]').forEach((x) => x.remove());
  return c.textContent ?? '';
}

describe('sonuç ekranı', () => {
  it('ana modüller üstte, deneyseller ayrı bölümde; olasılık gösterilmez', async () => {
    await toResults(predictFull);
    const exp = screen.getByTestId('experimental-section');
    expect(within(exp).queryByTestId('result-fibrosis_final')).toBeNull();
    expect(within(exp).getByTestId('result-htn_M1')).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/olasılık\s*[:=]\s*\d|probability|%\s?\d+\s*risk/i);
  });

  it('karar terimleri sözlükten; eşik üstü fibrozis -> FibroScan yönlendirmesi; ABSTAIN -> "Sonuç üretilmedi" ve neden', async () => {
    const p = structuredClone(predictFull) as unknown as PredictResponse;
    const fib = p.results.find((r) => r.model_id === 'fibrosis_final')!;
    fib.decision = { ...fib.decision!, research_class: 'ESIK_USTU', label_tr: 'Eşik üstü — araştırma sınıflaması (klinik karar değildir)' };
    await toResults(p);
    const card = screen.getByTestId('result-fibrosis_final');
    expect(within(card).getByTestId('decision')).toHaveTextContent(ui.terms_tr.decision.ESIK_USTU);
    expect(within(card).getByTestId('next-step')).toHaveTextContent('Ne yapmalıyım?');
    expect(within(card).getByTestId('next-step')).toHaveTextContent('FibroScan');
    expect(within(card).getByTestId('evidence-badges')).toHaveTextContent('İç test');
    expect(within(card).getByTestId('evidence-plain')).toHaveTextContent(ui.evidence_plain_tr.fibrosis_final);
    expect(card).toHaveTextContent('Hedef tanımı: FibroScan');
    const copd = screen.getByTestId('result-copd_S4_DEVICE');
    expect(within(copd).getByTestId('decision')).toHaveTextContent('Sonuç üretilmedi');
    expect(within(copd).getByTestId('reasons')).toHaveTextContent('Eksik bilgiler:');
    expect(within(copd).getByTestId('next-step')).toHaveTextContent(ui.next_steps_tr._default.ABSTAIN!);
    const anemia = screen.getByTestId('result-anemia_LR16');
    expect(within(anemia).getByTestId('decision')).toHaveTextContent('Bu analiz size uygun değil');
  });

  it('eşik altı -> "dışlamaz" yönlendirmesi; AF uygun değil -> EKG yönlendirmesi', async () => {
    await toResults(predictFull);
    const osteo = screen.getByTestId('result-osteo_final');
    const cls = osteo.getAttribute('data-class') as 'ESIK_USTU' | 'ESIK_ALTI';
    expect(within(osteo).getByTestId('next-step')).toHaveTextContent(ui.next_steps_tr.osteoporosis?.[cls] ?? ui.next_steps_tr._default[cls]!);
    expect(within(screen.getByTestId('result-af_S4_DEVICE')).getByTestId('next-step')).toHaveTextContent('EKG');
    for (const card of screen.getAllByTestId(/^result-/)) {
      const o = card.getAttribute('data-class') || card.getAttribute('data-status');
      if (o === 'ESIK_ALTI') expect(within(card).getByTestId('next-step')).toHaveTextContent('dışlamaz');
    }
  });

  it('metrik tabloları varsayılan kapalı ("Ayrıntılı test sonuçları")', async () => {
    await toResults(predictFull);
    for (const card of screen.getAllByTestId(/^result-/)) {
      const m = within(card).getByTestId('metrics') as HTMLDetailsElement;
      expect(m.open).toBe(false);
      expect(within(m).getByText('Ayrıntılı test sonuçları')).toBeInTheDocument();
    }
  });

  it('kartların görünür metninde ham alan adı ve model kimliği yok (yalnız teknik ayrıntıda)', async () => {
    await toResults(predictFull);
    const fieldNames = Object.keys(schema.fields);
    const ids = Object.keys(schema.models!);
    for (const card of screen.getAllByTestId(/^result-/)) {
      const txt = visibleText(card);
      for (const f of fieldNames) expect(txt, `${card.dataset.testid}: ${f}`).not.toMatch(new RegExp(`(?<![\\w])${f}(?![\\w])`));
      for (const id of ids) expect(txt, `${card.dataset.testid}: ${id}`).not.toContain(id);
      expect(txt).not.toMatch(/\bABSTAIN\b|NOT_APPLICABLE|ESIK_(USTU|ALTI)/);
      expect(within(card).getByTestId('tech-details')).toHaveTextContent(card.dataset.testid!.slice(7));
    }
  });

  it('yalnız seçilen analizlerin sonuçları gösterilir', async () => {
    await toResults(predictFull, ['liver_fibrosis']);
    expect(screen.getAllByTestId(/^result-/).map((e) => e.dataset.testid)).toEqual(['result-fibrosis_final']);
    expect(screen.queryByTestId('experimental-section')).toBeNull();
  });

  it('hedefi tanımlayan girdi uyarısı (HbA1c) kartta gösterilir', async () => {
    await toResults(predictFull);
    const dm = screen.getByTestId('result-dm_B');
    expect(within(dm).getByTestId('target-warning')).toHaveTextContent('HbA1c');
    expect(within(dm).getByTestId('selected-over')).toHaveTextContent(ui.text_tr.selected_over);
  });
});
