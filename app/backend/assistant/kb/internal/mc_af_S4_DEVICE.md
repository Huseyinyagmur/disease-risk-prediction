---
id: mc_af_S4_DEVICE
title: Model kartı — Atriyal fibrilasyon (AF) (`af_S4_DEVICE`)
source_ref: app/docs/model_cards/af_S4_DEVICE.md
card_sha256: ca319713b2df750dd110cdadec58b5f7e030d787222dd55481f7c31970f22d19
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Atriyal fibrilasyon (AF) (`af_S4_DEVICE`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `af_S4_DEVICE` (primary) |
| hastalık / hedef | Atriyal fibrilasyon (AF) |
| uygulamadaki durum | ana modül; mod `ecg_upload_demo`; `app_visible = true` |
| model ailesi | LightGBM (CalibratedResearchModel sarmalayıcı, ham skor) |
| en yüksek kanıt düzeyi | dış doğrulama (bağımsız, farklı kaynaklar; donmuş model + kilitli pipeline bileşimi) |
| model dosyası | `All_Disease_Improvement_Phase21/models/af_S4_DEVICE.joblib` (SHA256 `f4a61af71d7fa1dc…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | Phase21 (All_Disease_Improvement_Phase21); pipeline: phase_xxviii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

12 derivasyonlu 10 sn EKG kaydında ritmin AF mi sinüs ritmi mi olduğunu sınıflar (kayıttaki mevcut ritim). Paroksismal AF öyküsünü dışlamaz; gelecekte AF riskini tahmin etmez. Araştırma ve eğitim amaçlı EKG yükleme demosu.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme + iç test | PTB-XL 1.0.3 (PhysioNet), doi:10.13026/kfzx-aw45; Wagner ve ark., Sci Data 2020, doi:10.1038/s41597-020-0495-6; öznitelikler: PTB-XL+ ECGDeli öznitelikleri (PhysioNet PTB-XL+, `ecgdeli_features.csv`; sürüm numarası proje dosyalarında BULUNAMADI) | tek kurum arşivi (PTB, Almanya); kayıt tarihleri: bkz. §2 not |
| dış doğrulama | PhysioNet/CinC Challenge 2021 1.0.3, doi:10.13026/34va-7q14 (kaynaklar: cpsc_2018, cpsc_2018_extra, chapman_shaoxing, georgia) | dört hastane kaynağı; tarih aralığı BULUNAMADI |

PTB-XL kayıt tarihleri: 1984-11-09 – 2001-06-11 (PTB-XL `recording_date`, tüm veri tabanı; metadata).

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** Hastane EKG arşivi (PTB-XL: tek kurum). Genel nüfus taraması değildir.
- **Popülasyon (registry):** ≥18 yaş, hasta başına ilk EKG, yalnız insan-doğrulamalı AFIB xor SR; 10 s, 500 Hz EKG. Diğer ritimler (AFL, taşikardi, bradikardi, PAC, PVC vb.) eğitimde negatif DEĞİLDİ.
- **Uygunluk (kaynak):** PTB-XL'de hasta başına ilk EKG (etiket süzgecinden önce seçilir); `validated_by_human = True`; SCP kodlarında AFIB xor SR; yaş ≥ 18 (> 89 yaşlar HIPAA gereği 300 kodludur → eksik). Diğer ritimler (AFL, taşikardi, bradikardi, PAC, PVC) eğitimde yoktu. Kaynak: `prepare.py :: af()`.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** PTB-XL kayıtlarında insan-doğrulamalı 12 derivasyonlu EKG ritminin atriyal fibrilasyon mu sinüs ritmi mi olduğu (AF vs SR; mevcut ritim).
- **Ölçüm:** PTB-XL SCP ritim kodu (AFIB veya SR); kardiyolog/insan doğrulamalı kayıtlar (`validated_by_human`). Likelihood alanı kullanılmadı. Değerlendiricilerin demografisi BULUNAMADI. Etiketleme modelden bağımsızdır (veri seti yayın öncesi).
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 18 – 89 | `age_years` | `age_cap89_ptbxl` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `RR_Mean_Global` | numeric | ms | 300 – 2000 | `ecg_af_RR_Mean_Global` | `ecg_pipeline_output` |
| 4 | `RR_Mean_Global_iqr` | numeric | ms | 0 – 1500 | `ecg_af_RR_Mean_Global_iqr` | `ecg_pipeline_output` |
| 5 | `QRS_Dur_Global` | numeric | ms | 40 – 400 | `ecg_af_QRS_Dur_Global` | `ecg_pipeline_output` |
| 6 | `QRS_Dur_Global_iqr` | numeric | ms | 0 – 300 | `ecg_af_QRS_Dur_Global_iqr` | `ecg_pipeline_output` |
| 7 | `PR_Int_Global` | numeric | ms | 50 – 600 | `ecg_af_PR_Int_Global` | `ecg_pipeline_output` |
| 8 | `PR_Int_Global_iqr` | numeric | ms | 0 – 400 | `ecg_af_PR_Int_Global_iqr` | `ecg_pipeline_output` |
| 9 | `P_Dur_Global` | numeric | ms | 20 – 400 | `ecg_af_P_Dur_Global` | `ecg_pipeline_output` |
| 10 | `P_Dur_Global_iqr` | numeric | ms | 0 – 300 | `ecg_af_P_Dur_Global_iqr` | `ecg_pipeline_output` |
| 11 | `QT_Int_Global` | numeric | ms | 200 – 900 | `ecg_af_QT_Int_Global` | `ecg_pipeline_output` |
| 12 | `QT_Int_Global_iqr` | numeric | ms | 0 – 400 | `ecg_af_QT_Int_Global_iqr` | `ecg_pipeline_output` |

Sıra ve kategoriler: `Strong_Model_External_Validation_Phase26/frozen_model_manifest.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Eğitim: yaş %1,7 eksik (HIPAA > 89 kodu), EKG öznitelikleri %0 (`training_protocol.json > missing_fraction`); eğitim fold'u içi imputasyon (model pipeline'ı). Dış: pipeline başarısızı birincil analizde dışlandı, duyarlılık analizinde FN/TN sayıldı.
- **Uygulama (registry kuralı):** ZORUNLU: 12 feature'ın tamamı. Pipeline herhangi birini üretemezse (NaN) tahmin üretilmez. Yaş ≥ 90 → tahmin yok. Dondurulmuş imputer uygulama tarafında KULLANILMAZ.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — PTB-XL fold 10 (hasta düzeyinde ayrık) | 1572 (114) | 103 / 15 / 1443 / 11 | 0,873 [0,801–0,921] | 0,904 [0,835–0,945] | 0,010 [0,006–0,017] | 0,992 [0,987–0,996] | 0,980 [0,959–0,995] | evet |

#### Bağımsız dış doğrulama (farklı kaynaklar; donmuş model + kilitli pipeline)

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Dış doğrulama — Challenge 2021, 4 kaynak havuzu, AF vs SR (A2) | 7817 (3497) | 3247 / 11 / 4309 / 250 | raporlanmaz (prevalansa bağlı) | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | raporlanmaz (prevalansa bağlı) | 0,990 [0,987–0,992] | değerlendirilemez |
| Dış doğrulama — CPSC 2018, AF vs SR (A2) | 1905 (1087) | 1007 / 3 / 815 / 80 | raporlanmaz (prevalansa bağlı) | 0,926 [0,909–0,940] | 0,004 [0,001–0,011] | raporlanmaz (prevalansa bağlı) | 0,995 [0,992–0,997] | değerlendirilemez |
| Dış doğrulama — CPSC-Extra, AF vs SR (A2) — YORUMLANAMAZ (SR n=4) | 82 (78) | 74 / 0 / 4 / 4 | raporlanmaz (prevalansa bağlı) | 0,949 [0,875–0,980] | 0,000 [0,000–0,490] | raporlanmaz (prevalansa bağlı) | 0,990 [0,962–1,000] | değerlendirilemez |
| Dış doğrulama — Chapman-Shaoxing, AF vs SR (A2) | 3580 (1777) | 1742 / 5 / 1798 / 35 | raporlanmaz (prevalansa bağlı) | 0,980 [0,973–0,986] | 0,003 [0,001–0,006] | raporlanmaz (prevalansa bağlı) | 1,000 [0,999–1,000] | değerlendirilemez |
| Dış doğrulama — Georgia, AF vs SR (A2) | 2250 (555) | 424 / 3 / 1692 / 131 | raporlanmaz (prevalansa bağlı) | 0,764 [0,727–0,797] | 0,002 [0,001–0,005] | raporlanmaz (prevalansa bağlı) | 0,954 [0,941–0,967] | değerlendirilemez |
| Dış — ikincil analiz: AF vs SR + diğer ritimler (B), havuz | 5477 (3497) | 3247 / 143 / 1837 / 250 | raporlanmaz (prevalansa bağlı) | 0,929 [0,919–0,937] | 0,072 [0,062–0,084] | raporlanmaz (prevalansa bağlı) | 0,965 [0,960–0,970] | değerlendirilemez |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxvii/results/ci_metrics.csv` (SHA256 `87e6cc9bcee1…`); `phase_xxxiii/results/a2_results.csv` (SHA256 `72726837a07b…`); `phase_xxxiii/results/b_results.csv` (SHA256 `a1ae4debce97…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Üç hedef AF vs SR iç testte GA ile birlikte sağlandı; dış doğrulamada P prevalansa bağlı olduğu için değerlendirilemez. Diğer ritimlerde FPR 0,072 (sinüs taşikardisinde 0,181; PVC 0,306).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — PTB-XL fold 10 (hasta düzeyinde ayrık) | model − RR_iqr / RR_mean | 0,959 | 0,021 [0,006–0,037] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` |
| Dış doğrulama — Challenge 2021, 4 kaynak havuzu, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,968 | 0,021 [0,018–0,025] |  | `phase_xxxiii/results/a2_results.csv` |
| Dış doğrulama — CPSC 2018, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,978 | 0,017 [0,011–0,023] |  | `phase_xxxiii/results/a2_results.csv` |
| Dış doğrulama — CPSC-Extra, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,978 | 0,013 [-0,013–0,051] |  | `phase_xxxiii/results/a2_results.csv` |
| Dış doğrulama — Chapman-Shaoxing, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,992 | 0,008 [0,005–0,011] |  | `phase_xxxiii/results/a2_results.csv` |
| Dış doğrulama — Georgia, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,871 | 0,083 [0,062–0,103] |  | `phase_xxxiii/results/a2_results.csv` |
| Dış — ikincil analiz: AF vs SR + diğer ritimler (B), havuz | model − RR_iqr/RR_mean ≥ 0,138235 | 0,929 | 0,035 [0,028–0,044] |  | `phase_xxxiii/results/b_results.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Model yalnız AF vs sinüs ritmi ayırır; diğer ritimlere karşı FPR 0,072, sinüs taşikardisinde 0,181, PVC 0,306.
- Feature'lar yalnız AF-ECGDELI-OCTAVE-v1 ile üretilebilir (Octave 10.3.0 + ECGDeli v1.1 + vendor WFDB). Pipeline-golden uyumu: karar uyumu 0,99 (Wilson alt sınır 0,946); QT ve P/PR sapması sürüyor.
- Georgia kaynağında Recall 0,764; RR düzensizliği göstermeyen ilk 10 s'lik AF kayıtları kaçıyor.
- Pipeline başarısızlığı (zero_beats, ecgdeli_error, feature_error) → tahmin üretilmez.
- Olasılıklar kalibre değil; yalnız sabit eşikte karar. Pipeline sapması AF kayıtlarında olasılığı kaydırabilir (p95 |Δp| 0,24).
- Tek ritim kaydı; semptom/klinik bağlam yok. Klinik tanı DEĞİL.
- Eğitim/iç test öznitelikleri PTB-XL+ golden, dış/uygulama öznitelikleri kilitli Octave pipeline; karar uyumu 0,99 (GA alt sınırı 0,946) — bkz. AF doğrulama belgesi.
- PTB-XL ↔ Challenge kayıt düzeyi hash karşılaştırması yapılmadı; Challenge'da hasta kimliği yok.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `ecg_upload_demo` — EKG yükleme + kilitli Octave pipeline; demo. Modül etiketi: ana modül.
- **Uygulanabilirlik:** ECG sinyali + kilitli Octave pipeline gerekir (≈3,6 s/kayıt). Tek başına mobil/web formu ile ÜRETİLEMEZ.
- **Kurallar:** Yalnız `POST /ecg/af`: WFDB `.hea` + `.dat`/`.mat`, 500 Hz, 12 lead, ≥ 10 sn (uzunsa ilk 10 sn). NOT_APPLICABLE: yaş 18–89 dışı (≥ 90). ABSTAIN: yaş/cinsiyet yok, fs ≠ 500 Hz, < 5.000 örnek, pipeline başarısız (zero_beats, ECGDeli hatası, NaN öznitelik), 60 sn zaman aşımı, AF çalışma ortamı (Octave/ECGDeli/kilit) yok veya SHA uyuşmazlığı. `/predict` için her zaman NOT_APPLICABLE.
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
