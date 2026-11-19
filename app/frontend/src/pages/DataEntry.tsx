import { useEffect, useMemo, useRef, useState } from 'react';
import { api, ApiError, errorsByField } from '../api/client';
import type { EligibilityResponse } from '../api/types';
import { FieldInput } from '../components/FieldInput';
import { RoutingPanel } from '../components/RoutingPanel';
import { PageTitle } from '../components/ui';
import { DEMO_PROFILES } from '../demo/profiles';
import { buildPayload, formFields, isRequired, isVisible, type FieldValue } from '../lib/form';
import { useSession } from '../state/session';

export const ELIGIBILITY_DEBOUNCE_MS = 300;

export function DataEntry() {
  const { schema, values, setValues, resetValues, setPrediction, go, profileLabel, setProfileLabel } = useSession();
  const [elig, setElig] = useState<EligibilityResponse | null>(null);
  const [eligLoading, setEligLoading] = useState(false);
  const [eligError, setEligError] = useState<string | null>(null);
  const [submitErrors, setSubmitErrors] = useState<{ byField: Record<string, string[]>; general: string[] }>({ byField: {}, general: [] });
  const [submitting, setSubmitting] = useState(false);
  const [blockMsg, setBlockMsg] = useState<string | null>(null);
  const seq = useRef(0);

  const built = useMemo(() => (schema ? buildPayload(schema, values) : null), [schema, values]);

  // Canlı uygunluk sorgusu (debounce + eski yanıtları yok sayma)
  useEffect(() => {
    if (!schema || !built) return;
    const my = ++seq.current;
    const ctrl = new AbortController();
    setEligLoading(true);
    const t = setTimeout(() => {
      api
        .eligibility(built.fields, ctrl.signal)
        .then((r) => {
          if (my !== seq.current) return;
          setElig(r);
          setEligError(null);
        })
        .catch((e: unknown) => {
          if ((e as Error).name === 'AbortError' || my !== seq.current) return;
          setEligError(e instanceof ApiError ? `Uygunluk sorgusu başarısız: ${e.message}` : String(e));
        })
        .finally(() => {
          if (my === seq.current) setEligLoading(false);
        });
    }, ELIGIBILITY_DEBOUNCE_MS);
    return () => {
      clearTimeout(t);
      ctrl.abort();
    };
  }, [schema, built]);

  if (!schema) return <p className="text-sm text-slate-600">Şema yükleniyor…</p>;

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
  const visibleFields = formFields(schema).filter(([n]) => isVisible(schema, values, n));
  const nErrors = visibleFields.filter(([n]) => errorsFor(n).length > 0).length;

  const setField = (name: string, v: FieldValue) => {
    setBlockMsg(null);
    setSubmitErrors({ byField: {}, general: [] });
    setValues((old) => ({ ...old, [name]: v }));
  };

  const loadProfile = (id: string) => {
    const p = DEMO_PROFILES.find((x) => x.id === id);
    if (!p) return;
    setSubmitErrors({ byField: {}, general: [] });
    setBlockMsg(null);
    resetValues(structuredClone(p.values));
    setProfileLabel(p.title);
  };

  const clearForm = () => {
    resetValues({});
    setProfileLabel(null);
    setSubmitErrors({ byField: {}, general: [] });
    setBlockMsg(null);
  };

  const submit = async () => {
    if (!built) return;
    if (nErrors > 0) {
      setBlockMsg(`Hesaplanamadı: ${nErrors} alanda hata var. Alan altındaki mesajlara bakın.`);
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
        setSubmitErrors(errorsByField(e.detail));
        setBlockMsg('Sunucu doğrulaması başarısız (422). Alan altındaki mesajlara bakın.');
      } else setBlockMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageTitle sub="Form alanları, birimler, aralıklar ve koşullu sorular sunucudaki şemadan (/schema) üretilir. Girdiler yalnız bu sekmenin belleğinde tutulur; sayfa yenilenince silinir.">
        Ortak veri girişi
      </PageTitle>

      <section aria-label="Örnek profiller" className="mb-4 rounded-lg border border-dashed border-violet-300 bg-violet-50 p-3">
        <p className="mb-2 text-xs text-violet-900">
          <span className="font-semibold">Örnek profil yükle</span> — SENTETİK, elle üretilmiş profiller; gerçek kişi verisi değildir.
        </p>
        <div className="flex flex-wrap gap-2">
          {DEMO_PROFILES.map((p) => (
            <button key={p.id} type="button" title={p.description} data-testid={`profile-${p.id}`} onClick={() => loadProfile(p.id)}
              className="rounded border border-violet-300 bg-white px-3 py-1 text-xs text-violet-900 hover:bg-violet-100">
              {p.title}
            </button>
          ))}
          <button type="button" onClick={clearForm} data-testid="clear-form" className="rounded border border-slate-300 bg-white px-3 py-1 text-xs text-slate-700 hover:bg-slate-100">
            Formu temizle
          </button>
        </div>
        {profileLabel && <p className="mt-2 text-xs text-violet-900" data-testid="profile-loaded">Yüklü: {profileLabel} (sentetik)</p>}
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); void submit(); }} noValidate aria-label="Veri giriş formu">
          {generalErrors.length > 0 && (
            <div role="alert" className="rounded border border-rose-300 bg-rose-50 p-2 text-sm text-rose-800">{generalErrors.join(' · ')}</div>
          )}
          {schema.form.sections.map((sec, i) => {
            const fs = visibleFields.filter(([, f]) => f.form_section === sec.id);
            if (fs.length === 0) return null;
            return (
              <fieldset key={sec.id} className="rounded-lg border border-slate-200 bg-white p-4" data-testid={`section-${sec.id}`}>
                <legend className="px-1 text-base font-semibold text-slate-800">
                  {i + 1}. {sec.title_tr} {sec.optional && <span className="text-sm font-normal text-slate-500">(isteğe bağlı)</span>}
                </legend>
                {sec.description_tr && <p className="mb-3 text-xs text-slate-600">{sec.description_tr}</p>}
                <div className="grid gap-4 sm:grid-cols-2">
                  {fs.map(([name, spec]) => (
                    <FieldInput key={name} name={name} spec={spec} schema={schema} value={values[name]}
                      required={isRequired(schema, values, name)} errors={errorsFor(name)}
                      onChange={(v) => setField(name, v)} />
                  ))}
                </div>
              </fieldset>
            );
          })}
          <div className="sticky bottom-0 flex flex-wrap items-center gap-3 border-t border-slate-200 bg-slate-50/95 py-3">
            <button type="submit" disabled={submitting} data-testid="submit"
              className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
              {submitting ? 'Hesaplanıyor…' : 'Sonuçları hesapla'}
            </button>
            {nErrors > 0 && <span className="text-xs text-rose-700" data-testid="error-count">{nErrors} alanda hata</span>}
            {blockMsg && <span role="alert" className="text-xs text-rose-700" data-testid="block-msg">{blockMsg}</span>}
          </div>
        </form>
        <div className="lg:sticky lg:top-14 lg:max-h-[calc(100vh-4rem)] lg:overflow-y-auto">
          <RoutingPanel elig={elig} loading={eligLoading} error={eligError} />
        </div>
      </div>
    </div>
  );
}
