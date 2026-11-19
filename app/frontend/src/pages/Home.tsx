import { DisclaimerText } from '../components/ui';
import { useSession } from '../state/session';

export function Home() {
  const { go, loadError } = useSession();
  return (
    <div className="mx-auto max-w-3xl py-6">
      <h1 className="text-3xl font-semibold text-slate-900">HealthRisk AI — araştırma prototipi</h1>
      <p className="mt-4 text-slate-700">
        Bu uygulama, hastalığa özgü donmuş makine öğrenmesi modelleriyle kişinin <strong>mevcut klinik durumunu sınıflandırır</strong>
        (ör. şu anda teşhis edilmemiş diyabet ya da karaciğer sertliği eşiğinin üstünde olma). <strong>Gelecekte hastalık gelişme riskini tahmin etmez.</strong>
      </p>
      <p className="mt-3 text-slate-700">
        Girdiğiniz bilgilere göre hangi modelin çalışabileceği canlı olarak gösterilir. Her sonuç, modelin donmuş eşiğine göre
        "araştırma sınıflaması"dır; model olasılığı gösterilmez. Her kartta kanıt düzeyi (iç test / zamansal / dış doğrulama),
        test metrikleri ve sınırlılıklar yer alır.
      </p>
      <div className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-900">
        <p className="font-semibold">Önemli</p>
        <p className="text-sm"><DisclaimerText /></p>
      </div>
      <ul className="mt-4 list-disc pl-5 text-sm text-slate-600">
        <li>Veriler yalnız bu tarayıcı sekmesinin belleğinde tutulur; tarayıcı depolamasına yazılmaz, sayfa yenilenince silinir.</li>
        <li>Sunucu yalnız bu bilgisayarda (127.0.0.1) çalışır; istek içerikleri loglanmaz. Analitik/izleme yoktur.</li>
      </ul>
      {loadError && <p role="alert" className="mt-4 rounded bg-rose-50 p-3 text-sm text-rose-800">Sunucu bağlantısı yok: {loadError}</p>}
      <div className="mt-8 flex flex-wrap gap-3">
        <button type="button" onClick={() => go('form')} data-testid="start" className="rounded bg-slate-800 px-5 py-2.5 font-medium text-white hover:bg-slate-700">
          Başla
        </button>
        <button type="button" onClick={() => go('ecg')} data-testid="start-ecg" className="rounded border border-slate-800 px-5 py-2.5 font-medium text-slate-800 hover:bg-slate-100">
          EKG ile AF analizi
        </button>
      </div>
    </div>
  );
}
