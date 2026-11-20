# Model kartı — Anemi (`anemia_LR16`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `anemia_LR16` (primary) |
| hastalık / hedef | Anemi |
| uygulamadaki durum | deneysel; mod `standard`; `app_visible = true` |
| model ailesi | Lojistik regresyon + sigmoid kalibrasyon (CalibratedResearchModel) |
| en yüksek kanıt düzeyi | dış doğrulama (NHANES farklı döngüler; aynı anket programı, PREVIOUSLY_EXPOSED başka hedef) — bağımsız kurum doğrulaması DEĞİL |
| model dosyası | `Clinical_Optimization_Phase25/models/anemia_CBC_MATCHED16.joblib` (SHA256 `369bb07c766df54d…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | Clinical_Optimization_Phase25 (CBC_MATCHED16); dış doğrulama phase_xl |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

Uygun erişkinde düşük hemoglobini (erkek 20–65 Hb < 13; gebe olmayan kadın 20–44 Hb < 12 g/dL) Hb/Hct/MCH/MCHC kullanmadan hemogram ve biyokimyayla sınıflar. Demir eksikliği anemisi tanısı değildir.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): D 2005–06 (1.962 kişi, önceki geliştirme) + A 1999–2000 | genel nüfus |
| iç test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): A 1999–2000 holdout | önceden açılmış |
| dış (aynı program) | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): C 2003–04, E 2007–08, F 2009–10, I 2015–16 | bağımsız kurum değil; PREVIOUSLY_EXPOSED (başka hedef) |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD genel nüfus örneklemi (NHANES).
- **Popülasyon (registry):** NHANES erkek 20–65, kadın 20–44 (gebe değil, RIDEXPRG=2). Hb, MCH, MCHC, hematokrit girdi değil.
- **Uygunluk (kaynak):** Erkek 20–65, kadın 20–44 ve RIDEXPRG = 2 (gebe olmadığı doğrulanmış); gebeliği bilinmeyenler dışlandı.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** Uygun yetişkinlerde düşük hemoglobin: erkek 20–65 yaş Hb < 13 g/dL; kadın 20–44 yaş, gebe olmadığı doğrulanmış, Hb < 12 g/dL (demir eksikliği anemisi DEĞİL).
- **Ölçüm:** Laboratuvar Hb eşiği; yükseklik/sigara düzeltmesi yok.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 20 – 65 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r2 (v1: bmi_kgm2)` |
| 4 | `waist` | numeric | cm | 40 – 200 | `waist_cm` | `identity` |
| 5 | `smoker` | categorical | kategori | no, yes | `smoking_status` | `smoker_yesno` |
| 6 | `hba1c` | numeric | % | 3.0 – 18.0 | `hba1c_pct` | `identity` |
| 7 | `alt` | numeric | U/L | 3 – 1000 | `alt_ul` | `identity` |
| 8 | `ast` | numeric | U/L | 3 – 1000 | `ast_ul` | `identity` |
| 9 | `tc` | numeric | mg/dL | 50 – 600 | `total_chol_mgdl` | `identity` |
| 10 | `hdl` | numeric | mg/dL | 5 – 200 | `hdl_mgdl` | `identity` |
| 11 | `creatinine` | numeric | mg/dL | 0.2 – 15 | `creatinine_mgdl` | `identity` |
| 12 | `wbc` | numeric | 10^3/µL | 0.5 – 100 | `wbc_k_ul` | `identity` |
| 13 | `rbc` | numeric | 10^6/µL | 1.0 – 9.0 | `rbc_m_ul` | `identity` |
| 14 | `mcv` | numeric | fL | 50 – 140 | `mcv_fl` | `identity` |
| 15 | `rdw` | numeric | % | 8 – 35 | `rdw_pct` | `identity` |
| 16 | `albumin` | numeric | g/dL | 1.0 – 6.5 | `albumin_gdl` | `identity` |

Sıra ve kategoriler: `Strong_Model_External_Validation_Phase26/frozen_model_manifest.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| fit (D + A) | 3298 | 143 | `Clinical_Optimization_Phase25/00_MASTER_RESULTS.md §5` |
| validation (A) | 444 | 27 | aynı |
| iç test (A) | 410 | 21 | aynı |
| dış birleşik (C, E, F, I) | 11171 | 669 | `phase_xl/results/anemia_external.json` |

Örneklem büyüklüğü hesabı BULUNAMADI; iç test pozitif sayısı 21.

## 7. Eksik veri [11]

- **Geliştirme:** Fit içi imputasyon (Phase26 manifestinde kısmi eksikte dondurulmuş imputer); uygulamada katı kural: eksikse ABSTAIN.
- **Uygulama (registry kuralı):** ZORUNLU: 16 feature. Hb ölçülmüşse model yerine Hb eşiği kullanılmalı. Kadın için gebelik dışlanamıyorsa (ve yaş 20–44 dışındaysa) uygulanmaz. Dondurulmuş imputer kullanılmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi; A döngüsü içinde fit/validation/test; dış: farklı döngüler.

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** Phase25 protokolü (`development_protocol.json`): 3-fold StratifiedGroupKFold; fold içi ön işleme. LR16 "eş şemalı" karşılaştırma modeli testten önce ayrıca kaydedildi (önceden tanımlı ikincil; Phase26'da dış birincil).
- **Sınıf dengesizliği:** Yok (baseline).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.2703008990** (`Strong_Model_External_Validation_Phase26/frozen_model_manifest.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)
- Seçim kuralı (kaynak): **Bu fazda bulundu:** Phase25 kuralı (`development_protocol.json > threshold`): validation'da P ≥ 0,70, FPR ≤ 0,15, TP ≥ 5 içinde en yüksek Recall; yoksa F2 − 0,5·FPR + 0,25·P. Registry eşiği (0,2703) `anemia_CBC_MATCHED16.json` BALANCED senaryo eşiğiyle aynıdır.
- İkincil eşikler (yalnız raporlama): yok

