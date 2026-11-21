import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EligibilityResponse } from '../api/types';
import eligEmpty from '../test/fixtures/eligibility_empty.json';
import eligFull from '../test/fixtures/eligibility_full.json';
import { goStep, mockFetch, renderApp, schema, selectOnly, startAll } from '../test/helpers';

afterEach(() => vi.unstubAllGlobals());

const lastElig = (calls: { path: string; fields?: Record<string, unknown> }[]) =>
  [...calls].reverse().find((c) => c.path === '/eligibility')?.fields;

describe('veri giriş formu (sihirbaz)', () => {
  it('ilk adım analiz seçimi; bölümler ve alanlar şemadan üretilir; sabit uyarı görünür', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    expect(await screen.findByTestId('analysis-select')).toBeInTheDocument();
    expect(screen.getByTestId('step-title')).toHaveTextContent(schema.ui!.text_tr.select_title);
    expect(screen.queryByTestId('section-temel')).toBeNull();
    await startAll(u);
    for (const s of ['olcumler', 'oyku', 'laboratuvar', 'klinik', 'review']) expect(screen.getByTestId(`step-${s}`)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Yaş/)).toBeInTheDocument();
    expect(screen.queryByTestId('field-ecg_af_RR_Mean_Global')).toBeNull();
    expect(screen.getByTestId('disclaimer-text')).toHaveTextContent(schema.disclaimer as string);
  });

  it('koşullu soru: kadın seçilince gebelik (zorunlu) ve GDM soruları açılır, erkekte kapanır', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    const sex = screen.getByLabelText('Biyolojik cinsiyet');
    expect(screen.queryByTestId('field-pregnant')).toBeNull();
    await u.selectOptions(sex, 'female');
    await u.type(screen.getByLabelText(/^Yaş/), '30');
    const preg = screen.getByTestId('field-pregnant');
    expect(preg).toHaveTextContent('zorunlu');
    expect(within(preg).getByRole('option', { name: 'Bilmiyorum' })).toBeInTheDocument();
    await goStep(u, 'oyku');
    expect(screen.getByTestId('field-gestational_diabetes_hx')).toBeInTheDocument();
    await goStep(u, 'temel');
    await u.selectOptions(screen.getByLabelText('Biyolojik cinsiyet'), 'male');
    expect(screen.queryByTestId('field-pregnant')).toBeNull();
    await goStep(u, 'oyku');
    expect(screen.queryByTestId('field-gestational_diabetes_hx')).toBeNull();
  });

  it('ırk sorusu isteğe bağlı, sade açıklamalı ve "Belirtmek istemiyorum" seçeneği var; NHANES kodu yalnız teknik ayrıntıda', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    const f = screen.getByTestId('field-race_ethnicity');
    expect(f).toHaveTextContent('isteğe bağlı');
    expect(f).toHaveTextContent('sonuç üretmez');
    expect(f).not.toHaveTextContent('RIDRETH1');
    expect(f).not.toHaveTextContent('ABSTAIN');
    expect(within(f).getByRole('option', { name: /Belirtmek istemiyorum/ })).toBeInTheDocument();
    const btn = within(f).getByTestId('tech-btn-race_ethnicity');
    expect(btn).toHaveAttribute('aria-expanded', 'false');
    await u.click(btn);
    expect(btn).toHaveAttribute('aria-expanded', 'true');
    const tech = within(f).getByTestId('tech-race_ethnicity');
    expect(tech).toHaveTextContent('NHANES RIDRETH1');
    expect(tech).toHaveTextContent('race_ethnicity');
    expect(btn).toHaveAttribute('aria-controls', tech.id);
  });

  it('birim seçici: mmol/L seçilince değer ve birim olduğu gibi sunucuya gider (frontend dönüştürmez)', async () => {
    const { calls } = mockFetch();
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    await goStep(u, 'laboratuvar');
    const input = screen.getByLabelText(/^Kan şekeri \(açlık gerekmez\)/, { selector: 'input' });
    await u.type(input, '5,4');
    await u.selectOptions(screen.getByLabelText('Kan şekeri (açlık gerekmez) birimi'), 'mmol/L');
    await waitFor(() => expect(lastElig(calls)?.glucose_serum_mgdl).toEqual({ value: 5.4, unit: 'mmol/L' }));
    await u.selectOptions(screen.getByLabelText('Kan şekeri (açlık gerekmez) birimi'), 'mg/dL');
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
    await startAll(u);
    await u.type(screen.getByLabelText(/^Yaş/), '150');
    expect(await screen.findByTestId('err-age_years')).toHaveTextContent('makul aralık dışında [18, 120]');
    expect(screen.getByLabelText(/^Yaş/)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText(/^Yaş/).getAttribute('aria-describedby')).toContain('err-age_years');
    expect(screen.getByTestId('error-count')).toHaveTextContent('1 alanda hata');
  });

  it('biçim hatası: alan altında gösterilir; hesaplama engellenir ve hatalı adıma bağlantı verilir', async () => {
    const { calls } = mockFetch();
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    await goStep(u, 'olcumler');
    await u.type(screen.getByLabelText(/^Kilo/, { selector: 'input' }), 'yetmiş');
    expect(screen.getByTestId('err-weight_kg')).toHaveTextContent('Sayı girin');
    await goStep(u, 'review');
    await u.click(screen.getByTestId('submit'));
    expect(screen.getByTestId('block-msg')).toHaveTextContent('alanda hata');
    expect(calls.some((c) => c.path === '/predict')).toBe(false);
    await u.click(screen.getByTestId('error-step-olcumler'));
    expect(screen.getByTestId('err-weight_kg')).toBeInTheDocument();
  });
});

