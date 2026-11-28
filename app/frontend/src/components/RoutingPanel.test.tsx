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
      /^Sonuç üretilemez: EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz\.$/, // Phase L: sade metin
    );
    expect(within(item).getByTestId('state-badge')).toHaveTextContent(/^\?Sonuç üretilemez$/); // durum rozeti (Phase L: simge + terim)
    expect(within(item).queryByTestId('panel-also-af_S4_DEVICE')).toBeNull();
    expect(within(item).queryByRole('button', { name: /EKG kaydı yükle/ })).toBeNull();
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
    expect(line).toHaveTextContent(/^Bu analiz size uygun değil: Bu analiz yalnız 18–89 yaş arasındaki kişiler için geliştirildi \(girdiğiniz yaş: 95\)/);
    expect(line).not.toHaveTextContent(/age_cap89|model popülasyonu|\[/); // Phase L: teknik ham metin yalnız Teknik ayrıntı
    expect(line).not.toHaveTextContent('ortamı yok');
    expect(within(item).getByTestId('panel-also-af_S4_DEVICE')).toHaveTextContent(
      /^Ayrıca: EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz\.$/,
    );
    expect(within(item).queryByRole('button', { name: /EKG kaydı yükle/ })).toBeNull();
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
      /^Ayrıca: EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz\.$/,
    );
    expect(within(item).queryByRole('button', { name: /EKG kaydı yükle/ })).toBeNull();
  });

  it('ortam varken (önceki davranış): Eksik … EKG kaydı ve yükleme bağlantısı', async () => {
    mockFetch({ elig: () => eligEmpty });
    renderApp();
    await startAll(userEvent.setup());
    const item = await screen.findByTestId('panel-af_S4_DEVICE');
    expect(item).toHaveAttribute('data-state', 'MISSING');
    expect(within(item).getByTestId('panel-line-af_S4_DEVICE')).toHaveTextContent(/^Eksik bilgi: .*EKG/);
    expect(within(item).getByRole('button', { name: /EKG kaydı yükle/ })).toBeInTheDocument();
    // teknik ayrıntıda yalnız model kimliği (ortam ayrıntısı yok)
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).toHaveTextContent('af_S4_DEVICE');
    expect(within(item).getByTestId('panel-details-af_S4_DEVICE')).not.toHaveTextContent('pipeline');
  });

  it('stateLine/alsoLine: terim sözlükten + backend gerekçeleri (yalnız sözlükteki sadeleştirme), metin uydurmaz', () => {
    const af = afOf(eligAfEnvFull);
    expect(af.af_pipeline_available).toBe(false);
    expect(af.missing_fields).toEqual([]);
    const terms = schema.ui!.terms_tr.eligibility;
    // Phase L: ham gerekçe yerine app_config > ui.reason_rules_tr sade metni (ham metin Teknik ayrıntı içinde)
    expect(stateLine(af, schema)).toBe(terms.ABSTAIN + ': ' + 'EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz.');
    expect(alsoLine(af, schema)).toBeNull();
    const old = afOf(eligAfEnvAge95);
    expect(stateLine(old, schema)).toBe(terms.OUT_OF_SCOPE + ': Bu analiz yalnız 18–89 yaş arasındaki kişiler için geliştirildi (girdiğiniz yaş: 95). '
      + '90 yaş ve üstünde bu analiz sonuç üretmez (eğitim verisinde 89 yaş üstü gizlilik nedeniyle tek değerle kodlanmıştı).');
    expect(alsoLine(old, schema)).toBe('Ayrıca: EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz.');
    // diğer modeller ortamdan etkilenmez: boş formda AF dışındaki durumlar iki fixture'da aynı
    const other = (r: unknown) =>
      (r as EligibilityResponse).models.filter((m) => m.model_id !== 'af_S4_DEVICE').map((m) => [m.model_id, m.state, m.missing_fields]);
    expect(other(eligAfEnvMissing)).toEqual(other(eligEmpty));
  });
});
