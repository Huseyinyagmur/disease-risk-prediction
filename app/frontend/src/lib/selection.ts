// Phase XLVII: analiz seçimi ve sihirbaz adımları. Alan listesi ELLE TUTULMAZ: seçilen hastalıkların modellerine ait
// gerekli + koşullu alanlar backend /schema > models listesinden alınır. Model/uygunluk mantığı burada yoktur.
import type { ModelInfo, Schema } from '../api/types';
import { formFields, isVisible, type FormValues } from './form';

export interface AnalysisOption {
  diseaseKey: string;
  moduleLabel: string;
  modelIds: string[];
}

const MODULE_ORDER: Record<string, number> = { 'ana modül': 0, 'araştırma modülü': 1 };
const rank = (label: string) => MODULE_ORDER[label] ?? 2;

/** /models listesinden hastalık başına seçenekler (aynı hastalığın A/B modelleri tek seçenek). Sıra: ana → araştırma → deneysel. */
export function analysisOptions(models: ModelInfo[]): AnalysisOption[] {
  const by = new Map<string, AnalysisOption>();
  for (const m of models) {
    const o = by.get(m.disease_key) ?? { diseaseKey: m.disease_key, moduleLabel: m.module_label, modelIds: [] };
    o.modelIds.push(m.model_id);
    if (rank(m.module_label) < rank(o.moduleLabel)) o.moduleLabel = m.module_label;
    by.set(m.disease_key, o);
  }
  return [...by.values()].sort((a, b) => rank(a.moduleLabel) - rank(b.moduleLabel));
}

/** Seçilen hastalıkların gerektirdiği form alanları (backend gerekli alan listesinden). */
export function fieldsForSelection(schema: Schema, models: ModelInfo[], selected: string[]): Set<string> {
  const keys = new Set(selected);
  const out = new Set<string>();
  for (const m of models) {
    if (!keys.has(m.disease_key)) continue;
    const req = schema.models?.[m.model_id] ?? m.fields;
    for (const f of [...req.required, ...req.conditional]) if (schema.fields[f]?.form_input) out.add(f);
  }
  return out;
}

export const SELECT_STEP = 'select';
export const REVIEW_STEP = 'review';

/** Sihirbaz adımları: analiz seçimi → (seçime göre görünür alanı olan) form bölümleri → kontrol ve hesaplama. */
export function wizardSteps(schema: Schema, values: FormValues, allowed: Set<string>, hasSelection: boolean): string[] {
  if (!hasSelection) return [SELECT_STEP];
  const visible = formFields(schema).filter(([n]) => allowed.has(n) && isVisible(schema, values, n));
  const secs = schema.form.sections.map((s) => s.id).filter((id) => visible.some(([, f]) => f.form_section === id));
  return [SELECT_STEP, ...secs, REVIEW_STEP];
}
