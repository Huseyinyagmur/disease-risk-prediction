// Phase L: sunucu gerekçe ve alan hatası metinlerinin sade Türkçe karşılığı. Kurallar app_config > ui.reason_rules_tr ve
// ui.field_error_rules_tr içindedir (TEK KAYNAK); burada yalnız uygulanır. Ham metin "Teknik ayrıntı" içinde kalır.
// Yalnız gösterim: durum kodu, uygunluk kararı veya model mantığı burada değişmez.
import type { Schema, TextRule } from '../api/types';
import { fieldLabel } from './form';
import { humanize } from './ui';

export interface PlainReason {
  text: string;
  /** Aynı listede başka sade satır varsa gizlenir (ör. "model girdi aralığı" satırı; sade yaş satırı zaten var). */
  secondary: boolean;
}

const TECH = [
  /\b[a-z][a-z0-9]*_[a-z0-9_]+\b/, // snake_case kimlik
  /\[[^\]]*\]/, // köşeli parantezli aralık / liste
  /\w=\S/, // alan=değer
  /model popülasyonu|model girdi aralığı|makul aralık|şemada|doğrulanamıyor|katı yorum/i,
  /\b(pipeline|feature|policy|POST|pre-BD|NaN|schema|endpoint)\b/i,
];

/** Ana metinde kalmaması gereken teknik iz var mı? */
export function isTechnical(s: string): boolean {
  return TECH.some((re) => re.test(s));
}

function num(x: string): string {
  if (!/^-?\d+(\.\d+)?$/.test(x)) return x;
  const dec = x.split('.')[1]?.length ?? 0;
  return (dec > 2 ? Number(x).toFixed(1) : x).replace('.', ',');
}

function unitText(schema: Schema, u: string | undefined | null): string {
  if (!u) return '';
  return schema.ui?.unit_display_tr?.[u] ?? u;
}

function apply(schema: Schema, rule: TextRule, m: RegExpMatchArray): string {
  const g1 = m[1] ?? '';
  let s = (rule.text ?? '')
    .replace(/\{feature\}/g, schema.ui?.feature_labels_tr?.[g1] ?? fieldLabel(schema, g1))
    .replace(/\{label\}/g, fieldLabel(schema, g1))
    .replace(/\{short\}/g, schema.form.field_ui_tr?.[g1]?.short ?? fieldLabel(schema, g1)) // Phase L2: kısa ad
    .replace(/\{unit\}/g, unitText(schema, schema.fields[g1]?.unit))
    .replace(/\{unit(\d)\}/g, (_, i: string) => unitText(schema, m[Number(i)]));
  s = s.replace(/\$(\d)/g, (_, i: string) => num(m[Number(i)] ?? ''));
  s = s.replace(/(-?\d[\d,]*)–(-?\d[\d,]*) %/g, '%$1–$2'); // Türkçe yüzde biçimi: %3,0–18,0
  return s.replace(/\s+([.,;)])/g, '$1').replace(/\s{2,}/g, ' ').trim();
}

function match(rules: TextRule[] | undefined, raw: string): [TextRule, RegExpMatchArray] | null {
  for (const r of rules ?? []) {
    const m = raw.match(new RegExp(r.re, 'u'));
    if (m) return [r, m];
  }
  return null;
}

/** Tek gerekçe → sade metin; null = ana listede gösterilmez. Kural yoksa sözlük sadeleştirmesi (humanize) denenir;
 * sonuç hâlâ teknikse genel sade satır gösterilir. */
export function plainReason(schema: Schema | null, raw: string): PlainReason | null {
  if (!schema) return { text: raw, secondary: false };
  const hit = match(schema.ui?.reason_rules_tr, raw);
  if (hit) {
    const [rule, m] = hit;
    if (rule.hide) return null;
    return { text: apply(schema, rule, m), secondary: !!rule.hide_if_other };
  }
  const h = humanize(schema, raw);
  return { text: isTechnical(h) ? schema.ui?.text_tr.reason_fallback ?? h : h, secondary: false };
}

/** Gerekçe listesinin ana metinde gösterilecek sade hali (gizlenenler çıkarılır, tekrarlar birleştirilir). */
export function displayReasons(schema: Schema | null, raws: string[]): string[] {
  const ps = raws.map((r) => plainReason(schema, r)).filter((p): p is PlainReason => p !== null);
  const hasPrimary = ps.some((p) => !p.secondary);
  return [...new Set(ps.filter((p) => !p.secondary || !hasPrimary).map((p) => p.text))];
}

/** Alan doğrulama hatası (422 / field_errors) → sade metin (ör. "Kilo 25–300 kg arasında olmalı."). */
export function plainFieldError(schema: Schema | null, raw: string): string {
  if (!schema) return raw;
  const hit = match(schema.ui?.field_error_rules_tr, raw);
  if (hit) return apply(schema, hit[0], hit[1]);
  const h = humanize(schema, raw);
  return isTechnical(h) ? schema.ui?.text_tr.field_error_fallback ?? h : h;
}

/** Sunucu birim dönüşüm notu (ör. "albumin_gdl: 42 g/L -> 4.2 g/dL (x / 10)") → sade metin; işlem kodu yalnız Teknik ayrıntı. */
export function plainUnitNote(schema: Schema | null, raw: string): string {
  if (!schema) return raw;
  const hit = match(schema.ui?.unit_note_rules_tr, raw);
  return hit ? apply(schema, hit[0], hit[1]) : humanize(schema, raw);
}
