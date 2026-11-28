import type { ModelInfo, Schema } from '../api/types';
import { analysisOptions } from '../lib/selection';
import { t } from '../lib/ui';

interface Props {
  schema: Schema;
  models: ModelInfo[];
  selected: string[];
  onChange: (keys: string[]) => void;
}

/** "Hangi analizleri yapmak istiyorsunuz?" — seçenekler /models'tan (hastalık başına), grup metinleri app_config > ui'dan. */
export function AnalysisSelect({ schema, models, selected, onChange }: Props) {
  const ui = schema.ui;
  const opts = analysisOptions(models);
  const all = opts.map((o) => o.diseaseKey);
  const sel = new Set(selected);
  const toggle = (k: string) => onChange(sel.has(k) ? selected.filter((x) => x !== k) : all.filter((x) => sel.has(x) || x === k));
  const allOn = all.every((k) => sel.has(k));

  const groupBody = (moduleLabel: string) => (
    <ul className="grid gap-2 sm:grid-cols-2">
      {opts.filter((o) => o.moduleLabel === moduleLabel).map((o) => (
        <li key={o.diseaseKey}>
          <label className={`flex h-full cursor-pointer items-start gap-3 rounded-lg border p-3 ${sel.has(o.diseaseKey) ? 'border-indigo-600 bg-indigo-50' : 'border-slate-300 bg-white hover:border-slate-400'}`}>
            <input type="checkbox" className="mt-1 h-5 w-5 shrink-0 accent-indigo-700" checked={sel.has(o.diseaseKey)} onChange={() => toggle(o.diseaseKey)}
              data-testid={`select-${o.diseaseKey}`} aria-describedby={`hint-${o.diseaseKey}`} />
            <span className="min-w-0">
              <span className="block text-base font-medium text-slate-900">{ui?.disease_names_tr[o.diseaseKey] ?? o.diseaseKey}</span>
              <span id={`hint-${o.diseaseKey}`} className="mt-1 flex flex-wrap gap-1" data-testid={`needs-${o.diseaseKey}`}>
                <span className="sr-only">{t(schema, 'needs_label')}: </span>
                {(ui?.disease_needs_tr?.[o.diseaseKey] ?? []).map((n, i, all) => (
                  <span key={n.text} className={`rounded px-2 py-0.5 text-sm ${n.none ? 'bg-emerald-50 text-emerald-900 ring-1 ring-emerald-600/40' : 'bg-slate-100 text-slate-800 ring-1 ring-slate-400/50'}`}>
                    {n.text}{i < all.length - 1 && <span className="sr-only">,</span>}
                  </span>
                ))}
              </span>
            </span>
          </label>
        </li>
      ))}
    </ul>
  );

  return (
    <div data-testid="analysis-select" className="space-y-4">
      <p className="text-base text-slate-700">{t(schema, 'select_sub')}</p>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" data-testid="select-all" aria-pressed={allOn} onClick={() => onChange(allOn ? [] : all)}
          className={`rounded border px-3 py-1.5 text-sm font-medium ${allOn ? 'border-indigo-700 bg-indigo-700 text-white' : 'border-indigo-700 text-indigo-800 hover:bg-indigo-50'}`}>
          {t(schema, 'select_all')}
        </button>
        {selected.length > 0 && (
          <button type="button" data-testid="select-none" onClick={() => onChange([])} className="rounded border border-slate-400 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100">
            {t(schema, 'select_none')}
          </button>
        )}
        <span className="text-sm text-slate-700" aria-live="polite" data-testid="selected-count">{t(schema, 'selected_count', { n: selected.length })}</span>
      </div>
      {(ui?.analysis_groups_tr ?? []).map((g) => {
        if (!opts.some((o) => o.moduleLabel === g.module_label)) return null;
        const inner = (
          <>
            <p className="mb-2 text-sm text-slate-600">{g.description}</p>
            {groupBody(g.module_label)}
          </>
        );
        return g.collapsed ? (
          <details key={g.module_label} data-testid={`group-${g.module_label}`} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <summary className="cursor-pointer text-base font-semibold text-slate-800">
              {g.title}{' '}
              <span className="text-sm font-normal text-slate-600">
                ({t(schema, 'selected_count', { n: opts.filter((o) => o.moduleLabel === g.module_label && sel.has(o.diseaseKey)).length })})
              </span>
            </summary>
            <div className="mt-2">{inner}</div>
          </details>
        ) : (
          <fieldset key={g.module_label} data-testid={`group-${g.module_label}`} className="rounded-lg border border-slate-200 bg-white p-3">
            <legend className="px-1 text-base font-semibold text-slate-800">{g.title}</legend>
            {inner}
          </fieldset>
        );
      })}
    </div>
  );
}
