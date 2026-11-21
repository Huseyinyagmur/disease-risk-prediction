---
id: mc_ckd_B
title: Model kartı — Böbrek — laboratuvarlı (`ckd_B`)
source_ref: app/docs/model_cards/ckd_B.md
card_sha256: ac9a55221cdc66b50342c3f66d7b9ef50f733b4ea0a3027e5fcabc6884e85035
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Böbrek — laboratuvarlı (`ckd_B`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `ckd_B` (secondary (laboratuvar varsa)) |
| hastalık / hedef | Böbrek — laboratuvarlı |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | LightGBM |
| en yüksek kanıt düzeyi | iç test (NHANES I; PREVIOUSLY_EXPOSED) |
| model dosyası | `phase_xxxv/models/ckd_B_final.joblib` (SHA256 `6b45bd673c7f00a4…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxxv |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Böbrek hastalığı tanısı olmayan erişkinde tek ziyarette eGFR < 60 veya UACR ≥ 30 mg/g olup olmadığını rutin laboratuvar eklenmiş girdilerle (glukoz, HbA1c, TK, HDL, hemoglobin; kreatinin/UACR girdi değil) sıralar. KDIGO KBH tanısı (3 ay) değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): E 2007–08, F 2009–10, G 2011–12, H 2013–14 | genel nüfus |
| iç test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): I 2015–16 | aynı program; PREVIOUSLY_EXPOSED (başka hedef) |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.
- **Popülasyon (registry):** Model A ile aynı.
- **Uygunluk (kaynak):** Yaş ≥ 20, MEC, kreatinin ve UACR var, gebe değil, diyaliz değil, KIQ022 = Hayır (`phase_xxxv/01_cohort.md`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Model A ile aynı.
- **Ölçüm:** CKD-EPI 2021 (ırksız) eGFR < 60 veya UACR ≥ 30 mg/g; E-2007 kreatinin CDC Deming düzeltmeli dosya.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 20 – 80 | `age_years` | `age_cap80` |
| 2 | `sex_female` | categorical | 0/1 | 0.0, 1.0 | `sex` | `sex_female01` |
| 3 | `race_mexam` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_mexam` |
| 4 | `race_othhisp` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_othhisp` |
| 5 | `race_black` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_black` |
| 6 | `race_other` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_other` |
| 7 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 8 | `waist` | numeric | cm | 40 – 200 | `waist_cm` | `identity` |
| 9 | `sbp` | numeric | mmHg | 70 – 260 | `sbp_1..3_mmhg` | `sbp_mean_23` |
| 10 | `dbp` | numeric | mmHg | 30 – 150 | `dbp_1..3_mmhg` | `dbp_mean_23` |
| 11 | `htn_told` | categorical | 0/1 | 0.0, 1.0 | `told_hypertension` | `bool01` |
| 12 | `dm_told` | categorical | 0/1 | 0.0, 1.0 | `told_diabetes` | `bool01` |
| 13 | `chd_hist` | categorical | 0/1 | 0.0, 1.0 | `hx_coronary_disease` | `bool01` |
| 14 | `chf` | categorical | 0/1 | 0.0, 1.0 | `hx_heart_failure` | `bool01` |
| 15 | `stroke` | categorical | 0/1 | 0.0, 1.0 | `hx_stroke` | `bool01` |
| 16 | `htn_med` | categorical | 0/1 | 0.0, 1.0 | `told_hypertension+on_bp_medication` | `htn_med_rule` |
| 17 | `dm_insulin` | categorical | 0/1 | 0.0, 1.0 | `told_diabetes+on_insulin` | `dm_insulin_train (v1: dm_insulin_rule)` |
| 18 | `dm_pills` | categorical | 0/1 | 0.0, 1.0 | `told_diabetes+on_diabetes_pills` | `dm_pills_train (v1: dm_pills_rule)` |
| 19 | `smoke_current` | categorical | 0/1 | 0.0, 1.0 | `smoking_status` | `smoke_current01` |
| 20 | `smoke_former` | categorical | 0/1 | 0.0, 1.0 | `smoking_status` | `smoke_former01` |
| 21 | `glucose` | numeric | mg/dL | 30 – 800 | `glucose_serum_mgdl` | `identity` |
| 22 | `hba1c` | numeric | % | 3.0 – 18.0 | `hba1c_pct` | `identity` |
| 23 | `tc` | numeric | mg/dL | 50 – 600 | `total_chol_mgdl` | `identity` |
| 24 | `hdl` | numeric | mg/dL | 5 – 200 | `hdl_mgdl` | `identity` |
| 25 | `hemoglobin` | numeric | g/dL | 3 – 22 | `hemoglobin_gdl` | `identity` |

Sıra ve kategoriler: `phase_xxxv/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Fold içi medyan imputasyon (`dev_feature_missingness.csv`). Uygulamada imputasyon yok.
- **Uygulama (registry kuralı):** ZORUNLU: 25 feature. Lab eksikse B üretilmez; A'ya düşülür. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES I 2015–16 (kilitli tek sefer) | 4812 (716) | 540 / 1187 / 2909 / 176 | 0,313 [0,291–0,335] | 0,754 [0,721–0,784] | 0,290 [0,276–0,304] | 0,943 [0,934–0,951] | 0,805 [0,788–0,823] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxxv/results/test_operating_points.csv` (SHA256 `51aafe9a16ec…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Hiçbir eşikte sağlanmadı.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES I 2015–16 (kilitli tek sefer) | B − SCORED | 0,759 | 0,047 [0,035–0,058] |  | `phase_xxxv/results/test_delta_auc.csv` |
| İç test — NHANES I 2015–16 (kilitli tek sefer) | B − A | 0,791 | 0,015 [0,009–0,021] |  | `phase_xxxv/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Model A'nın tüm sınırlılıkları geçerli. Rutin lab katkısı küçük: B−A ΔAUC +0,015.
- Hemoglobin yalnız B'de (SCORED anemi bileşeni lab olduğu için).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Rutin laboratuvar sonuçları gerekir.
- **Kurallar:** `ckd_A` ile aynı uygunluk; ek olarak glukoz, HbA1c, TK, HDL, hemoglobin zorunlu. Eksikse `ckd_A`'ya düşer.
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