describe('analiz seçimine göre alan filtreleme (backend gerekli alan listesi)', () => {
  const modelFields = (ids: string[]) => {
    const s = new Set<string>();
    for (const id of ids) for (const f of [...schema.models![id].required, ...schema.models![id].conditional]) if (schema.fields[f]?.form_input) s.add(f);
    return s;
  };
  const shownFields = () => [...document.querySelectorAll('[data-testid^="field-"]')].map((e) => e.getAttribute('data-testid')!.slice(6));

  async function collectAllSteps(u: ReturnType<typeof userEvent.setup>) {
    const ids = [...screen.getByTestId('wizard-steps').querySelectorAll('button[data-testid^="step-"]')]
      .map((e) => e.getAttribute('data-testid')!.slice(5))
      .filter((s) => s !== 'select' && s !== 'review');
    const seen = new Set<string>();
    for (const id of ids) {
      await goStep(u, id);
      shownFields().forEach((f) => seen.add(f));
    }
    return { ids, seen };
  }

  it('yalnız karaciğer fibrozisi: form yalnız fibrosis_final alanlarını gösterir; klinik adımı yok; istek yalnız bu alanları taşır', async () => {
    const { calls } = mockFetch();
    const u = userEvent.setup();
    renderApp();
    await selectOnly(u, ['liver_fibrosis']);
    await u.click(screen.getByTestId('profile-fibrosis_ready')); // tüm alanları dolduran sentetik profil
    const { ids, seen } = await collectAllSteps(u);
    expect(ids).toEqual(['temel', 'olcumler', 'oyku', 'laboratuvar']);
    const expected = modelFields(['fibrosis_final']);
    for (const f of seen) expect(expected.has(f)).toBe(true);
    expect(seen.has('alt_ul') && seen.has('platelets_k_ul')).toBe(true);
    expect(seen.has('fracture_hip') || seen.has('fev1_pre_ml') || seen.has('cad_st_slope')).toBe(false);
    await waitFor(() => expect(Object.keys(lastElig(calls) ?? {})).toContain('alt_ul'));
    for (const k of Object.keys(lastElig(calls)!)) expect(expected.has(k)).toBe(true);
    expect(lastElig(calls)!.fracture_hip).toBeUndefined();
  });

  it('yalnız osteoporoz: tahlil adımı yok; kırık soruları var', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await selectOnly(u, ['osteoporosis']);
    const { ids, seen } = await collectAllSteps(u);
    expect(ids).not.toContain('laboratuvar');
    expect(ids).not.toContain('klinik');
    expect(seen.has('fracture_hip')).toBe(true);
    for (const f of seen) expect(modelFields(['osteo_final']).has(f)).toBe(true);
  });

  it('yalnız AF: yalnız yaş ve cinsiyet sorulur; EKG notu gösterilir', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await selectOnly(u, ['af']);
    const { ids, seen } = await collectAllSteps(u);
    expect(ids).toEqual(['temel']);
    expect([...seen].sort()).toEqual(['age_years', 'sex']);
    await goStep(u, 'temel');
    expect(screen.getByTestId('af-form-note')).toHaveTextContent('EKG');
  });

  it('Tümü: tüm modellerin alanları (birleşim); deneysel grup varsayılan kapalı', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    expect((await screen.findByTestId('group-deneysel')).hasAttribute('open')).toBe(false);
    await u.click(screen.getByTestId('select-all'));
    expect(screen.getByTestId('selected-count')).toHaveTextContent('9 analiz seçildi');
    const { ids, seen } = await collectAllSteps(u);
    expect(ids).toEqual(['temel', 'olcumler', 'oyku', 'laboratuvar', 'klinik']);
    const union = modelFields(Object.keys(schema.models!));
    for (const f of seen) expect(union.has(f)).toBe(true);
    expect(seen.has('rip3_pgml')).toBe(false); // hiçbir uygulama modeli kullanmıyor
  });

  it('canlı panel yalnız seçilen analizleri gösterir', async () => {
    mockFetch({ elig: () => eligFull });
    const u = userEvent.setup();
    renderApp();
    expect(await screen.findByTestId('panel-empty')).toBeInTheDocument();
    await selectOnly(u, ['liver_fibrosis', 'osteoporosis']);
    await screen.findByTestId('panel-fibrosis_final');
    const ids = screen.getAllByTestId(/^panel-(?!line|warnings|empty|also|details)/).map((e) => e.getAttribute('data-testid'));
    expect(ids).toEqual(['panel-fibrosis_final', 'panel-osteo_final']);
    expect(screen.queryByTestId('panel-warnings')).toBeNull(); // diyabet uyarısı seçilmeyen analize ait
  });
});

