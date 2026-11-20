# Model kartı — Koroner arter hastalığı (CAD) (`cad_DEVICE`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `cad_DEVICE` (primary) |
| hastalık / hedef | Koroner arter hastalığı (CAD) |
| uygulamadaki durum | deneysel; mod `clinical_mode`; `app_visible = true` |
| model ailesi | Lojistik regresyon + sigmoid kalibrasyon (CalibratedClassifierCV, OOF) |
| en yüksek kanıt düzeyi | iç test + düzeltilmiş teknik tekrar (bağımsız dış doğrulama DEĞİL) |
| model dosyası | `models/cad/DEVICE.joblib` (SHA256 `ef3a3b73a7ba7ca5…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | V2 başlangıcı (kök models/cad); düzeltilmiş teknik tekrar: phase_xli |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Anjiyografiye yönlendirilmiş semptomatik hastada >%50 koroner daralma (UCI `num > 0`) olup olmadığını efor testi ve EKG bulgularıyla sınıflar. Genel nüfus taraması değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme + iç test | UCI Heart Disease, doi:10.24432/C52P4X (Cleveland; teknik tekrar: Hungarian, VA Long Beach) | Cleveland Clinic hastane kohortu; toplama tarihleri BULUNAMADI |
| teknik tekrar | UCI Hungarian (n = 95) ve VA Long Beach (n = 64), eksiksiz vaka alt kümesi | önceden hatalı skorlanmış; PREVIOUSLY_EXPOSED |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** Hastane, anjiyografiye yönlendirilmiş hastalar (seçilmiş, eski kohort).
- **Popülasyon (registry):** UCI Cleveland eğitim (n=303 türevi; eğitim 181); hastane kohortu, semptomatik/anjiyografiye yönlendirilmiş kişiler (genel popülasyon DEĞİL).
- **Uygunluk (kaynak):** UCI Cleveland 303 satır; kopya/çelişki 0; `ca`, `thal`, `num` girdi değil (`models/cad/DEVICE.json`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** UCI kohortlarında anjiyografik >%50 koroner daralma (num>0) bulunup bulunmaması (mevcut durum).
- **Ölçüm:** Anjiyografik çap daralması > %50 (UCI `num > 0`); değerlendirici ve körleme bilgisi BULUNAMADI.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 20 – 100 | `age_years` | `identity` |
| 2 | `sex` | categorical | kategori | 0.0, 1.0 | `sex` | `cad_sex_strfloat` |
| 3 | `cp` | categorical | kategori | 1.0, 2.0, 3.0, 4.0 | `cad_chest_pain_type` | `cad_cp_strfloat` |
| 4 | `trestbps` | numeric | mmHg | 50 – 300 | `sbp_1_mmhg` | `cad_trestbps` |
| 5 | `chol` | numeric | mg/dL | 30 – 1000 | `total_chol_mgdl` | `identity` |
| 6 | `fbs` | categorical | kategori | 0.0, 1.0 | `glucose_fasting_mgdl` | `fasting_gt120_strfloat` |
| 7 | `restecg` | categorical | kategori | 0.0, 1.0, 2.0 | `cad_resting_ecg` | `cad_restecg_strfloat` |
| 8 | `thalach` | numeric | atım/dk | 20 – 260 | `cad_max_hr_bpm` | `identity` |
| 9 | `exang` | categorical | kategori | 0.0, 1.0 | `cad_exercise_angina` | `cad_exang_strfloat` |
| 10 | `oldpeak` | numeric | mm | -10 – 20 | `cad_st_depression_mm` | `identity` |
| 11 | `slope` | categorical | kategori | 1.0, 2.0, 3.0 | `cad_st_slope` | `cad_slope_strfloat` |

Sıra ve kategoriler: `Strong_Model_External_Validation_Phase26/frozen_model_manifest.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| fit | 181 | 83 | `models/cad/DEVICE.json (n 303, pozitif 139; validation ve test 28'er pozitif)` |
| validation (eşik seçimi) | 61 | 28 | `models/cad/DEVICE.json > validation` |
| iç test | 61 | 28 | `phase_xxvii/results/ci_metrics.csv` |
| teknik tekrar Hungarian | 95 | 68 | `phase_xli/results/cad_v2_rescore.json` |
| teknik tekrar VA | 64 | 54 | aynı |

Küçük örneklem (test n = 61); GA geniş. Örneklem büyüklüğü hesabı BULUNAMADI.

## 7. Eksik veri [11]

- **Geliştirme:** Cleveland'da eksik 0. Eğitim fold'u içi imputasyon tanımlı; çıkarımda zorunlu girdi eksikse ABSTAIN. Teknik tekrar eksiksiz-vaka alt kümesidir (pozitif olmayan yaş/KB/kolesterol/kalp hızı eksik sayıldı).
- **Uygulama (registry kuralı):** ZORUNLU: 11 feature. Herhangi biri eksikse tahmin üretilmez (model manifesti: "inference abstains on any missing required input"). Kategori string-float biçimine dönüştürülemiyorsa tahmin yok.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Satır (kişi) düzeyi tabakalı rastgele bölme: önce %20 test, kalanın %25'i validation (181/61/61); `src/training/train.py`, `random_state = SEED` (model meta verisinde seed 42). Zamansal değil.

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** Kök V2 eğitim kodu (`src/training/train.py`): aileler × stratejiler için fit kümesinde 3-fold GridSearchCV (amaç AP); her aday ham ve sigmoid-OOF olarak validation'da değerlendirildi. Sıralama: P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 sağlanıyorsa en yüksek validation AP, sağlanmıyorsa en yüksek F1; eşitlikte düşük Brier. Seçilen: LR (C = 0,1), strateji baseline, sigmoid-OOF (`models/cad/DEVICE.json`).
- **Sınıf dengesizliği:** Yok (baseline).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.5401802970** (`Strong_Model_External_Validation_Phase26/frozen_model_manifest.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)
- Seçim kuralı (kaynak): **Bu fazda bulundu:** kök V2 `src/evaluation/metrics.py :: choose_threshold` — validation'da P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 sağlayan noktalar arasında en yüksek F1; yoksa tüm noktalarda en yüksek F1. Registry eşiği 0,5402 `results/cad_DEVICE_validation_thresholds.csv`'de bu kuralın seçtiği satırla aynıdır (feasible = true).
- İkincil eşikler (yalnız raporlama): yok

## 11. Kalibrasyon [12e]

- Registry: sigmoid_oof (Platt; yine de klinik olasılık DEĞİL).
- Sigmoid (Platt), eğitim OOF; klinik olasılık değildir.

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — UCI Cleveland (önceden açılmış) | 61 (28) | 23 / 3 / 30 / 5 | 0,885 [0,710–0,960] | 0,821 [0,644–0,921] | 0,091 [0,031–0,236] | 0,857 [0,706–0,937] | 0,948 [0,888–0,990] | evet |

#### Teknik tekrar (bağımsız dış doğrulama DEĞİL)

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Teknik tekrar — UCI Hungarian (eksiksiz vaka, seçilmiş) | 95 (68) | 60 / 10 / 17 / 8 | 0,857 [0,757–0,921] | 0,882 [0,785–0,939] | 0,370 [0,215–0,558] | 0,680 [0,484–0,828] | 0,852 [0,766–0,928] | hayır |
| Teknik tekrar — UCI VA Long Beach (eksiksiz vaka, seçilmiş) | 64 (54) | 54 / 7 / 3 / 0 | 0,885 [0,782–0,943] | 1,000 [0,934–1,000] | 0,700 [0,397–0,892] | 1,000 [0,439–1,000] | 0,667 [0,437–0,859] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xli/results/cad_v2_rescore.json` (SHA256 `42d892124edc…`); `phase_xxvii/results/ci_metrics.csv` (SHA256 `87e6cc9bcee1…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil; n=61). Düzeltilmiş dış tekrarlarda FPR 0,37–0,70 (hedef yok).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — UCI Cleveland (önceden açılmış) | model − LR(age, sex) | 0,695 | 0,253 [0,147–0,382] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` |
| İç test — UCI Cleveland (önceden açılmış) | model − Tek değişken: thalach (− yön; fit AUC=0.282) | 0,775 | 0,173 [0,072–0,290] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` |
| Teknik tekrar — UCI Hungarian (eksiksiz vaka, seçilmiş) | model − LR(yaş, cinsiyet) | 0,662 | 0,190 [0,072–0,315] | KATKI_VAR | `phase_xli/results/cad_v2_rescore.json` |
| Teknik tekrar — UCI VA Long Beach (eksiksiz vaka, seçilmiş) | model − LR(yaş, cinsiyet) | 0,612 | 0,055 [-0,164–0,288] | KANIT_YETERSIZ | `phase_xli/results/cad_v2_rescore.json` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

İç testte alt grup analizi yok (n = 61; BULUNAMADI). Merkez bazında teknik tekrar sonuçları performans tablosundadır.

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- Kategorik girdiler string-float biçiminde olmalı ('1.0'); '1' biçimi sessizce bilinmeyen sayılır ve one-hot sıfırlanır (V2 kodlama hatası, ERRATA_CAD_V2.md). Uygulama dönüşüm tablosunu birebir uygulamalı.
- İç test n=61 (28 pozitif): geniş GA. Düzeltilmiş dış tekrar seçilmiş eksiksiz-vaka alt kümesi (Hungarian 95, VA 64; negatif 27 ve 10).
- Girdiler efor testi ve EKG gerektirir; genel popülasyon taraması için uygun değil. Hedef anjiyografik darlık (klinik semptom/risk değil).
- BASIC/LAB panelleri yeniden skorlanmadı ve bu kayda alınmadı. Doğrulanmış tek düzeltilmiş kanıt: phase_xli DEVICE teknik tekrarı.
- Eğitim verisinde kişi kimliği yok (satır = kişi varsayımı).
- V2 dış sonuçları kategori kodlama hatası nedeniyle geçersizdi; yalnız Phase XLI düzeltilmiş teknik tekrar geçerlidir (ERRATA_CAD_V2).

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `clinical_mode` — efor testi/EKG girdisi; klinik ortamda girilir. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Efor testi sonuçları ve istirahat EKG'si olan klinik girdi gerekir; kendi beyanıyla doldurulamaz.
- **Kurallar:** Klinik mod (`clinical_mode`). NOT_APPLICABLE: yaş 20–100 dışı. ABSTAIN: 11 zorunlu alandan (göğüs ağrısı tipi, istirahat KB, kolesterol, açlık glukozu > 120, istirahat EKG, maks. kalp hızı, efor anjinası, ST depresyonu, ST eğimi, yaş, cinsiyet) biri eksik veya şema dışı kategori.
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

- `models/cad/DEVICE.json`
- `results/cad_results.json`
- `src/evaluation/metrics.py`
- `phase_xxvii/02_baselines.md`
- `phase_xli/01_cad_rescore.md`
- `phase_xlii/ERRATA_CAD_V2.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 23, kısmen 20, yok 8, uygulanamaz 1. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
