import type { EligibilityResponse, EligModel, Schema } from '../api/types';
import { fieldLabel, type FieldValue, type FormValues } from '../lib/form';
import { displayReasons } from '../lib/plain';
import { humanize, modelName, t, term } from '../lib/ui';
import { useSession } from '../state/session';
import { ModulePill, StateBadge, TechDetails } from './ui';

const MODULE_ORDER: Record<string, number> = { 'ana modül': 0, 'araştırma modülü': 1 };
export const moduleRank = (label: string) => MODULE_ORDER[label] ?? 2;

export function sortByModule<T extends { module_label: string }>(xs: T[]): T[] {
  return [...xs].sort((a, b) => moduleRank(a.module_label) - moduleRank(b.module_label));
}

/** Ana durumdan ayrı, aynı anda geçerli nedenler (backend `additional_reasons`); yoksa null. */
export function alsoLine(m: EligModel, schema: Schema | null = null): string | null {
  const xs = m.additional_reasons ?? [];
  const plain = displayReasons(schema, xs);
  return plain.length ? t(schema, 'also', { x: plain.join('; ') }) : null;
}

/** Panel satırı: durum terimi (sözlük) + kişiye özel ayrıntı. Phase L: gerekçeler sade metne çevrilir (lib/plain). */
export function stateLine(m: EligModel, schema: Schema | null): string {
  const head = term(schema, 'eligibility', m.state);
  switch (m.state) {
    case 'READY':
      return head;
    case 'MISSING':
      return head + ': ' + m.missing_fields.map((f) => fieldLabel(schema, f)).join(', ');
    default:
      return head + ': ' + displayReasons(schema, m.reasons).join(' ');
  }
}

interface Props {
  elig: EligibilityResponse | null;
  loading: boolean;
  error: string | null;
  /** Phase XLVII: yalnız seçilen hastalıklar (disease_key) gösterilir. */
  selected: string[];
}

const answered = (v: FieldValue | undefined) => !!v && v.value !== null && v.value !== '';

/** Phase L2: modelin formdan girilen zorunlu alanlarından kaçı yanıtlandı (yalnız gösterim; durum sunucudan gelir). */
export function progressOf(schema: Schema | null, values: FormValues, modelId: string): { a: number; n: number } {
  const req = (schema?.models?.[modelId]?.required ?? []).filter((f) => schema?.fields[f]?.form_input);
  return { a: req.filter((f) => answered(values[f])).length, n: req.length };
}

/** Phase L2: birden çok analizde aynı sade gerekçe → panelin üstünde bir kez. */
export function commonReasons(schema: Schema | null, models: EligModel[]): string[] {
  const seen = new Map<string, number>();
  for (const m of models.filter((x) => x.state === 'MISSING' || x.state === 'ABSTAIN')) {
    for (const r of new Set(displayReasons(schema, m.reasons))) seen.set(r, (seen.get(r) ?? 0) + 1);
  }
  return [...seen].filter(([, n]) => n >= 2).map(([r]) => r);
}