describe('sihirbaz gezinme', () => {
  it('ileri/geri, ilerleme çubuğu ve adım sayacı; veri adımlar arasında bellekte kalır; odak başlığa taşınır', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await screen.findByTestId('analysis-select');
    expect(screen.getByTestId('wizard-next')).toBeDisabled(); // seçim yok
    expect(screen.getByTestId('select-required')).toBeInTheDocument();
    expect(screen.queryByTestId('submit')).toBeNull();
    await u.click(screen.getByTestId('select-all'));
    const bar = screen.getByTestId('wizard-progress');
    expect(bar).toHaveAttribute('aria-valuenow', '1');
    expect(bar).toHaveAttribute('aria-valuemax', '7');
    await u.click(screen.getByTestId('wizard-next'));
    expect(screen.getByTestId('step-of')).toHaveTextContent('Adım 2 / 7');
    expect(screen.getByTestId('step-title')).toHaveFocus();
    expect(screen.getByTestId('step-temel')).toHaveAttribute('aria-current', 'step');
    await u.type(screen.getByLabelText(/^Yaş/), '58');
    await u.click(screen.getByTestId('wizard-next'));
    expect(screen.getByTestId('section-olcumler')).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Yaş/)).toBeNull();
    await u.click(screen.getByTestId('wizard-back'));
    expect(screen.getByLabelText(/^Yaş/)).toHaveValue('58');
    await goStep(u, 'review');
    expect(screen.getByTestId('wizard-next')).toBeDisabled();
    expect(screen.getByTestId('review-temel')).toHaveTextContent('1 /');
    await goStep(u, 'select');
    expect(screen.getByTestId('wizard-back')).toBeDisabled();
  });

  it('örnek profil, seçim yokken "Tümü"nü seçer; hesapla butonu form sonunda (sabit/üst üste binen çubuk değil)', async () => {
    mockFetch();
    const u = userEvent.setup();
    renderApp();
    await u.click(await screen.findByTestId('profile-fibrosis_ready'));
    expect(screen.getByTestId('selected-count')).toHaveTextContent('9 analiz seçildi');
    const bar = screen.getByTestId('wizard-bar');
    expect(bar.className).not.toMatch(/\b(sticky|fixed)\b/);
    expect(bar.closest('form')).not.toBeNull();
    expect(within(bar).getByTestId('submit')).toBeInTheDocument();
  });
});