## 11. Kalibrasyon [12e]

- Registry: sigmoid (OOF Platt; klinik olasılık DEĞİL).
- Sigmoid (fit 3-fold OOF); klinik olasılık değildir.

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — NHANES A 1999–2000 (Phase25 holdout; önceden açılmış) | 410 (21) | 17 / 4 / 385 / 4 | 0,810 [0,600–0,923] | 0,810 [0,600–0,923] | 0,010 [0,004–0,026] | 0,990 [0,974–0,996] | 0,991 [0,980–0,999] | evet |

#### Farklı NHANES döngüleri — aynı program (bağımsız kurum doğrulaması DEĞİL)

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C, E, F, I birleşik | 11171 (669) | 591 / 242 / 10260 / 78 | 0,709 [0,678–0,739] | 0,883 [0,857–0,906] | 0,023 [0,020–0,026] | 0,992 [0,991–0,994] | 0,991 [0,989–0,993] | evet |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C 2003–04 | 2265 (89) | 82 / 25 / 2151 / 7 | 0,766 [0,678–0,836] | 0,921 [0,846–0,961] | 0,011 [0,008–0,017] | 0,997 [0,993–0,998] | 0,995 [0,991–0,998] | evet |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES E 2007–08 | 2881 (156) | 149 / 85 / 2640 / 7 | 0,637 [0,573–0,696] | 0,955 [0,910–0,978] | 0,031 [0,025–0,038] | 0,997 [0,995–0,999] | 0,994 [0,992–0,996] | hayır |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES F 2009–10 | 3188 (183) | 165 / 102 / 2903 / 18 | 0,618 [0,558–0,674] | 0,902 [0,850–0,937] | 0,034 [0,028–0,041] | 0,994 [0,990–0,996] | 0,993 [0,989–0,995] | hayır |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES I 2015–16 | 2837 (241) | 195 / 30 / 2566 / 46 | 0,867 [0,816–0,905] | 0,809 [0,755–0,854] | 0,012 [0,008–0,016] | 0,982 [0,977–0,987] | 0,991 [0,987–0,994] | evet |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xl/results/anemia_external.json` (SHA256 `3b7944c1880e…`); `phase_xxvii/results/ci_metrics.csv` (SHA256 `87e6cc9bcee1…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil). Dış: P hedefte C/I'da (0,77/0,87), E/F'de altında (0,64/0,62); Recall ≥ 0,75 ve FPR ≤ 0,15 tüm döngülerde sağlandı.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — NHANES A 1999–2000 (Phase25 holdout; önceden açılmış) | model − Hct_proxy=RBC×MCV/10 sabit (E<39, K<36) | 0,990 | 0,002 [-0,003–0,008] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C, E, F, I birleşik | model − Hct_proxy kuralı | 0,988 | 0,004 [0,002–0,005] | KATKI_VAR | `phase_xl/results/anemia_external.json` |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C 2003–04 | model − Hct_proxy kuralı | 0,994 | 0,001 [-0,001–0,003] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES E 2007–08 | model − Hct_proxy kuralı | 0,992 | 0,002 [-0,000–0,004] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES F 2009–10 | model − Hct_proxy kuralı | 0,990 | 0,003 [0,000–0,006] | KATKI_VAR | `phase_xl/results/anemia_external.json` |
| Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES I 2015–16 | model − Hct_proxy kuralı | 0,990 | 0,001 [-0,002–0,004] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.

| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |
|---|---|---|---|---|---|---|
| sex_male | 278 (8) | 6 / 2 / 268 / 2 | 0,750 [0,409–0,929] | 0,750 [0,409–0,929] | 0,007 [0,002–0,027] | 0,994 |
| sex_female | 132 (13) | 11 / 2 / 117 / 2 | 0,846 [0,578–0,957] | 0,846 [0,578–0,957] | 0,017 [0,005–0,059] | 0,985 |
| dış: döngü başına | — | — | — | — | — | performans tablosu |

Kaynak: `Clinical_Optimization_Phase25/results/anemia_subgroup_metrics.csv`. Oran GA'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı (sayımlar yoksa kaynak dosyadaki değer).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- ML katkısı pratikte YOK: Hct_proxy = RBC×MCV/10 kuralına göre ΔAUC +0,002…+0,004 (eşdeğer). Model Hb'yi aynı hemogramdan yeniden hesaplıyor (Hb varyansının R²=0,943'ü RBC ve MCV ile açıklanıyor).
- İç test küçük (21 pozitif). Dış test aynı anket programı; E/F döngülerinde Precision hedefin altında.
- Etiyoloji yok (demir eksikliği vb.); yükseklik/sigara Hb düzeltmesi yok. Gebelik durumu bilinmeyen kadın uygun değil.
- Kreatinin standardize ölçek (E-2007 CDC düzeltmesi yayımlanmış dosyada uygulanmış); I döngüsü CBC yöntemi (DxH 800) Phase XL'de belgelenmiş, diğer yöntem farkları sınırlılık.
- Anemi için doğrudan Hb ölçümü varken bu modelin klinik katkısı yoktur; uygulama değeri "Hb yokken CBC ile tarama" ile sınırlı.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: deneysel.
- **Uygulanabilirlik:** Tam kan sayımı + biyokimya sonuçları gerekir; 16 alan.
- **Kurallar:** NOT_APPLICABLE: erkek 20–65 dışı, kadın 20–44 dışı, gebe. ABSTAIN: yaş, cinsiyet, gebelik (kadın 20–44) yanıtsız veya 16 alandan biri eksik. Hemoglobin girilirse TARGET_DEFINING_INPUT uyarısı.
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

- `Clinical_Optimization_Phase25/00_MASTER_RESULTS.md`
- `Clinical_Optimization_Phase25/development_protocol.json`
- `Clinical_Optimization_Phase25/models/anemia_CBC_MATCHED16.json`
- `phase_xl/02_anemia_external.md`
- `phase_xxvii/02_baselines.md`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 25, kısmen 18, yok 6, uygulanamaz 3. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
