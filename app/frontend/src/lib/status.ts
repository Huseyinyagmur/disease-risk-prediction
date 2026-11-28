// Phase L: durum → görünüm TEK KAYNAĞI (phase_l/01_design_contract.md). Her durumun tek rengi ve tek simgesi vardır;
// seçim paneli, özet şeridi, sonuç kartı aynı eşlemeyi kullanır. Renk tek taşıyıcı değildir: metin + simge her zaman var.
// Metin burada tutulmaz (app_config > ui.terms_tr / text_tr).
import type { EligState, ModelResult, Schema } from '../api/types';
import { outcomeOf } from './ui';

export type ResultKey = 'ESIK_USTU' | 'ESIK_ALTI' | 'ABSTAIN' | 'NOT_APPLICABLE' | 'ECG_REQUIRED';

interface Look {
  /** sonuç kutusu (kenar + zemin + metin) */
  box: string;
  /** simge rozeti (dolu) */
  badge: string;
  /** özet şeridindeki hap */
  chip: string;
  symbol: string;
}

export const RESULT_LOOK: Record<ResultKey, Look> = {
  ESIK_USTU: { box: 'border-orange-700 bg-orange-50 text-orange-950', badge: 'bg-orange-700 text-white', chip: 'border-orange-700 bg-orange-50 text-orange-950', symbol: '▲' },
  ESIK_ALTI: { box: 'border-sky-700 bg-sky-50 text-sky-950', badge: 'bg-sky-700 text-white', chip: 'border-sky-700 bg-sky-50 text-sky-950', symbol: '▼' },
  ABSTAIN: { box: 'border-dashed border-slate-500 bg-white text-slate-900', badge: 'bg-slate-600 text-white', chip: 'border-dashed border-slate-500 bg-white text-slate-900', symbol: '?' },
  ECG_REQUIRED: { box: 'border-dashed border-slate-500 bg-white text-slate-900', badge: 'bg-slate-600 text-white', chip: 'border-dashed border-slate-500 bg-white text-slate-900', symbol: '…' },
  NOT_APPLICABLE: { box: 'border-stone-400 bg-stone-100 text-stone-900', badge: 'bg-stone-600 text-white', chip: 'border-stone-400 bg-stone-100 text-stone-900', symbol: '–' },
};

export const ELIG_LOOK: Record<EligState, { cls: string; symbol: string }> = {
  READY: { cls: 'border-emerald-600 bg-emerald-50 text-emerald-900', symbol: '✓' },
  MISSING: { cls: 'border-amber-500 bg-amber-50 text-amber-950', symbol: '!' },
  OUT_OF_SCOPE: { cls: 'border-stone-400 bg-stone-100 text-stone-900', symbol: '–' },
  ABSTAIN: { cls: 'border-dashed border-slate-500 bg-white text-slate-900', symbol: '?' },
};

/** Phase L2: hiç bilgi girilmemiş analiz — nötr (uyarı rengi değil). */
export const NOT_STARTED_LOOK = { cls: 'border-slate-300 bg-slate-50 text-slate-700', symbol: '○' };

/** Phase XLVIII: AF formdan (/predict) EKG'siz -> "EKG kaydı gerekiyor" (yaş kapsam dışı vb. NOT_APPLICABLE metni değişmez).
 * Yalnız sunum; durum kodu ve gerekçe sunucudan gelir. Önek metni app_config > ui.text_tr. (Phase L: ResultCard'dan taşındı.) */
export function needsEcg(r: ModelResult, schema: Schema | null): boolean {
  const pre = schema?.ui?.text_tr.ecg_required_reason_prefix;
  return r.model_id === 'af_S4_DEVICE' && r.status === 'NOT_APPLICABLE' && !!pre && r.reasons.some((x) => x.startsWith(pre));
}

/** Sonucun gösterim durumu: AF formdan EKG'siz → ECG_REQUIRED; diğerleri araştırma sınıfı / durum kodu. */
export function resultKey(r: ModelResult, schema: Schema | null): ResultKey {
  return needsEcg(r, schema) ? 'ECG_REQUIRED' : outcomeOf(r);
}

export const SUMMARY_ORDER: ResultKey[] = ['ESIK_USTU', 'ESIK_ALTI', 'ABSTAIN', 'ECG_REQUIRED', 'NOT_APPLICABLE'];
