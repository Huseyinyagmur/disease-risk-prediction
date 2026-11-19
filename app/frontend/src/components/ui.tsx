import type { ReactNode } from 'react';
import type { EligState, Evidence, Metric, Tier } from '../api/types';
import { useSession, type Page } from '../state/session';

/** Uyarı metni frontend'de TUTULMAZ: tek kaynak backend'dir (/schema yanıtındaki `disclaimer`). Metin gelmeden önce veya
 * sunucuya ulaşılamazsa yalnız durum bildirilir (uyarının yerine geçen bir metin uydurulmaz). */
export function DisclaimerText() {
  const { disclaimer, loadError } = useSession();
  if (disclaimer) return <span data-testid="disclaimer-text">{disclaimer}</span>;
  return (
    <span data-testid="disclaimer-missing" className="italic">
      {loadError ? 'Sunucuya ulaşılamadı; araştırma uyarısı yüklenemedi. Sunucu olmadan sonuç üretilmez.' : 'Araştırma uyarısı sunucudan yükleniyor…'}
    </span>
  );
}

export function DisclaimerBar() {
  return (
    <div role="note" aria-label="Sabit uyarı" data-testid="disclaimer"
      className="sticky top-0 z-30 border-b border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900">
      <span className="font-semibold">Uyarı: </span>
      <DisclaimerText />
    </div>
  );
}

const NAV: [Page, string][] = [
  ['home', 'Giriş'],
  ['form', 'Veri girişi'],
  ['results', 'Sonuçlar'],
  ['ecg', 'EKG ile AF'],
  ['models', 'Model kartları'],
  ['about', 'Hakkında'],
];

export function NavBar() {
  const { page, go } = useSession();
  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-7xl flex-wrap items-center gap-1 px-4 py-2" aria-label="Ana gezinme">
        <span className="mr-4 font-semibold text-slate-800">HealthRisk AI <span className="font-normal text-slate-500">· araştırma prototipi</span></span>
        {NAV.map(([p, label]) => (
          <button key={p} type="button" onClick={() => go(p)} aria-current={page === p ? 'page' : undefined}
            className={`rounded px-3 py-1.5 text-sm ${page === p ? 'bg-slate-800 text-white' : 'text-slate-700 hover:bg-slate-100'}`}>
            {label}
          </button>
        ))}
      </nav>
    </header>
  );
}

export function PageTitle({ children, sub }: { children: ReactNode; sub?: ReactNode }) {
  return (
    <div className="mb-4">
      <h1 className="text-2xl font-semibold text-slate-900">{children}</h1>
      {sub && <p className="mt-1 text-sm text-slate-600">{sub}</p>}
    </div>
  );
}

const STATE_STYLE: Record<EligState, [string, string]> = {
  READY: ['Çalışabilir', 'bg-emerald-100 text-emerald-800 border-emerald-300'],
  MISSING: ['Eksik', 'bg-amber-100 text-amber-900 border-amber-300'],
  OUT_OF_SCOPE: ['Kapsam dışı', 'bg-slate-200 text-slate-700 border-slate-300'],
  ABSTAIN: ['Karar verilemez', 'bg-rose-100 text-rose-800 border-rose-300'],
};

