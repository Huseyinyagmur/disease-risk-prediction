import type { ModelInfo, ModelResult, Schema } from '../api/types';
import { fieldLabel } from '../lib/form';
import { humanize, modelName, nextStep, outcomeOf, t, term } from '../lib/ui';
import { Collapsible, EvidenceBadges, EvidenceTable, ModulePill, TechDetails } from './ui';

const CLS: Record<string, string> = {
  ESIK_USTU: 'border-orange-500 bg-orange-50 text-orange-950',
  ESIK_ALTI: 'border-slate-400 bg-slate-50 text-slate-900',
  NOT_APPLICABLE: 'border-slate-400 bg-slate-100 text-slate-800',
  ABSTAIN: 'border-rose-400 bg-rose-50 text-rose-900',
};

/** Karar metni terim sözlüğünden (app_config > ui.terms_tr): OK → decision terimi, diğer durumlar → result terimi. */
export function decisionText(r: ModelResult, schema: Schema | null): { text: string; cls: string } {
  const o = outcomeOf(r);
  const text = o === 'ESIK_USTU' || o === 'ESIK_ALTI' ? term(schema, 'decision', o) : term(schema, 'result', r.status);
  return { text, cls: CLS[o] };
}

const isMissingReason = (x: string) => x.startsWith('eksik zorunlu alan');

interface Props {
  r: ModelResult;
  info?: ModelInfo;
  schema: Schema | null;
  experimental?: boolean;
  onEcg?: () => void;
}

export function ResultCard({ r, info, schema, experimental, onEcg }: Props) {
  const d = decisionText(r, schema);
  const outcome = outcomeOf(r);
  const reasons = r.reasons.filter((x) => !isMissingReason(x)).map((x) => humanize(schema, x));
  const evPlain = schema?.ui?.evidence_plain_tr[r.model_id];
  return (
    <article data-testid={`result-${r.model_id}`} data-status={r.status} data-class={r.decision?.research_class ?? ''}
      className={`min-w-0 rounded-lg border p-4 shadow-sm ${experimental ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-slate-200 bg-white'}`}>
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold text-slate-900">{modelName(schema, r.model_id, r.disease)}</h3>
        <ModulePill label={r.module_label} />
      </header>

      <div className={`mb-2 rounded border px-3 py-2 ${d.cls}`} data-testid="decision">
        <p className="text-sm font-semibold">{d.text}</p>
        {r.decision && <p className="text-xs">{r.decision.label_tr}. {t(schema, 'no_probability')}</p>}
      </div>

      <div className="mb-2 rounded border border-indigo-200 bg-indigo-50 px-3 py-2 text-indigo-950" data-testid="next-step">
        <p className="text-xs font-semibold">{t(schema, 'what_to_do')}</p>
        <p className="text-sm">{nextStep(schema, r.disease_key, outcome)}</p>
      </div>

      {(r.warnings ?? []).map((w, i) => (
        <p key={i} role="alert" data-testid="target-warning" className="mb-2 rounded border border-orange-400 bg-orange-50 p-2 text-xs text-orange-950">
          ⚠ {humanize(schema, w.message_tr)}
        </p>
      ))}

      {r.status !== 'OK' && (reasons.length > 0 || r.missing_fields.length > 0) && (
        <div className="mb-2 text-xs" data-testid="reasons">
          <p className="font-medium">{r.status === 'ABSTAIN' ? t(schema, 'reasons_abstain') : t(schema, 'reasons_na')}</p>
          {reasons.length > 0 && <ul className="list-disc pl-5">{reasons.map((x) => <li key={x}>{x}</li>)}</ul>}
          {r.missing_fields.length > 0 && (
            <p className="mt-1">{t(schema, 'missing_list', { x: r.missing_fields.map((f) => fieldLabel(schema, f)).join(', ') })}</p>
          )}
        </div>
      )}
      {r.status === 'OK' && reasons.length > 0 && <p className="mb-2 text-xs text-slate-700">{reasons.join(' · ')}</p>}
      {r.fallback_from && <p className="mb-2 text-xs text-slate-700" data-testid="fallback">{t(schema, 'fallback')}</p>}
      {r.selected_over && <p className="mb-2 text-xs text-slate-700" data-testid="selected-over">{t(schema, 'selected_over')}</p>}
      {r.model_id === 'af_S4_DEVICE' && r.status === 'NOT_APPLICABLE' && onEcg && (
        <button type="button" onClick={onEcg} className="mb-2 rounded border border-indigo-400 px-3 py-1 text-xs text-indigo-900 hover:bg-indigo-50">
          {t(schema, 'go_ecg')}
        </button>
      )}

      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-700">{t(schema, 'evidence')}:</span>
        <EvidenceBadges evidence={r.evidence} />
      </div>
      {evPlain && <p className="mb-2 text-xs text-slate-800" data-testid="evidence-plain">{evPlain}</p>}
      <div className="space-y-2">
        {info && (
          <Collapsible title={t(schema, 'target')} testId="target">
            <p className="text-xs"><span className="font-medium">{t(schema, 'target_def')}:</span> {info.target_definition}</p>
          </Collapsible>
        )}
        <Collapsible title={t(schema, 'metrics')} testId="metrics">
          <EvidenceTable evidence={r.evidence} />
        </Collapsible>
        <Collapsible title={t(schema, 'limitations', { n: r.limitations.length })}>
          <ul className="list-disc space-y-1 pl-5 text-xs">{r.limitations.map((x) => <li key={x}>{x}</li>)}</ul>
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
