# Model kartı — Atriyal fibrilasyon (AF) (`af_S4_DEVICE`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

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

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| fit (fold 1–8) | 8839 | 560 | `phase_xlvi/results/af_split_check.json` |
| validation (fold 9; eşik seçimi) | 1614 | 117 | aynı |
| iç test (fold 10) | 1572 | 114 | aynı; Phase XXVII ci_metrics |
| dış A2 havuz (AF vs SR) | 7817 | 3497 | `phase_xxxiii/results/a2_results.csv` |
| dış B havuz (AF vs SR + diğer ritim) | 5477 | 3497 | `phase_xxxiii/results/b_results.csv` |

Örneklem büyüklüğü hesaplanmadı; veri setinin uygun tüm kişileri kullanıldı (BULUNAMADI: önceden güç/kesinlik hesabı).

## 7. Eksik veri [11]

- **Geliştirme:** Eğitim: yaş %1,7 eksik (HIPAA > 89 kodu), EKG öznitelikleri %0 (`training_protocol.json > missing_fraction`); eğitim fold'u içi imputasyon (model pipeline'ı). Dış: pipeline başarısızı birincil analizde dışlandı, duyarlılık analizinde FN/TN sayıldı.
- **Uygulama (registry kuralı):** ZORUNLU: 12 feature'ın tamamı. Pipeline herhangi birini üretemezse (NaN) tahmin üretilmez. Yaş ≥ 90 → tahmin yok. Dondurulmuş imputer uygulama tarafında KULLANILMAZ.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi, PTB-XL resmî `strat_fold`: 1–8 fit, 9 validation, 10 test; kişi kesişimi 0 (bu fazda doğrulandı). Zamansal değil. Dış: Challenge 2021, farklı kaynaklar.

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** Phase21 eğitim protokolü (`All_Disease_Improvement_Phase21/training_protocol.json`, seed 20261111): 8 aile (Dummy, LR, RF, ExtraTrees, HistGB, XGBoost, LightGBM, CatBoost); yalnız fit kümesinde 3-fold StratifiedGroupKFold (kişi grubu); en iyi 2 aile-panel için Optuna (görev başına ≤ 6 deneme); seçim CV AP ile; test ve dış veri seçimde kullanılmadı. Seçilen: LightGBM, HPO uygulandı; parametreler `selected_model_registry.json`.
- **Sınıf dengesizliği:** Phase21: azınlık/çoğunluk < 0,8 ise LR class_weight, ROS, RUS, SMOTENC adayları yalnız eğitim fold'unda; seçilen strateji modelin meta verisinde. Seçilen strateji: baseline (yeniden örnekleme yok).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.2360882764** (`Strong_Model_External_Validation_Phase26/frozen_model_manifest.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)
- Seçim kuralı (kaynak): Phase21 eşik kuralı (`training_protocol.json > threshold`): validation kümesinde önce P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 birlikte; yoksa R ≥ 0,60, FPR ≤ 0,25; içinde F2 − 0,5·FPR + 0,25·P en büyük ("BALANCED" senaryosu). **Bu fazda bulundu:** registry eşiği `All_Disease_Improvement_Phase21/selected_model_registry.json` içindeki BALANCED senaryo eşiğiyle bit düzeyinde aynıdır (XLIII registry'de "kural BULUNAMADI" yazıyordu). Hangi dalın (birincil/yedek) uygulandığı: senaryo kaydında `constraints_met = true`.
- İkincil eşikler (yalnız raporlama): yok

## 11. Kalibrasyon [12e]

- Registry: raw (kalibrasyon uygulanmadı).
- Phase21: ham skor ile fit kümesi OOF üzerinde sigmoid kalibrasyon karşılaştırıldı; validation'da seçildi (isotonic yalnız ≥ 1000 fit ve sınıf başına ≥ 100 ise). Seçilen: raw. Olasılık klinik olasılık değildir; pipeline sapması AF kayıtlarında olasılığı kaydırabilir.

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

## 14. Alt gruplar [14, 23a, 23b]

Dış doğrulamada kaynak başına sonuçlar performans tablosundadır (Georgia Recall 0,764). Diğer ritimlerde FPR: sinüs taşikardisi 0,181, PVC 0,306, PAC 0,153 (`phase_xxxiii/results/b_rhythm_fpr.csv`). Yaş/cinsiyet alt grup analizi bu karta alınmadı (BULUNAMADI: kilitli alt grup tablosu).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

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
- `phase_xxvii/PHASE_XXVII_REPORT.md`
- `phase_xxviii/PHASE_XXVIII_REPORT.md`
- `phase_xxix/PHASE_XXIX_REPORT.md`
- `phase_xxxiii/PHASE_XXXIII_REPORT.md`
- `phase_xlvi/af_validation_dossier.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 25, kısmen 20, yok 5, uygulanamaz 2. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
