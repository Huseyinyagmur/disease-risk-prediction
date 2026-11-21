---
id: mc_osteo_final
title: Model kartı — Osteoporoz (DXA femur T-skoru ≤ −2,5) (`osteo_final`)
source_ref: app/docs/model_cards/osteo_final.md
card_sha256: 5bd4f29bbb487ee798f06976b3c716dc2efe2bbe54dfcd138c0d339f956d20b9
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Model kartı — Osteoporoz (DXA femur T-skoru ≤ −2,5) (`osteo_final`)

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `osteo_final` (primary) |
| hastalık / hedef | Osteoporoz (DXA femur T-skoru ≤ −2,5) |
| uygulamadaki durum | araştırma modülü; mod `standard`; `app_visible = true` |
| model ailesi | Lojistik regresyon (imblearn Pipeline; strateji yok) |
| en yüksek kanıt düzeyi | zamansal test (NHANES J 2017–18; DXA etiketi ilk kez) — bağımsız kurum doğrulaması DEĞİL |
| model dosyası | `phase_xxx/models/osteo_final.joblib` (SHA256 `2c31bd8770b59975…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.6.0; kayıtlı venv `.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxx (kilitli; klinik fayda phase_xxxi) |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

≥ 50 yaşta DXA femur T-skoru ≤ −2,5 (osteoporoz) olup olmadığını DXA'sız girdilerle sıralar; DXA'ya yönlendirme araştırması.

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): D 2005–06, E 2007–08, F 2009–10, H 2013–14 (DXXFEM) | genel nüfus |
| zamansal test | NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ (döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında): J 2017–18 | DXA etiketi projede ilk kez |

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.
- **Popülasyon (registry):** NHANES ≥ 50 yaş, geçerli femur DXA; erkek ve kadın (kadın referansla). Osteoporoz prevalansı %7 civarı.
- **Uygunluk (kaynak):** Yaş ≥ 50, DXA taranmış, geçerli femur boynu ve total femur ölçümü, kilo/boy tam (`phase_xxx/00_data_inventory.md` §3).
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** DXA ile min(femur boynu, total femur) T-skoru ≤ −2,5 (NHANES III 20–29 yaş beyaz kadın referansı) olması (mevcut durum; DXA girdi DEĞİL).
- **Ölçüm:** min(femur boynu, total femur) T ≤ −2,5; T = (BMD − μ)/σ, NHANES III 20–29 yaş Hispanik olmayan beyaz kadın referansı (erkekte de). DXA cihaz ölçümü.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 50 – 80 | `age_years` | `age_cap80` |
| 2 | `sex` | categorical | kategori | female, male | `sex` | `sex_str` |
| 3 | `weight` | numeric | kg | 25 – 300 | `weight_kg` | `identity` |
| 4 | `height` | numeric | cm | 100 – 230 | `height_cm` | `identity` |
| 5 | `bmi` | numeric | kg/m2 | 12 – 80 | `height_cm+weight_kg` | `bmi_kgm2_r1 (v1: bmi_kgm2)` |
| 6 | `smoker_current` | categorical | kategori | no, yes | `smoking_status` | `smoker_yesno` |
| 7 | `alcohol_3plus` | categorical | kategori | no, yes | `alcohol_drinks_per_day` | `alcohol_ge3_yesno` |
| 8 | `glucocorticoid` | categorical | kategori | no, yes | `glucocorticoid_ge1month` | `bool_yesno` |
| 9 | `fx_hip` | categorical | kategori | no, yes | `fracture_hip` | `bool_yesno` |
| 10 | `fx_wrist` | categorical | kategori | no, yes | `fracture_wrist` | `bool_yesno` |
| 11 | `fx_spine` | categorical | kategori | no, yes | `fracture_spine` | `bool_yesno` |
| 12 | `fx_after20` | categorical | kategori | no, yes | `fracture_after_age20` | `bool_yesno` |
| 13 | `parent_hip_fx` | categorical | kategori | no, yes | `parent_hip_fracture` | `bool_yesno` |
| 14 | `no_period_12m` | categorical | kategori | na_male, no, yes | `sex+menses_absent_12m` | `osteo_period_yesno` |
| 15 | `age_last_period` | numeric | yıl | 10 – 70 | `age_last_period_years` | `osteo_age_last_period` |
| 16 | `hrt_ever` | categorical | kategori | na_male, no, yes | `sex+hrt_ever` | `osteo_hrt` |

