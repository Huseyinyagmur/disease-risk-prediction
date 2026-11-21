import { sortByModule } from '../components/RoutingPanel';
import { Collapsible, EvidenceBadges, EvidenceTable, ModulePill, PageTitle, TechDetails } from '../components/ui';
import { fieldLabel } from '../lib/form';
import { modelName, t } from '../lib/ui';
import { useSession } from '../state/session';

const MODE_TR: Record<string, string> = {
  standard: 'standart (form + isteğe bağlı laboratuvar)',
  clinical_mode: 'klinik mod (klinik değerlendirme / cihaz ölçümü gerekir)',
  ecg_upload_demo: 'EKG yükleme',
};

export function ModelCards() {
  const { models, schema } = useSession();
  if (!models) return <p className="text-sm text-slate-600">Model listesi yükleniyor…</p>;
  return (
    <div>
      <PageTitle sub="Sunucudaki registry'den (/models) — yalnız uygulamada görünür modeller. Metrikler registry'den aynen alınmıştır.">
        Model kartları
      </PageTitle>
      <div className="grid gap-4 xl:grid-cols-2">
        {sortByModule(models).map((m) => (
          <article key={m.model_id} data-testid={`card-${m.model_id}`}
            className={`rounded-lg border p-4 ${m.module_label === 'deneysel' ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-slate-200 bg-white'}`}>
            <header className="mb-2 flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold">{modelName(schema, m.model_id, m.disease)}</h2>
              <ModulePill label={m.module_label} />
              {!m.enabled && <span className="rounded bg-rose-100 px-2 text-xs text-rose-800">devre dışı</span>}
            </header>
            <dl className="space-y-1 text-xs">
              <div><dt className="inline font-medium">Hedef: </dt><dd className="inline">{m.target_definition}</dd></div>
              <div><dt className="inline font-medium">Veri / popülasyon: </dt><dd className="inline">{m.population}</dd></div>
              <div><dt className="inline font-medium">Eksik girdi kuralı: </dt><dd className="inline">{m.missing_input_rule}</dd></div>
            </dl>
            <div className="my-2 flex flex-wrap items-center gap-2"><span className="text-xs">{t(schema, 'evidence')}:</span><EvidenceBadges evidence={m.evidence} /></div>
            {schema?.ui?.evidence_plain_tr[m.model_id] && <p className="mb-2 text-xs" data-testid="evidence-plain">{schema.ui.evidence_plain_tr[m.model_id]}</p>}
            <div className="space-y-2">
              <Collapsible title={t(schema, 'metrics')} testId="metrics">
                <EvidenceTable evidence={m.evidence} />
              </Collapsible>
              <Collapsible title={`Öznitelik girdileri (${m.fields.required.length} zorunlu, ${m.fields.conditional.length} koşullu)`}>
                <p className="text-xs"><span className="font-medium">Zorunlu:</span> {m.fields.required.map((f) => fieldLabel(schema, f)).join(', ')}</p>
                {m.fields.conditional.length > 0 && (
                  <p className="mt-1 text-xs"><span className="font-medium">Koşullu:</span> {m.fields.conditional.map((f) => fieldLabel(schema, f)).join(', ')}</p>
                )}
              </Collapsible>
              <Collapsible title={`Sınırlılıklar (${m.limitations.length})`}>
                <ul className="list-disc space-y-1 pl-5 text-xs">{m.limitations.map((x) => <li key={x}>{x}</li>)}</ul>
              </Collapsible>
              {m.schema_v2_changes.length > 0 && (
                <Collapsible title={`Şema v2 değişiklikleri (${m.schema_v2_changes.length})`}>
                  <ul className="list-disc space-y-1 pl-5 text-xs">
                    {m.schema_v2_changes.map((c) => <li key={c.feature + c.new_transform}><span className="font-mono">{c.feature}</span>: {c.old_transform} → {c.new_transform}. {c.reason}</li>)}
                  </ul>
                </Collapsible>
              )}
              <TechDetails testId="tech-details" items={[
                [t(schema, 'tech_model'), <span className="font-mono">{m.model_id}</span>],
                [t(schema, 'tech_definition'), m.disease],
                ['Rol / mod', `${m.role} · ${MODE_TR[m.app_mode] ?? m.app_mode} · ${m.endpoint}`],
              ]} />
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
