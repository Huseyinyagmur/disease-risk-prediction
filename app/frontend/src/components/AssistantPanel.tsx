// Phase XLVIII: "Açıklama asistanı" — her sayfada açılabilir. Sohbet YALNIZ bu bileşenin React belleğindedir (tarayıcı
// depolaması yok); sayfa yenilenince silinir. Görünür metinlerin tek kaynağı app_config > ui.text_tr.
// Phase L2 (phase_l2/01_design_brief.md): masaüstünde (≥ 1024 px) sağdan kayan çekmece + hafif karartma (içerik daralmaz,
// en çok 2 sütun okunur); "genişlet" ortada en çok 860 px; tablet/mobilde tam ekran. Kipli iletişim kutusu: aria-modal,
// arka plan inert (App), Esc kapatır, Tab panel içinde döner. Mesaj balonları (kullanıcı sağda, asistan solda), satır en
// çok ~680 px, örnek sorular küçük chip'ler, "yazıyor" göstergesi. Sunucunun her yanıta eklediği uzun uyarı balondan
// çıkarılır; panelin altında kısa tek satır uyarı her zaman görünür (API değişmez).
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
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
const MAX_CHIPS = 4;

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

/** Phase L2: sunucunun yanıt sonuna eklediği uzun araştırma uyarısı balonda tekrar gösterilmez (panel altında kısa satır var). */
export function stripDisclaimer(text: string, disclaimer: string | null | undefined): string {
  if (!disclaimer) return text;
  const tt = text.trimEnd();
  return tt.endsWith(disclaimer) ? tt.slice(0, -disclaimer.length).trimEnd() : text;
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

const FOCUSABLE = 'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select,summary,[tabindex]:not([tabindex="-1"])';

export function AssistantPanel({ onOpenChange }: { onOpenChange?: (open: boolean) => void }) {
  const { schema, prediction, ecg, selected, disclaimer } = useSession();
  const desktop = useDesktop();
  const [open, setOpen] = useState(false);
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
  const panelRef = useRef<HTMLElement>(null);
  const openBtn = useRef<HTMLButtonElement>(null);

  const labels = useMemo(() => resultLabels(prediction, ecg, schema, selected), [prediction, ecg, schema, selected]);
  const suggest = useMemo(() => suggestedQuestions(schema, labels), [schema, labels]);

  useEffect(() => {
    onOpenChange?.(open);
  }, [open, onOpenChange]);

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
    setWide(false);
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
      push({ role: 'bot', text: stripDisclaimer(r.answer, r.disclaimer ?? disclaimer), sources: r.sources, notice: r.emergency_notice });
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

  // Kipli iletişim kutusu: Esc kapatır; Tab / Shift+Tab panel içinde döner.
  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key === 'Escape') {
      close();
      return;
    }
    if (e.key !== 'Tab' || !panelRef.current) return;
    const els = [...panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    if (els.length === 0) return;
    const first = els[0];
    const last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  const disabled = status !== null && !status.enabled;
  const layout = !desktop ? 'fullscreen' : wide ? 'centered' : 'drawer';
  const frame = {
    drawer: 'fixed inset-y-0 right-0 w-full max-w-[460px] border-l border-slate-200 shadow-2xl',
    centered: 'fixed inset-x-0 top-[8vh] mx-auto h-auto max-h-[min(84vh,760px)] min-h-[min(420px,84vh)] w-[calc(100%-4rem)] max-w-[860px] rounded-xl border border-slate-200 shadow-2xl',
    fullscreen: 'fixed inset-0',
  }[layout];
  const chips = suggest.qs.slice(0, MAX_CHIPS);

  return (
    <>
      {!open && (
        <button type="button" ref={openBtn} data-testid="assistant-open" onClick={() => setOpen(true)}
          className="fixed bottom-4 right-4 z-40 rounded-full bg-indigo-700 px-5 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-300">
          {t(schema, 'asst_open')}
        </button>
      )}
      {open && desktop && (
        <div data-testid="assistant-backdrop" aria-hidden="true" onClick={close} className="fixed inset-0 z-40 bg-slate-900/30" />
      )}
      {open && (
        <section ref={panelRef} role="dialog" aria-modal="true" aria-labelledby="assistant-title" data-testid="assistant-panel"
          data-layout={layout} onKeyDown={onKeyDown}
          className={`${frame} z-50 flex flex-col overflow-hidden bg-slate-50`}>
          <header className="border-b border-slate-200 bg-white px-5 py-3">
            <div className="flex items-center justify-between gap-3">
              <h2 id="assistant-title" className="text-base font-semibold text-slate-900">{t(schema, 'asst_title')}</h2>
              <div className="flex shrink-0 items-center gap-1">
              {msgs.length > 0 && (
                <button type="button" onClick={() => setMsgs([])} data-testid="assistant-clear"
                  className="rounded-md px-2 py-1 text-xs text-slate-700 hover:bg-slate-100">{t(schema, 'asst_new_chat')}</button>
              )}
              {desktop && (
                <button type="button" onClick={() => setWide((w) => !w)} data-testid="assistant-expand" aria-pressed={wide}
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100">
                  {wide ? t(schema, 'asst_shrink') : t(schema, 'asst_expand')}
                </button>
              )}
              <button type="button" onClick={close} aria-label={t(schema, 'asst_close')} data-testid="assistant-close"
                className="rounded-md px-2 py-1 text-lg leading-none text-slate-600 hover:bg-slate-100">✕</button>
              </div>
            </div>
            <p className="mt-0.5 text-xs text-emerald-800" data-testid="assistant-local-note">{t(schema, 'asst_local_note')}</p>
          </header>

          <div ref={listRef} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4" data-testid="assistant-messages" aria-live="polite">
            <div className="mx-auto flex w-full max-w-[720px] flex-col gap-3">
              {status === null && !statusErr && <p className="text-xs text-slate-600">{t(schema, 'asst_checking')}</p>}
              {(disabled || statusErr) && (
                <p role="alert" data-testid="assistant-disabled" className="rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">
                  {t(schema, 'asst_disabled', { reason: statusErr ?? status?.reason ?? 'BULUNAMADI' })}
                </p>
              )}
              {msgs.length === 0 && !disabled && (
                <div data-testid="assistant-examples" data-from-results={suggest.fromResults ? 'true' : 'false'}
                  className="mr-auto max-w-[680px] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3">
                  <p className="text-[15px] leading-relaxed text-slate-900" data-testid="assistant-welcome">{t(schema, 'asst_welcome')}</p>
                  <p className="mt-2 text-xs font-medium text-slate-600">{suggest.fromResults ? t(schema, 'asst_suggest_title') : t(schema, 'asst_examples_title')}</p>
                  <div className="mt-1.5 flex flex-wrap gap-2">
                    {chips.map((x) => (
                      <button key={x} type="button" data-testid="assistant-chip" disabled={busy || disabled} onClick={() => void ask(x)}
                        className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm text-indigo-900 hover:border-indigo-400 hover:bg-indigo-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:opacity-50">
                        {x}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {msgs.map((m) =>
                m.role === 'user' ? (
                  <div key={m.id} data-testid="assistant-msg-user"
                    className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-indigo-700 px-4 py-2.5 text-[15px] leading-relaxed text-white">
                    <span className="sr-only">{t(schema, 'asst_you')}: </span>
                    {m.text}
                  </div>
                ) : (
                  <div key={m.id} data-testid={`assistant-msg-${m.role}`}
                    className={`mr-auto w-fit max-w-[680px] rounded-2xl rounded-bl-md px-4 py-3 text-[15px] leading-relaxed ${m.role === 'error' ? 'border border-rose-300 bg-rose-50 text-rose-900' : 'border border-slate-200 bg-white text-slate-900'}`}>
                    <span className="sr-only">{t(schema, 'asst_bot')}: </span>
                    {m.notice && (
                      <div role="alert" data-testid="assistant-emergency-notice"
                        className="mb-3 rounded-lg border-2 border-red-700 bg-red-50 p-3 text-red-950">
                        <p className="text-sm font-bold">⚠ {t(schema, 'asst_emergency_title')}</p>
                        <p className="text-[15px] font-semibold">{m.notice}</p>
                      </div>
                    )}
                    {m.text.split(/\n{2,}/).map((para, i) => <p key={i} className="mb-2 whitespace-pre-line last:mb-0">{para}</p>)}
                    {m.sources && m.sources.length > 0 && (
                      <details data-testid="assistant-sources" className="mt-2 border-t border-slate-100 pt-2 text-xs text-slate-700">
                        <summary className="cursor-pointer font-medium text-slate-600">{t(schema, 'asst_sources_n', { n: m.sources.length })}</summary>
                        <ol className="mt-1 list-decimal space-y-1 pl-5">
                          {m.sources.map((s) => <SourceItem key={s.doc_id} s={s} internalLabel={t(schema, 'asst_internal_doc')} />)}
                        </ol>
                      </details>
                    )}
                  </div>
                ),
              )}
              {busy && (
                <div role="status" data-testid="assistant-waiting"
                  className="mr-auto flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600">
                  <span className="flex gap-1" aria-hidden="true">
                    {[0, 150, 300].map((d) => (
                      <span key={d} className="h-1.5 w-1.5 rounded-full bg-slate-400 motion-safe:animate-bounce" style={{ animationDelay: `${d}ms` }} />
                    ))}
                  </span>
                  <span>{t(schema, 'asst_typing')}</span>
                  <span className="sr-only">{t(schema, 'asst_waiting')}</span>
                </div>
              )}
            </div>
          </div>

          <form onSubmit={onSubmit} className="border-t border-slate-200 bg-white px-4 py-3">
            <div className="mx-auto w-full max-w-[720px] space-y-2">
              {labels.length > 0 && (
                <label className="flex items-start gap-2 text-xs text-slate-700">
                  <input type="checkbox" checked={withResults} onChange={(e) => setWithResults(e.target.checked)} data-testid="assistant-with-results" className="mt-0.5" />
                  <span>{t(schema, 'asst_with_results', { n: labels.length })}</span>
                </label>
              )}
              <div className="flex items-end gap-2">
                <label htmlFor="assistant-input" className="sr-only">{t(schema, 'asst_placeholder')}</label>
                <textarea id="assistant-input" ref={inputRef} rows={2} maxLength={500} value={q} data-testid="assistant-input"
                  placeholder={t(schema, 'asst_placeholder')} disabled={busy || disabled}
                  onChange={(e) => setQ(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void ask(q); } }}
                  className="min-w-0 flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3 py-2 text-[15px] focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                <button type="submit" disabled={busy || disabled || !q.trim()} data-testid="assistant-send"
                  className="rounded-xl bg-indigo-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-800 disabled:bg-slate-200 disabled:text-slate-600">
                  {t(schema, 'asst_send')}
                </button>
              </div>
              <p className="text-xs text-slate-600" data-testid="assistant-disclaimer">{t(schema, 'asst_disclaimer_short')}</p>
            </div>
          </form>
        </section>
      )}
    </>
  );
}
