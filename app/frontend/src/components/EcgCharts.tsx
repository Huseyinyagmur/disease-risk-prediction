// Görüntüleme: backend'in döndürdüğü lead II (250 Hz) ve R tepe zamanları. Frontend hesap yapmaz;
// yalnız gelen dizileri çizer. RR takogramı backend'in rr_ms dizisidir.
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { EcgDisplay } from '../api/types';

const INK = '#334155'; // slate-700 — tek seri, nötr
const ACCENT = '#c2410c'; // orange-700 — R tepe işaretleri
const GRID = '#e2e8f0';

export function EcgTrace({ d }: { d: EcgDisplay }) {
  const data = d.signal_mv.map((v, i) => ({ t: +(i / d.fs_hz).toFixed(3), mv: v }));
  return (
    <figure data-testid="ecg-trace" aria-label={`Lead ${d.lead}, ilk ${d.duration_s} saniye; ${d.r_peaks_s?.length ?? 0} R tepesi`}>
      <figcaption className="mb-1 text-sm font-medium text-slate-800">
        Lead {d.lead} — ilk {d.duration_s} sn <span className="font-normal text-slate-500">(y: mV, x: saniye; dikey çizgiler: ECGDeli R tepeleri)</span>
      </figcaption>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 16, left: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="t" type="number" domain={[0, d.duration_s]} tickCount={11} tick={{ fontSize: 11, fill: '#64748b' }} stroke={GRID} />
            <YAxis dataKey="mv" width={44} tick={{ fontSize: 11, fill: '#64748b' }} stroke={GRID} domain={['auto', 'auto']} />
            <Tooltip formatter={(v: number) => [`${v} mV`, `Lead ${d.lead}`]} labelFormatter={(t: number) => `${t} s`} isAnimationActive={false} />
            {(d.r_peaks_s ?? []).map((t) => (
              <ReferenceLine key={t} x={t} stroke={ACCENT} strokeOpacity={0.55} strokeWidth={1} />
            ))}
            <Line type="linear" dataKey="mv" stroke={INK} strokeWidth={1.25} dot={false} isAnimationActive={false} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}

export function RrTachogram({ d }: { d: EcgDisplay }) {
  const rr = d.rr_ms ?? [];
  if (rr.length === 0) return <p className="text-xs text-slate-500">R tepesi bulunamadı; RR takogramı çizilemedi.</p>;
  const data = rr.map((v, i) => ({ beat: i + 1, rr: v }));
  return (
    <figure data-testid="rr-tachogram" aria-label={`RR aralıkları, ${rr.length} aralık`}>
      <figcaption className="mb-1 text-sm font-medium text-slate-800">
        Ardışık RR aralıkları <span className="font-normal text-slate-500">(y: ms; düzensiz zikzak: RR düzensizliği; düz çizgi: düzenli ritim)</span>
      </figcaption>
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 16, left: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="beat" type="number" domain={[1, Math.max(2, rr.length)]} allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} stroke={GRID}
              label={{ value: 'aralık no', position: 'insideBottom', offset: -8, fontSize: 11, fill: '#64748b' }} />
            <YAxis width={48} domain={[0, 'auto']} tick={{ fontSize: 11, fill: '#64748b' }} stroke={GRID} />
            <Tooltip formatter={(v: number) => [`${v} ms`, 'RR']} labelFormatter={(b: number) => `aralık ${b}`} isAnimationActive={false} />
            <Line type="linear" dataKey="rr" stroke={INK} strokeWidth={2} dot={{ r: 4, fill: INK, stroke: '#fff', strokeWidth: 2 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-1 text-xs text-slate-600">
        <summary className="cursor-pointer">RR değerleri (tablo)</summary>
        <p className="mt-1 font-mono">{rr.map((v) => v.toFixed(0)).join(', ')} ms</p>
      </details>
    </figure>
  );
}
