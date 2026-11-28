// Oturum durumu YALNIZ React belleğindedir. localStorage / sessionStorage / IndexedDB / çerez kullanılmaz;
// sayfa yenilenince tüm girdiler ve sonuçlar silinir.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, ApiError } from '../api/client';
import type { EcgResponse, ModelInfo, PredictResponse, Schema } from '../api/types';
import type { FormValues } from '../lib/form';
import { defaultSelection } from '../lib/selection';

export type Page = 'home' | 'form' | 'results' | 'ecg' | 'models' | 'about';

interface Session {
  page: Page;
  go: (p: Page) => void;
  schema: Schema | null;
  models: ModelInfo[] | null;
  loadError: string | null;
  /** Sabit araştırma uyarısı — TEK KAYNAK backend (app_config.json > disclaimer_tr; /schema yanıtının `disclaimer` alanı). */
  disclaimer: string | null;
  values: FormValues;
  setValues: (fn: (v: FormValues) => FormValues) => void;
  resetValues: (v?: FormValues) => void;
  profileLabel: string | null;
  setProfileLabel: (s: string | null) => void;
  prediction: PredictResponse | null;
  setPrediction: (p: PredictResponse | null) => void;
  ecg: EcgResponse | null;
  setEcg: (p: EcgResponse | null) => void;
  /** Phase XLVII: seçilen analizler (disease_key) ve sihirbaz adımı — yalnız bellekte. */
  selected: string[];
  setSelected: (keys: string[]) => void;
  step: string;
  setStep: (s: string) => void;
}

const Ctx = createContext<Session | null>(null);

export function SessionProvider({ children, initialPage = 'home' }: { children: ReactNode; initialPage?: Page }) {
  const [page, setPage] = useState<Page>(initialPage);
  const [schema, setSchema] = useState<Schema | null>(null);
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [disclaimer, setDisclaimer] = useState<string | null>(null);
  const [values, setValuesState] = useState<FormValues>({});
  const [profileLabel, setProfileLabel] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [ecg, setEcg] = useState<EcgResponse | null>(null);
  const [selected, setSelectedState] = useState<string[]>([]);
  const [step, setStep] = useState<string>('select');

  useEffect(() => {
    let alive = true;
    Promise.all([api.schema(), api.models()])
      .then(([s, m]) => {
        if (!alive) return;
        setSchema(s);
        setModels(m.models);
        // Phase L: ilk açılışta yalnız ana modüller + araştırma modülü seçili (app_config > ui.default_selected_module_labels)
        setSelectedState((cur) => (cur.length ? cur : defaultSelection(s, m.models)));
        setDisclaimer(typeof s.disclaimer === 'string' && s.disclaimer ? s.disclaimer : null);
      })
      .catch((e: unknown) => {
        if (alive) setLoadError(e instanceof ApiError ? e.message : String(e));
      });
    return () => {
      alive = false;
    };
  }, []);

  const go = useCallback((p: Page) => {
    setPage(p);
    if (typeof window !== 'undefined' && typeof window.scrollTo === 'function') {
      try {
        window.scrollTo({ top: 0 });
      } catch {
        /* jsdom */
      }
    }
  }, []);
  const setValues = useCallback((fn: (v: FormValues) => FormValues) => {
    setValuesState(fn);
    setPrediction(null); // girdi değişince eski sonuç geçersiz
  }, []);
  const resetValues = useCallback((v: FormValues = {}) => {
    setValuesState(v);
    setPrediction(null);
  }, []);
  const setSelected = useCallback((keys: string[]) => {
    setSelectedState(keys);
    setPrediction(null); // seçim değişince gönderilen alanlar değişir; eski sonuç geçersiz
  }, []);

  const value = useMemo<Session>(
    () => ({
      page, go, schema, models, loadError, disclaimer, values, setValues, resetValues, profileLabel, setProfileLabel,
      prediction, setPrediction, ecg, setEcg, selected, setSelected, step, setStep,
    }),
    [page, go, schema, models, loadError, disclaimer, values, setValues, resetValues, profileLabel, prediction, ecg, selected, setSelected, step],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): Session {
  const s = useContext(Ctx);
  if (!s) throw new Error('SessionProvider yok');
  return s;
}
