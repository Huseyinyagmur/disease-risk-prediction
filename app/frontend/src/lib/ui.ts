// Phase XLVII: arayüz metinleri. TEK KAYNAK backend app_config.json (> ui ve > form.field_ui_tr), /schema yanıtıyla
// gelir. Bu dosyada görünür metin TUTULMAZ; yalnız anahtar → metin eşlemesi ve yer tutucu doldurma yapılır.
// Eksik anahtar "⟦anahtar⟧" olarak görünür (testler DOM'da "⟦" olmadığını denetler).
import type { ModelResult, Outcome, Schema } from '../api/types';

export const MISSING_MARK = '⟦';

export type Vars = Record<string, string | number>;

export function fill(s: string, vars?: Vars): string {
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}

export function t(schema: Schema | null, key: string, vars?: Vars): string {
  const s = schema?.ui?.text_tr[key];
  return s === undefined ? `${MISSING_MARK}${key}⟧` : fill(s, vars);
}

/** Durum terimi (sözlük). kind: eligibility (canlı panel) | result | decision | tiers. */
export function term(schema: Schema | null, kind: 'eligibility' | 'result' | 'decision' | 'tiers', code: string): string {
  return schema?.ui?.terms_tr[kind]?.[code] ?? `${MISSING_MARK}${kind}.${code}⟧`;
}

export function modelName(schema: Schema | null, modelId: string, fallback: string): string {
  return schema?.ui?.model_names_tr[modelId] ?? fallback;
}

export function outcomeOf(r: Pick<ModelResult, 'status' | 'decision'>): Outcome {
  if (r.status === 'OK' && r.decision) return r.decision.research_class;
  return r.status === 'NOT_APPLICABLE' ? 'NOT_APPLICABLE' : 'ABSTAIN';
}

/** Yönlendirme metni (next_steps_tr): hastalığa özgü metin, yoksa varsayılan. */
export function nextStep(schema: Schema | null, diseaseKey: string, outcome: Outcome): string {
  const ns = schema?.ui?.next_steps_tr;
  return ns?.[diseaseKey]?.[outcome] ?? ns?._default?.[outcome] ?? `${MISSING_MARK}next_steps.${outcome}⟧`;
}

/** Sunucu gerekçe/not metnindeki ham alan adlarını sade etiketlere çevirir ve sözlükteki teknik ifadeleri sadeleştirir.
 * Yalnız gösterim; ham metin "Teknik ayrıntı" içinde ayrıca gösterilir. */
export function humanize(schema: Schema | null, text: string): string {
  if (!schema) return text;
  let out = text;
  for (const [a, b] of schema.ui?.reason_replacements_tr ?? []) out = out.split(a).join(b);
  const names = Object.keys(schema.fields).sort((a, b) => b.length - a.length);
  for (const n of names) {
    if (!out.includes(n)) continue;
    const lab = schema.form.field_ui_tr?.[n]?.label ?? schema.fields[n].label_tr;
    out = out.replace(new RegExp(`(?<![\\w])${n}(?![\\w])`, 'g'), lab);
  }
  return out;
}
