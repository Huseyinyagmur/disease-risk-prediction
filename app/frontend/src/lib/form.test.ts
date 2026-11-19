import { describe, expect, it } from 'vitest';
import { schema } from '../test/helpers';
import { buildPayload, formFields, isRequired, isVisible, parseNumber, unitOptions } from './form';

const v = (value: string | boolean | null, unit?: string) => ({ value, ...(unit ? { unit } : {}) });

describe('form tanımı /schema\'dan', () => {
  it('yalnız form_input alanları; EKG pipeline alanları formda yok', () => {
    const names = formFields(schema).map(([n]) => n);
    expect(names).toContain('age_years');
    expect(names.some((n) => n.startsWith('ecg_'))).toBe(false);
    expect(names.length).toBe(Object.values(schema.fields).filter((f) => f.form_input).length);
  });
  it('her form alanının bir bölümü var ve bölüm şemada tanımlı', () => {
    const ids = new Set(schema.form.sections.map((s) => s.id));
    for (const [n, f] of formFields(schema)) expect(ids.has(f.form_section ?? ''), n).toBe(true);
  });
});

describe('koşullu sorular (ask_when_rule)', () => {
  it('gebelik sorusu yalnız kadında', () => {
    expect(isVisible(schema, {}, 'pregnant')).toBe(false);
    expect(isVisible(schema, { sex: v('male') }, 'pregnant')).toBe(false);
    expect(isVisible(schema, { sex: v('female') }, 'pregnant')).toBe(true);
  });
  it('gebelik zorunluluğu: kadın ve yaş ≥ 18 (required_when_rule)', () => {
    expect(isRequired(schema, { sex: v('female') }, 'pregnant')).toBe(false);
    expect(isRequired(schema, { sex: v('female'), age_years: v('17.5') }, 'pregnant')).toBe(false);
    expect(isRequired(schema, { sex: v('female'), age_years: v('18') }, 'pregnant')).toBe(true);
  });
  it('son adet yaşı: kadın VE son 12 ayda adet yok', () => {
    expect(isVisible(schema, { sex: v('female') }, 'age_last_period_years')).toBe(false);
    expect(isVisible(schema, { sex: v('female'), menses_absent_12m: v(false) }, 'age_last_period_years')).toBe(false);
    expect(isVisible(schema, { sex: v('female'), menses_absent_12m: v(true) }, 'age_last_period_years')).toBe(true);
  });
  it('tansiyon ilacı yalnız tansiyon tanısı varsa; GDM yalnız kadında; diyabet ilaçları herkese (v2)', () => {
    expect(isVisible(schema, {}, 'on_bp_medication')).toBe(false);
    expect(isVisible(schema, { told_hypertension: v(true) }, 'on_bp_medication')).toBe(true);
    expect(isVisible(schema, { sex: v('male') }, 'gestational_diabetes_hx')).toBe(false);
    expect(isVisible(schema, {}, 'on_insulin')).toBe(true);
  });
});

describe('istek gövdesi (dönüşüm yok)', () => {
  it('şema biriminde sayı düz, başka birimde {value, unit} olarak gider', () => {
    const { fields } = buildPayload(schema, {
      glucose_serum_mgdl: v('5,4', 'mmol/L'),
      total_chol_mgdl: v('190', 'mg/dL'),
      age_years: v('55'),
    });
    expect(fields.glucose_serum_mgdl).toEqual({ value: 5.4, unit: 'mmol/L' });
    expect(fields.total_chol_mgdl).toBe(190);
    expect(fields.age_years).toBe(55);
  });
  it('gizli (ask_when sağlanmayan) alanlar gönderilmez', () => {
    const { fields } = buildPayload(schema, { sex: v('male'), pregnant: v(true), gestational_diabetes_hx: v(true) });
    expect(fields).toEqual({ sex: 'male' });
  });
  it('sayı olmayan girdi biçim hatası olur ve gönderilmez', () => {
    const { fields, formatErrors } = buildPayload(schema, { weight_kg: v('70kg'), height_cm: v('') });
    expect(fields).toEqual({});
    expect(formatErrors.weight_kg).toMatch(/Sayı girin/);
  });
  it('aralık denetimi frontend\'de yapılmaz (sunucu yetkili): aralık dışı değer de gönderilir', () => {
    expect(buildPayload(schema, { age_years: v('150') }).fields.age_years).toBe(150);
  });
  it('parseNumber', () => {
    expect(parseNumber('1,5')).toBe(1.5);
    expect(parseNumber('-2')).toBe(-2);
    expect(parseNumber('1e3')).toBeNull();
    expect(parseNumber('')).toBeNull();
  });
});

describe('birim seçici seçenekleri', () => {
  it('ilk seçenek şema birimi, ardından unit_conversions kaynak birimleri', () => {
    expect(unitOptions(schema, 'glucose_serum_mgdl')).toEqual(['mg/dL', 'mmol/L']);
    expect(unitOptions(schema, 'creatinine_mgdl')).toEqual(['mg/dL', 'µmol/L']);
    expect(unitOptions(schema, 'age_years')).toEqual(['yıl']);
  });
});
