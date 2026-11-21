// Phase XLVIII: "Açıklama asistanı" paneli — her sayfada açılabilir. Sohbet YALNIZ bu bileşenin React belleğindedir
// (tarayıcı depolaması yok); sayfa yenilenince silinir. Görünür metinlerin tek kaynağı app_config > ui.text_tr.
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';
import type { AssistantResponse, AssistantSource, AssistantStatus } from '../api/types';
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

export function AssistantPanel() {
  const { schema, prediction, ecg, selected } = useSession();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [statusErr, setStatusErr] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [withResults, setWithResults] = useState(true);
  const nextId = useRef(1);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const labels = useMemo(() => resultLabels(prediction, ecg, schema, selected), [prediction, ecg, schema, selected]);
  const examples = (schema?.ui?.text_tr.asst_examples ?? '').split('|').filter(Boolean);

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

  const disabled = status !== null && !status.enabled;
  return (
    <>
      {!open && (
        <button type="button" data-testid="assistant-open" onClick={() => setOpen(true)}
          className="fixed bottom-4 right-4 z-40 rounded-full bg-indigo-800 px-4 py-2 text-sm font-semibold text-white shadow-lg hover:bg-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-400">
          {t(schema, 'asst_open')}
        </button>
      )}
      {open && (
        <section role="dialog" aria-modal="false" aria-labelledby="assistant-title" data-testid="assistant-panel"
          className="fixed inset-x-2 bottom-2 z-40 flex max-h-[85vh] flex-col rounded-lg border border-slate-300 bg-white shadow-2xl sm:inset-x-auto sm:right-4 sm:w-[26rem]"
          onKeyDown={(e) => { if (e.key === 'Escape') setOpen(false); }}>
          <header className="flex items-start justify-between gap-2 border-b border-slate-200 px-3 py-2">
            <div>
              <h2 id="assistant-title" className="text-base font-semibold text-slate-900">{t(schema, 'asst_title')}</h2>
              <p className="text-[11px] text-emerald-800" data-testid="assistant-local-note">{t(schema, 'asst_local_note')}</p>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label={t(schema, 'asst_close')} data-testid="assistant-close"
              className="rounded px-2 py-1 text-slate-600 hover:bg-slate-100">✕</button>
          </header>

          <div ref={listRef} className="flex-1 space-y-2 overflow-y-auto px-3 py-2 text-sm" data-testid="assistant-messages" aria-live="polite">
            <p className="text-xs text-slate-700">{t(schema, 'asst_intro')}</p>
            {status === null && !statusErr && <p className="text-xs text-slate-500">{t(schema, 'asst_checking')}</p>}
            {(disabled || statusErr) && (
              <p role="alert" data-testid="assistant-disabled" className="rounded border border-rose-300 bg-rose-50 p-2 text-xs text-rose-900">
                {t(schema, 'asst_disabled', { reason: statusErr ?? status?.reason ?? 'BULUNAMADI' })}
              </p>
            )}
            {msgs.length === 0 && !disabled && (
              <div data-testid="assistant-examples">
                <p className="mb-1 text-xs font-medium text-slate-700">{t(schema, 'asst_examples_title')}</p>
                <div className="flex flex-wrap gap-1">
                  {examples.map((x) => (
                    <button key={x} type="button" disabled={busy || disabled} onClick={() => void ask(x)}
                      className="rounded-full border border-indigo-300 px-2 py-1 text-xs text-indigo-900 hover:bg-indigo-50 disabled:opacity-50">
                      {x}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {msgs.map((m) => (
              <div key={m.id} data-testid={`assistant-msg-${m.role}`}
                className={m.role === 'user' ? 'ml-8 rounded bg-slate-100 p-2' : m.role === 'error' ? 'rounded border border-rose-300 bg-rose-50 p-2 text-rose-900' : 'mr-4 rounded border border-indigo-200 bg-indigo-50 p-2 text-indigo-950'}>
                <p className="mb-0.5 text-[11px] font-semibold text-slate-600">{m.role === 'user' ? t(schema, 'asst_you') : t(schema, 'asst_bot')}</p>
                {m.notice && (
                  <div role="alert" data-testid="assistant-emergency-notice"
                    className="mb-2 rounded-md border-2 border-red-600 bg-red-50 p-2 text-red-900">
                    <p className="text-xs font-bold uppercase tracking-wide">⚠ {t(schema, 'asst_emergency_title')}</p>
                    <p className="text-sm font-semibold">{m.notice}</p>
                  </div>
                )}
                {m.text.split(/\n{2,}/).map((para, i) => <p key={i} className="mb-1 whitespace-pre-line">{para}</p>)}
                {m.sources && m.sources.length > 0 && (
                  <div data-testid="assistant-sources" className="mt-1 border-t border-indigo-200 pt-1 text-xs">
                    <p className="font-medium">{t(schema, 'asst_sources')}</p>
                    <ol className="list-decimal pl-5">
                      {m.sources.map((s) => <SourceItem key={s.doc_id} s={s} internalLabel={t(schema, 'asst_internal_doc')} />)}
                    </ol>
                  </div>
                )}
              </div>
            ))}
            {busy && (
              <p role="status" data-testid="assistant-waiting" className="flex items-center gap-2 text-xs text-slate-700">
                <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-indigo-700 border-t-transparent" aria-hidden="true" />
                {t(schema, 'asst_waiting')}
              </p>
            )}
          </div>

          <form onSubmit={onSubmit} className="space-y-1 border-t border-slate-200 px-3 py-2">
            {labels.length > 0 && (
              <label className="flex items-start gap-2 text-[11px] text-slate-700">
                <input type="checkbox" checked={withResults} onChange={(e) => setWithResults(e.target.checked)} data-testid="assistant-with-results" className="mt-0.5" />
                <span>{t(schema, 'asst_with_results', { n: labels.length })}</span>
              </label>
            )}
            <div className="flex gap-2">
              <label htmlFor="assistant-input" className="sr-only">{t(schema, 'asst_placeholder')}</label>
              <textarea id="assistant-input" ref={inputRef} rows={2} maxLength={500} value={q} data-testid="assistant-input"
                placeholder={t(schema, 'asst_placeholder')} disabled={busy || disabled}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void ask(q); } }}
                className="min-w-0 flex-1 resize-none rounded border border-slate-300 px-2 py-1 text-sm" />
              <button type="submit" disabled={busy || disabled || !q.trim()} data-testid="assistant-send"
                className="self-end rounded bg-indigo-800 px-3 py-1.5 text-sm text-white hover:bg-indigo-900 disabled:opacity-50">
                {t(schema, 'asst_send')}
              </button>
            </div>
            {msgs.length > 0 && (
              <button type="button" onClick={() => setMsgs([])} className="text-[11px] text-slate-600 underline">{t(schema, 'asst_clear')}</button>
            )}
          </form>
        </section>
      )}
    </>
  );
}
