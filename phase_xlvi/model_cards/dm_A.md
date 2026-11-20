# Model kartı — Diyabet (teşhis edilmemiş) (`dm_A`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `dm_A` (primary) |
| hastalık / hedef | Diyabet (teşhis edilmemiş) |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | Lojistik regresyon (class_weight; imputer+scaler+LR) |
| en yüksek kanıt düzeyi | iç test (NHANES içi; zamansal değil; PREVIOUSLY_EXPOSED_PERSONS başka hedef; diyabet hedefinde yeni kişiler) |
| model dosyası | `phase_xlii/models/dm_A_final.joblib` (SHA256 `669e780c484f558e…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xlii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Diyabet tanısı olmayan erişkinde tek ziyaret ölçümüyle teşhis edilmemiş diyabet (HbA1c ≥ %6,5 veya açlıkta FPG ≥ 126) olup olmadığını laboratuvarsız girdilerle sıralar. Tarama sıralayıcısıdır; ADA tanısı (doğrulama testi) değildir.

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
- **Popülasyon (registry):** NHANES ≥20 yaş, gebe değil, diyabet tanısı/ilacı yok (DIQ010≠1, insülin/hap yok), HbA1c ölçülmüş. Prevalans ≈ %4,4.
- **Uygunluk (kaynak):** Yaş ≥ 20, MEC muayenesi, gebe değil, HbA1c ölçülmüş; hariç: diyabet tanısı (DIQ010 = 1), DIQ010 7/9/eksik, tanısız ama insülin/hap kullanan (`phase_xlii/01_cohort.md`).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Farkında olmayan erişkinde tek ziyaret ölçümüyle HbA1c ≥ 6,5% veya (açlık alt örnekleminde) FPG ≥ 126 mg/dL olması (teşhis edilmemiş diyabet; mevcut durum).
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

Sıra ve kategoriler: `phase_xlii/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| geliştirme (E, F, I, J) | 17950 | 829 | `phase_xlii/01_cohort.md` |
| iç test (G + H) | 8895 | 389 | aynı |

Örneklem büyüklüğü hesabı BULUNAMADI; uygun tüm kişiler.

## 7. Eksik veri [11]

- **Geliştirme:** Geliştirmede BMI %1,1, bel %4,4, KB %3,9, GDM %5,7 eksik; fold içinde medyan imputasyon. Uygulamada imputasyon yok: zorunlu alan eksikse ABSTAIN.
- **Uygulama (registry kuralı):** ZORUNLU: 16 feature (gdm: erkek için otomatik 0). Kadında GDM yanıtı yoksa tahmin yok. Diyabet tanısı/ilacı varsa model uygulanmaz. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN (varsayım yok).
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi, döngü bazlı (G+H test; diğerleri geliştirme). Zamansal değil. Test kişileri diyabet hedefinde yeni, başka hedeflerde görülmüş (PREVIOUSLY_EXPOSED_PERSONS).

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** `phase_xxxi/config/cv_protocol_v2.md`: konfigürasyon (Optuna, iç 3-fold, amaç PR-AUC) tüm geliştirme verisinde bir kez seçilir; sabit konfigürasyonla dış 5-fold CV; eşik havuzlu OOF'tan; fold–havuz AUC farkı > 0,02 ise uyarı. Adaylar LR ve LightGBM; seçim kuralı havuzlu OOF AUC (fark < 0,01 ise LR) → LR (class_weight, C = 0,0422).
- **Sınıf dengesizliği:** class_weight = balanced (skorlar yukarı kaymış; olasılık değildir).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.4958988256** (`phase_xlii/config/model_lock.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: havuzlu OOF Recall>=0.75 sağlayan en yüksek eşik
- Seçim kuralı (kaynak): Birincil: havuzlu OOF'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,4959). İkincil: ADA ≥ 5 geliştirme yönlendirme oranına eşlenen eşik (0,4704).
- İkincil eşikler (yalnız raporlama): referral_matched = 0.4704

## 11. Kalibrasyon [12e]

- Registry: yok (class_weight nedeniyle olasılık şişik; ham skor).
- Uygulanmadı. Testte ort. skor gözlenen oranın çok üstünde (en üst %10: 0,806 → 0,158); sıralama monoton.

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | 8895 (389) | 285 / 2483 / 6023 / 104 | 0,103 [0,092–0,115] | 0,733 [0,687–0,774] | 0,292 [0,282–0,302] | 0,983 [0,979–0,986] | 0,800 [0,781–0,819] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xlii/results/test_operating_points.csv` (SHA256 `5af8d3f2b8f3…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Hiçbir eşikte sağlanmadı (P 0,09–0,12; %4,4 prevalansta yapısal olarak zor). Birincil eşikte Recall ≥ 0,75 testte korunmadı (0,733).

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | A − ADA | 0,758 | 0,042 [0,028–0,055] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` |
| İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | A − yaş+BMI | 0,747 | 0,054 [0,040–0,068] | tür: ikincil | `phase_xlii/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.

| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |
|---|---|---|---|---|---|---|
| yaş: <45 | 4235 (77) | 36 / 360 / 3798 / 41 | 0,091 [0,066–0,123] | 0,468 [0,360–0,578] | 0,087 [0,078–0,096] | 0,852 |
| yaş: >=45 | 4660 (312) | 249 / 2123 / 2225 / 63 | 0,105 [0,093–0,118] | 0,798 [0,750–0,839] | 0,488 [0,473–0,503] | 0,720 |
| ırk: Meksikalı Amerikalı | 1019 (58) | 45 / 354 / 607 / 13 | 0,113 [0,085–0,148] | 0,776 [0,653–0,864] | 0,368 [0,338–0,399] | 0,788 |
| ırk: Diğer Hispanik | 844 (51) | 44 / 264 / 529 / 7 | 0,143 [0,108–0,186] | 0,863 [0,743–0,932] | 0,333 [0,301–0,366] | 0,811 |
| ırk: Hispanik olmayan beyaz | 3698 (109) | 78 / 855 / 2734 / 31 | 0,084 [0,068–0,103] | 0,716 [0,625–0,792] | 0,238 [0,225–0,252] | 0,826 |
| ırk: Hispanik olmayan siyah | 1919 (98) | 75 / 708 / 1113 / 23 | 0,096 [0,077–0,118] | 0,765 [0,672–0,838] | 0,389 [0,367–0,411] | 0,772 |
| ırk: Diğer/çok ırklı | 1415 (73) | 43 / 302 / 1040 / 30 | 0,125 [0,094–0,164] | 0,589 [0,474–0,695] | 0,225 [0,203–0,248] | 0,771 |
| döngü: G | 4288 (204) | 148 / 1186 / 2898 / 56 | 0,111 [0,095–0,129] | 0,725 [0,661–0,782] | 0,290 [0,277–0,305] | 0,802 |
| döngü: H | 4607 (185) | 137 / 1297 / 3125 / 48 | 0,096 [0,081–0,112] | 0,741 [0,673–0,798] | 0,293 [0,280–0,307] | 0,800 |

Kaynak: `phase_xlii/results/test_subgroups.csv`. Oran GA'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı (sayımlar yoksa kaynak dosyadaki değer).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- Tarama sıralayıcısı; P ≈ 0,10: pozitif yönlendirilenlerin ~%10'u gerçekten pozitif. Kişilerin ≈ %1/3'ü yönlendiriliyor. NPV 0,983.
- Etiket tek ziyaret ölçümüdür; ADA doğrulama testi yok. FPG yalnız açlık alt örnekleminde (%45) ölçülmüş.
- Bağımsız (NHANES dışı) dış doğrulama ve zamansal olmayan iç test. ADA skoruna göre ΔAUC +0,042 (küçük).
- Survey ağırlığı/PSU/strata kullanılmadı. ADA fiziksel aktivite maddesi operasyonel; ADA GDM'li güncel formu BULUNAMADI.
- "Diğer/çok ırklı" grupta tüm kurallarda Recall düşük; <45 yaşta Recall 0,47–0,58.
- Model yalnız diyabet TANISI almamış kişi için geçerli; tanılı/ilaç kullananlara uygulanmaz.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Kullanıcı formuyla doldurulabilir (ölçüm gerektiren: boy/kilo/bel/tansiyon).
- **Kurallar:** NOT_APPLICABLE: yaş < 20, gebe, diyabet tanısı, tanısız ama insülin/hap kullanan. ABSTAIN: yaş, cinsiyet, ırk, gebelik (kadın; "bilmiyorum" dahil), diyabet tanısı sorusu yanıtsız veya zorunlu alan eksik (3 tansiyon okuması dahil). HbA1c/açlık glukozu girilirse TARGET_DEFINING_INPUT uyarısı. `dm_B` laboratuvar varsa önce denenir.
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
