import type { EcgDisplay } from '../api/types';
import { EcgTrace, RrTachogram } from './EcgCharts';

export function EcgRrPanel({ d }: { d: EcgDisplay }) {
  return (
    <section className="mt-4 space-y-4 rounded-lg border border-slate-200 bg-white p-4" aria-label="EKG grafiği" data-testid="ecg-display">
      <EcgTrace d={d} />
      <RrTachogram d={d} />
      <p className="text-[11px] text-slate-500">{d.note}</p>
    </section>
  );
}
