// Phase XLVIII: "Açıklama asistanı" paneli — her sayfada açılabilir. Sohbet YALNIZ bu bileşenin React belleğindedir
// (tarayıcı depolaması yok); sayfa yenilenince silinir. Görünür metinlerin tek kaynağı app_config > ui.text_tr.
// Phase L: masaüstünde (≥ 1024 px) sağda tam yükseklik yan panel (ekranın ~%38'i, sürüklenerek / ok tuşlarıyla
// boyutlandırılır, "genişlet" ile neredeyse tam ekran); içerik panel kadar daralır (onLayout). Tablet/mobilde tam ekran.
// Örnek sorular, o an görülen sonuçların yalnız ETİKETLERİNDEN (hastalık + durum) seçilir; ham değer kullanılmaz.
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type PointerEvent as RPointerEvent } from 'react';
import { api, ApiError } from '../api/client';
import type { AssistantResponse, AssistantResultLabel, AssistantSource, AssistantStatus, Schema } from '../api/types';
import { resultLabels } from '../lib/assistant';
import { t } from '../lib/ui';
import { useSession } from '../state/session';

interface Msg {
  id: number;
  role: 'user' | 'bot' | 'error';
  text: string;
  sources?: AssistantSource[];
  notice?: string;
}

const DESKTOP_QUERY = '(min-width: 1024px)';
const MIN_W = 360;
const STEP_W = 32;

function useDesktop(): boolean {
  const query = () => (typeof window !== 'undefined' && typeof window.matchMedia === 'function' ? window.matchMedia(DESKTOP_QUERY) : null);
  const [on, setOn] = useState(() => !!query()?.matches);
  useEffect(() => {
    const mq = query();
    if (!mq) return;
    const fn = () => setOn(mq.matches);
    mq.addEventListener?.('change', fn);
    return () => mq.removeEventListener?.('change', fn);
  }, []);
  return on;
}

const vw = () => (typeof window !== 'undefined' ? window.innerWidth : 1440);
const clampW = (w: number) => Math.round(Math.min(Math.max(w, MIN_W), vw() * 0.92));

/** Gördüğünüz sonuçlara göre örnek sorular (yalnız etiket). Etiket yoksa varsayılan örnekler. */
export function suggestedQuestions(schema: Schema | null, labels: AssistantResultLabel[]): { fromResults: boolean; qs: string[] } {
  const byO = schema?.ui?.asst_examples_by_outcome_tr ?? {};
  const byD = schema?.ui?.asst_examples_by_disease_tr ?? {};
  const qs: string[] = [];
  for (const l of labels) {
    if (byO[l.outcome]) qs.push(byO[l.outcome]);
    if ((l.outcome === 'ESIK_USTU' || l.outcome === 'ESIK_ALTI') && byD[l.disease_key]) qs.push(byD[l.disease_key]);
  }
  const uniq = [...new Set(qs)].slice(0, 5);
  if (uniq.length) return { fromResults: true, qs: uniq };
  return { fromResults: false, qs: (schema?.ui?.text_tr.asst_examples ?? '').split('|').filter(Boolean) };
}

function SourceItem({ s, internalLabel }: { s: AssistantSource; internalLabel: string }) {
  const label = s.section ? `${s.title} — ${s.section}` : s.title;
  if (s.kind === 'external' && s.url) {
    return (
      <li>
        <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-indigo-800 underline hover:text-indigo-950">{label}</a>
        {s.publisher && <span className="text-slate-600"> · {s.publisher}</span>}
      </li>
    );
  }
  return (
    <li>
      <span className="font-medium">{internalLabel}:</span> {label}
    </li>
  );
}

function detailText(e: unknown): string {
  if (e instanceof ApiError) return typeof e.detail === 'string' ? e.detail : e.message;
  return String(e);
}

