import type { EligibilityResponse, EligModel, Schema } from '../api/types';
import { fieldLabel } from '../lib/form';
import { useSession } from '../state/session';
import { ModulePill, StateBadge } from './ui';

const MODULE_ORDER: Record<string, number> = { 'ana modül': 0, 'araştırma modülü': 1 };
export const moduleRank = (label: string) => MODULE_ORDER[label] ?? 2;

export function sortByModule<T extends { module_label: string }>(xs: T[]): T[] {
  return [...xs].sort((a, b) => moduleRank(a.module_label) - moduleRank(b.module_label));
}

/** Ana durumdan ayrı, aynı anda geçerli nedenler (backend `additional_reasons`); yoksa null. */
export function alsoLine(m: EligModel): string | null {
  const xs = m.additional_reasons ?? [];
  return xs.length ? 'Ayrıca: ' + xs.join('; ') : null;
}

export function stateLine(m: EligModel, schema: Schema | null): string {
  switch (m.state) {
    case 'READY':
      return 'Çalışabilir';
    case 'MISSING':
      return 'Eksik: ' + m.missing_fields.map((f) => fieldLabel(schema, f)).join(', ');
    case 'OUT_OF_SCOPE':
      return 'Kapsam dışı: ' + m.reasons.join('; ');
    default:
      return 'Karar verilemez: ' + m.reasons.join('; ');
  }
}

interface Props {
  elig: EligibilityResponse | null;
  loading: boolean;
  error: string | null;
}

export function RoutingPanel({ elig, loading, error }: Props) {
  const { schema, go } = useSession();
  return (
    <aside aria-label="Model yönlendirme paneli" data-testid="routing-panel"
      className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-800">Canlı model yönlendirme</h2>
        <span className="text-[11px] text-slate-500" aria-live="polite">{loading ? 'güncelleniyor…' : elig ? 'güncel' : ''}</span>
      </div>
      <p className="mb-2 text-[11px] text-slate-500">
        Sunucudaki uygunluk denetimi (/eligibility). Model çalıştırılmaz; yalnız hangi modelin girdilerinizle çalışabileceği gösterilir.
      </p>
      {error && <p role="alert" className="mb-2 rounded bg-rose-50 p-2 text-xs text-rose-800">{error}</p>}
      <ul className="space-y-2">
        {elig &&
          sortByModule(elig.models).map((m) => (
            <li key={m.model_id} data-testid={`panel-${m.model_id}`} data-state={m.state}
              className={`rounded border p-2 ${m.module_label === 'deneysel' ? 'border-slate-100 bg-slate-50 text-slate-600' : 'border-slate-200'}`}>
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-sm font-medium">{m.disease}</span>
                <ModulePill label={m.module_label} />
              </div>
              <div className="mt-1 flex items-start gap-2">
                <StateBadge state={m.state} />
                <span className="text-[11px] text-slate-500">{m.model_id}</span>
              </div>
              <p className="mt-1 text-xs" data-testid={`panel-line-${m.model_id}`}>{stateLine(m, schema)}</p>
              {alsoLine(m) && (
                <p className="mt-0.5 text-[11px] text-slate-600" data-testid={`panel-also-${m.model_id}`}>{alsoLine(m)}</p>
              )}
              {m.state === 'MISSING' && m.reasons.length > 0 && (
                <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-500">
                  {m.reasons.filter((r) => !r.startsWith('eksik zorunlu alan')).map((r) => <li key={r}>{r}</li>)}
                </ul>
              )}
              {m.details && m.details.length > 0 && (
                <details className="mt-1 text-[11px] text-slate-500" data-testid={`panel-details-${m.model_id}`}>
                  <summary className="cursor-pointer">Teknik ayrıntı</summary>
                  <ul className="list-disc pl-4">{m.details.map((d) => <li key={d}>{d}</li>)}</ul>
                </details>
              )}
              {m.endpoint === '/ecg/af' && m.state !== 'OUT_OF_SCOPE' && m.af_pipeline_available !== false && (
                <button type="button" onClick={() => go('ecg')} className="mt-1 text-xs text-indigo-700 underline">EKG kaydı yükle →</button>
              )}
            </li>
          ))}
      </ul>
      {elig && elig.warnings.length > 0 && (
        <div className="mt-3 space-y-1" data-testid="panel-warnings">
          {elig.warnings.map((w, i) => (
            <p key={i} className="rounded border border-orange-300 bg-orange-50 p-2 text-xs text-orange-900">⚠ {w.message_tr}</p>
          ))}
        </div>
      )}
    </aside>
  );
}
