// Backend (app/backend) yanıt tipleri. Yalnız gösterim için kullanılır; olasılık/eşik alanı YOKTUR.

export type Rule = { field: string; op: 'eq' | 'gte'; value: string | number | boolean };

export interface FieldSpec {
  label_tr: string;
  type: 'numeric' | 'categorical' | 'boolean' | 'device';
  input_source?: string;
  unit?: string;
  plausible_range?: [number, number];
  categories?: (string | boolean)[];
  note?: string;
  ask_when?: string;
  required_when?: string;
  ask_when_rule?: Rule[];
  required_when_rule?: Rule[];
  form_input: boolean;
  form_section: string | null;
}

export interface UnitOption {
  from_unit: string;
  to_unit: string;
  op: string;
}

export interface FormSection {
  id: string;
  title_tr: string;
  optional: boolean;
  description_tr?: string;
}

export interface Schema {
  schema_version: string;
  fields: Record<string, FieldSpec>;
  unit_conversions: Record<string, UnitOption[]>;
  form: {
    sections: FormSection[];
    category_labels_tr: Record<string, Record<string, string>>;
    virtual_field_labels_tr: Record<string, string>;
    /** Phase XLVII: sade etiket / yardım / kaynak değişken (yalnız sunum; app_config.json > form.field_ui_tr). */
    field_ui_tr?: Record<string, FieldUi>;
  };
  policy: Record<string, unknown>;
  /** Backend'in model başına gerekli alan listesi (tek kaynak; arayüzde elle liste tutulmaz). */
  models?: Record<string, { required: string[]; conditional: string[] }>;
  /** Phase XLVII: arayüz metinleri (app_config.json > ui; tek kaynak). */
  ui?: UiText;
  disclaimer?: string;
}

export interface FieldUi {
  label: string;
  help?: string;
  source?: string;
}

export type Outcome = 'ESIK_USTU' | 'ESIK_ALTI' | 'ABSTAIN' | 'NOT_APPLICABLE';

export interface UiText {
  terms_tr: {
    eligibility: Record<string, string>;
    result: Record<string, string>;
    decision: Record<string, string>;
    tiers: Record<string, string>;
  };
  glossary_tr: { term: string; code: string; text: string }[];
  disease_names_tr: Record<string, string>;
  disease_hints_tr: Record<string, string>;
  model_names_tr: Record<string, string>;
  evidence_plain_tr: Record<string, string>;
  next_steps_tr: Record<string, Partial<Record<Outcome, string>>>;
  analysis_groups_tr: { module_label: string; title: string; description: string; collapsed?: boolean }[];
  reason_replacements_tr?: [string, string][];
  text_tr: Record<string, string>;
}

export interface Metric {
  value: number;
  ci95?: [number, number];
}

export interface Tier {
  source?: string;
  n?: number;
  n_pos?: number | null;
  precision?: Metric | null;
  recall?: Metric | null;
  fpr?: Metric | null;
  auc?: Metric | null;
  npv?: Metric | number | null;
  tier_label: string;
  [k: string]: unknown;
}

export interface Evidence {
  highest_tier?: string;
  research_target_note?: string;
  tiers: Partial<Record<'internal_test' | 'temporal' | 'external', Tier>>;
  note?: string;
}

export interface ModelInfo {
  model_id: string;
  disease: string;
  disease_key: string;
  role: string;
  app_mode: string;
  module_label: string;
  enabled: boolean;
  endpoint: string;
  fields: { required: string[]; conditional: string[] };
  target_definition: string;
  population: string;
  missing_input_rule: string;
  evidence: Evidence;
  limitations: string[];
  schema_v2_changes: { feature: string; old_transform: string; new_transform: string; reason: string }[];
}

export type EligState = 'READY' | 'MISSING' | 'OUT_OF_SCOPE' | 'ABSTAIN';

export interface EligModel {
  model_id: string;
  disease: string;
  disease_key: string;
  role: string;
  app_mode: string;
  module_label: string;
  endpoint: string;
  state: EligState;
  missing_fields: string[];
  unknown_categories: { field: string; value: string }[];
  reasons: string[];
  /** Phase XLVI kapanış: ana durumla aynı anda geçerli diğer nedenler (ör. AF çalışma ortamı yok). Arayüz: "Ayrıca: …". */
  additional_reasons?: string[];
  /** Teknik ayrıntı (Phase XLVI): ör. AF çalışma ortamı sorunlarının tam metni. */
  details?: string[];
  /** Yalnız AF satırında (Phase XLVI): kilitli Octave/ECGDeli pipeline'ı kullanılabilir mi. */
  af_pipeline_available?: boolean;
}

export interface FieldError {
  field: string | null;
  msg: string;
}

export interface Warning {
  code: string;
  fields: string[];
  message_tr: string;
  disease_key?: string;
}

export interface EligibilityResponse {
  models: EligModel[];
  field_errors: FieldError[];
  unit_conversion_notes: string[];
  warnings: Warning[];
}

export interface Decision {
  research_class: 'ESIK_USTU' | 'ESIK_ALTI';
  label_tr: string;
  threshold: string;
  threshold_rule: string;
}

export interface ModelResult {
  model_id: string;
  disease: string;
  disease_key: string;
  role: string;
  app_mode: string;
  module_label: string;
  status: 'OK' | 'ABSTAIN' | 'NOT_APPLICABLE';
  reasons: string[];
  missing_fields: string[];
  unknown_categories: { field: string; value: string }[];
  decision: Decision | null;
  evidence: Evidence;
  limitations: string[];
  warnings?: Warning[];
  selected_over?: string | null;
  fallback_from?: { model_id: string; status: string; reasons: string[]; missing_fields: string[]; note: string };
  pipeline?: {
    version: string;
    pre_step?: string;
    record_samples?: number | null;
    window?: string | null;
    octave_seconds?: number | null;
    wall_seconds?: number | null;
    features_ms?: Record<string, number> | null;
  };
  display?: EcgDisplay;
}

export interface EcgDisplay {
  lead: string;
  fs_hz: number;
  source_fs_hz: number;
  duration_s: number;
  signal_mv: (number | null)[];
  r_peaks_s: number[] | null;
  rr_ms: number[] | null;
  note: string;
}

export interface PredictResponse {
  results: ModelResult[];
  unit_conversion_notes: string[];
  note: string;
}

export interface EcgResponse {
  result: ModelResult;
  note: string;
}

// Phase XLVIII: açıklama asistanı (POST /assistant/ask). Yalnız etiketler gönderilir; ham sağlık değeri alanı yoktur.
export type AssistantOutcome = 'ESIK_USTU' | 'ESIK_ALTI' | 'ABSTAIN' | 'NOT_APPLICABLE' | 'ECG_REQUIRED';

export interface AssistantResultLabel {
  disease_key: string;
  outcome: AssistantOutcome;
  missing_fields: string[];
}

export interface AssistantSource {
  doc_id: string;
  title: string;
  section: string;
  kind: 'internal' | 'external';
  publisher?: string | null;
  url?: string;
  ref?: string;
  attribution?: string | null;
}

export interface AssistantResponse {
  route: string;
  answer: string;
  sources: AssistantSource[];
  llm_used: boolean;
  local_model: boolean;
  disclaimer: string;
}

export interface AssistantStatus {
  enabled: boolean;
  reason: string | null;
  local_only?: boolean;
  chat_model?: { name: string; digest: string } | null;
}
