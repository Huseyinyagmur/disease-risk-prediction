import type { ModelInfo, ModelResult, Schema } from '../api/types';
import { fieldLabel } from '../lib/form';
import { displayReasons } from '../lib/plain';
import { needsEcg, RESULT_LOOK, resultKey } from '../lib/status';
import { humanize, modelName, nextStep, outcomeOf, t, term } from '../lib/ui';
import { Collapsible, EvidenceBadges, EvidenceTable, ModulePill, TechDetails } from './ui';

/** Karar metni terim sözlüğünden (app_config > ui.terms_tr): OK → decision terimi, diğer durumlar → result terimi.
 * Phase L: renk sınıfı lib/status.ts (tek kaynak). */
export function decisionText(r: ModelResult, schema: Schema | null): { text: string; cls: string } {
  const o = outcomeOf(r);
  const text = o === 'ESIK_USTU' || o === 'ESIK_ALTI' ? term(schema, 'decision', o) : term(schema, 'result', r.status);
  return { text, cls: RESULT_LOOK[o].box };
}

export { needsEcg } from '../lib/status'; // Phase L: lib/status.ts'e taşındı (geriye uyum)

interface Props {
  r: ModelResult;
  info?: ModelInfo;
  schema: Schema | null;
  experimental?: boolean;
  onEcg?: () => void;
}

export function ResultCard({ r, info, schema, experimental, onEcg }: Props) {
  const d = decisionText(r, schema);
  const ecgNeeded = needsEcg(r, schema);
  if (ecgNeeded) d.text = t(schema, 'ecg_required');
  const key = resultKey(r, schema);
  const look = RESULT_LOOK[key];
  const outcome = outcomeOf(r);
  // Phase L: ana listede yalnız sade satırlar (ham metin Teknik ayrıntı içinde).
  const reasons = displayReasons(schema, r.reasons);
  const evPlain = schema?.ui?.evidence_plain_tr[r.model_id];
  const limitations = [...r.limitations, ...(schema?.ui?.limitations_extra_tr?.[r.model_id] ?? [])];
  return (
    <article id={`card-${r.model_id}`} data-testid={`result-${r.model_id}`} data-status={r.status} data-class={r.decision?.research_class ?? ''}
      data-key={key}
      className={`min-w-0 scroll-mt-20 rounded-lg border p-4 ${experimental ? 'border-slate-200 bg-slate-50' : 'border-slate-200 bg-white'}`}>
      <header className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{modelName(schema, r.model_id, r.disease)}</h3>
        <ModulePill label={r.module_label} />
      </header>

      <div className={`mb-3 flex items-start gap-3 rounded-lg border-2 px-4 py-3 ${look.box}`} data-testid="decision">
        <span aria-hidden="true" className={`mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${look.badge}`}>
          {look.symbol}
        </span>
        <div>
          <p className="text-lg font-semibold leading-snug">{d.text}</p>
          {r.decision && <p className="mt-0.5 text-sm opacity-90" data-testid="decision-note">{t(schema, 'decision_note')}</p>}
        </div>
      </div>

      <div className="mb-3 border-l-4 border-indigo-600 pl-3 text-slate-900" data-testid="next-step">
        <p className="text-sm font-semibold text-indigo-900">{t(schema, 'what_to_do')}</p>
        <p className="text-base">{nextStep(schema, r.disease_key, outcome)}</p>
      </div>

      {(r.warnings ?? []).map((w, i) => (
        <p key={i} role="alert" data-testid="target-warning" className="mb-3 rounded border border-orange-700 bg-orange-50 p-2 text-sm text-orange-950">
          ⚠ {humanize(schema, w.message_tr)}
        </p>
      ))}

      {r.status !== 'OK' && (reasons.length > 0 || r.missing_fields.length > 0) && (
        <div className="mb-3 text-sm text-slate-800" data-testid="reasons">
          <p className="font-semibold">{r.status === 'ABSTAIN' ? t(schema, 'reasons_abstain') : ecgNeeded ? t(schema, 'reasons_needed') : t(schema, 'reasons_na')}</p>
          {reasons.length > 0 && <ul className="list-disc pl-5">{reasons.map((x) => <li key={x}>{x}</li>)}</ul>}
          {r.missing_fields.length > 0 && (
            <p className="mt-1">{t(schema, 'missing_list', { x: r.missing_fields.map((f) => fieldLabel(schema, f)).join(', ') })}</p>
          )}
        </div>
      )}
      {r.status === 'OK' && reasons.length > 0 && <ul className="mb-3 list-disc pl-5 text-sm text-slate-700">{reasons.map((x) => <li key={x}>{x}</li>)}</ul>}
      {r.fallback_from && <p className="mb-3 text-sm text-slate-700" data-testid="fallback">{t(schema, 'fallback')}</p>}
      {r.selected_over && <p className="mb-3 text-sm text-slate-700" data-testid="selected-over">{t(schema, 'selected_over')}</p>}
      {r.model_id === 'af_S4_DEVICE' && r.status === 'NOT_APPLICABLE' && onEcg && (
        <button type="button" onClick={onEcg} className="mb-3 rounded border border-indigo-700 px-3 py-1.5 text-sm font-medium text-indigo-900 hover:bg-indigo-50">
          {t(schema, 'go_ecg')}
        </button>
      )}

      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-700">{t(schema, 'evidence')}:</span>
        <EvidenceBadges evidence={r.evidence} />
      </div>
      {evPlain && <p className="mb-3 text-sm text-slate-700" data-testid="evidence-plain">{evPlain}</p>}
      <div className="space-y-2">
        {info && (
          <Collapsible title={t(schema, 'target')} testId="target">
            <p className="text-sm"><span className="font-medium">{t(schema, 'target_def')}:</span> {info.target_definition}</p>
          </Collapsible>
        )}
        <Collapsible title={t(schema, 'metrics')} testId="metrics">
          <EvidenceTable evidence={r.evidence} />
        </Collapsible>
        <Collapsible title={t(schema, 'limitations', { n: limitations.length })} testId="limitations">
          <ul className="list-disc space-y-1 pl-5 text-sm">{limitations.map((x) => <li key={x}>{x}</li>)}</ul>
        </Collapsible>
        <TechDetails testId="tech-details" items={[
          [t(schema, 'tech_model'), <span className="font-mono">{r.model_id}</span>],
          [t(schema, 'tech_definition'), r.disease],
          ...r.reasons.map((x) => [t(schema, 'tech_note'), x] as [string, string]),
          ...(r.fallback_from ? [[t(schema, 'tech_note'), `${r.fallback_from.note} (${r.fallback_from.model_id}: ${r.fallback_from.status})`] as [string, string]] : []),
          ...(r.selected_over ? [[t(schema, 'tech_note'), `${r.model_id} ← ${r.selected_over}`] as [string, string]] : []),
        ]} />
      </div>
    </article>
  );
}
