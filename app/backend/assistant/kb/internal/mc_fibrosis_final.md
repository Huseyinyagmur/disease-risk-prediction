---
id: mc_fibrosis_final
title: Model kartı — Karaciğer fibrozisi (LSM ≥ 8 kPa) (`fibrosis_final`)
source_ref: app/docs/model_cards/fibrosis_final.md
card_sha256: f71004041e90bc725814bf81e1570b1f76556d9241ce6beb727d13a7f1dcdaa2
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Karaciğer fibrozisi (LSM ≥ 8 kPa) (`fibrosis_final`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `fibrosis_final` (primary) |
| hastalık / hedef | Karaciğer fibrozisi (LSM ≥ 8 kPa) |
| uygulamadaki durum | ana modül; mod `standard`; `app_visible = true` |
| model ailesi | CatBoost (imblearn Pipeline, strateji yok) |
| en yüksek kanıt düzeyi | iç test (NHANES L 2021–23; PREVIOUSLY_EXPOSED: kişiler CAP hedefi için görülmüş) |
| model dosyası | `phase_xxxi/models/fibrosis_final.joblib` (SHA256 `7f349c4a29663e00…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxxi |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

FibroScan karaciğer sertliği (LSM) ≥ 8,0 kPa olup olmadığını rutin laboratuvar ve antropometriyle sınıflar (ileri değerlendirmeye yönlendirme sıralayıcısı). Histolojik fibrozis evresi değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): P 2017–Mar 2020 (LUX FibroScan) | genel nüfus |
| iç test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): L Ağu 2021–Ağu 2023 | aynı program; L kişileri CAP hedefi için görülmüş (PREVIOUSLY_EXPOSED) |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.
- **Popülasyon (registry):** NHANES ≥ 20 yaş, gebe değil, FibroScan kalitesi tam (LUAXSTAT=1), ALT/AST/trombosit/albümin/BMI mevcut. Açlık şartı aranmadı.
- **Uygunluk (kaynak):** Yaş ≥ 20, gebe değil, FibroScan tam (LUAXSTAT = 1), LSM var, FIB-4/NFS girdileri tam (ALT, AST, trombosit, albümin, BMI). Açlık şartı yok (`phase_xxxi/results/fibrosis_eligibility_counts.json`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** FibroScan karaciğer sertliği (LSM) ≥ 8,0 kPa (AASLD 2023 VCTE bandı) olması; histolojik ≥F2 ile birebir değil (mevcut durum).
- **Ölçüm:** VCTE (FibroScan) medyan LSM ≥ 8,0 kPa (AASLD 2023 bandı). Cihaz ölçümü; operatör bilgisi BULUNAMADI.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 20 – 80 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 4 | `waist` | numeric | cm | 40 – 200 | `waist_cm` | `identity` |
| 5 | `weight` | numeric | kg | 25 – 300 | `weight_kg` | `identity` |
| 6 | `alt` | numeric | U/L | 3 – 1000 | `alt_ul` | `identity` |
| 7 | `ast` | numeric | U/L | 3 – 1000 | `ast_ul` | `identity` |
| 8 | `ggt` | numeric | U/L | 1 – 2000 | `ggt_ul` | `identity` |
| 9 | `alp` | numeric | U/L | 10 – 1500 | `alp_ul` | `identity` |
| 10 | `albumin` | numeric | g/dL | 1.0 – 6.5 | `albumin_gdl` | `identity` |
| 11 | `platelets` | numeric | 10^3/µL | 10 – 1500 | `platelets_k_ul` | `identity` |
| 12 | `glucose` | numeric | mg/dL | 30 – 800 | `glucose_serum_mgdl` | `identity` |
| 13 | `hba1c` | numeric | % | 3.0 – 18.0 | `hba1c_pct` | `identity` |
| 14 | `diabetes` | categorical | kategori | no, yes | `told_diabetes+on_insulin+on_diabetes_pills` | `diabetes_yesno` |
| 15 | `tg` | numeric | mg/dL | 10 – 5000 | `tg_mgdl` | `identity` |
| 16 | `hdl` | numeric | mg/dL | 5 – 200 | `hdl_mgdl` | `identity` |
| 17 | `alcohol_dpd` | numeric | içki/gün | 0 – 30 | `alcohol_drinks_per_day` | `alcohol_dpd` |

Sıra ve kategoriler: `phase_xxxi/config/fibrosis_model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Uygunluk ölçütü gereği FIB-4/NFS girdileri tam; diğer girdiler pipeline içi imputasyon. Uygulamada imputasyon yok.
- **Uygulama (registry kuralı):** ZORUNLU: 17 feature. Dondurulmuş imputer kullanılmaz. Diyabet durumu (told/insulin/pills) yanıtlanmamışsa tahmin yok.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | 4714 (587) | 451 / 1430 / 2697 / 136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,952 [0,943–0,959] | 0,794 [0,773–0,813] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxxi/results/fibrosis_test_results.csv` (SHA256 `646a2383886c…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Üçlü hedef sağlanmadı; eşik Recall ≥ 0,85 hedefiyle seçilmişti, testte 0,768 (tarama hedefi 0,85 altında). Yönlendirme oranı 0,399.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | model − FIB-4 | 0,597 | 0,197 [0,169–0,225] |  | `phase_xxxi/results/fibrosis_test_results.csv` |
| İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | model − NFS | 0,698 | 0,096 [0,075–0,117] |  | `phase_xxxi/results/fibrosis_test_results.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- CV AUC 0,835 → test AUC 0,794: kayma işareti. Test PREVIOUSLY_EXPOSED; bağımsız dış doğrulama ve zamansal doğrulama yok.
- Açlıksız serum glukoz/TG kullanıldı (protokolde gerekçeli sapma). LSM ≥ 8 kPa histolojik fibrozisle birebir değildir; hedef ölçüm (LSM) girdi DEĞİL.
- FIB-4'e göre ΔAUC +0,197, NFS'ye göre +0,096 (ikisi de anlamlı), ancak FIB-4/NFS bu hedef için kalibre edilmemiş basit baseline'lardır.
- Düşük P (0,24) ve FPR 0,35: yalnız ön tarama sıralayıcısı. Cinsiyete özgü eşikler yalnız ikincil.
- Hepatit B/C ve alkol dışı etiyoloji ayrımı yok. Klinik tanı DEĞİL.
- FIB-4 ve NFS biyopside ilerlemiş fibrozis için geliştirildi; buradaki hedef farklıdır (bkz. 01_reference_score_analysis.md).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: ana modül.
- **Uygulanabilirlik:** Biyokimya + CBC (trombosit) + HbA1c sonuçları gerekir; formla doldurulabilir ama 17 alan.
- **Kurallar:** NOT_APPLICABLE: yaş < 20, gebe. ABSTAIN: yaş, cinsiyet, gebelik (kadın) yanıtsız veya 17 alandan biri eksik (ALT, AST, GGT, ALP, albümin, trombosit, glukoz, HbA1c, TG, HDL, alkol dahil).
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
