// Phase L madde 1: sunucunun ürettiği TÜM uygunluk / ret / aralık metinleri (phase_l/scripts/scan_reasons.py ile toplandı)
// ana metinde sade Türkçe görünür: snake_case kimlik, köşeli parantezli aralık veya İngilizce/teknik terim kalmaz.
import { describe, expect, it } from 'vitest';
import { schema } from '../test/helpers';
import scan from '../test/fixtures/reason_scan.json';
import { displayReasons, isTechnical, plainFieldError, plainReason, plainUnitNote } from './plain';

const reasons = Object.keys(scan.reasons);
const fieldErrors = Object.entries(scan.field_errors) as [string, { field: string | null }][];

describe('sade gerekçe metinleri', () => {
  it('tarama gerçekten metin içeriyor (boş fikstürle geçmesin)', () => {
    expect(reasons.length).toBeGreaterThan(50);
    expect(fieldErrors.length).toBeGreaterThan(30);
  });

  it.each(reasons)('gerekçe sade: %s', (raw) => {
    const p = plainReason(schema, raw);
    if (p === null) return; // ana listede hiç gösterilmez (yalnız teknik ayrıntı)
    expect(isTechnical(p.text), p.text).toBe(false);
  });

  it.each(fieldErrors)('alan hatası sade: %s', (raw, meta) => {
    const p = plainFieldError(schema, raw);
    expect(isTechnical(p), p).toBe(false);
    expect(p.length).toBeGreaterThan(5);
    void meta;
  });

  it('kilo aralık hatası alan etiketinden ortak kalıpla', () => {
    expect(plainFieldError(schema, 'weight_kg=500 kg makul aralık dışında [25, 300]')).toBe('Kilo 25–300 kg arasında olmalı.');
    expect(plainFieldError(schema, 'albumin_gdl=23 g/dL makul aralık dışında [1.0, 6.5]')).toBe('Albümin 1,0–6,5 g/dL arasında olmalı.');
  });

  it('yüzde aralığı Türkçe biçimde', () => {
    expect(plainFieldError(schema, 'hba1c_pct=46 % makul aralık dışında [3.0, 18.0]')).toBe('HbA1c %3,0–18,0 arasında olmalı.');
  });

  it('birim dönüşüm notu sade: ok ve işlem kodu yok', () => {
    const n = plainUnitNote(schema, 'albumin_gdl: 42 g/L -> 4.2 g/dL (x / 10)');
    expect(n).toBe('Albümin: 42 g/L, 4,2 g/dL olarak kullanıldı.');
    expect(isTechnical(n)).toBe(false);
  });

  it('Phase L2: tüm form alanlarının kısa adı var; aralık mesajı soru biçimli değil ve kısa', () => {
    const fields = Object.entries(schema.fields).filter(([, f]) => f.form_input);
    for (const [n] of fields) expect(schema.form.field_ui_tr?.[n]?.short, n).toBeTruthy();
    expect(plainFieldError(schema, 'age_last_period_years=150 yıl makul aralık dışında [10, 70]')).toBe('Son adet yaşı 10–70 yıl arasında olmalı.');
    for (const [n, f] of fields.filter(([, f]) => f.type === 'numeric')) {
      const [lo, hi] = f.plausible_range as [number, number];
      const msg = plainFieldError(schema, `${n}=${hi * 2 + 10} ${f.unit} makul aralık dışında [${lo}, ${hi}]`);
      expect(msg, n).not.toMatch(/\?/);
      expect(msg.length, msg).toBeLessThanOrEqual(64);
      expect(isTechnical(msg), msg).toBe(false);
    }
  });

  it('gebelik "bilmiyorum" metni', () => {
    expect(plainReason(schema, 'gebelik durumu "bilmiyorum": popülasyon "gebe değil" doğrulanamıyor (katı yorum)')?.text)
      .toBe('Gebelik durumu bilinmediği için bu analiz yapılamadı; model gebe olmayan kişilerde geliştirildi.');
  });

  it('model girdi aralığı satırı, sade yaş satırı varken ana listede gösterilmez', () => {
    const shown = displayReasons(schema, ['yaş 30 model popülasyonu dışında (≥ 50)', 'age=30 yıl model girdi aralığı dışında [50, 80]']);
    expect(shown).toEqual(['Bu analiz yalnız 50 yaş ve üstündeki kişiler için geliştirildi (girdiğiniz yaş: 30).']);
  });

  it('model girdi aralığı tek nedense sade biçimde gösterilir', () => {
    const shown = displayReasons(schema, ['bmi=111.11 kg/m2 model girdi aralığı dışında [12, 80]']);
    expect(shown).toHaveLength(1);
    expect(shown[0]).toContain('Vücut kitle indeksi');
    expect(isTechnical(shown[0])).toBe(false);
  });

  it('tanınmayan teknik metin genel sade satıra düşer', () => {
    expect(plainReason(schema, 'beklenmeyen_durum [1, 2] pipeline')?.text).toBe(schema.ui!.text_tr.reason_fallback);
  });

  it('isTechnical kendisi doğru ayırır', () => {
    expect(isTechnical('age=30 yıl model girdi aralığı dışında [50, 80]')).toBe(true);
    expect(isTechnical('Kilo 25–300 kg arasında olmalı.')).toBe(false);
  });
});
