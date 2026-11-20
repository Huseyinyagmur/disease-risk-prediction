# Model kartı — KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) (`copd_S4_DEVICE`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `copd_S4_DEVICE` (primary) |
| hastalık / hedef | KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) |
| uygulamadaki durum | deneysel; mod `clinical_mode`; `app_visible = true` |
| model ailesi | Lojistik regresyon (CalibratedResearchModel, ham skor) |
| en yüksek kanıt düzeyi | zamansal tekrar (aynı anket, farklı döngü; PREVIOUSLY_EXPOSED) — bağımsız klinik kohort DEĞİL |
| model dosyası | `All_Disease_Improvement_Phase21/models/copd_S4_DEVICE.joblib` (SHA256 `9584633d095d5a9e…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | Phase21; zamansal tekrar phase_xxvii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Bronkodilatör testine alınmış (pre-BD obstrüksiyonlu) 40–79 yaş kişide post-BD FEV1/FVC < 0,70'in sürüp sürmediğini sınıflar. Genel nüfusta KOAH taraması değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme + iç test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): G 2011–12 (SPX) | BD testine seçilmiş alt grup |
| zamansal tekrar | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): F 2009–10, E 2007–08 | aynı program, önceden raporlanmış (PREVIOUSLY_EXPOSED) |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** NHANES spirometri alt örneklemi; BD testine seçilmiş kişiler.
- **Popülasyon (registry):** NHANES 40–79 yaş, pre-BD FEV1/FVC < LLN ve/veya < 0,70 nedeniyle bronkodilatör testi yapılmış ve ATS A/B kalitesinde tamamlamış kişiler. Negatif = bronkodilatörle düzelen kişiler (sağlıklı popülasyon DEĞİL).
- **Uygunluk (kaynak):** 40–79 yaş, pre-BD FEV1/FVC < LLN ve/veya < 0,70 nedeniyle BD testi yapılmış, ATS A/B kalitesinde.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Post-bronkodilatör FEV1/FVC < 0,70 (sabit oran) olması; popülasyon: bronkodilatör testine seçilmiş kişiler.
- **Ölçüm:** Post-BD FEV1/FVC < 0,70 (sabit oran; ATS kaliteli spirometri). Klinik KOAH adjudikasyonu yok.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 40 – 79 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 4 | `smoker` | categorical | kategori | no, yes | `smoking_status` | `smoker_yesno` |
| 5 | `fev1_pre` | numeric | mL | 200 – 7000 | `fev1_pre_ml` | `identity` |
| 6 | `fvc_pre` | numeric | mL | 300 – 9000 | `fvc_pre_ml` | `identity` |

Sıra ve kategoriler: `Strong_Model_External_Validation_Phase26/frozen_model_manifest.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| fit | 108 | BULUNAMADI | `All_Disease_Improvement_Phase21/config/copd_splits.json (toplam 182, pozitif 97)` |
| validation | 37 | 20 | `selected_model_registry.json (BALANCED)` |
| iç test | 37 | 20 | `phase_xxvii/results/ci_metrics.csv` |
| zamansal F | 250 | 156 | aynı |
| zamansal E | 274 | 163 | aynı |

Çok küçük geliştirme (fit 108) ve iç test (37). Örneklem büyüklüğü hesabı BULUNAMADI.

## 7. Eksik veri [11]

- **Geliştirme:** BMI %1,1 eksik (fit içi imputasyon); spirometri eksiksiz.
- **Uygulama (registry kuralı):** ZORUNLU: 6 feature. Yaş 40–79 dışı veya pre-BD FEV1/FVC ≥ 0,70 ise model uygulanmaz (eğitim popülasyonu dışı). fev1_pre ≤ fvc_pre. Dondurulmuş imputer kullanılmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi rastgele fit/validation/test (G içinde); zamansal tekrar F ve E döngüleri.

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** Phase21 eğitim protokolü (`All_Disease_Improvement_Phase21/training_protocol.json`, seed 20261111): 8 aile (Dummy, LR, RF, ExtraTrees, HistGB, XGBoost, LightGBM, CatBoost); yalnız fit kümesinde 3-fold StratifiedGroupKFold (kişi grubu); en iyi 2 aile-panel için Optuna (görev başına ≤ 6 deneme); seçim CV AP ile; test ve dış veri seçimde kullanılmadı. Seçilen: LR (L1, C = 4,98), HPO uygulandı.
- **Sınıf dengesizliği:** Phase21: azınlık/çoğunluk < 0,8 ise LR class_weight, ROS, RUS, SMOTENC adayları yalnız eğitim fold'unda; seçilen strateji modelin meta verisinde. Seçilen: baseline.

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.5707211331** (`Strong_Model_External_Validation_Phase26/frozen_model_manifest.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)
- Seçim kuralı (kaynak): Phase21 eşik kuralı (`training_protocol.json > threshold`): validation kümesinde önce P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 birlikte; yoksa R ≥ 0,60, FPR ≤ 0,25; içinde F2 − 0,5·FPR + 0,25·P en büyük ("BALANCED" senaryosu). **Bu fazda bulundu:** registry eşiği `All_Disease_Improvement_Phase21/selected_model_registry.json` içindeki BALANCED senaryo eşiğiyle bit düzeyinde aynıdır (XLIII registry'de "kural BULUNAMADI" yazıyordu). Hangi dalın (birincil/yedek) uygulandığı: senaryo kaydında `constraints_met = true`.
- İkincil eşikler (yalnız raporlama): yok

## 11. Kalibrasyon [12e]

- Registry: raw.
- Phase21: ham skor ile fit kümesi OOF üzerinde sigmoid kalibrasyon karşılaştırıldı; validation'da seçildi (isotonic yalnız ≥ 1000 fit ve sınıf başına ≥ 100 ise). Seçilen: raw.

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 | 37 (20) | 13 / 0 / 17 / 7 | 1,000 [0,772–1,000] | 0,650 [0,433–0,819] | 0,000 [0,000–0,184] | 0,708 [0,508–0,851] | 0,921 [0,824–0,988] | hayır |

#### Zamansal doğrulama

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Zamansal tekrar — NHANES F 2009–10 | 250 (156) | 118 / 9 / 85 / 38 | 0,929 [0,871–0,962] | 0,756 [0,683–0,817] | 0,096 [0,051–0,172] | 0,691 [0,605–0,766] | 0,898 [0,857–0,934] | evet |
| Zamansal tekrar — NHANES E 2007–08 | 274 (163) | 117 / 9 / 102 / 46 | 0,929 [0,870–0,962] | 0,718 [0,644–0,781] | 0,081 [0,043–0,147] | 0,689 [0,611–0,758] | 0,901 [0,865–0,933] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxvii/results/ci_metrics.csv` (SHA256 `87e6cc9bcee1…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: F 2009–10'da 3 hedef nokta tahminiyle sağlandı (GA ile değil; E 2007–08'de Recall 0,718 < 0,75). Seçilmiş popülasyonda P/FPR genel popülasyona taşınamaz.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 | model − pre-BD FEV1/FVC < 0.70 | 0,912 | 0,009 [-0,059–0,076] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` |
| Zamansal tekrar — NHANES F 2009–10 | model − pre-BD FEV1/FVC < 0.70 | 0,875 | 0,023 [-0,005–0,052] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` |
| Zamansal tekrar — NHANES E 2007–08 | model − pre-BD FEV1/FVC < 0.70 | 0,899 | 0,002 [-0,019–0,025] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

Alt grup analizi yok (küçük örneklem). Döngü bazlı sonuçlar (G, F, E) performans tablosundadır.

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- Hedef popülasyon dar: yalnız pre-BD spirometride obstrüksiyon saptanıp BD testine alınmış kişiler. Genel popülasyon KOAH taramasında KULLANILAMAZ; FPR/Precision genel popülasyona taşınamaz.
- Model pre-BD FEV1/FVC < 0,70 kuralına eşdeğer: ΔAUC +0,009 (−0,059…+0,076).
- İç test n=37 (20 pozitif). Zamansal tekrar aynı anket programı; kişi takibi yok.
- Astımı ayırt etmez; klinik KOAH tanısı DEĞİL (post-BD sabit oran).
- Sigara = şu an içen (never/former → no); paket-yıl yok.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `clinical_mode` — kaliteli pre-BD spirometri; dar hedef popülasyon. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Kalite-kontrollü spirometri (pre-BD FEV1 ve FVC, mL) gerekir ve kişi yalnız pre-BD obstrüksiyon saptanmış 40–79 yaş olmalıdır.
- **Kurallar:** Klinik mod. NOT_APPLICABLE: yaş 40–79 dışı veya pre-BD FEV1/FVC ≥ 0,70 (hedef popülasyon yalnız obstrüksiyonlu ve BD testine alınmış kişiler). ABSTAIN: yaş, FEV1, FVC, BMI, sigara eksik.
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
- `phase_xxvii/04_copd_temporal_validation.md`
- `phase_xxvii/02_baselines.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 25, kısmen 18, yok 6, uygulanamaz 3. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
