import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EligibilityResponse } from '../api/types';
import eligEmpty from '../test/fixtures/eligibility_empty.json';
import eligFull from '../test/fixtures/eligibility_full.json';
import { mockFetch, renderApp, schema } from '../test/helpers';

afterEach(() => vi.unstubAllGlobals());

const lastElig = (calls: { path: string; fields?: Record<string, unknown> }[]) =>
  [...calls].reverse().find((c) => c.path === '/eligibility')?.fields;

describe('veri giriş formu', () => {
  it('bölümler ve alanlar şemadan üretilir; sabit uyarı görünür', async () => {
    mockFetch();
    renderApp();
    expect(await screen.findByTestId('section-temel')).toBeInTheDocument();
    for (const s of ['olcumler', 'oyku', 'laboratuvar', 'klinik']) expect(screen.getByTestId(`section-${s}`)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Yaş/)).toBeInTheDocument();
    expect(screen.queryByTestId('field-ecg_af_RR_Mean_Global')).toBeNull();
    // metin backend'den (fixture = backend /schema yanıtı)
    expect(screen.getByTestId('disclaimer-text')).toHaveTextContent(schema.disclaimer as string);
  });

  it('koşullu soru: kadın seçilince gebelik (zorunlu) ve GDM soruları açılır, erkekte kapanır', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    const sex = await screen.findByLabelText('Biyolojik cinsiyet');
    expect(screen.queryByTestId('field-pregnant')).toBeNull();
    await u.selectOptions(sex, 'female');
    await u.type(screen.getByLabelText(/^Yaş/), '30');
    const preg = screen.getByTestId('field-pregnant');
    expect(preg).toHaveTextContent('zorunlu');
    expect(within(preg).getByRole('option', { name: 'Bilmiyorum' })).toBeInTheDocument();
    expect(screen.getByTestId('field-gestational_diabetes_hx')).toBeInTheDocument();
    await u.selectOptions(sex, 'male');
    expect(screen.queryByTestId('field-pregnant')).toBeNull();
    expect(screen.queryByTestId('field-gestational_diabetes_hx')).toBeNull();
  });

  it('ırk sorusu isteğe bağlı, açıklamalı ve "Belirtmek istemiyorum" seçeneği var', async () => {
    mockFetch();
    renderApp();
    const f = await screen.findByTestId('field-race_ethnicity');
    expect(f).toHaveTextContent('isteğe bağlı');
    expect(f).toHaveTextContent('ABSTAIN');
    expect(within(f).getByRole('option', { name: /Belirtmek istemiyorum/ })).toBeInTheDocument();
  });

  it('birim seçici: mmol/L seçilince değer ve birim olduğu gibi sunucuya gider (frontend dönüştürmez)', async () => {
    const { calls } = mockFetch();
    const u = userEvent.setup();
    renderApp();
    const input = await screen.findByLabelText(/^Serum glukoz/, { selector: 'input' });
    await u.type(input, '5,4');
    await u.selectOptions(screen.getByLabelText('Serum glukoz (açlık şartı yok) birimi'), 'mmol/L');
    await waitFor(() => expect(lastElig(calls)?.glucose_serum_mgdl).toEqual({ value: 5.4, unit: 'mmol/L' }));
    await u.selectOptions(screen.getByLabelText('Serum glukoz (açlık şartı yok) birimi'), 'mg/dL');
    await waitFor(() => expect(lastElig(calls)?.glucose_serum_mgdl).toBe(5.4));
  });

  it('aralık hatası: sunucunun field_errors mesajı alanın altında gösterilir', async () => {
    mockFetch({
      elig: (f) =>
        f.age_years === 150
          ? { ...eligEmpty, field_errors: [{ field: 'age_years', msg: 'age_years=150 yıl makul aralık dışında [18, 120]' }] }
          : eligEmpty,
    });
    const u = userEvent.setup();
    renderApp();
    await u.type(await screen.findByLabelText(/^Yaş/), '150');
    expect(await screen.findByTestId('err-age_years')).toHaveTextContent('makul aralık dışında [18, 120]');
    expect(screen.getByLabelText(/^Yaş/)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('error-count')).toHaveTextContent('1 alanda hata');
  });

  it('biçim hatası: sayı olmayan girdi alan altında gösterilir ve hesaplama engellenir', async () => {
    const { calls } = mockFetch();
    const u = userEvent.setup();
    renderApp();
    await u.type(await screen.findByLabelText(/^Kilo/, { selector: 'input' }), 'yetmiş');
    expect(screen.getByTestId('err-weight_kg')).toHaveTextContent('Sayı girin');
    await u.click(screen.getByTestId('submit'));
    expect(screen.getByTestId('block-msg')).toHaveTextContent('alanda hata');
    expect(calls.some((c) => c.path === '/predict')).toBe(false);
  });
});