Sıra ve kategoriler: `phase_xxx/config/osteo_model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 7. Eksik veri [11]

- **Geliştirme:** Yapısal boşluklar (erkekte menopoz soruları) eğitimdeki imputasyon kuralıyla; kullanıcı yanıtsızsa ABSTAIN.
- **Uygulama (registry kuralı):** ZORUNLU: 16 feature. Kadında no_period_12m/hrt_ever yanıtı zorunlu; erkekte 'na_male' otomatik. age_last_period: yalnız adeti kesilmiş kadında zorunlu, diğerlerinde yapısal boş. Yaş < 50 → model uygulanmaz.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### Zamansal doğrulama

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| Zamansal test — NHANES J 2017–18 | 2275 (164) | 128 / 486 / 1625 / 36 | 0,208 [0,178–0,242] | 0,780 [0,711–0,837] | 0,230 [0,213–0,249] | 0,978 [0,970–0,984] | 0,849 [0,818–0,880] | hayır |
| Zamansal test — kadın | 1082 (133) | 113 / 368 / 581 / 20 | 0,235 [0,199–0,275] | 0,850 [0,779–0,900] | 0,388 [0,357–0,419] | 0,967 [0,949–0,978] | 0,816 [0,776–0,854] | hayır |
| Zamansal test — erkek | 1193 (31) | 15 / 118 / 1044 / 16 | 0,113 [0,070–0,178] | 0,484 [0,320–0,652] | 0,102 [0,085–0,120] | 0,985 [0,976–0,991] | 0,817 [0,734–0,883] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxx/results/osteo_test_results.csv` (SHA256 `186c84e49e83…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı. NPV ve GA'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Üçlü hedef (ve tarama hedefi Recall ≥ 0,85) sağlanmadı; eşik Recall ≥ 0,85 için seçilmişti, testte 0,780.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| Zamansal test — NHANES J 2017–18 | model − (−OST) | 0,824 | 0,025 [0,012–0,038] |  | `phase_xxx/results/osteo_test_results.csv` |
| Zamansal test — kadın | model − (−OST) | 0,801 | 0,015 [0,002–0,029] |  | `phase_xxx/results/osteo_test_results.csv` |
| Zamansal test — erkek | model − (−OST) | 0,802 | 0,015 [-0,008–0,044] |  | `phase_xxx/results/osteo_test_results.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 15. Sınırlılıklar [26]

- Cinsiyetler arası Recall çok farklı: erkeklerde 0,48 (tek eşik). Cinsiyete özgü eşik yok.
- Düşük P (0,21; prevalans düşük). CV havuzlu OOF OST'yi geçemedi; testte OST'ye göre ΔAUC +0,025 (küçük ama anlamlı). Phase XXXI: eşit Recall'da yönlendirme farkları GA 0'ı içeriyor.
- DXA cihaz/yazılım çapraz kalibrasyonu BULUNAMADI (yalnız-H duyarlılık modeli benzer sonuç). Romatoid artrit/ikincil osteoporoz girdisi BULUNAMADI. Kadın OST eşiği ikincil kaynaktan.
- Alkol harmonizasyonu (D–H: ALQ120Q/U×ALQ130; J: ALQ121×ALQ130) sabit tabloyla; uygulamada alkol ≥3 içki/gün sorusu doğrudan sorulmalı.
- Hedef osteoporoz DXA tanımıdır, kırık riski değil. KNHANES doğrulaması yapılamadı (steroid ve ebeveyn kalça kırığı girdisi yok).
- OST karşılaştırması ve OST'nin özgün popülasyonu (postmenopozal Asyalı kadınlar): 01_reference_score_analysis.md.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `standard` — kullanıcı formu / laboratuvar girdisi. Modül etiketi: araştırma modülü.
- **Uygulanabilirlik:** Formla doldurulabilir (laboratuvarsız). Yaş 50–80 ve cinsiyete özgü sorular gerekir.
- **Kurallar:** NOT_APPLICABLE: yaş < 50. ABSTAIN: yaş veya 16 alandan biri eksik. Erkekte menopoz soruları yapısal boşluktur (eğitimdeki `na_male` kuralı; eksik sayılmaz).
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.