export function StateBadge({ state }: { state: EligState }) {
  const [label, cls] = STATE_STYLE[state];
  return <span data-testid="state-badge" data-state={state} className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${cls}`}>{label}</span>;
}

export function ModulePill({ label }: { label: string }) {
  const cls = label === 'ana modül' ? 'bg-indigo-100 text-indigo-800' : label === 'araştırma modülü' ? 'bg-sky-100 text-sky-800' : 'bg-slate-100 text-slate-600';
  return <span data-testid="module-label" className={`inline-block rounded-full px-2 py-0.5 text-xs ${cls}`}>{label}</span>;
}

const TIER_ORDER: ['internal_test' | 'temporal' | 'external', string][] = [
  ['internal_test', 'İç test'],
  ['temporal', 'Zamansal doğrulama'],
  ['external', 'Dış doğrulama'],
];

export function EvidenceBadges({ evidence }: { evidence: Evidence }) {
  return (
    <div className="flex flex-wrap gap-1" data-testid="evidence-badges">
      {TIER_ORDER.map(([k, label]) => {
        const has = !!evidence.tiers[k];
        return (
          <span key={k} title={has ? 'Bu kanıt düzeyi mevcut' : 'Bu kanıt düzeyi yok'}
            className={`rounded border px-2 py-0.5 text-xs ${has ? 'border-teal-400 bg-teal-50 text-teal-800' : 'border-dashed border-slate-300 text-slate-400 line-through'}`}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

const fmt = (x: number | undefined | null, d = 3) => (x === undefined || x === null ? '—' : x.toFixed(d).replace('.', ','));

export function MetricCell({ m }: { m: Metric | number | null | undefined }) {
  if (m === null || m === undefined) return <span className="text-slate-400" title="registry'de değer yok">—</span>;
  if (typeof m === 'number') return <span>{fmt(m)}</span>;
  return (
    <span>
      {fmt(m.value)}
      {m.ci95 && <span className="text-slate-500"> [{fmt(m.ci95[0])}–{fmt(m.ci95[1])}]</span>}
    </span>
  );
}

export function EvidenceTable({ evidence }: { evidence: Evidence }) {
  const rows = TIER_ORDER.filter(([k]) => evidence.tiers[k]).map(([k, label]) => [label, evidence.tiers[k] as Tier] as const);
  return (
    <div className="space-y-2">
      {evidence.highest_tier && (
        <p className="text-xs text-slate-600"><span className="font-medium">En yüksek kanıt düzeyi:</span> {evidence.highest_tier}</p>
      )}
      {rows.length === 0 ? (
        <p className="text-xs text-slate-500">Kanıt metriği BULUNAMADI.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs" data-testid="metrics-table">
            <thead className="text-slate-500">
              <tr>
                <th className="py-1 pr-2 font-medium">Düzey</th>
                <th className="py-1 pr-2 font-medium">n (pozitif)</th>
                <th className="py-1 pr-2 font-medium">Precision [%95 GA]</th>
                <th className="py-1 pr-2 font-medium">Recall [%95 GA]</th>
                <th className="py-1 pr-2 font-medium">FPR [%95 GA]</th>
                <th className="py-1 pr-2 font-medium">AUC [%95 GA]</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, t]) => (
                <tr key={label} className="border-t border-slate-100 align-top">
                  <td className="py-1 pr-2">
                    <div className="font-medium">{label}</div>
                    {t.source && <div className="text-slate-500">{t.source}</div>}
                  </td>
                  <td className="py-1 pr-2">{t.n ?? '—'} ({t.n_pos ?? '—'})</td>
                  <td className="py-1 pr-2"><MetricCell m={t.precision} /></td>
                  <td className="py-1 pr-2"><MetricCell m={t.recall} /></td>
                  <td className="py-1 pr-2"><MetricCell m={t.fpr} /></td>
                  <td className="py-1 pr-2"><MetricCell m={t.auc} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {evidence.research_target_note && (
        <p className="text-xs text-slate-600"><span className="font-medium">Araştırma hedefleri (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15):</span> {evidence.research_target_note}</p>
      )}
      <p className="text-[11px] text-slate-400">Metrikler registry'den aynen alınmıştır; uygulamada yeniden hesaplanmamıştır. CV sonuçları kanıt olarak gösterilmez. "—" = registry'de değer yok.</p>
    </div>
  );
}

export function Collapsible({ title, children, defaultOpen = false }: { title: string; children: ReactNode; defaultOpen?: boolean }) {
  return (
    <details className="group rounded border border-slate-200 bg-white" open={defaultOpen}>
      <summary className="cursor-pointer select-none px-3 py-2 text-sm font-medium text-slate-700">{title}</summary>
      <div className="border-t border-slate-100 px-3 py-2">{children}</div>
    </details>
  );
}
