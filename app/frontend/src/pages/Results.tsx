import { ResultCard } from '../components/ResultCard';
import { moduleRank } from '../components/RoutingPanel';
import { PageTitle } from '../components/ui';
import { useSession } from '../state/session';

export function Results() {
  const { prediction, models, schema, go } = useSession();
  if (!prediction) {
    return (
      <div>
        <PageTitle>Sonuçlar</PageTitle>
        <p className="text-sm text-slate-600">Henüz sonuç yok. Önce veri girişini doldurup "Sonuçları hesapla"ya basın.</p>
        <button type="button" onClick={() => go('form')} className="mt-3 rounded bg-slate-800 px-4 py-2 text-sm text-white">Veri girişine git</button>
      </div>
    );
  }
  const info = (id: string) => models?.find((m) => m.model_id === id);
  const sorted = [...prediction.results].sort((a, b) => moduleRank(a.module_label) - moduleRank(b.module_label));
  const main = sorted.filter((r) => r.module_label !== 'deneysel');
  const exp = sorted.filter((r) => r.module_label === 'deneysel');
  return (
    <div>
      <PageTitle sub="Her kart donmuş modelin donmuş eşiğine göre araştırma sınıflamasıdır. Kanıt düzeyleri ayrı gösterilir; olasılık gösterilmez.">
        Sonuçlar
      </PageTitle>
      {prediction.unit_conversion_notes.length > 0 && (
        <div className="mb-4 rounded border border-sky-200 bg-sky-50 p-2 text-xs text-sky-900" data-testid="unit-notes">
          <p className="font-medium">Sunucuda yapılan birim dönüşümleri:</p>
          <ul className="list-disc pl-5">{prediction.unit_conversion_notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </div>
      )}
      <section aria-label="Ana ve araştırma modülleri" className="mb-6">
        <h2 className="mb-2 text-lg font-semibold text-slate-800">Ana modüller ve araştırma modülü</h2>
        <div className="grid gap-4 xl:grid-cols-2">
          {main.map((r) => <ResultCard key={r.model_id} r={r} info={info(r.model_id)} schema={schema} onEcg={() => go('ecg')} />)}
        </div>
      </section>
      <section aria-label="Deneysel modüller" data-testid="experimental-section" className="rounded-lg bg-slate-100 p-3">
        <h2 className="mb-1 text-lg font-semibold text-slate-600">Deneysel modüller</h2>
        <p className="mb-3 text-xs text-slate-500">Bu modüller "deneysel" etiketlidir (modül etiketi danışman tanımıdır; kanıt düzeyi her kartta ayrıca gösterilir). Sonuçlarını ana modüllerle aynı ağırlıkta yorumlamayın.</p>
        <div className="grid gap-4 xl:grid-cols-2">
          {exp.map((r) => <ResultCard key={r.model_id} r={r} info={info(r.model_id)} schema={schema} experimental />)}
        </div>
      </section>
      <p className="mt-4 text-xs text-slate-500">{prediction.note}</p>
    </div>
  );
}
