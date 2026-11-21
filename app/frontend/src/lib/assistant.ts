// Phase XLVIII: açıklama asistanına giden oturum ETİKETLERİ. Yalnız hastalık anahtarı, durum kodu ve eksik alan ADLARI
// gönderilir; form değerleri, ölçümler, EKG sinyali veya öznitelik değerleri hiçbir zaman eklenmez.
import type { AssistantOutcome, AssistantResultLabel, EcgResponse, ModelResult, PredictResponse, Schema } from '../api/types';
import { needsEcg } from '../components/ResultCard';

export function outcomeLabel(r: ModelResult, schema: Schema | null): AssistantOutcome {
  if (needsEcg(r, schema)) return 'ECG_REQUIRED';
  if (r.status === 'OK' && r.decision) return r.decision.research_class;
  return r.status === 'NOT_APPLICABLE' ? 'NOT_APPLICABLE' : 'ABSTAIN';
}

export function resultLabels(prediction: PredictResponse | null, ecg: EcgResponse | null, schema: Schema | null,
  selected: string[] = []): AssistantResultLabel[] {
  const rs: ModelResult[] = [...(prediction?.results ?? [])];
  if (ecg?.result) {
    const i = rs.findIndex((r) => r.model_id === ecg.result.model_id);
    if (i >= 0) rs[i] = ecg.result;
    else rs.push(ecg.result);
  }
  return rs
    .filter((r) => selected.length === 0 || selected.includes(r.disease_key) || r === ecg?.result)
    .map((r) => ({ disease_key: r.disease_key, outcome: outcomeLabel(r, schema), missing_fields: [...r.missing_fields] }));
}
