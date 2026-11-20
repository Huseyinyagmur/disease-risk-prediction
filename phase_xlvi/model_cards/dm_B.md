# Model kartı — Diyabet (teşhis edilmemiş) — laboratuvarlı (`dm_B`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

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

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| geliştirme (E, F, I, J) | 17950 | 829 | `phase_xlii/01_cohort.md` |
| iç test (G + H) | 8895 | 389 | aynı |

Örneklem büyüklüğü hesabı BULUNAMADI; uygun tüm kişiler.

## 7. Eksik veri [11]

- **Geliştirme:** Geliştirmede BMI %1,1, bel %4,4, KB %3,9, GDM %5,7 eksik; fold içinde medyan imputasyon. Uygulamada imputasyon yok: zorunlu alan eksikse ABSTAIN.
- **Uygulama (registry kuralı):** ZORUNLU: 21 feature. Lab alanlarından biri eksikse B üretilmez; A'ya geri dönülebilir (A kendi kuralını sağlıyorsa). Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi, döngü bazlı (G+H test; diğerleri geliştirme). Zamansal değil. Test kişileri diyabet hedefinde yeni, başka hedeflerde görülmüş (PREVIOUSLY_EXPOSED_PERSONS).

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** `phase_xxxi/config/cv_protocol_v2.md`: konfigürasyon (Optuna, iç 3-fold, amaç PR-AUC) tüm geliştirme verisinde bir kez seçilir; sabit konfigürasyonla dış 5-fold CV; eşik havuzlu OOF'tan; fold–havuz AUC farkı > 0,02 ise uyarı. Adaylar LR ve LightGBM → LR (class_weight, C = 0,0696).
- **Sınıf dengesizliği:** class_weight = balanced (skorlar yukarı kaymış; olasılık değildir).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.5314872247** (`phase_xlii/config/model_lock.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: havuzlu OOF Recall>=0.75 sağlayan en yüksek eşik
- Seçim kuralı (kaynak): Birincil: havuzlu OOF'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,5315). İkincil: ADA-eşleşmeli (0,4549).
- İkincil eşikler (yalnız raporlama): referral_matched = 0.4549

## 11. Kalibrasyon [12e]

- Registry: yok (ham skor).
- Uygulanmadı. Testte ort. skor gözlenen oranın çok üstünde (en üst %10: 0,806 → 0,158); sıralama monoton.

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

## 14. Alt gruplar [14, 23a, 23b]

Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.

| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |
|---|---|---|---|---|---|---|
| yaş: <45 | 4235 (77) | 45 / 273 / 3885 / 32 | 0,142 [0,107–0,184] | 0,584 [0,473–0,688] | 0,066 [0,059–0,074] | 0,897 |
| yaş: >=45 | 4660 (312) | 233 / 1730 / 2618 / 79 | 0,119 [0,105–0,134] | 0,747 [0,696–0,792] | 0,398 [0,383–0,413] | 0,743 |
| ırk: Meksikalı Amerikalı | 1019 (58) | 48 / 258 / 703 / 10 | 0,157 [0,120–0,202] | 0,828 [0,711–0,904] | 0,268 [0,241–0,297] | 0,850 |
| ırk: Diğer Hispanik | 844 (51) | 36 / 232 / 561 / 15 | 0,134 [0,099–0,180] | 0,706 [0,570–0,813] | 0,293 [0,262–0,325] | 0,815 |
| ırk: Hispanik olmayan beyaz | 3698 (109) | 78 / 677 / 2912 / 31 | 0,103 [0,084–0,127] | 0,716 [0,625–0,792] | 0,189 [0,176–0,202] | 0,851 |
| ırk: Hispanik olmayan siyah | 1919 (98) | 70 / 582 / 1239 / 28 | 0,107 [0,086–0,133] | 0,714 [0,618–0,794] | 0,320 [0,299–0,341] | 0,784 |
| ırk: Diğer/çok ırklı | 1415 (73) | 46 / 254 / 1088 / 27 | 0,153 [0,117–0,198] | 0,630 [0,515–0,732] | 0,189 [0,169–0,211] | 0,808 |
| döngü: G | 4288 (204) | 150 / 967 / 3117 / 54 | 0,134 [0,116–0,156] | 0,735 [0,671–0,791] | 0,237 [0,224–0,250] | 0,831 |
| döngü: H | 4607 (185) | 128 / 1036 / 3386 / 57 | 0,110 [0,093–0,129] | 0,692 [0,622–0,754] | 0,234 [0,222–0,247] | 0,819 |

Kaynak: `phase_xlii/results/test_subgroups.csv`. Oran GA'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı (sayımlar yoksa kaynak dosyadaki değer).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

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

- `phase_xlii/PHASE_XLII_REPORT.md`
- `phase_xlii/01_cohort.md`
- `phase_xlii/02_dev_cv.md`
- `phase_xlii/03_test_results.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 24, kısmen 19, yok 6, uygulanamaz 3. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