describe('canlı yönlendirme paneli', () => {
  it('durum rozetleri: Çalışabilir / Eksik: … / Kapsam dışı: … ve modül etiketleri', async () => {
    mockFetch({ elig: () => eligFull });
    renderApp();
    const fib = await screen.findByTestId('panel-fibrosis_final');
    expect(fib).toHaveAttribute('data-state', 'READY');
    expect(within(fib).getByTestId('panel-line-fibrosis_final')).toHaveTextContent('Çalışabilir');
    expect(within(fib).getByTestId('module-label')).toHaveTextContent('ana modül');
    const copd = screen.getByTestId('panel-copd_S4_DEVICE');
    expect(copd).toHaveAttribute('data-state', 'MISSING');
    expect(copd).toHaveTextContent('Eksik: Bronkodilatör ÖNCESİ FEV1, Bronkodilatör ÖNCESİ FVC');
    const an = screen.getByTestId('panel-anemia_LR16');
    expect(an).toHaveAttribute('data-state', 'OUT_OF_SCOPE');
    expect(an).toHaveTextContent('Kapsam dışı: yaş 55: kadında model popülasyonu 20–44');
    const af = screen.getByTestId('panel-af_S4_DEVICE');
    expect(af).toHaveTextContent('EKG kaydı (.hea + .dat/.mat)');
    // ana modüller üstte
    const ids = screen.getAllByTestId(/^panel-(?!line|warnings)/).map((e) => e.getAttribute('data-testid'));
    expect(ids.slice(0, 2).sort()).toEqual(['panel-af_S4_DEVICE', 'panel-fibrosis_final']);
    expect(ids[2]).toBe('panel-osteo_final');
    expect(screen.getByTestId('panel-warnings')).toHaveTextContent('Diyabet hedefini tanımlayan ölçüm');
  });

  it('Karar verilemez durumu (ör. gebelik "bilmiyorum") gerekçesiyle gösterilir', async () => {
    const e = structuredClone(eligEmpty) as unknown as EligibilityResponse;
    e.models[2] = { ...e.models[2], state: 'ABSTAIN', missing_fields: [], reasons: ['gebelik durumu "bilmiyorum": popülasyon "gebe değil" doğrulanamıyor (katı yorum)'] };
    mockFetch({ elig: () => e });
    renderApp();
    const p = await screen.findByTestId(`panel-${e.models[2].model_id}`);
    expect(p).toHaveTextContent('Karar verilemez: gebelik durumu "bilmiyorum"');
  });

  it('sunucuya ulaşılamazsa panel hata gösterir', async () => {
    const { fn } = mockFetch();
    fn.mockImplementation(async (url: string) => {
      if (String(url).endsWith('/eligibility')) throw new TypeError('Failed to fetch');
      const path = String(url).replace(/^\/api/, '');
      const body = path === '/schema' ? (await import('../test/fixtures/schema.json')).default : (await import('../test/fixtures/models.json')).default;
      return new Response(JSON.stringify(body), { status: 200 });
    });
    renderApp();
    expect(await screen.findByText(/Uygunluk sorgusu başarısız/)).toBeInTheDocument();
  });
});