describe('canlı yönlendirme paneli', () => {
  it('durum terimleri sözlükten: Hesaplanabilir / Eksik bilgi: … / Bu analiz size uygun değil: … ve modül etiketleri', async () => {
    mockFetch({ elig: () => eligFull });
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    const fib = await screen.findByTestId('panel-fibrosis_final');
    expect(fib).toHaveAttribute('data-state', 'READY');
    expect(within(fib).getByTestId('panel-line-fibrosis_final')).toHaveTextContent('Hesaplanabilir');
    expect(within(fib).getByTestId('module-label')).toHaveTextContent('ana modül');
    // model kimliği yalnız (kapalı) teknik ayrıntıda
    const det = within(fib).getByTestId('panel-details-fibrosis_final') as HTMLDetailsElement;
    expect(det.open).toBe(false);
    expect(det).toHaveTextContent('fibrosis_final');
    const outside = fib.cloneNode(true) as HTMLElement;
    outside.querySelector('[data-testid="panel-details-fibrosis_final"]')!.remove();
    expect(outside).not.toHaveTextContent('fibrosis_final');
    const copd = screen.getByTestId('panel-copd_S4_DEVICE');
    expect(copd).toHaveAttribute('data-state', 'MISSING');
    expect(within(copd).getByTestId('panel-line-copd_S4_DEVICE')).toHaveTextContent(
      'Eksik bilgi: FEV1 — bronş açıcı ilaç öncesi, FVC — bronş açıcı ilaç öncesi',
    );
    const an = screen.getByTestId('panel-anemia_LR16');
    expect(an).toHaveAttribute('data-state', 'OUT_OF_SCOPE');
    expect(an).toHaveTextContent('Bu analiz size uygun değil: yaş 55: kadında analizin geliştirildiği grup 20–44');
    const af = screen.getByTestId('panel-af_S4_DEVICE');
    expect(af).toHaveTextContent('EKG kaydı (.hea + .dat/.mat)');
    const ids = screen.getAllByTestId(/^panel-(?!line|warnings|also|details)/).map((e) => e.getAttribute('data-testid'));
    expect(ids.slice(0, 2).sort()).toEqual(['panel-af_S4_DEVICE', 'panel-fibrosis_final']);
    expect(ids[2]).toBe('panel-osteo_final');
    expect(screen.getByTestId('panel-warnings')).toHaveTextContent('Diyabet hedefini tanımlayan ölçüm');
  });

  it('Sonuç üretilemez durumu (ör. gebelik "bilmiyorum") gerekçesiyle gösterilir', async () => {
    const e = structuredClone(eligEmpty) as unknown as EligibilityResponse;
    e.models[2] = { ...e.models[2], state: 'ABSTAIN', missing_fields: [], reasons: ['gebelik durumu "bilmiyorum": popülasyon "gebe değil" doğrulanamıyor (katı yorum)'] };
    mockFetch({ elig: () => e });
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    const p = await screen.findByTestId(`panel-${e.models[2].model_id}`);
    expect(p).toHaveTextContent('Sonuç üretilemez: gebelik durumu "bilmiyorum"');
  });

  it('sunucuya ulaşılamazsa panel hata gösterir', async () => {
    const { fn } = mockFetch();
    fn.mockImplementation(async (url: string) => {
      if (String(url).endsWith('/eligibility')) throw new TypeError('Failed to fetch');
      const path = String(url).replace(/^\/api/, '');
      const body = path === '/schema' ? (await import('../test/fixtures/schema.json')).default : (await import('../test/fixtures/models.json')).default;
      return new Response(JSON.stringify(body), { status: 200 });
    });
    const u = userEvent.setup();
    renderApp();
    await startAll(u);
    expect(await screen.findByText(/Durum sorgusu başarısız/)).toBeInTheDocument();
  });
});
