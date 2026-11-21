---
id: int_about
title: Hakkında
source_ref: frontend/src/pages/About.tsx + app_config.json
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Hakkında

## Yöntem özeti
- Her model kişinin mevcut klinik durumunu sınıflandırır (hedef aynı ziyaretteki ölçüm/tanıdır); gelecekteki hastalık riskini tahmin etmez.
- Protokol (hedef, popülasyon, öznitelikler, bölme, baseline, model ve eşik seçim kuralı) sonuç verisi açılmadan yazılıp SHA256 ile kilitlendi. Bölme kişi düzeyindedir; ön işleme, hiperparametre ve eşik seçimi yalnız geliştirme verisinde yapıldı.
- Test kümesi model ve eşik kilitlendikten sonra bir kez açıldı. Hedefi tanımlayan ölçüm (ör. diyabette HbA1c) model girdisi değildir.
- Proje kuralı gereği her modelde klinik baseline zorunludur (ML katkısı ΔAUC ile; ayrıntılar faz raporlarında). Metrikler Precision, Recall ve FPR birlikte, %95 güven aralıklarıyla raporlanır.
- Uygulama modelleri yeniden eğitmez; eşik, kalibrasyon, öznitelik sırası ve birimler değiştirilmez. Eksik girdi tahminle doldurulmaz: zorunlu alan eksikse model sonuç üretmez.
- Model olasılıkları kalibre klinik olasılık değildir ve gösterilmez; yalnız donmuş eşiğin üstü/altı ("araştırma sınıflaması") verilir.
## Kanıta duyarlı yönlendirme
Arayüz, her modeli kanıtının gücüne ve kişinin verisine göre konumlandırır:
- Canlı panel, girdikleriniz değiştikçe seçtiğiniz her analizin durumunu sunucudan sorar (durum terimleri yukarıdaki "Terimler" bölümündedir) ve eksik bilgileri ya da uygun olmama nedenini (ör. yaş aralığı, gebelik) gösterir. Birden fazla neden varsa ana satır kişiye özel nedeni gösterir, diğerleri altında Ayrıca: … olarak listelenir (ör. "Ayrıca: Octave/ECGDeli AF çalışma ortamı yok").
- Kanıt düzeyleri ayrı tutulur: iç test, zamansal doğrulama ve bağımsız dış doğrulama ayrı rozet ve tablolarda gösterilir; çapraz doğrulama sonuçları kanıt olarak gösterilmez.
- Modül etiketi: AF ve karaciğer fibrozisi "ana modül", osteoporoz "araştırma modülü", diğerleri "deneysel"dir; deneysel sonuçlar ayrı bölümde, gri tonda gösterilir.
- Hedefi tanımlayan girdi uyarısı: hastalığı tanımlayan değer (ör. HbA1c, ölçülen yüksek tansiyon, hemoglobin, kreatinin) girilmişse model yerine doğrudan klinik eşik kullanılması gerektiği belirtilir.
- Laboratuvarlı / laboratuvarsız modeller: diyabet ve böbrekte laboratuvar değerleri tamsa laboratuvarlı model, değilse form modeli kullanılır; hangisinin kullanıldığı kartta yazar.
## Veri kaynakları (model başına, registry'den)
Örnek EKG kayıtları: PTB-XL 1.0.3 (PhysioNet), ayrıntı ve atıf app/frontend/README.md'de.
## Gizlilik
Girdiler yalnız sekme belleğinde tutulur (tarayıcı depolaması kullanılmaz), sayfa yenilenince silinir. Sunucu yalnız 127.0.0.1'de çalışır; istek gövdeleri loglanmaz. Analitik yoktur.

## Araştırma uyarısı

Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir; negatif sonuç hastalığı dışlamaz; tanı ve tedavi için hekime başvurun.

## Sunucu gizlilik politikası

İstek gövdeleri ve sağlık verileri hiçbir log’a yazılmaz ve diske saklanmaz. Yalnız anonim sayaçlar (uç nokta başına istek sayısı, durum kodu sayısı, toplam/ortalama süre) bellekte tutulur ve /health’te döner. /ecg/af yüklemeleri yalnız işlem süresince geçici klasörde bulunur ve yanıt öncesi silinir (kilitli Octave pipeline dosya girişi ister).