export function AssistantPanel({ onLayout }: { onLayout?: (rightPx: number) => void }) {
  const { schema, prediction, ecg, selected, disclaimer } = useSession();
  const desktop = useDesktop();
  const [open, setOpen] = useState(false);
  const [width, setWidth] = useState(() => clampW(vw() * 0.38));
  const [wide, setWide] = useState(false);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [statusErr, setStatusErr] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [withResults, setWithResults] = useState(true);
  const nextId = useRef(1);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const openBtn = useRef<HTMLButtonElement>(null);

  const labels = useMemo(() => resultLabels(prediction, ecg, schema, selected), [prediction, ecg, schema, selected]);
  const suggest = useMemo(() => suggestedQuestions(schema, labels), [schema, labels]);
  const panelW = wide ? clampW(vw() * 0.92) : width;

  // İçerik, yan panel kadar daralır (yalnız masaüstü). Genişletilmiş panel içeriğin üstüne biner; içerik en çok %50 daralır.
  useEffect(() => {
    onLayout?.(open && desktop ? Math.min(width, Math.round(vw() * 0.5)) : 0);
  }, [open, desktop, width, onLayout]);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    setStatusErr(null);
    api.health()
      .then((h) => {
        if (alive) setStatus((h.assistant as AssistantStatus | undefined) ?? { enabled: false, reason: 'BULUNAMADI' });
      })
      .catch((e: unknown) => {
        if (alive) setStatusErr(detailText(e));
      });
    inputRef.current?.focus();
    return () => {
      alive = false;
    };
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo?.({ top: listRef.current.scrollHeight });
  }, [msgs, busy]);

  const close = useCallback(() => {
    setOpen(false);
    setTimeout(() => openBtn.current?.focus(), 0);
  }, []);

  const ask = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    const push = (m: Omit<Msg, 'id'>) => setMsgs((xs) => [...xs, { ...m, id: nextId.current++ }]);
    push({ role: 'user', text });
    setQ('');
    setBusy(true);
    try {
      const r: AssistantResponse = await api.assistantAsk(text, withResults ? labels : []);
      push({ role: 'bot', text: r.answer, sources: r.sources, notice: r.emergency_notice });
    } catch (e) {
      push({ role: 'error', text: t(schema, 'asst_error', { msg: detailText(e) }) });
      if (e instanceof ApiError && e.status === 503) setStatus({ enabled: false, reason: detailText(e) });
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void ask(q);
  };

  // Sürükleyerek boyutlandırma (sol kenar). Klavye: ← genişlet, → daralt.
  const onDragStart = (e: RPointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    setWide(false);
    const move = (ev: PointerEvent) => setWidth(clampW(window.innerWidth - ev.clientX));
    const prevSelect = document.body.style.userSelect;
    document.body.style.userSelect = 'none'; // sürükleme sırasında metin seçimi kapalı
    const up = () => {
      document.body.style.userSelect = prevSelect;
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  const disabled = status !== null && !status.enabled;
  const frame = desktop
    ? 'fixed inset-y-0 right-0 z-40 border-l border-slate-300 shadow-xl'
    : 'fixed inset-0 z-50';
  return (
    <>
      {!open && (
        <button type="button" ref={openBtn} data-testid="assistant-open" onClick={() => setOpen(true)}
          className="fixed bottom-4 right-4 z-40 rounded-full bg-indigo-800 px-5 py-3 text-base font-semibold text-white shadow-lg hover:bg-indigo-900 focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-300">
          {t(schema, 'asst_open')}
        </button>
      )}
      {open && (
        <section role="dialog" aria-modal="false" aria-labelledby="assistant-title" data-testid="assistant-panel"
          data-layout={desktop ? (wide ? 'side-wide' : 'side') : 'fullscreen'}
          style={desktop ? { width: panelW } : undefined}
          className={`${frame} flex flex-col bg-white`}
          onKeyDown={(e) => { if (e.key === 'Escape') close(); }}>
          {desktop && (
            <div role="separator" aria-orientation="vertical" aria-label={t(schema, 'asst_resize')} tabIndex={0}
              aria-valuemin={MIN_W} aria-valuemax={Math.round(vw() * 0.92)} aria-valuenow={panelW} data-testid="assistant-resize"
              onPointerDown={onDragStart}
              onKeyDown={(e) => {
                if (e.key === 'ArrowLeft') { setWide(false); setWidth((w) => clampW(w + STEP_W)); }
                if (e.key === 'ArrowRight') { setWide(false); setWidth((w) => clampW(w - STEP_W)); }
              }}
              className="absolute inset-y-0 -left-1.5 w-3 cursor-col-resize focus:outline-none focus-visible:bg-indigo-300/60 hover:bg-indigo-200/60" />
          )}
          <header className="flex items-start justify-between gap-2 border-b border-slate-200 px-4 py-3">
            <div className="min-w-0">
              <h2 id="assistant-title" className="text-lg font-semibold text-slate-900">{t(schema, 'asst_title')}</h2>
              <p className="text-sm text-emerald-800" data-testid="assistant-local-note">{t(schema, 'asst_local_note')}</p>
            </div>
            <div className="flex shrink-0 gap-1">
              {desktop && (
                <button type="button" onClick={() => setWide((w) => !w)} data-testid="assistant-expand" aria-pressed={wide}
                  className="rounded border border-slate-300 px-2 py-1 text-sm text-slate-700 hover:bg-slate-100">
                  {wide ? t(schema, 'asst_shrink') : t(schema, 'asst_expand')}
                </button>
              )}
              <button type="button" onClick={close} aria-label={t(schema, 'asst_close')} data-testid="assistant-close"
                className="rounded px-2 py-1 text-lg leading-none text-slate-600 hover:bg-slate-100">✕</button>
            </div>
          </header>

          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto overscroll-contain px-4 py-3 text-base" data-testid="assistant-messages" aria-live="polite">
            <p className="text-sm text-slate-700">{t(schema, 'asst_intro')}</p>
            {status === null && !statusErr && <p className="text-sm text-slate-600">{t(schema, 'asst_checking')}</p>}
            {(disabled || statusErr) && (
              <p role="alert" data-testid="assistant-disabled" className="rounded border border-rose-300 bg-rose-50 p-2 text-sm text-rose-900">
                {t(schema, 'asst_disabled', { reason: statusErr ?? status?.reason ?? 'BULUNAMADI' })}
              </p>
            )}
            {msgs.length === 0 && !disabled && (
              <div data-testid="assistant-examples" data-from-results={suggest.fromResults ? 'true' : 'false'}>
                <p className="mb-2 text-sm font-semibold text-slate-800">{suggest.fromResults ? t(schema, 'asst_suggest_title') : t(schema, 'asst_examples_title')}</p>
                <div className="grid gap-2">
                  {suggest.qs.map((x) => (
                    <button key={x} type="button" disabled={busy || disabled} onClick={() => void ask(x)}
                      className="rounded-lg border border-indigo-300 bg-white px-4 py-3 text-left text-base text-indigo-950 hover:bg-indigo-50 disabled:opacity-50">
                      {x}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {msgs.map((m) => (
              <div key={m.id} data-testid={`assistant-msg-${m.role}`}
                className={m.role === 'user' ? 'ml-8 rounded-lg bg-slate-100 p-3' : m.role === 'error' ? 'rounded-lg border border-rose-300 bg-rose-50 p-3 text-rose-900' : 'rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-slate-900'}>
                <p className="mb-1 text-sm font-semibold text-slate-600">{m.role === 'user' ? t(schema, 'asst_you') : t(schema, 'asst_bot')}</p>
                {m.notice && (
                  <div role="alert" data-testid="assistant-emergency-notice"
                    className="mb-3 rounded-lg border-2 border-red-700 bg-red-50 p-3 text-red-950">
                    <p className="text-base font-bold">⚠ {t(schema, 'asst_emergency_title')}</p>
                    <p className="text-base font-semibold">{m.notice}</p>
                  </div>
                )}
                {m.text.split(/\n{2,}/).map((para, i) => <p key={i} className="mb-2 whitespace-pre-line leading-relaxed">{para}</p>)}
                {m.sources && m.sources.length > 0 && (
                  <details data-testid="assistant-sources" className="mt-1 border-t border-indigo-200 pt-2 text-sm">
                    <summary className="cursor-pointer font-medium">{t(schema, 'asst_sources_n', { n: m.sources.length })}</summary>
                    <ol className="mt-1 list-decimal space-y-1 pl-5">
                      {m.sources.map((s) => <SourceItem key={s.doc_id} s={s} internalLabel={t(schema, 'asst_internal_doc')} />)}
                    </ol>
                  </details>
                )}
              </div>
            ))}
            {busy && (
              <p role="status" data-testid="assistant-waiting" className="flex items-center gap-2 text-sm text-slate-700">
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-700 border-t-transparent motion-reduce:animate-none" aria-hidden="true" />
                {t(schema, 'asst_waiting')}
              </p>
            )}
          </div>

          <form onSubmit={onSubmit} className="space-y-2 border-t border-slate-200 px-4 py-3">
            {labels.length > 0 && (
              <label className="flex items-start gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={withResults} onChange={(e) => setWithResults(e.target.checked)} data-testid="assistant-with-results" className="mt-1" />
                <span>{t(schema, 'asst_with_results', { n: labels.length })}</span>
              </label>
            )}
            <div className="flex gap-2">
              <label htmlFor="assistant-input" className="sr-only">{t(schema, 'asst_placeholder')}</label>
              <textarea id="assistant-input" ref={inputRef} rows={2} maxLength={500} value={q} data-testid="assistant-input"
                placeholder={t(schema, 'asst_placeholder')} disabled={busy || disabled}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void ask(q); } }}
                className="min-w-0 flex-1 resize-none rounded border border-slate-400 px-3 py-2 text-base" />
              <button type="submit" disabled={busy || disabled || !q.trim()} data-testid="assistant-send"
                className="self-end rounded bg-indigo-800 px-4 py-2 text-base font-medium text-white hover:bg-indigo-900 disabled:opacity-50">
                {t(schema, 'asst_send')}
              </button>
            </div>
            {msgs.length > 0 && (
              <button type="button" onClick={() => setMsgs([])} className="text-sm text-slate-700 underline">{t(schema, 'asst_clear')}</button>
            )}
            {disclaimer && <p className="text-xs text-amber-900" data-testid="assistant-disclaimer">{disclaimer}</p>}
          </form>
        </section>
      )}
    </>
  );
}
