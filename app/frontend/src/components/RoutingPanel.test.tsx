import { screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EligibilityResponse } from '../api/types';
import eligAfEnvMissing from '../test/fixtures/eligibility_af_env_missing.json';
import eligAfEnvAge95 from '../test/fixtures/eligibility_af_env_missing_age95.json';
import eligAfEnvFull from '../test/fixtures/eligibility_af_env_missing_full_form.json';
import eligEmpty from '../test/fixtures/eligibility_empty.json';
import { mockFetch, renderApp, schema, startAll } from '../test/helpers';
import userEvent from '@testing-library/user-event';
import { alsoLine, stateLine } from './RoutingPanel';

afterEach(() => vi.unstubAllGlobals());

// Phase XLVI Görev 5: AF çalışma ortamı (Octave/ECGDeli + kilitli pipeline) yokken panel "Eksik: EKG kaydı" değil
// "Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok" göstermeli. Kapanış düzeltmesi: kişiye özel neden (kapsam dışı
// yaş, eksik alan) varsa ana etiket odur ve ortam nedeni altında "Ayrıca: …" satırında gösterilir. Fixture'lar gerçek
// backend yanıtıdır (phase_xlvi/scripts/gen_af_env_fixture.py).
describe('canlı panel — AF çalışma ortamı', () => {
  const afOf = (r: unknown) => (r as EligibilityResponse).models.find((m) => m.model_id === 'af_S4_DEVICE')!;

  it('ortam yokken, form tam (kişiye özel neden yok): Karar verilemez + gerekçe; Ayrıca satırı yok; EKG yükleme yok', async () => {
    mockFetch({ elig: () => eligAfEnvFull });
    renderApp();
    await startAll(userEvent.setup());
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'ABSTAIN');
    expect(within(item).getByTestId('panel-line-af_S4_DEVICE')).toHaveTextContent(
      /^Sonuç üretilemez: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).getByTestId('state-badge')).toHaveTextContent(/^Sonuç üretilemez$/); // durum rozeti
    expect(within(item).queryByTestId('panel-also-af_S4_DEVICE')).toBeNull();
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
    expect(item).not.toHaveTextContent('Eksik bilgi');
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).toHaveTextContent('kilitli AF pipeline dosyaları bulunamadı');
  });

  it('ortam yokken, yaş 95: ana etiket Kapsam dışı: yaş …; altında Ayrıca: AF çalışma ortamı yok', async () => {
    mockFetch({ elig: () => eligAfEnvAge95 });
    renderApp();
    await startAll(userEvent.setup());
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'OUT_OF_SCOPE');
    const line = within(item).getByTestId('panel-line-af_S4_DEVICE');
    expect(line).toHaveTextContent(/^Bu analiz size uygun değil: yaş 95 analizin geliştirildiği grup dışında \(18–89\)/);
    expect(line).not.toHaveTextContent('ortamı yok');
    expect(within(item).getByTestId('panel-also-af_S4_DEVICE')).toHaveTextContent(
      /^Ayrıca: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
  });

  it('ortam yokken, boş form: ana etiket Eksik (EKG kaydı değil, yaş); altında Ayrıca: ortam yok', async () => {
    mockFetch({ elig: () => eligAfEnvMissing });
    renderApp();
    await startAll(userEvent.setup());
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'MISSING');
    const line = within(item).getByTestId('panel-line-af_S4_DEVICE');
    expect(line).toHaveTextContent(/^Eksik bilgi: /);
    expect(line).not.toHaveTextContent('EKG');
    expect(within(item).getByTestId('panel-also-af_S4_DEVICE')).toHaveTextContent(
      /^Ayrıca: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
  });

  it('ortam varken (önceki davranış): Eksik … EKG kaydı ve yükleme bağlantısı', async () => {
    mockFetch({ elig: () => eligEmpty });
    renderApp();
    await startAll(userEvent.setup());
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'MISSING');
    expect(within(item).getByTestId('panel-line-af_S4_DEVICE')).toHaveTextContent(/^Eksik bilgi: .*EKG/);
    expect(within(item).getByText(/EKG kaydı yükle/)).toBeInTheDocument();
    // teknik ayrıntıda yalnız model kimliği (ortam ayrıntısı yok)
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).toHaveTextContent('af_S4_DEVICE');
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).not.toHaveTextContent('pipeline');
  });

  it('stateLine/alsoLine: terim sözlükten + backend gerekçeleri (yalnız sözlükteki sadeleştirme), metin uydurmaz', () => {
    const af = afOf(eligAfEnvFull);
    expect(af.af_pipeline_available).toBe(false);
    expect(af.missing_fields).toEqual([]);
    const terms = schema.ui!.terms_tr.eligibility;
    expect(stateLine(af, schema)).toBe(terms.ABSTAIN + ': ' + af.reasons.join('; '));
    expect(alsoLine(af, schema)).toBeNull();
    const old = afOf(eligAfEnvAge95);
    const plain = (x: string) => x.replace('model popülasyonu', 'analizin geliştirildiği grup');
    expect(stateLine(old, schema)).toBe(terms.OUT_OF_SCOPE + ': ' + old.reasons.map(plain).join('; '));
    expect(alsoLine(old, schema)).toBe('Ayrıca: ' + old.additional_reasons!.join('; '));
    // diğer modeller ortamdan etkilenmez: boş formda AF dışındaki durumlar iki fixture'da aynı
    const other = (r: unknown) =>
      (r as EligibilityResponse).models.filter((m) => m.model_id !== 'af_S4_DEVICE').map((m) => [m.model_id, m.state, m.missing_fields]);
    expect(other(eligAfEnvMissing)).toEqual(other(eligEmpty));
  });
});
