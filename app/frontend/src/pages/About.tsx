import { sortByModule } from '../components/RoutingPanel';
import { DisclaimerText, PageTitle } from '../components/ui';
import { useSession } from '../state/session';

export function About() {
  const { models } = useSession();
  return (
    <div className="max-w-4xl space-y-6 text-sm text-slate-700">
      <PageTitle>Hakkında</PageTitle>

      <section>
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Yöntem özeti</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>Her model kişinin <strong>mevcut</strong> klinik durumunu sınıflandırır (hedef aynı ziyaretteki ölçüm/tanıdır); gelecekteki hastalık riskini tahmin etmez.</li>
          <li>Protokol (hedef, popülasyon, öznitelikler, bölme, baseline, model ve eşik seçim kuralı) sonuç verisi açılmadan yazılıp SHA256 ile kilitlendi. Bölme kişi düzeyindedir; ön işleme, hiperparametre ve eşik seçimi yalnız geliştirme verisinde yapıldı.</li>
          <li>Test kümesi model ve eşik kilitlendikten sonra bir kez açıldı. Hedefi tanımlayan ölçüm (ör. diyabette HbA1c) model girdisi değildir.</li>
          <li>Proje kuralı gereği her modelde klinik baseline zorunludur (ML katkısı ΔAUC ile; ayrıntılar faz raporlarında). Metrikler Precision, Recall ve FPR birlikte, %95 güven aralıklarıyla raporlanır.</li>
          <li>Uygulama modelleri yeniden eğitmez; eşik, kalibrasyon, öznitelik sırası ve birimler değiştirilmez. Eksik girdi tahminle doldurulmaz: zorunlu alan eksikse model karar üretmez (ABSTAIN).</li>
          <li>Model olasılıkları kalibre klinik olasılık değildir ve gösterilmez; yalnız donmuş eşiğin üstü/altı ("araştırma sınıflaması") verilir.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Kanıta duyarlı yönlendirme</h2>
        <p>Arayüz, her modeli kanıtının gücüne ve kişinin verisine göre konumlandırır:</p>
        <ul className="mt-1 list-disc space-y-1 pl-5">
          <li><strong>Canlı panel</strong>, girdikleriniz değiştikçe her modelin durumunu sunucudan sorar: <em>Çalışabilir</em>, <em>Eksik: …</em> (hangi alanların gerektiği), <em>Kapsam dışı: …</em> (ör. yaş aralığı, gebelik) veya <em>Karar verilemez</em> (ör. gebelik "bilmiyorum").</li>
          <li><strong>Kanıt düzeyleri ayrı tutulur:</strong> iç test, zamansal doğrulama ve bağımsız dış doğrulama ayrı rozet ve tablolarda gösterilir; çapraz doğrulama sonuçları kanıt olarak gösterilmez.</li>
          <li><strong>Modül etiketi:</strong> AF ve karaciğer fibrozisi "ana modül", osteoporoz "araştırma modülü", diğerleri "deneysel"dir; deneysel sonuçlar ayrı bölümde, gri tonda gösterilir.</li>
          <li><strong>Hedefi tanımlayan girdi uyarısı:</strong> hastalığı tanımlayan değer (ör. HbA1c, ölçülen yüksek tansiyon, hemoglobin, kreatinin) girilmişse model yerine doğrudan klinik eşik kullanılması gerektiği belirtilir.</li>
          <li><strong>Laboratuvarlı / laboratuvarsız modeller:</strong> diyabet ve böbrekte laboratuvar değerleri tamsa laboratuvarlı model, değilse form modeli kullanılır; hangisinin kullanıldığı kartta yazar.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Veri kaynakları (model başına, registry'den)</h2>
        {!models ? (
          <p>Yükleniyor…</p>
        ) : (
          <table className="w-full text-left text-xs" data-testid="about-sources">
            <thead className="text-slate-500"><tr><th className="py-1 pr-2">Model</th><th className="py-1 pr-2">Popülasyon / veri</th><th className="py-1">Kanıt kaynakları</th></tr></thead>
            <tbody>
              {sortByModule(models).map((m) => (
                <tr key={m.model_id} className="border-t border-slate-100 align-top">
                  <td className="py-1 pr-2 font-medium">{m.disease}<div className="font-normal text-slate-500">{m.model_id}</div></td>
                  <td className="py-1 pr-2">{m.population}</td>
                  <td className="py-1">
                    {Object.values(m.evidence.tiers).map((t) => t && <div key={t.tier_label}>{t.tier_label}: {t.source ?? 'BULUNAMADI'}</div>)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="mt-2 text-xs">Örnek EKG kayıtları: PTB-XL 1.0.3 (PhysioNet), ayrıntı ve atıf app/frontend/README.md'de.</p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Gizlilik</h2>
        <p>Girdiler yalnız sekme belleğinde tutulur (tarayıcı depolaması kullanılmaz), sayfa yenilenince silinir. Sunucu yalnız 127.0.0.1'de çalışır; istek gövdeleri loglanmaz. Analitik yoktur.</p>
      </section>

      <p className="rounded border border-amber-300 bg-amber-50 p-3 text-amber-900"><DisclaimerText /></p>
    </div>
  );
}