export function RoutingPanel({ elig, loading, error, selected }: Props) {
  const { schema, go, values } = useSession();
  const keys = new Set(selected);
  const shown = elig ? sortByModule(elig.models.filter((m) => keys.has(m.disease_key))) : [];
  const warnings = (elig?.warnings ?? []).filter((w) => !w.disease_key || keys.has(w.disease_key));
  const common = commonReasons(schema, shown);
  return (
    <aside aria-label={t(schema, 'panel_title')} data-testid="routing-panel"
      className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-base font-semibold text-slate-900">{t(schema, 'panel_title')}</h2>
        <span className="text-xs text-slate-600" aria-live="polite">{loading ? t(schema, 'panel_updating') : elig ? t(schema, 'panel_current') : ''}</span>
      </div>
      <p className="mt-0.5 text-xs text-slate-600">{t(schema, 'panel_sub')}</p>
      {error && <p role="alert" className="mt-2 rounded-md bg-rose-50 p-2 text-xs text-rose-800">{t(schema, 'panel_error', { msg: error })}</p>}
      {selected.length === 0 && <p className="mt-2 text-sm text-slate-600" data-testid="panel-empty">{t(schema, 'panel_empty')}</p>}
      {common.length > 0 && (
        <p className="mt-2 rounded-md bg-slate-50 px-2 py-1.5 text-xs text-slate-700" data-testid="panel-common">
          {t(schema, 'panel_common', { x: common.join(' ') })}
        </p>
      )}
      <ul className="mt-1 divide-y divide-slate-100">
        {shown.map((m) => {
          const { a, n } = progressOf(schema, values, m.model_id);
          const notStarted = m.state === 'MISSING' && n > 0 && a === 0;
          const extra = displayReasons(schema, m.reasons).filter((r) => !common.includes(r));
          const also = alsoLine(m, schema);
          const ecgLink = m.endpoint === '/ecg/af' && m.state !== 'OUT_OF_SCOPE' && m.af_pipeline_available !== false;
          const tech = (
            <TechDetails testId={`panel-details-${m.model_id}`} items={[
              [t(schema, 'tech_model'), <span className="font-mono">{m.model_id}</span>],
              ...(m.details ?? []).map((d) => [t(schema, 'tech_note'), d] as [string, string]),
            ]} />
          );
          return (
            <li key={m.model_id} data-testid={`panel-${m.model_id}`} data-state={m.state} data-display={notStarted ? 'NOT_STARTED' : m.state}
              className="py-2.5">
              <div className="flex flex-wrap items-baseline gap-x-1.5">
                <span className="text-sm font-medium text-slate-900">{modelName(schema, m.model_id, m.disease)}</span>
                <ModulePill label={m.module_label} />
              </div>
              <div className="mt-1.5 flex items-center gap-2">
                <StateBadge state={m.state} notStarted={notStarted} />
                {n > 0 && (
                  <>
                  <div className="h-1.5 min-w-[2rem] flex-1 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
                    <div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.round((a / n) * 100)}%` }} />
                  </div>
                  <span className="shrink-0 text-xs tabular-nums text-slate-600" data-testid={`panel-progress-${m.model_id}`}>
                    {t(schema, 'panel_progress', { a, n })}
                  </span>
                  </>
                )}
              </div>
              {m.state === 'READY' && <p className="sr-only" data-testid={`panel-line-${m.model_id}`}>{stateLine(m, schema)}</p>}
              {(m.state === 'OUT_OF_SCOPE' || m.state === 'ABSTAIN') && (
                <p className="mt-1 text-xs text-slate-700" data-testid={`panel-line-${m.model_id}`}>{stateLine(m, schema)}</p>
              )}
              {also && <p className="mt-1 text-xs text-slate-700" data-testid={`panel-also-${m.model_id}`}>{also}</p>}
              {m.state === 'MISSING' ? (
                <details className="mt-1 text-xs text-slate-700" data-testid={`panel-missing-${m.model_id}`}>
                  <summary className="cursor-pointer text-indigo-800">{t(schema, 'panel_show_missing')}</summary>
                  <p className="mt-1" data-testid={`panel-line-${m.model_id}`}>{stateLine(m, schema)}</p>
                  {extra.length > 0 && <ul className="mt-1 list-disc pl-4">{extra.map((r) => <li key={r}>{r}</li>)}</ul>}
                  {tech}
                </details>
              ) : tech}
              {ecgLink && (
                <button type="button" onClick={() => go('ecg')} className="mt-1 text-xs font-medium text-indigo-800 underline">{t(schema, 'ecg_link')}</button>
              )}
            </li>
          );
        })}
      </ul>
      {warnings.length > 0 && (
        <div className="mt-2 space-y-1" data-testid="panel-warnings">
          {warnings.map((w, i) => (
            <p key={i} className="rounded-md border border-orange-300 bg-orange-50 p-2 text-xs text-orange-900">⚠ {humanize(schema, w.message_tr)}</p>
          ))}
        </div>
      )}
    </aside>
  );
}
