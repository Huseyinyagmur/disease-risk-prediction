---
id: mc_copd_S4_DEVICE
title: Model kartı — KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) (`copd_S4_DEVICE`)
source_ref: app/docs/model_cards/copd_S4_DEVICE.md
card_sha256: a425897afd153436121f85847470ae5ed97bc3b19bdaed091de7f892045219bc
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) (`copd_S4_DEVICE`)

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

## 7. Eksik veri [11]

- **Geliştirme:** BMI %1,1 eksik (fit içi imputasyon); spirometri eksiksiz.
- **Uygulama (registry kuralı):** ZORUNLU: 6 feature. Yaş 40–79 dışı veya pre-BD FEV1/FVC ≥ 0,70 ise model uygulanmaz (eğitim popülasyonu dışı). fev1_pre ≤ fvc_pre. Dondurulmuş imputer kullanılmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

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
