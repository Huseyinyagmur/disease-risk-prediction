import { useEffect, useMemo, useRef, useState } from 'react';
import { api, ApiError, errorsByField } from '../api/client';
import type { EligibilityResponse } from '../api/types';
import { AnalysisSelect } from '../components/AnalysisSelect';
import { FieldInput } from '../components/FieldInput';
import { RoutingPanel } from '../components/RoutingPanel';
import { PageTitle } from '../components/ui';
import { DEMO_PROFILES } from '../demo/profiles';
import { buildPayload, formFields, isRequired, isVisible, type FieldValue } from '../lib/form';
import { analysisOptions, fieldsForSelection, REVIEW_STEP, SELECT_STEP, wizardSteps } from '../lib/selection';
import { t } from '../lib/ui';
import { useSession } from '../state/session';

export const ELIGIBILITY_DEBOUNCE_MS = 300;

const answered = (v: FieldValue | undefined) => !!v && v.value !== null && v.value !== '';

export function DataEntry() {
  const {
    schema, models, values, setValues, resetValues, setPrediction, go, profileLabel, setProfileLabel, selected, setSelected, step, setStep,
  } = useSession();
  const [elig, setElig] = useState<EligibilityResponse | null>(null);
  const [eligLoading, setEligLoading] = useState(false);
  const [eligError, setEligError] = useState<string | null>(null);
  const [submitErrors, setSubmitErrors] = useState<{ byField: Record<string, string[]>; general: string[] }>({ byField: {}, general: [] });
  const [submitting, setSubmitting] = useState(false);
  const [blockMsg, setBlockMsg] = useState<string | null>(null);
  const seq = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const prevStep = useRef<string | null>(null);

  const allowed = useMemo(
    () => (schema && models ? fieldsForSelection(schema, models, selected) : new Set<string>()),
    [schema, models, selected],
  );
  const built = useMemo(
    () => (schema ? buildPayload(schema, values, allowed) : null),
    [schema, values, allowed],
  );
  const hasSelection = selected.length > 0;

  // Canlı uygunluk sorgusu (debounce + eski yanıtları yok sayma). Analiz seçilmemişse sorgu yapılmaz.
  useEffect(() => {
    if (!schema || !built) return;
    if (!hasSelection) {
      seq.current++;
      setElig(null);
      setEligLoading(false);
      return;
    }
    const my = ++seq.current;
    const ctrl = new AbortController();
    setEligLoading(true);
    const timer = setTimeout(() => {
      api
        .eligibility(built.fields, ctrl.signal)
        .then((r) => {
          if (my !== seq.current) return;
          setElig(r);
          setEligError(null);
        })
        .catch((e: unknown) => {
          if ((e as Error).name === 'AbortError' || my !== seq.current) return;
          setEligError(e instanceof ApiError ? e.message : String(e));
        })
        .finally(() => {
          if (my === seq.current) setEligLoading(false);
        });
    }, ELIGIBILITY_DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [schema, built, hasSelection]);

  const steps = schema ? wizardSteps(schema, values, allowed, hasSelection) : [SELECT_STEP];
  const cur = steps.includes(step) ? step : SELECT_STEP;
  const idx = steps.indexOf(cur);

  // Adım değişince odak adım başlığına taşınır (klavye/ekran okuyucu); ilk açılışta odak çalınmaz.
  useEffect(() => {
    if (prevStep.current !== null && prevStep.current !== cur) heading.current?.focus();
    prevStep.current = cur;
  }, [cur]);

  // Metinler şemayla gelir; şema gelmeden yalnız durum bildirilir.
  if (!schema || !models) return <p className="text-sm text-slate-600">Şema yükleniyor…</p>;

  const backendErrors: Record<string, string[]> = {};
  const generalErrors: string[] = [...submitErrors.general];
  for (const e of elig?.field_errors ?? []) {
    if (e.field) (backendErrors[e.field] ??= []).push(e.msg);
    else generalErrors.push(e.msg);
  }
  const errorsFor = (name: string): string[] => {
    const f = built?.formatErrors[name];
    if (f) return [f];
    return backendErrors[name] ?? submitErrors.byField[name] ?? [];
  };
  const visibleFields = formFields(schema).filter(([n]) => allowed.has(n) && isVisible(schema, values, n));
  const errorFields = visibleFields.filter(([n]) => errorsFor(n).length > 0);
  const nErrors = errorFields.length;
  const errorSteps = steps.filter((s) => errorFields.some(([, f]) => f.form_section === s));
  const sectionOf = (id: string) => schema.form.sections.find((s) => s.id === id);
  const stepTitle = (s: string) =>
    s === SELECT_STEP ? t(schema, 'step_select') : s === REVIEW_STEP ? t(schema, 'step_review') : sectionOf(s)?.title_tr ?? s;
  const fieldsOf = (sec: string) => visibleFields.filter(([, f]) => f.form_section === sec);

  const setField = (name: string, v: FieldValue) => {
    setBlockMsg(null);
    setSubmitErrors({ byField: {}, general: [] });
    setValues((old) => ({ ...old, [name]: v }));
  };

  const changeSelection = (keys: string[]) => {
    setBlockMsg(null);
    setSelected(keys);
  };

  const loadProfile = (id: string) => {
    const p = DEMO_PROFILES.find((x) => x.id === id);
    if (!p) return;
    setSubmitErrors({ byField: {}, general: [] });
    setBlockMsg(null);
    resetValues(structuredClone(p.values));
    setProfileLabel(p.title);
    if (!hasSelection) setSelected(analysisOptions(models).map((o) => o.diseaseKey));
  };

  const clearForm = () => {
    resetValues({});
    setProfileLabel(null);
    setSubmitErrors({ byField: {}, general: [] });
    setBlockMsg(null);
  };

  const submit = async () => {
    if (!built || !hasSelection) return;
    if (nErrors > 0) {
      setBlockMsg(t(schema, 'errors_block', { n: nErrors }));
      return;
    }
    setSubmitting(true);
    setBlockMsg(null);
    try {
      const r = await api.predict(built.fields);
      setPrediction(r);
      go('results');
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        const errs = errorsByField(e.detail);
        setSubmitErrors(errs);
        setBlockMsg(t(schema, 'server_422'));
        const first = steps.find((s) => Object.keys(errs.byField).some((f) => schema.fields[f]?.form_section === s));
        if (first) setStep(first);
      } else setBlockMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const sec = sectionOf(cur);
  const afSelected = selected.includes('af');

  return (
    <div>
      <PageTitle sub={t(schema, 'page_sub')}>{t(schema, 'page_title')}</PageTitle>

      <section aria-label={t(schema, 'profile_title')} className="mb-4 rounded-lg border border-dashed border-violet-400 bg-violet-50 p-3">
        <p className="mb-2 text-xs text-violet-900">
          <span className="font-semibold">{t(schema, 'profile_title')}</span> — {t(schema, 'profile_note')}
        </p>
        <div className="flex flex-wrap gap-2">
          {DEMO_PROFILES.map((p) => (
            <button key={p.id} type="button" title={p.description} data-testid={`profile-${p.id}`} onClick={() => loadProfile(p.id)}
              className="rounded border border-violet-400 bg-white px-3 py-1 text-xs text-violet-900 hover:bg-violet-100">
              {p.title}
            </button>
          ))}
          <button type="button" onClick={clearForm} data-testid="clear-form" className="rounded border border-slate-400 bg-white px-3 py-1 text-xs text-slate-700 hover:bg-slate-100">
            {t(schema, 'clear_form')}
          </button>
        </div>
        {profileLabel && <p className="mt-2 text-xs text-violet-900" data-testid="profile-loaded">{t(schema, 'profile_loaded', { name: profileLabel })}</p>}
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className="min-w-0 space-y-4" onSubmit={(e) => { e.preventDefault(); void submit(); }} noValidate aria-label={t(schema, 'page_title')}>
          <nav aria-label={t(schema, 'wizard_label')} data-testid="wizard-steps" className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="mb-2 flex items-center justify-between gap-2 text-xs text-slate-700">
              <span data-testid="step-of">{t(schema, 'step_of', { i: idx + 1, n: steps.length })}</span>
            </div>
            <div role="progressbar" aria-label={t(schema, 'wizard_label')} aria-valuemin={1} aria-valuemax={steps.length} aria-valuenow={idx + 1}
              aria-valuetext={t(schema, 'step_of', { i: idx + 1, n: steps.length })} data-testid="wizard-progress"
              className="mb-3 h-2 w-full overflow-hidden rounded bg-slate-200">
              <div className="h-full bg-indigo-600 transition-all" style={{ width: `${Math.round(((idx + 1) / steps.length) * 100)}%` }} />
            </div>
            <ol className="flex flex-wrap gap-1">
              {steps.map((s, i) => (
                <li key={s}>
                  <button type="button" data-testid={`step-${s}`} aria-current={s === cur ? 'step' : undefined} onClick={() => setStep(s)}
                    className={`rounded px-2 py-1 text-xs ${s === cur ? 'bg-slate-800 font-semibold text-white' : 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-100'}`}>
                    {i + 1}. {stepTitle(s)}
                    {errorSteps.includes(s) && <span className={s === cur ? 'ml-1 text-rose-200' : 'ml-1 text-rose-700'}> ⚠</span>}
                  </button>
                </li>
              ))}
            </ol>
          </nav>

          {generalErrors.length > 0 && (
            <div role="alert" className="rounded border border-rose-300 bg-rose-50 p-2 text-sm text-rose-800">{generalErrors.join(' · ')}</div>
          )}

          <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid={`step-panel-${cur}`}>
            <h2 ref={heading} tabIndex={-1} id="step-title" data-testid="step-title" className="mb-3 text-lg font-semibold text-slate-900 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500">
              {cur === SELECT_STEP ? t(schema, 'select_title') : stepTitle(cur)}
              {sec?.optional && <span className="ml-1 text-sm font-normal text-slate-600">({t(schema, 'optional')})</span>}
            </h2>

            {cur === SELECT_STEP && <AnalysisSelect schema={schema} models={models} selected={selected} onChange={changeSelection} />}

            {sec && (
              <fieldset aria-labelledby="step-title" data-testid={`section-${sec.id}`}>
                {sec.description_tr && <p className="mb-3 text-xs text-slate-700">{sec.description_tr}</p>}
                {sec.id === 'temel' && afSelected && (
                  <p className="mb-3 rounded border border-sky-300 bg-sky-50 p-2 text-xs text-sky-900" data-testid="af-form-note">{t(schema, 'af_form_note')}</p>
                )}
                <div className="grid gap-4 sm:grid-cols-2">
                  {fieldsOf(sec.id).map(([name, spec]) => (
                    <FieldInput key={name} name={name} spec={spec} schema={schema} value={values[name]}
                      required={isRequired(schema, values, name)} errors={errorsFor(name)}
                      onChange={(v) => setField(name, v)} />
                  ))}
                </div>
              </fieldset>
            )}

            {cur === REVIEW_STEP && (
              <div data-testid="review-panel" className="space-y-3 text-sm">
                <p className="text-slate-700">{t(schema, 'review_sub')}</p>
                <ul className="list-disc pl-5" data-testid="review-analyses">
                  {analysisOptions(models).filter((o) => selected.includes(o.diseaseKey)).map((o) => (
                    <li key={o.diseaseKey}>{schema.ui?.disease_names_tr[o.diseaseKey] ?? o.diseaseKey}</li>
                  ))}
                </ul>
                {afSelected && <p className="rounded border border-sky-300 bg-sky-50 p-2 text-xs text-sky-900">{t(schema, 'af_form_note')}</p>}
                <ul className="divide-y divide-slate-100 rounded border border-slate-200">
                  {steps.filter((s) => s !== SELECT_STEP && s !== REVIEW_STEP).map((s) => {
                    const fs = fieldsOf(s);
                    return (
                      <li key={s} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2" data-testid={`review-${s}`}>
                        <span>
                          <span className="font-medium">{stepTitle(s)}</span>{' '}
                          <span className="text-xs text-slate-600">{t(schema, 'answered', { a: fs.filter(([n]) => answered(values[n])).length, n: fs.length })}</span>
                        </span>
                        <button type="button" onClick={() => setStep(s)} className="text-xs text-indigo-800 underline">{stepTitle(s)} →</button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>

          <div data-testid="wizard-bar" className="flex flex-wrap items-center gap-3 border-t border-slate-200 pt-3">
            <button type="button" data-testid="wizard-back" disabled={idx === 0} onClick={() => setStep(steps[idx - 1])}
              className="rounded border border-slate-400 bg-white px-4 py-2 text-sm text-slate-800 hover:bg-slate-100 disabled:opacity-50">
              ← {t(schema, 'back')}
            </button>
            <button type="button" data-testid="wizard-next" disabled={idx >= steps.length - 1} onClick={() => setStep(steps[idx + 1])}
              className="rounded border border-slate-800 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100 disabled:opacity-50">
              {t(schema, 'next')} →
            </button>
            <span className="hidden flex-1 sm:block" />
            {hasSelection && (
              <button type="submit" disabled={submitting} data-testid="submit"
                className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
                {submitting ? t(schema, 'submitting') : t(schema, 'submit')}
              </button>
            )}
            {!hasSelection && <p className="text-xs text-slate-700" data-testid="select-required">{t(schema, 'select_required')}</p>}
            {nErrors > 0 && <span className="text-xs text-rose-700" data-testid="error-count">{t(schema, 'error_count', { n: nErrors })}</span>}
          </div>
          {blockMsg && (
            <div role="alert" className="rounded border border-rose-300 bg-rose-50 p-2 text-xs text-rose-800" data-testid="block-msg">
              <p>{blockMsg}</p>
              {errorSteps.length > 0 && (
                <p className="mt-1">
                  {t(schema, 'errors_in_steps')}{' '}
                  {errorSteps.map((s) => (
                    <button key={s} type="button" data-testid={`error-step-${s}`} onClick={() => setStep(s)} className="mr-2 underline">{stepTitle(s)}</button>
                  ))}
                </p>
              )}
            </div>
          )}
        </form>
        <div className="lg:sticky lg:top-14 lg:max-h-[calc(100vh-4rem)] lg:self-start lg:overflow-y-auto">
          <RoutingPanel elig={elig} loading={eligLoading} error={eligError} selected={selected} />
        </div>
      </div>
    </div>
  );
}
