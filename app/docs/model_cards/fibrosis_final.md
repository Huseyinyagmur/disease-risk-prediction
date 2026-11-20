# Model kartı — Karaciğer fibrozisi (LSM ≥ 8 kPa) (`fibrosis_final`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

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

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| geliştirme (P) | 6826 | 697 | `phase_xxxi/results/fib_dev_summary.json (prevalans 0,1021)` |
| iç test (L) | 4714 | 587 | `phase_xxxi/results/fibrosis_test_results.csv` |

Örneklem büyüklüğü hesabı BULUNAMADI.

## 7. Eksik veri [11]

- **Geliştirme:** Uygunluk ölçütü gereği FIB-4/NFS girdileri tam; diğer girdiler pipeline içi imputasyon. Uygulamada imputasyon yok.
- **Uygulama (registry kuralı):** ZORUNLU: 17 feature. Dondurulmuş imputer kullanılmaz. Diyabet durumu (told/insulin/pills) yanıtlanmamışsa tahmin yok.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Döngü bazlı (P geliştirme, L test); kişi düzeyi ayrık (SEQN kesişimi 0). Zamansal sıralı ama test önceden başka hedefte kullanılmış.

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** `phase_xxxi/config/cv_protocol_v2.md`: konfigürasyon (Optuna, iç 3-fold, amaç PR-AUC) tüm geliştirme verisinde bir kez seçilir; sabit konfigürasyonla dış 5-fold CV; eşik havuzlu OOF'tan; fold–havuz AUC farkı > 0,02 ise uyarı. Adaylar LR, LightGBM, XGBoost, CatBoost → CatBoost (strateji none).
- **Sınıf dengesizliği:** Seçilen ailede yok (none).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.0614969601** (`phase_xxxi/config/fibrosis_model_lock.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: Recall>=0.85_max_esik
- Seçim kuralı (kaynak): Birincil: havuzlu OOF'ta Recall ≥ 0,85 sağlayan en yüksek eşik (0,0615); testte Recall 0,768 (hedef korunmadı). İkincil (kilitli, raporlama): cinsiyete özgü eşikler; geliştirmede FIB-4 ≥ 1,3 Recall'una eşlenmiş eşik.
- İkincil eşikler (yalnız raporlama): female_secondary = 0.0635, male_secondary = 0.0583, fib4_matched_secondary = 0.2661

## 11. Kalibrasyon [12e]

- Registry: yok (ham skor).
- Uygulanmadı (ham skor).

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

## 14. Alt gruplar [14, 23a, 23b]

Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.

| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |
|---|---|---|---|---|---|---|
| Duyarlılık: LSM≥12 (aynı model/eşik) | 4714 (217) | 190 / 1691 / 2806 / 27 | 0,101 [0,088–0,115] | 0,876 [0,825–0,913] | 0,376 [0,362–0,390] | 0,851 |
| Duyarlılık: açlık alt örneklemi | 2471 (280) | 215 / 768 / 1423 / 65 | 0,219 [0,194–0,246] | 0,768 [0,715–0,813] | 0,351 [0,331–0,371] | 0,789 |
| female: birincil tek eşik | 2564 (282) | 216 / 657 / 1625 / 66 | 0,247 [0,220–0,277] | 0,766 [0,713–0,812] | 0,288 [0,270–0,307] | 0,804 |
| male: birincil tek eşik | 2150 (305) | 235 / 773 / 1072 / 70 | 0,233 [0,208–0,260] | 0,770 [0,720–0,814] | 0,419 [0,397–0,442] | 0,777 |

Kaynak: `phase_xxxi/results/fibrosis_test_results.csv`. Oran GA'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı (sayımlar yoksa kaynak dosyadaki değer).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

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

- `phase_xxxi/PHASE_XXXI_REPORT.md`
- `phase_xxxi/03_fibrosis_dev.md`
- `phase_xxxi/04_fibrosis_test.md`
- `phase_xxxi/config/protocol_fibrosis.md`
- `phase_xlvi/01_reference_score_analysis.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 24, kısmen 17, yok 8, uygulanamaz 3. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
