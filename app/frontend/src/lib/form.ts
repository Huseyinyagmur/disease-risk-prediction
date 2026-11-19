// Form durumu ve istek gövdesi. Bu dosyada birim dönüşümü, eşik, olasılık veya uygunluk kararı YOKTUR:
// değer ve seçilen birim olduğu gibi backend'e gönderilir. Yalnız sunucunun ayrıştırdığı ask_when_rule /
// required_when_rule koşulları (eşitlik / ≥) sorunun gösterilip gösterilmeyeceği için değerlendirilir.
import type { FieldSpec, Rule, Schema } from '../api/types';

export type Answer = string | boolean | null;

export interface FieldValue {
  value: Answer; // sayısal alanlarda kullanıcının yazdığı metin
  unit?: string; // sayısal alanlarda seçilen birim (varsayılan: şema birimi)
}

export type FormValues = Record<string, FieldValue>;

export function formFields(schema: Schema): [string, FieldSpec][] {
  return Object.entries(schema.fields).filter(([, f]) => f.form_input);
}

/** Şema alanının o anki ham yanıtı (koşul değerlendirmesi için). Sayısal alanlarda yalnız şema biriminde sayı. */
function ruleValue(schema: Schema, values: FormValues, field: string): Answer | number {
  const v = values[field];
  if (!v || v.value === null || v.value === '') return null;
  const spec = schema.fields[field];
  if (spec?.type === 'numeric') {
    if (v.unit && v.unit !== spec.unit) return null; // yaş vb. tek birimli; farklı birimde koşul değerlendirilmez
    const n = parseNumber(String(v.value));
    return n === null ? null : n;
  }
  return v.value;
}

export function rulesHold(schema: Schema, values: FormValues, rules: Rule[] | undefined): boolean {
  if (!rules || rules.length === 0) return true;
  return rules.every((r) => {
    const v = ruleValue(schema, values, r.field);
    if (v === null) return false;
    if (r.op === 'eq') return v === r.value;
    return typeof v === 'number' && v >= Number(r.value);
  });
}

export function isVisible(schema: Schema, values: FormValues, name: string): boolean {
  const spec = schema.fields[name];
  if (!spec || !spec.form_input) return false;
  return rulesHold(schema, values, spec.ask_when_rule);
}

export function isRequired(schema: Schema, values: FormValues, name: string): boolean {
  const spec = schema.fields[name];
  return !!spec?.required_when_rule && rulesHold(schema, values, spec.required_when_rule);
}

/** Ondalık virgül kabul edilir ("5,2" -> 5.2). Bu bir yazım ayrıştırmasıdır, birim dönüşümü değildir. */
export function parseNumber(text: string): number | null {
  const t = text.trim().replace(',', '.');
  if (t === '' || !/^[-+]?(\d+\.?\d*|\.\d+)$/.test(t)) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

export function unitOptions(schema: Schema, name: string): string[] {
  const base = schema.fields[name]?.unit;
  const extra = (schema.unit_conversions[name] ?? []).map((u) => u.from_unit);
  return base ? [base, ...extra.filter((u) => u !== base)] : extra;
}

export interface BuiltPayload {
  fields: Record<string, unknown>;
  formatErrors: Record<string, string>; // sayı olarak okunamayan değerler (gönderilmez)
}

/** Görünür ve yanıtlanmış alanlardan istek gövdesi. Gizli (ask_when sağlanmayan) alanlar gönderilmez. */
export function buildPayload(schema: Schema, values: FormValues): BuiltPayload {
  const fields: Record<string, unknown> = {};
  const formatErrors: Record<string, string> = {};
  for (const [name, spec] of formFields(schema)) {
    const v = values[name];
    if (!v || v.value === null || v.value === '') continue;
    if (!isVisible(schema, values, name)) continue;
    if (spec.type === 'numeric') {
      const n = parseNumber(String(v.value));
      if (n === null) {
        formatErrors[name] = 'Sayı girin (ondalık ayırıcı nokta veya virgül).';
        continue;
      }
      fields[name] = v.unit && v.unit !== spec.unit ? { value: n, unit: v.unit } : n;
    } else {
      fields[name] = v.value;
    }
  }
  return { fields, formatErrors };
}

export function fieldLabel(schema: Schema | null, name: string): string {
  if (!schema) return name;
  return schema.fields[name]?.label_tr ?? schema.form.virtual_field_labels_tr[name] ?? name;
}

export function categoryLabel(schema: Schema, field: string, cat: string | boolean): string {
  const key = String(cat);
  const own = schema.form.category_labels_tr[field]?.[key];
  if (own) return own;
  if (typeof cat === 'boolean' || key === 'unknown') return schema.form.category_labels_tr._boolean?.[key] ?? key;
  return key;
}
