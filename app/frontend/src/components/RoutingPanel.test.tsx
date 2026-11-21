import { screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EligibilityResponse } from '../api/types';
import eligAfEnvMissing from '../test/fixtures/eligibility_af_env_missing.json';
import eligAfEnvAge95 from '../test/fixtures/eligibility_af_env_missing_age95.json';
import eligAfEnvFull from '../test/fixtures/eligibility_af_env_missing_full_form.json';
import eligEmpty from '../test/fixtures/eligibility_empty.json';
import { mockFetch, renderApp, schema } from '../test/helpers';
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
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'ABSTAIN');
    expect(within(item).getByTestId('panel-line-af_S4_DEVICE')).toHaveTextContent(
      /^Karar verilemez: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).getByText('Karar verilemez')).toBeInTheDocument(); // durum rozeti
    expect(within(item).queryByTestId('panel-also-af_S4_DEVICE')).toBeNull();
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
    expect(item).not.toHaveTextContent('Eksik');
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).toHaveTextContent('kilitli AF pipeline dosyaları bulunamadı');
  });

  it('ortam yokken, yaş 95: ana etiket Kapsam dışı: yaş …; altında Ayrıca: AF çalışma ortamı yok', async () => {
    mockFetch({ elig: () => eligAfEnvAge95 });
    renderApp();
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'OUT_OF_SCOPE');
    const line = within(item).getByTestId('panel-line-af_S4_DEVICE');
    expect(line).toHaveTextContent(/^Kapsam dışı: yaş 95 model popülasyonu dışında \(18–89\)/);
    expect(line).not.toHaveTextContent('ortamı yok');
    expect(within(item).getByTestId('panel-also-af_S4_DEVICE')).toHaveTextContent(
      /^Ayrıca: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
  });

  it('ortam yokken, boş form: ana etiket Eksik (EKG kaydı değil, yaş); altında Ayrıca: ortam yok', async () => {
    mockFetch({ elig: () => eligAfEnvMissing });
    renderApp();
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'MISSING');
    const line = within(item).getByTestId('panel-line-af_S4_DEVICE');
    expect(line).toHaveTextContent(/^Eksik: /);
    expect(line).not.toHaveTextContent('EKG');
    expect(within(item).getByTestId('panel-also-af_S4_DEVICE')).toHaveTextContent(
      /^Ayrıca: Octave\/ECGDeli AF çalışma ortamı yok$/,
    );
    expect(within(item).queryByText(/EKG kaydı yükle/)).toBeNull();
  });

  it('ortam varken (önceki davranış): Eksik … EKG kaydı ve yükleme bağlantısı', async () => {
    mockFetch({ elig: () => eligEmpty });
    renderApp();
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'MISSING');
    expect(within(item).getByTestId('panel-line-af_S4_DEVICE')).toHaveTextContent(/^Eksik: .*EKG/);
    expect(within(item).getByText(/EKG kaydı yükle/)).toBeInTheDocument();
    expect(within(item).queryByTestId('panel-details-af_S4_DEVICE')).toBeNull();
  });

  it('stateLine/alsoLine: backend gerekçelerini aynen kullanır, metin uydurmaz', () => {
    const af = afOf(eligAfEnvFull);
    expect(af.af_pipeline_available).toBe(false);
    expect(af.missing_fields).toEqual([]);
    expect(stateLine(af, schema)).toBe('Karar verilemez: ' + af.reasons.join('; '));
    expect(alsoLine(af)).toBeNull();
    const old = afOf(eligAfEnvAge95);
    expect(stateLine(old, schema)).toBe('Kapsam dışı: ' + old.reasons.join('; '));
    expect(alsoLine(old)).toBe('Ayrıca: ' + old.additional_reasons!.join('; '));
    // diğer modeller ortamdan etkilenmez: boş formda AF dışındaki durumlar iki fixture'da aynı
    const other = (r: unknown) =>
      (r as EligibilityResponse).models.filter((m) => m.model_id !== 'af_S4_DEVICE').map((m) => [m.model_id, m.state, m.missing_fields]);
    expect(other(eligAfEnvMissing)).toEqual(other(eligEmpty));
  });
});
