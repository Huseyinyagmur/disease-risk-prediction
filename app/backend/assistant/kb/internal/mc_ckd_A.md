---
id: mc_ckd_A
title: Model kartı — Böbrek (farkında olunmayan tek ziyaret renal anormalliği) (`ckd_A`)
source_ref: app/docs/model_cards/ckd_A.md
card_sha256: a1eaa832d1f71975d1d75c61a9bbe8b673e63986223a94d46a089c66b78b2ce2
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Böbrek (farkında olunmayan tek ziyaret renal anormalliği) (`ckd_A`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `ckd_A` (primary) |
| hastalık / hedef | Böbrek (farkında olunmayan tek ziyaret renal anormalliği) |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | LightGBM (imputer + LGBM) |
| en yüksek kanıt düzeyi | iç test (NHANES I 2015–16; PREVIOUSLY_EXPOSED başka hedef; zamansal değil) |
| model dosyası | `phase_xxxv/models/ckd_A_final.joblib` (SHA256 `b107cbb4ed99e13b…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxxv |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Böbrek hastalığı tanısı olmayan erişkinde tek ziyarette eGFR < 60 veya UACR ≥ 30 mg/g olup olmadığını laboratuvarsız girdilerle sıralar. KDIGO KBH tanısı (3 ay) değildir.

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
- **Popülasyon (registry):** NHANES ≥ 20 yaş, gebe/diyaliz değil, "doktor zayıf/başarısız böbrek dedi mi" = Hayır. Prevalans ≈ %15.
- **Uygunluk (kaynak):** Yaş ≥ 20, MEC, kreatinin ve UACR var, gebe değil, diyaliz değil, KIQ022 = Hayır (`phase_xxxv/01_cohort.md`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Farkında olmayan erişkinde tek ziyaret eGFR < 60 (CKD-EPI 2021) VEYA UACR ≥ 30 mg/g (böbrek hastalığı tanısı DEĞİL; KDIGO 3 ay şartı karşılanmaz).
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

Sıra ve kategoriler: `phase_xxxv/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Fold içi medyan imputasyon (`dev_feature_missingness.csv`). Uygulamada imputasyon yok.
- **Uygulama (registry kuralı):** ZORUNLU: 20 feature (htn_med, dm_insulin, dm_pills: yapısal atlama kurallarıyla 0). Tanılı böbrek hastalığı/diyaliz varsa model uygulanmaz. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES I 2015–16 (kilitli tek sefer) | 4812 (716) | 549 / 1322 / 2774 / 167 | 0,293 [0,273–0,314] | 0,767 [0,734–0,796] | 0,323 [0,309–0,337] | 0,943 [0,934–0,951] | 0,791 [0,773–0,809] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxxv/results/test_operating_points.csv` (SHA256 `51aafe9a16ec…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Hiçbir model ve eşikte sağlanmadı (P 0,29–0,31, FPR 0,29–0,32; %15 prevalansta P ≥ 0,70 yapısal olarak zor).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES I 2015–16 (kilitli tek sefer) | A − SCORED | 0,759 | 0,032 [0,020–0,043] |  | `phase_xxxv/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Kazanç esas olarak yalnız-UACR pozitiflerinde ve < 60 yaşta; ≥ 60 yaşta tarama kuralı fiilen "yaşa göre herkese test" (FPR 0,74–0,90).
- Etiket tek ziyaret; geçici albüminüri dışlanamaz; KIQ022 öz-bildirim. Yaş ve cinsiyet eGFR denkleminin girdisidir (hedef bileşeniyle mekanik bağ).
- Modifiye SCORED karşılaştırması orijinal yayınla karşılaştırılamaz (PVD/proteinüri yok; SCORED puanları birincil metinle doğrulanamadı).
- Test tek dönem (2015–16), PREVIOUSLY_EXPOSED; bağımsız dış doğrulama yok. Survey tasarımı kullanılmadı.
- Kullanıcı biliyorsa eGFR/UACR doğrudan kullanılmalı (hedefi tanımlar).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Formla doldurulabilir (laboratuvarsız; ölçüm gerektiren: boy/kilo/bel/tansiyon).
- **Kurallar:** NOT_APPLICABLE: yaş < 20, gebe, "doktor zayıf/başarısız böbrek dedi", diyaliz. ABSTAIN: yaş, cinsiyet, ırk, gebelik, böbrek tanısı sorusu yanıtsız veya zorunlu alan eksik (2. ve 3. tansiyon okuması dahil). Kreatinin veya idrar albümin+kreatinin girilirse TARGET_DEFINING_INPUT uyarısı. `ckd_B` laboratuvar varsa önce denenir.
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
