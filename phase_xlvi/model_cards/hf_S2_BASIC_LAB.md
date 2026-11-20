# Model kartı — Kalp yetmezliği (`hf_S2_BASIC_LAB`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `hf_S2_BASIC_LAB` (primary (araştırma amaçlı)) |
| hastalık / hedef | Kalp yetmezliği |
| uygulamadaki durum | uygulamada değil (registry_only); mod `registry_only`; `app_visible = false` |
| model ailesi | XGBoost + sigmoid kalibrasyon (CalibratedResearchModel) |
| en yüksek kanıt düzeyi | iç test (n=37) |
| model dosyası | `All_Disease_Improvement_Phase21/models/heart_failure_S2_BASIC_LAB.joblib` (SHA256 `57db837eb7fb99f0…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | Phase21; baseline karşılaştırması phase_xxvii; dondurulmuş manifest Strong_Model_External_Validation_Phase26 |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Kaynak veri setinde klinik kalp yetmezliği ile sağlıklı kontrolü RIP3 ELISA ve temel bilgilerle ayırır (vaka-kontrol). Yalnız registry'de.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme + iç test | Mendeley Data 7v4w66wxj8.1, doi:10.17632/7v4w66wxj8.1 (RIP3 kalp yetmezliği; birincil yayın PMID 32598878) | tek merkez vaka-kontrol; tarih aralığı BULUNAMADI |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** Hastane vaka-kontrol çalışması (HF hastaları vs sağlıklı gönüllüler).
- **Popülasyon (registry):** Mendeley 7v4w66wxj8.1 (özel RIP3 ELISA çalışması): HF hastaları (akut/kronik karışık) vs sağlıklı kontrol; fit n=110. Semptomlu kontrol veya genel popülasyon DEĞİL.
- **Uygunluk (kaynak):** Kaynaktaki 184 uygun kişi (89 HF, 95 kontrol); yaş ≥ 18; LVEF/BNP/NYHA girdi değil.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Kaynak veri setinde klinik olarak tanılı kalp yetmezliği (HF) ile sağlıklı kontrol ayrımı (vaka-kontrol; mevcut durum).
- **Ölçüm:** Kaynak çalışmanın klinik HF grubu; adjudikasyon ayrıntıları kısmen yayımlanmış (BULUNAMADI).
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 18 – 100 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 4 | `smoker` | categorical | kategori | no, yes | `smoking_status` | `smoker_yesno` |
| 5 | `rip3` | numeric | pg/mL | 0 – 5000 | `rip3_pgml` | `identity` |

Sıra ve kategoriler: `Strong_Model_External_Validation_Phase26/frozen_model_manifest.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| fit | 110 | BULUNAMADI | `heart_failure_splits.json (toplam 184, pozitif 89)` |
| validation | 37 | 18 | `selected_model_registry.json` |
| iç test | 37 | 18 | `phase_xxvii/results/ci_metrics.csv` |

Çok küçük (test n = 37); GA çok geniş.

## 7. Eksik veri [11]

- **Geliştirme:** BMI %5,4, sigara %1,6 eksik (fit içi imputasyon).
- **Uygulama (registry kuralı):** ZORUNLU: 5 feature (rip3 dahil). rip3 yoksa model yok (S1_BASIC kayıtlı değil). Dondurulmuş imputer kullanılmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi rastgele (fit/validation/test 110/37/37).

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** Phase21 eğitim protokolü (`All_Disease_Improvement_Phase21/training_protocol.json`, seed 20261111): 8 aile (Dummy, LR, RF, ExtraTrees, HistGB, XGBoost, LightGBM, CatBoost); yalnız fit kümesinde 3-fold StratifiedGroupKFold (kişi grubu); en iyi 2 aile-panel için Optuna (görev başına ≤ 6 deneme); seçim CV AP ile; test ve dış veri seçimde kullanılmadı. Seçilen: XGBoost, HPO yok.
- **Sınıf dengesizliği:** Phase21: azınlık/çoğunluk < 0,8 ise LR class_weight, ROS, RUS, SMOTENC adayları yalnız eğitim fold'unda; seçilen strateji modelin meta verisinde. Seçilen: baseline.

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.4476970842** (`Strong_Model_External_Validation_Phase26/frozen_model_manifest.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)
- Seçim kuralı (kaynak): Phase21 eşik kuralı (`training_protocol.json > threshold`): validation kümesinde önce P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 birlikte; yoksa R ≥ 0,60, FPR ≤ 0,25; içinde F2 − 0,5·FPR + 0,25·P en büyük ("BALANCED" senaryosu). **Bu fazda bulundu:** registry eşiği `All_Disease_Improvement_Phase21/selected_model_registry.json` içindeki BALANCED senaryo eşiğiyle bit düzeyinde aynıdır (XLIII registry'de "kural BULUNAMADI" yazıyordu). Hangi dalın (birincil/yedek) uygulandığı: senaryo kaydında `constraints_met = true`.
- İkincil eşikler (yalnız raporlama): yok

## 11. Kalibrasyon [12e]

- Registry: sigmoid (Platt; klinik olasılık DEĞİL).
- Phase21: ham skor ile fit kümesi OOF üzerinde sigmoid kalibrasyon karşılaştırıldı; validation'da seçildi (isotonic yalnız ≥ 1000 fit ve sınıf başına ≥ 100 ise). Seçilen: sigmoid (Platt).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — Mendeley 7v4w66wxj8.1 (n=37) | 37 (18) | 14 / 3 / 16 / 4 | 0,824 [0,590–0,938] | 0,778 [0,548–0,910] | 0,158 [0,055–0,376] | 0,800 [0,584–0,919] | 0,950 [0,877–0,997] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxvii/results/ci_metrics.csv` (SHA256 `87e6cc9bcee1…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: İç testte P ve Recall hedefte, FPR 0,158 > 0,15 (GA geniş). Dış doğrulama YAPILAMADI (Phase XXXIX: uyumlu RIP3 assay'li başka veri BULUNAMADI).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — Mendeley 7v4w66wxj8.1 (n=37) | model − LR(age, sex, bmi) | 0,579 | 0,371 [0,158–0,588] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` |
| İç test — Mendeley 7v4w66wxj8.1 (n=37) | model − Tek değişken: rip3 (+ yön; fit AUC=0.927) | 0,956 | -0,006 [-0,044–0,023] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

Alt grup analizi yok (n = 37).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- Eğitim n=110, test n=37 (18 pozitif): GA çok geniş; sonuç kararsız.
- Tek değişkene (RIP3) eşdeğer: ΔAUC vs RIP3 −0,006 (−0,044…+0,023); çok değişkenli katkı kanıtı yok.
- Vaka-kontrol tasarımı (sağlıklı kontrol); genel popülasyon veya semptomlu kişilerde performans bilinmiyor. HF alt tipi/LVEF/BNP yok.
- RIP3 rutin klinik test değildir; assay/birim uyumu başka laboratuvarlarda doğrulanmadı (BULUNAMADI).
- Dış doğrulama YOK.
- Dış doğrulama yapılamadı: uyumlu RIP3 ölçümlü başka veri BULUNAMADI (Phase XXXIX).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `registry_only` — RIP3 özel assay; n=37; dış doğrulama yok. Modül etiketi: uygulamada değil (registry_only).
- **Uygulanabilirlik:** UYGULAMAYA ALINAMAZ (şimdilik): RIP3 özel assay değeri ve sağlıklı-kontrol tasarımı; kullanıcı girdisiyle üretilemez.
- **Kurallar:** Uygulamada YOK (`app_visible = false`, `registry_only`): RIP3 özel ELISA ölçümü gerekir; test n = 37.
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.

## 17. Etik, gizlilik ve açık bilim [17, 18a–f, 19]

- **Etik [17]:** proje, kamuya açık ve kimliksizleştirilmiş verinin ikincil analizidir. Veri toplamanın etik onayı veri
  sağlayıcısınındır (kaynak belgelerinde). Bu proje için ayrı bir etik kurul onayı: BULUNAMADI.
- **Gizlilik (uygulama):** istek gövdesi ve sağlık verisi loglanmaz ve diske yazılmaz; tarayıcıda kalıcı saklama yok; sunucu yalnız
  127.0.0.1 (Phase XLIV `test_privacy.py`, Phase XLV Playwright gizlilik testleri).
- **Fon [18a] / çıkar çatışması [18b]:** BULUNAMADI.
- **Protokol [18c]:** kilitli protokol ve model kilidi dosyaları kaynak fazda (bkz. §18). **Kayıt [18d]:** çalışma kaydı yapılmadı.
- **Veri paylaşımı [18e]:** veriler kaynaklarından açık erişimle alınabilir (lisanslar README). **Kod [18f]:** uygulama ve registry
  GitHub deposunda; faz betiklerinin tamamı depoda değildir.
- **Hasta/halk katılımı [19]:** yapılmadı.

## 18. Kaynak dosyalar

- `All_Disease_Improvement_Phase21/training_protocol.json`
- `All_Disease_Improvement_Phase21/selected_model_registry.json`
- `phase_xxvii/02_baselines.md`
- `phase_xxxix/PHASE_XXXIX_REPORT.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 21, kısmen 20, yok 9, uygulanamaz 2. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
