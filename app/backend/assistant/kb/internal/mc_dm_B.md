---
id: mc_dm_B
title: Model kartı — Diyabet (teşhis edilmemiş) — laboratuvarlı (`dm_B`)
source_ref: app/docs/model_cards/dm_B.md
card_sha256: 7d67c31feeee92dda38df420eb27bad1be6f2384e5f22d8681de653449c3dd2a
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Diyabet (teşhis edilmemiş) — laboratuvarlı (`dm_B`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `dm_B` (secondary (laboratuvar varsa)) |
| hastalık / hedef | Diyabet (teşhis edilmemiş) — laboratuvarlı |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | Lojistik regresyon (class_weight) |
| en yüksek kanıt düzeyi | iç test (NHANES içi; zamansal değil) |
| model dosyası | `phase_xlii/models/dm_B_final.joblib` (SHA256 `ccaf1dccd008f4df…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xlii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Diyabet tanısı olmayan erişkinde tek ziyaret ölçümüyle teşhis edilmemiş diyabet (HbA1c ≥ %6,5 veya açlıkta FPG ≥ 126) olup olmadığını rutin laboratuvar eklenmiş girdilerle (TK, HDL, TG, ALT, ürik asit; HbA1c/glukoz girdi değil) sıralar. Tarama sıralayıcısıdır; ADA tanısı (doğrulama testi) değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): E 2007–08, F 2009–10, I 2015–16, J 2017–18 | ABD genel nüfus örneklemi |
| iç test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): G 2011–12, H 2013–14 | aynı program; kişi düzeyinde ayrık döngüler |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD sivil, kurum dışı nüfusunun olasılık örneklemi (NHANES MEC muayenesi). Tasarım ağırlıkları kullanılmadı.
- **Popülasyon (registry):** Model A ile aynı.
- **Uygunluk (kaynak):** Yaş ≥ 20, MEC muayenesi, gebe değil, HbA1c ölçülmüş; hariç: diyabet tanısı (DIQ010 = 1), DIQ010 7/9/eksik, tanısız ama insülin/hap kullanan (`phase_xlii/01_cohort.md`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Model A ile aynı (teşhis edilmemiş diyabet: HbA1c ≥ 6,5% veya açlıkta FPG ≥ 126 mg/dL; HbA1c/glukoz girdi DEĞİL).
- **Ölçüm:** HbA1c (laboratuvar) ≥ %6,5 veya geçerli açlık alt örnekleminde (8–24 sa) FPG ≥ 126 mg/dL; I/J'de CDC C311→C501 geri denklemi. Objektif laboratuvar ölçümü; tek ziyaret.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 20 – 80 | `age_years` | `age_cap80` |
| 2 | `sex_male` | categorical | 0/1 | 0.0, 1.0 | `sex` | `sex_male01` |
| 3 | `race_mexam` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_mexam` |
| 4 | `race_othhisp` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_othhisp` |
| 5 | `race_black` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_black` |
| 6 | `race_other` | categorical | 0/1 | 0.0, 1.0 | `race_ethnicity` | `race_other` |
| 7 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 8 | `waist` | numeric | cm | 40 – 200 | `waist_cm` | `identity` |
| 9 | `sbp` | numeric | mmHg | 70 – 260 | `sbp_1..3_mmhg` | `sbp_mean_all` |
| 10 | `dbp` | numeric | mmHg | 30 – 150 | `dbp_1..3_mmhg` | `dbp_mean_all` |
| 11 | `htn_dx_med` | categorical | 0/1 | 0.0, 1.0 | `told_hypertension+on_bp_medication` | `htn_dx_med` |
| 12 | `fam_dm` | categorical | 0/1 | 0.0, 1.0 | `family_hx_diabetes` | `bool01` |
| 13 | `gdm` | categorical | 0/1 | 0.0, 1.0 | `sex+gestational_diabetes_hx` | `gdm_rule` |
| 14 | `pa_rec` | categorical | 0/1 | 0.0, 1.0 | `recreational_activity` | `bool01` |
| 15 | `smoke_current` | categorical | 0/1 | 0.0, 1.0 | `smoking_status` | `smoke_current01` |
| 16 | `smoke_former` | categorical | 0/1 | 0.0, 1.0 | `smoking_status` | `smoke_former01` |
| 17 | `tc` | numeric | mg/dL | 50 – 600 | `total_chol_mgdl` | `identity` |
| 18 | `hdl` | numeric | mg/dL | 5 – 200 | `hdl_mgdl` | `identity` |
| 19 | `tg_log` | numeric | ln(mg/dL) | 2.3026 – 8.5172 | `tg_mgdl` | `ln_clip1` |
| 20 | `alt_log` | numeric | ln(U/L) | 1.0986 – 6.9078 | `alt_ul` | `ln_clip1` |
| 21 | `uric_acid` | numeric | mg/dL | 0.5 – 20 | `uric_acid_mgdl` | `identity` |

Sıra ve kategoriler: `phase_xlii/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Geliştirmede BMI %1,1, bel %4,4, KB %3,9, GDM %5,7 eksik; fold içinde medyan imputasyon. Uygulamada imputasyon yok: zorunlu alan eksikse ABSTAIN.
- **Uygulama (registry kuralı):** ZORUNLU: 21 feature. Lab alanlarından biri eksikse B üretilmez; A'ya geri dönülebilir (A kendi kuralını sağlıyorsa). Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | 8895 (389) | 278 / 2003 / 6503 / 111 | 0,122 [0,109–0,136] | 0,715 [0,668–0,757] | 0,235 [0,227–0,245] | 0,983 [0,980–0,986] | 0,825 [0,808–0,843] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xlii/results/test_operating_points.csv` (SHA256 `5af8d3f2b8f3…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.
Not: fpr.value: kaynak dosyada ham değer 0.23548 → 0,235; registry ve uygulama 0,236 gösterir (kaynak rapordaki çift yuvarlama); auc.value: kaynak dosyada ham değer 0.82548 → 0,825; registry ve uygulama 0,826 gösterir (kaynak rapordaki çift yuvarlama).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Hiçbir eşikte sağlanmadı (P 0,10–0,12).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − ADA | 0,758 | 0,067 [0,050–0,083] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` |
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − A | 0,800 | 0,025 [0,014–0,036] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` |
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − yaş+BMI | 0,747 | 0,079 [0,061–0,097] | tür: ikincil | `phase_xlii/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Model A'nın tüm sınırlılıkları geçerli. Rutin lab katkısı küçük ama anlamlı (ΔAUC B−A +0,025).
- TG biyokimya değeri (LBXSTR; CDC LBXTR önerir); E-2007 LX20 analitleri düzeltmesiz; J laboratuvarlarına CDC geri denklemi uygulanmıştı (eğitim).
- Kullanıcı HbA1c/glukoz bilse bile modele girilmez (hedefi tanımlar); bu değerler varsa doğrudan tanı eşikleri kullanılmalıdır.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Rutin biyokimya sonuçları gerekir.
- **Kurallar:** `dm_A` ile aynı uygunluk; ek olarak TK, HDL, TG, ALT, ürik asit zorunlu. Eksikse sonuç `dm_A`'ya düşer (`fallback_from`).
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
