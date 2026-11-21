import type { EligibilityResponse, EligModel, Schema } from '../api/types';
import { fieldLabel } from '../lib/form';
import { humanize, modelName, t, term } from '../lib/ui';
import { useSession } from '../state/session';
import { ModulePill, StateBadge, TechDetails } from './ui';

const MODULE_ORDER: Record<string, number> = { 'ana modül': 0, 'araştırma modülü': 1 };
export const moduleRank = (label: string) => MODULE_ORDER[label] ?? 2;

export function sortByModule<T extends { module_label: string }>(xs: T[]): T[] {
  return [...xs].sort((a, b) => moduleRank(a.module_label) - moduleRank(b.module_label));
}

const isMissingReason = (r: string) => r.startsWith('eksik zorunlu alan');

/** Ana durumdan ayrı, aynı anda geçerli nedenler (backend `additional_reasons`); yoksa null. */
export function alsoLine(m: EligModel, schema: Schema | null = null): string | null {
  const xs = m.additional_reasons ?? [];
  return xs.length ? t(schema, 'also', { x: xs.map((x) => humanize(schema, x)).join('; ') }) : null;
}

/** Panel satırı: durum terimi (sözlük) + kişiye özel ayrıntı. Ham alan adları etikete çevrilir. */
export function stateLine(m: EligModel, schema: Schema | null): string {
  const head = term(schema, 'eligibility', m.state);
  switch (m.state) {
    case 'READY':
      return head;
    case 'MISSING':
      return head + ': ' + m.missing_fields.map((f) => fieldLabel(schema, f)).join(', ');
    default:
      return head + ': ' + m.reasons.map((r) => humanize(schema, r)).join('; ');
  }
}

interface Props {
  elig: EligibilityResponse | null;
  loading: boolean;
  error: string | null;
  /** Phase XLVII: yalnız seçilen hastalıklar (disease_key) gösterilir. */
  selected: string[];
}

export function RoutingPanel({ elig, loading, error, selected }: Props) {
  const { schema, go } = useSession();
  const keys = new Set(selected);
  const shown = elig ? sortByModule(elig.models.filter((m) => keys.has(m.disease_key))) : [];
  const warnings = (elig?.warnings ?? []).filter((w) => !w.disease_key || keys.has(w.disease_key));
  return (
    <aside aria-label={t(schema, 'panel_title')} data-testid="routing-panel"
      className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-800">{t(schema, 'panel_title')}</h2>
        <span className="text-[11px] text-slate-600" aria-live="polite">{loading ? t(schema, 'panel_updating') : elig ? t(schema, 'panel_current') : ''}</span>
      </div>
      <p className="mb-2 text-[11px] text-slate-600">{t(schema, 'panel_sub')}</p>
      {error && <p role="alert" className="mb-2 rounded bg-rose-50 p-2 text-xs text-rose-800">{t(schema, 'panel_error', { msg: error })}</p>}
      {selected.length === 0 && <p className="text-xs text-slate-600" data-testid="panel-empty">{t(schema, 'panel_empty')}</p>}
      <ul className="space-y-2">
        {shown.map((m) => {
          const extra = m.state === 'MISSING' ? m.reasons.filter((r) => !isMissingReason(r)) : [];
          const also = alsoLine(m, schema);
          return (
            <li key={m.model_id} data-testid={`panel-${m.model_id}`} data-state={m.state}
              className={`rounded border p-2 ${m.module_label === 'deneysel' ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-slate-200'}`}>
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-sm font-medium">{modelName(schema, m.model_id, m.disease)}</span>
                <ModulePill label={m.module_label} />
              </div>
              <div className="mt-1"><StateBadge state={m.state} /></div>
              <p className="mt-1 text-xs" data-testid={`panel-line-${m.model_id}`}>{stateLine(m, schema)}</p>
              {also && <p className="mt-0.5 text-[11px] text-slate-700" data-testid={`panel-also-${m.model_id}`}>{also}</p>}
              {extra.length > 0 && (
                <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-700">
                  {extra.map((r) => <li key={r}>{humanize(schema, r)}</li>)}
                </ul>
              )}
              <TechDetails testId={`panel-details-${m.model_id}`} items={[
                [t(schema, 'tech_model'), <span className="font-mono">{m.model_id}</span>],
                ...(m.details ?? []).map((d) => [t(schema, 'tech_note'), d] as [string, string]),
              ]} />
              {m.endpoint === '/ecg/af' && m.state !== 'OUT_OF_SCOPE' && m.af_pipeline_available !== false && (
                <button type="button" onClick={() => go('ecg')} className="mt-1 text-xs text-indigo-800 underline">{t(schema, 'ecg_link')}</button>
              )}
            </li>
          );
        })}
      </ul>
      {warnings.length > 0 && (
        <div className="mt-3 space-y-1" data-testid="panel-warnings">
          {warnings.map((w, i) => (
            <p key={i} className="rounded border border-orange-300 bg-orange-50 p-2 text-xs text-orange-900">⚠ {humanize(schema, w.message_tr)}</p>
          ))}
        </div>
      )}
    </aside>
  );
}
