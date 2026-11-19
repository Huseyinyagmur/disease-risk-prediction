# Health Risk AI Research V2 — proje kuralları

## Genel
- Kullanıcıya Türkçe, kısa ve teknik yanıt ver. Faz sonunda kısa özet: ne yapıldı, ne doğrulandı, ne açık kaldı.
- Bu bir ML araştırma reposudur: hastalığa özgü modeller kişinin MEVCUT klinik durumunu sınıflandırır (gelecek risk tahmini değil).
- Doğruluk ve tekrarlanabilirlik token tasarrufundan önce gelir. Denetim, envanter ve kontaminasyon kontrollerinde gerektiği kadar geniş ara (tüm phase_* klasörleri dahil).

## Klasör ve dosya kuralları
- Her faz kendi klasöründe çalışır (ör. phase_xxxiii/). Yeni çıktılar yalnız o fazın klasörüne yazılır.
- Önceki tüm faz klasörleri, model dosyaları, eşikler, kilit dosyaları ve ham veriler SALT OKUNURDUR.
- Faz başında ve sonunda SHA256 bütünlük kontrolü yapılır (önceki dosyalarda değişen/silinen = 0, faz dışı yeni dosya = 0).
- Betikler faz klasöründe scripts/ altında, sabit seed'li ve yeniden çalıştırılabilir olur.

## Model geliştirme kuralları
- Protokol (hedef tanımı, popülasyon, feature listesi, split, baseline, model seçim kuralı, eşik kuralı) sonuç verisi açılmadan yazılır ve SHA256 ile kilitlenir. Değişiklik gerekirse v2 olarak, gerekçesiyle ve sonuç görülmeden yeniden kilitlenir.
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi olamaz.
- Split kişi düzeyindedir; mümkünse zamansaldır. Preprocessing, imputation, resampling, hiperparametre ve eşik seçimi yalnız geliştirme verisinde yapılır.
- CV yöntemi: phase_xxxi/config/cv_protocol_v2.md (konfigürasyon bir kez seçilir, sabit konfigürasyonla dış CV, eşik havuzlu OOF'tan; fold–havuz AUC farkı > 0,02 ise uyarı).
- Test kümesi model ve eşik kilitlendikten sonra yalnız bir kez açılır. Test sonucuna bakılarak model, eşik veya feature seçimi yapılmaz. Önceki test kişileri yeni test sayılmaz.
- Her modelde klinik baseline zorunludur; ML katkısı ΔAUC (paired bootstrap %95 GA) ile gösterilir.

## Dış doğrulama kuralları
- Donmuş model yeniden fit edilmez; eşik, kalibrasyon, feature sırası ve birimler değiştirilmez.
- Eksik veya klinik anlamı uyuşmayan feature tahminle doldurulmaz.
- AF için feature pipeline: AF-ECGDELI-OCTAVE-v1 (phase_xxviii/config/af_pipeline_lock.json).

## Raporlama
- Metrikler: Precision, Recall, FPR birlikte; oranlar için Wilson %95 GA, AUC için bootstrap GA.
- Araştırma hedefleri: P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 (aynı model ve eşikte). Klinik onay kriteri değildir.
- İç test, zamansal doğrulama ve bağımsız dış doğrulama sonuçları ayrı tablolarda gösterilir; CV sonuçları "aday" olarak etiketlenir.
- Bulunamayan bilgi "BULUNAMADI" yazılır. Metrik, test sonucu, kaynak veya çalıştırılmamış kontrol uydurulmaz. Başarı abartılmaz; sınırlılıklar açıkça yazılır.
- Model olasılıkları klinik olasılık olarak sunulmaz (clinical_probability_eligibility=false).

## İzinler
- Resmi kaynaklardan (PhysioNet, CDC/NHANES, UCI, Mendeley Data, Zenodo) veri indirmek ve gerekli Python paketlerini kurmak serbesttir; indirilen dosyalar mümkünse resmi checksum ile doğrulanır.
- git commit/push, ham verinin veya önceki faz dosyalarının değiştirilmesi/silinmesi için kullanıcı onayı gerekir.
## Uygulama (app/)
- Uygulama kodu kök dizinde app/ altında geliştirilir (faz klasörü kuralının istisnası).
- app/ modelleri yalnız phase_xliii/registry/models.json üzerinden yükler; model, eşik, registry ve önceki faz dosyaları salt okunurdur.
- app/ hiçbir test/sealed veri dosyasını okumaz. Doğrulama yalnız geliştirme verisi ve sentetik girdiyle yapılır.
- Model olasılığı arayüzde gösterilmez; yalnız "araştırma sınıflaması" (eşik üstü/altı), kanıt düzeyi ve sınırlılıklar.