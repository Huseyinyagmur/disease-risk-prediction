---
id: mc_htn_M1
title: Model kartı — Hipertansiyon (`htn_M1`)
source_ref: app/docs/model_cards/htn_M1.md
card_sha256: 99fe36cbe7e29d425ffe316ad0b0681f12212afed9cf3dd4625aec43e4277a00
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Hipertansiyon (`htn_M1`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `htn_M1` (primary) |
| hastalık / hedef | Hipertansiyon |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | Lojistik regresyon (RandomOverSampler; imblearn Pipeline) |
| en yüksek kanıt düzeyi | zamansal test (C 2003–04; ölçüm yöntemi kaymalı: auskültatuvar vs oskilometrik) — bağımsız kurum doğrulaması DEĞİL |
| model dosyası | `phase_xxxvii/models/htn3_M1.joblib` (SHA256 `4beed37322418679…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxxvii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Tek ziyarette ölçülen KB ≥ 140/90 veya antihipertansif ilaç kullanımı (mevcut durum) olup olmadığını, ölçülen tansiyonu girdi almadan sınıflar.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): P 2017–Mar 2020, L Ağu 2021–Ağu 2023 | genel nüfus; oskilometrik KB |
| zamansal test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): C 2003–04 | auskültatuvar (cıvalı) KB; ölçüm yöntemi kaymalı |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.
- **Popülasyon (registry):** NHANES ≥ 18 yaş, gebe değil, ≥2 geçerli BP okuması. Geliştirme P+L (2017–2023), test C (2003–04).
- **Uygunluk (kaynak):** Yaş ≥ 18, gebe değil, ≥ 2 geçerli KB okuması (> 0), BMI var; testte Phase21 işitme dış testindekiler hariç.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Tek ziyarette ölçülen kan basıncı ≥ 140/90 mmHg VEYA antihipertansif ilaç kullanımı (mevcut durum; ölçülen tansiyon girdi DEĞİL).
- **Ölçüm:** Ortalama SBP ≥ 140 veya DBP ≥ 90 (geçerli okumalar) veya ilaç kullanımı (öz bildirim). Test döngüsünde hekim, geliştirmede cihaz ölçümü.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 18 – 80 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `race` | categorical | kategori | mexican_american, nh_black, nh_white, other_hispanic, other_incl_multi | `race_ethnicity` | `race_str` |
| 4 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 5 | `waist` | numeric | cm | 40 – 200 | `waist_cm` | `identity` |
| 6 | `smoking` | categorical | kategori | current, former, never | `smoking_status` | `smoking_str` |
| 7 | `alcohol_dpd` | numeric | içki/gün | 0 – 30 | `alcohol_drinks_per_day` | `alcohol_dpd` |
| 8 | `diabetes` | categorical | kategori | no, yes | `told_diabetes+on_insulin+on_diabetes_pills` | `diabetes_yesno` |
| 9 | `hba1c` | numeric | % | 3.0 – 18.0 | `hba1c_pct` | `identity` |
| 10 | `tc` | numeric | mg/dL | 50 – 600 | `total_chol_mgdl` | `identity` |
| 11 | `hdl` | numeric | mg/dL | 5 – 200 | `hdl_mgdl` | `identity` |
| 12 | `egfr` | numeric | mL/dk/1.73m2 | 5 – 160 | `creatinine_mgdl+age_years+sex` | `egfr_ckdepi2021_cap80 (v1: egfr_ckdepi2021)` |
| 13 | `uacr_log` | numeric | ln(1+mg/g) | 0.0 – 10.4 | `urine_albumin_mgl+urine_creatinine_mgdl` | `uacr_log1p` |

Sıra ve kategoriler: `phase_xxxvii/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Testte sigara %16,3, alkol %23,1 eksik; geliştirmede öğrenilen medyan/mod ile dolduruldu. Uygulamada imputasyon yok.
- **Uygulama (registry kuralı):** ZORUNLU: 13 feature. Sigara/alkol eksikse (C testinde medyan/mod ile doldurulmuştu) uygulamada TAHMİN ÜRETİLMEZ. race_ethnicity yanıtsızsa ABSTAIN. Dondurulmuş imputer kullanılmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### Zamansal doğrulama

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Zamansal test — NHANES C 2003–04 (ölçüm yöntemi kaymalı) | 2798 (1001) | 767 / 325 / 1472 / 234 | 0,702 [0,675–0,729] | 0,766 [0,739–0,791] | 0,181 [0,164–0,199] | 0,863 [0,846–0,878] | 0,875 [0,862–0,887] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxxvii/results/test_operating_points.csv` (SHA256 `35ef0ffdc761…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Hiçbir eşikte üçlü hedef sağlanmadı (birincil: FPR 0,181; ikincil: Recall 0,665).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| Zamansal test — NHANES C 2003–04 (ölçüm yöntemi kaymalı) | M1 − LR(yaş, cinsiyet, BMI) | 0,863 | 0,012 [0,007–0,018] |  | `phase_xxxvii/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Yaş+cinsiyet+BMI baseline'ına katkı yalnız +0,012 AUC (GA +0,007…+0,018): ML katkısı çok küçük; tek eşik pratikte yaş kuralı gibi çalışıyor (≥60 yaşta FPR 0,85, <60 yaşta Recall 0,31).
- Test etiketi auskültatuvar (hekim, cıvalı) — geliştirme oskilometrik (Omron): etiket ölçeği kayması ölçülmedi. Test 14–20 yıl önce.
- Tek ziyaret fenotipi; beyaz önlük/maskeli HTN ayırt edilemez. Test kümesi seçilmiş C alt kümesi.
- Kalibrasyon: ROS nedeniyle olasılıklar yüksek (O/E 0,88). Klinik olasılık değildir.
- Ölçülen tansiyon girdi DEĞİL: kullanıcının tansiyonu biliniyorsa doğrudan ≥140/90 kuralı kullanılmalı.
- Bu kayıtta laboratuvarsız HTN modeli YOK: M1 (kullanıcı ön seçimi) beş laboratuvar girdisi ister; phase_xxxii modelleri kayda alınmadı (L testi CONTAMINATED etiketli, phase_xxxvi §2).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Laboratuvar sonuçları gerekir (HbA1c, TC, HDL, kreatinin, idrar albümin/kreatinin). Laboratuvarsız kullanıcı için tahmin üretilmez.
- **Kurallar:** NOT_APPLICABLE: yaş < 18, gebe. ABSTAIN: yaş, cinsiyet, ırk, gebelik (kadın) yanıtsız veya 13 alandan biri eksik (HbA1c, TK, HDL, kreatinin → eGFR, idrar albümin/kreatinin → UACR dahil). Ölçülen tansiyon ≥ 140/90 veya ilaç → TARGET_DEFINING_INPUT uyarısı.
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
