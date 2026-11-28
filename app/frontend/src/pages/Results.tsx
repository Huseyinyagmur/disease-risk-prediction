import type { ModelResult, Schema } from '../api/types';
import { ResultCard } from '../components/ResultCard';
import { moduleRank } from '../components/RoutingPanel';
import { PageTitle } from '../components/ui';
import { plainUnitNote } from '../lib/plain';
import { RESULT_LOOK, resultKey, SUMMARY_ORDER } from '../lib/status';
import { modelName, t } from '../lib/ui';
import { useSession } from '../state/session';

/** Phase L: sonuç özeti şeridi — "3 analiz: 1 eşik üstü, 1 eşik altı, 1 sonuç üretilmedi" + karta bağlantılı liste. */
export function ResultSummary({ results, schema }: { results: ModelResult[]; schema: Schema | null }) {
  const keyed = results.map((r) => ({ r, k: resultKey(r, schema) }));
  const counts = SUMMARY_ORDER.map((k) => [k, keyed.filter((x) => x.k === k).length] as const).filter(([, n]) => n > 0);
  return (
    <section aria-label={t(schema, 'summary_label')} data-testid="results-summary" className="mb-6 rounded-lg border border-slate-300 bg-white p-4">
      <p className="text-lg font-semibold text-slate-900" data-testid="summary-line">
        {t(schema, 'summary_line', { n: results.length })}:{' '}
        {counts.map(([k, n], i) => (
          <span key={k}>
            {i > 0 && ', '}
            <span data-testid={`summary-${k}`}>{t(schema, `summary_${k}`, { n })}</span>
          </span>
        ))}
      </p>
      <ul className="mt-3 flex flex-wrap gap-2">
        {keyed.map(({ r, k }) => (
          <li key={r.model_id}>
            <a href={`#card-${r.model_id}`} data-testid={`summary-item-${r.model_id}`}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 ${RESULT_LOOK[k].chip}`}>
              <span aria-hidden="true" className="font-bold">{RESULT_LOOK[k].symbol}</span>
              {modelName(schema, r.model_id, r.disease)}
            </a>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-slate-700">{t(schema, 'summary_note')}</p>
    </section>
  );
}

export function Results() {
  const { prediction, models, schema, go, selected } = useSession();
  if (!prediction) {
    return (
      <div>
        <PageTitle>{t(schema, 'results_title')}</PageTitle>
        <p className="text-base text-slate-700">{t(schema, 'results_empty')}</p>
        <button type="button" onClick={() => go('form')} className="mt-3 rounded bg-slate-800 px-4 py-2 text-sm text-white">{t(schema, 'results_go_form')}</button>
      </div>
    );
  }
  const info = (id: string) => models?.find((m) => m.model_id === id);
  // Phase XLVII: yalnız seçilen analizler (seçim yoksa tümü).
  const keys = new Set(selected);
  const shown = selected.length ? prediction.results.filter((r) => keys.has(r.disease_key)) : prediction.results;
  const sorted = [...shown].sort((a, b) => moduleRank(a.module_label) - moduleRank(b.module_label));
  const main = sorted.filter((r) => r.module_label !== 'deneysel');
  const exp = sorted.filter((r) => r.module_label === 'deneysel');
  return (
    <div>
      <PageTitle sub={t(schema, 'results_sub')}>{t(schema, 'results_title')}</PageTitle>
      <ResultSummary results={sorted} schema={schema} />
      {selected.length > 0 && <p className="mb-3 text-sm text-slate-700" data-testid="results-filtered">{t(schema, 'results_filtered', { n: shown.length })}</p>}
      {prediction.unit_conversion_notes.length > 0 && (
        <div className="mb-4 rounded border border-sky-200 bg-sky-50 p-2 text-sm text-sky-900" data-testid="unit-notes">
          <p className="font-medium">{t(schema, 'unit_notes')}</p>
          <ul className="list-disc pl-5">{prediction.unit_conversion_notes.map((n) => <li key={n}>{plainUnitNote(schema, n)}</li>)}</ul>
        </div>
      )}
      {main.length > 0 && (
        <section aria-label={t(schema, 'results_main')} className="mb-6">
          <h2 className="mb-2 text-xl font-semibold text-slate-800">{t(schema, 'results_main')}</h2>
          <div className="grid gap-4 xl:grid-cols-2">
            {main.map((r) => <ResultCard key={r.model_id} r={r} info={info(r.model_id)} schema={schema} onEcg={() => go('ecg')} />)}
          </div>
        </section>
      )}
      {exp.length > 0 && (
        <section aria-label={t(schema, 'results_exp')} data-testid="experimental-section" className="rounded-lg bg-slate-100 p-3">
          <h2 className="mb-1 text-xl font-semibold text-slate-700">{t(schema, 'results_exp')}</h2>
          <p className="mb-3 text-sm text-slate-700">{t(schema, 'results_exp_note')}</p>
          <div className="grid gap-4 xl:grid-cols-2">
            {exp.map((r) => <ResultCard key={r.model_id} r={r} info={info(r.model_id)} schema={schema} experimental />)}
          </div>
        </section>
      )}
      <p className="mt-4 text-sm text-slate-600">{prediction.note}</p>
    </div>
  );
}
