import type { ModelInfo, ModelResult, Schema } from '../api/types';
import { fieldLabel } from '../lib/form';
import { Collapsible, EvidenceBadges, EvidenceTable, ModulePill } from './ui';

export function decisionText(r: ModelResult): { text: string; cls: string } {
  if (r.status === 'OK' && r.decision) {
    return r.decision.research_class === 'ESIK_USTU'
      ? { text: 'İleri değerlendirme önerilir', cls: 'border-orange-400 bg-orange-50 text-orange-900' }
      : { text: 'Eşik altında', cls: 'border-slate-300 bg-slate-50 text-slate-800' };
  }
  if (r.status === 'NOT_APPLICABLE') return { text: 'Kapsam dışı — karar üretilmedi', cls: 'border-slate-300 bg-slate-100 text-slate-700' };
  return { text: 'Karar üretilmedi (ABSTAIN)', cls: 'border-rose-300 bg-rose-50 text-rose-800' };
}

interface Props {
  r: ModelResult;
  info?: ModelInfo;
  schema: Schema | null;
  experimental?: boolean;
  onEcg?: () => void;
}

export function ResultCard({ r, info, schema, experimental, onEcg }: Props) {
  const d = decisionText(r);
  return (
    <article data-testid={`result-${r.model_id}`} data-status={r.status} data-class={r.decision?.research_class ?? ''}
      className={`rounded-lg border p-4 shadow-sm ${experimental ? 'border-slate-200 bg-slate-50 text-slate-600' : 'border-slate-200 bg-white'}`}>
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className={`text-base font-semibold ${experimental ? 'text-slate-600' : 'text-slate-900'}`}>{r.disease}</h3>
        <ModulePill label={r.module_label} />
        <span className="text-xs text-slate-500">{r.model_id}</span>
      </header>

      <div className={`mb-2 rounded border px-3 py-2 ${d.cls}`} data-testid="decision">
        <p className="text-sm font-semibold">{d.text}</p>
        {r.decision && <p className="text-xs">{r.decision.label_tr}. Model olasılığı gösterilmez (klinik olasılık değildir).</p>}
      </div>

      {(r.warnings ?? []).map((w, i) => (
        <p key={i} role="alert" data-testid="target-warning" className="mb-2 rounded border border-orange-400 bg-orange-50 p-2 text-xs text-orange-900">
          ⚠ {w.message_tr}
        </p>
      ))}

      {r.status !== 'OK' && r.reasons.length > 0 && (
        <div className="mb-2 text-xs" data-testid="reasons">
          <p className="font-medium">{r.status === 'ABSTAIN' ? 'Neden:' : 'Gerekçe:'}</p>
          <ul className="list-disc pl-5">{r.reasons.map((x) => <li key={x}>{x}</li>)}</ul>
          {r.missing_fields.length > 0 && (
            <p className="mt-1">Eksik alanlar: {r.missing_fields.map((f) => fieldLabel(schema, f)).join(', ')}</p>
          )}
        </div>
      )}
      {r.status === 'OK' && r.reasons.length > 0 && (
        <p className="mb-2 text-xs text-slate-500">{r.reasons.join(' · ')}</p>
      )}
      {r.fallback_from && (
        <p className="mb-2 text-xs text-slate-600" data-testid="fallback">
          {r.fallback_from.note} ({r.fallback_from.model_id}: {r.fallback_from.status}
          {r.fallback_from.missing_fields.length > 0 && `; eksik: ${r.fallback_from.missing_fields.map((f) => fieldLabel(schema, f)).join(', ')}`}).
        </p>
      )}
      {r.selected_over && <p className="mb-2 text-xs text-slate-600">Laboratuvarlı model kullanıldı ({r.model_id}; {r.selected_over} yerine).</p>}
      {r.model_id === 'af_S4_DEVICE' && r.status === 'NOT_APPLICABLE' && onEcg && (
        <button type="button" onClick={onEcg} className="mb-2 rounded border border-indigo-300 px-3 py-1 text-xs text-indigo-800 hover:bg-indigo-50">
          EKG ile AF analizine git →
        </button>
      )}

      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-600">Kanıt düzeyi:</span>
        <EvidenceBadges evidence={r.evidence} />
      </div>
      {info && (
        <p className="mb-2 text-xs"><span className="font-medium">Hedef tanımı:</span> {info.target_definition}</p>
      )}
      <div className="space-y-2">
        <Collapsible title="Test metrikleri (P, R, FPR, %95 GA)" defaultOpen={!experimental}>
          <EvidenceTable evidence={r.evidence} />
        </Collapsible>
        <Collapsible title={`Sınırlılıklar (${r.limitations.length})`}>
          <ul className="list-disc space-y-1 pl-5 text-xs">{r.limitations.map((x) => <li key={x}>{x}</li>)}</ul>
        </Collapsible>
      </div>
    </article>
  );
}
