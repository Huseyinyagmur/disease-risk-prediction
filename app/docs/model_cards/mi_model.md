# Model kartı — Miyokard enfarktüsü (EKG bulgusu) (`mi_model`)

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `mi_model` (primary) |
| hastalık / hedef | Miyokard enfarktüsü (EKG bulgusu) |
| uygulamadaki durum | uygulamada değil (registry_only); mod `registry_only`; `app_visible = false` |
| model ailesi | LightGBM (sınıf ağırlıklı; imblearn Pipeline) |
| en yüksek kanıt düzeyi | iç test |
| model dosyası | `phase_xxxviii/models/mi_model.joblib` (SHA256 `8ae84fd58d9bafdf…`) |
| çalışma ortamı | Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0; kayıtlı venv `Focused_Current_Disease_Improvement_2026/.venv` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | phase_xxxviii |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

PTB-XL kaydında kardiyoloğun MI (eski/akut, EKG bulgusu) kodlamasının NORM kayıtlardan ayrımı. Troponin veya görüntülemeye dayalı MI tanısı değildir. Yalnız registry'de (uygulamada yok).

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
| geliştirme + iç test | PTB-XL 1.0.3 (PhysioNet), doi:10.13026/kfzx-aw45; Wagner ve ark., Sci Data 2020, doi:10.1038/s41597-020-0495-6; öznitelikler: PTB-XL+ ECGDeli öznitelikleri (PhysioNet PTB-XL+, `ecgdeli_features.csv`; sürüm numarası proje dosyalarında BULUNAMADI) (168 lead bazlı + global) | tek kurum arşivi |

PTB-XL kayıt tarihleri: 1984-11-09 – 2001-06-11 (PTB-XL `recording_date`, tüm veri tabanı; metadata).

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** Hastane EKG arşivi (tek kurum).
- **Popülasyon (registry):** ≥18 yaş, hasta başına ilk doğrulanmış EKG; MI vs NORM (başka anormallikler negatifte yok).
- **Uygunluk (kaynak):** İnsan doğrulamalı kayıtlar; hasta başına ilk doğrulanmış EKG; yaş ≥ 18 (300 → 90); MI süper sınıfı (14 kod, INJ* dahil) vs yalnız NORM; tutarsız hastalar (herhangi bir kaydı MI, seçilen kaydı değil) negatiften dışlandı. AF test kişileri ve parity kişileri testten dışlandı. Kaynak: `phase_xxxviii/01_cohort.md`.
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** PTB-XL'de kardiyoloğun aynı EKG'yi MI (eski veya akut) olarak kodlamasının NORM kayıtlardan ayrımı (kod: MI; hedef = EKG okuması, troponin/görüntüleme değil).
- **Ölçüm:** PTB-XL SCP tanısal süper sınıfı (resmî `example_physionet.py` toplama kuralı; likelihood eşiği yok). Kardiyolog EKG okuması; değerlendirici demografisi BULUNAMADI.
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |
|---|---|---|---|---|---|---|
| 1 | `age` | numeric | yıl | 18 – 90 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 2 | `sex` | categorical | PTB-XL kodu 0=erkek 1=kadın | 0.0, 1.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 3 | `PQ_Int_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 4 | `PQ_Int_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 5 | `PQ_Int_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 6 | `PQ_Int_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 7 | `PQ_Int_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 8 | `PQ_Int_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 9 | `PQ_Int_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 10 | `PQ_Int_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 11 | `PQ_Int_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 12 | `PQ_Int_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 13 | `PQ_Int_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 14 | `PQ_Int_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 15 | `PQ_Int_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 16 | `PR_Int_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 17 | `PR_Int_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 18 | `PR_Int_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 19 | `PR_Int_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 20 | `PR_Int_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 21 | `PR_Int_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 22 | `PR_Int_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 23 | `PR_Int_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 24 | `PR_Int_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 25 | `PR_Int_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 26 | `PR_Int_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 27 | `PR_Int_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 28 | `PR_Int_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 29 | `P_Amp_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 30 | `P_Amp_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 31 | `P_Amp_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 32 | `P_Amp_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 33 | `P_Amp_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 34 | `P_Amp_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 35 | `P_Amp_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 36 | `P_Amp_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 37 | `P_Amp_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 38 | `P_Amp_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 39 | `P_Amp_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 40 | `P_Amp_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 41 | `P_DurFull_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 42 | `P_DurFull_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 43 | `P_DurFull_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 44 | `P_DurFull_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 45 | `P_DurFull_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 46 | `P_DurFull_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 47 | `P_DurFull_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 48 | `P_DurFull_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 49 | `P_DurFull_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 50 | `P_DurFull_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 51 | `P_DurFull_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 52 | `P_DurFull_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 53 | `P_Dur_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 54 | `Q_Amp_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 55 | `Q_Amp_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 56 | `Q_Amp_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 57 | `Q_Amp_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 58 | `Q_Amp_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 59 | `Q_Amp_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 60 | `Q_Amp_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 61 | `Q_Amp_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 62 | `Q_Amp_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 63 | `Q_Amp_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 64 | `Q_Amp_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 65 | `Q_Amp_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 66 | `QRS_Dur_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 67 | `QRS_Dur_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 68 | `QRS_Dur_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 69 | `QRS_Dur_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 70 | `QRS_Dur_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 71 | `QRS_Dur_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 72 | `QRS_Dur_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 73 | `QRS_Dur_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 74 | `QRS_Dur_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 75 | `QRS_Dur_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 76 | `QRS_Dur_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 77 | `QRS_Dur_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 78 | `QRS_Dur_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 79 | `QT_IntCorr_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 80 | `QT_IntCorr_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 81 | `QT_IntCorr_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 82 | `QT_IntCorr_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 83 | `QT_IntCorr_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 84 | `QT_IntCorr_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 85 | `QT_IntCorr_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 86 | `QT_IntCorr_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 87 | `QT_IntCorr_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 88 | `QT_IntCorr_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 89 | `QT_IntCorr_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 90 | `QT_IntCorr_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 91 | `QT_IntFramingham_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 92 | `QT_Int_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 93 | `QT_Int_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 94 | `QT_Int_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 95 | `QT_Int_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 96 | `QT_Int_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 97 | `QT_Int_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 98 | `QT_Int_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 99 | `QT_Int_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 100 | `QT_Int_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 101 | `QT_Int_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 102 | `QT_Int_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 103 | `QT_Int_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 104 | `QT_Int_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 105 | `R_Amp_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 106 | `R_Amp_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 107 | `R_Amp_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 108 | `R_Amp_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 109 | `R_Amp_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 110 | `R_Amp_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 111 | `R_Amp_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 112 | `R_Amp_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 113 | `R_Amp_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 114 | `R_Amp_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 115 | `R_Amp_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 116 | `R_Amp_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 117 | `RR_Mean_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 118 | `S_Amp_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 119 | `S_Amp_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 120 | `S_Amp_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 121 | `S_Amp_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 122 | `S_Amp_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 123 | `S_Amp_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 124 | `S_Amp_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 125 | `S_Amp_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 126 | `S_Amp_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 127 | `S_Amp_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 128 | `S_Amp_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 129 | `S_Amp_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 130 | `ST_Elev_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 131 | `ST_Elev_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 132 | `ST_Elev_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 133 | `ST_Elev_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 134 | `ST_Elev_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 135 | `ST_Elev_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 136 | `ST_Elev_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 137 | `ST_Elev_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 138 | `ST_Elev_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 139 | `ST_Elev_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 140 | `ST_Elev_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 141 | `ST_Elev_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 142 | `T_Amp_I` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 143 | `T_Amp_II` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 144 | `T_Amp_III` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 145 | `T_Amp_V1` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 146 | `T_Amp_V2` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 147 | `T_Amp_V3` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 148 | `T_Amp_V4` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 149 | `T_Amp_V5` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 150 | `T_Amp_V6` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 151 | `T_Amp_aVF` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 152 | `T_Amp_aVL` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 153 | `T_Amp_aVR` | numeric | mV | -10.0 – 10.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 154 | `T_DurFull_I` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 155 | `T_DurFull_II` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 156 | `T_DurFull_III` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 157 | `T_DurFull_V1` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 158 | `T_DurFull_V2` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 159 | `T_DurFull_V3` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 160 | `T_DurFull_V4` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 161 | `T_DurFull_V5` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 162 | `T_DurFull_V6` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 163 | `T_DurFull_aVF` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 164 | `T_DurFull_aVL` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 165 | `T_DurFull_aVR` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 166 | `T_Dur_Global` | numeric | ms | 0.0 – 3000.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 167 | `HA__Global` | categorical | ECGDeli elektriksel aks kategorisi (1–6, string float) | 1.0, 2.0, 3.0, 4.0, 5.0, 6.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |
| 168 | `ST_Elev_missing` | categorical | 0/1 | 0.0, 1.0 | `ecg_ptbxl_ecgdeli_168` | `ptbxl_group` |

Sıra ve kategoriler: `phase_xxxviii/config/model_lock.json` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; CAD'de UCI kodları; KY'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.

## 6. Örnek sayıları [10, 20a, 21]

| küme | n | pozitif | kaynak |
|---|---|---|---|
| geliştirme (fold 1–8) | 7230 | 2037 | `phase_xxxviii/02_dev_cv.md` |
| iç test (fold 9 + fold 10 AF-test dışı) | 1474 | 521 | `phase_xxxviii/03_test_results.md` |
| iç test temiz alt küme | 368 | 160 | aynı |

Örneklem büyüklüğü hesaplanmadı; uygun tüm kayıtlar.

## 7. Eksik veri [11]

- **Geliştirme:** Eksiklik `phase_xxxviii/results/t0_feature_missingness.csv`; `ST_Elev_missing` göstergesi modele girdi olarak eklendi. Eğitimde imblearn pipeline içi imputasyon.
- **Uygulama (registry kuralı):** ZORUNLU: 168 feature. Yalnız PTB-XL+ eğitiminde olduğu gibi ST_Elev ailesi (12 sütun) birlikte NaN ise ve ST_Elev_missing=1 ise kabul; diğer her eksik → tahmin yok.
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

Kişi düzeyi PTB-XL fold'ları: 1–8 geliştirme, 9 + 10 test. Zamansal değil. Test kişilerinin 1.106'sı AF eşik seçiminde kullanıldı (PREVIOUSLY_EXPOSED, başka hedef).

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** `phase_xxxi/config/cv_protocol_v2.md`: konfigürasyon (Optuna, iç 3-fold, amaç PR-AUC) tüm geliştirme verisinde bir kez seçilir; sabit konfigürasyonla dış 5-fold CV; eşik havuzlu OOF'tan; fold–havuz AUC farkı > 0,02 ise uyarı. Adaylar LR ve LightGBM; LightGBM − LR = +0,026 (≥ 0,01) → LightGBM (class_weight).
- **Sınıf dengesizliği:** class_weight (LightGBM).

## 10. Karar eşiği ve seçim kuralı [15]

- Birincil (uygulamada kullanılan) eşik: **0.0442566427** (`phase_xxxviii/config/model_lock.json`); karar `skor ≥ eşik` → "eşik üstü" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.
- Registry kural metni: birincil_P>=0.70_FPR<=0.15_maxR
- Seçim kuralı (kaynak): Birincil: havuzlu OOF'ta P ≥ 0,70 ve FPR ≤ 0,15 içinde en yüksek Recall (kilitli 0,0443). Bu kural eşiği FPR sınırına dayatır (OOF FPR 0,149). İkincil (yalnız rapor): Recall ≥ 0,75 sağlayan en yüksek eşik 0,8634.
- İkincil eşikler (yalnız raporlama): threshold_recall075_reporting_only = 0.8634

## 11. Kalibrasyon [12e]

- Registry: yok (ham skor, class_weight).
- Uygulanmadı (ham skor; class_weight nedeniyle olasılık ölçeği kaymış).

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

#### İç test

| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|
| İç test — tümü (fold 9 + fold 10 AF-test dışı) | 1474 (521) | 491 / 138 / 815 / 30 | 0,781 [0,747–0,811] | 0,942 [0,919–0,959] | 0,145 [0,124–0,169] | 0,964 [0,950–0,975] | 0,973 [0,965–0,980] | evet |
| İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | 368 (160) | 156 / 36 / 172 / 4 | 0,812 [0,751–0,861] | 0,975 [0,937–0,990] | 0,173 [0,128–0,230] | 0,977 [0,943–0,991] | 0,972 [0,958–0,984] | hayır |

Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): `phase_xxxviii/results/test_operating_points.csv` (SHA256 `8843170fae76…`).
Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap'ı.

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: Tüm testte 3 hedef nokta tahminiyle sağlandı (FPR GA üst sınırı 0,169 > 0,15); temiz alt kümede FPR 0,173 (hedef yok). MI dışı anormallikler negatife katılınca FPR 0,396.

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|
| İç test — tümü (fold 9 + fold 10 AF-test dışı) | model − B1 yaş+cinsiyet LR | 0,818 | 0,155 [0,134–0,175] |  | `phase_xxxviii/results/test_delta_auc.csv` |
| İç test — tümü (fold 9 + fold 10 AF-test dışı) | model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz) | — | 0,667 [0,638–0,695] | B2 AUC < 0,5; geçerli kural baseline'ı kurulamadı (Phase XXXVIII 02 §4) | `phase_xxxviii/results/test_delta_auc.csv` |
| İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | model − B1 yaş+cinsiyet LR | 0,823 | 0,149 [0,113–0,190] |  | `phase_xxxviii/results/test_delta_auc.csv` |
| İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz) | — | 0,646 [0,589–0,701] | B2 AUC < 0,5; geçerli kural baseline'ı kurulamadı (Phase XXXVIII 02 §4) | `phase_xxxviii/results/test_delta_auc.csv` |

ΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).

## 14. Alt gruplar [14, 23a, 23b]

Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.

| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |
|---|---|---|---|---|---|---|
| yerlesim_alt | — (212) | — | — | 0,887 [0,837–0,923] | — | — |
| yerlesim_on | — (192) | — | — | 0,984 [0,955–0,995] | — | — |
| yerlesim_yan | — (13) | — | — | 0,769 [0,497–0,918] | — | — |
| yerlesim_arka | — (0) | — | — | — | — | — |
| yerlesim_coklu | — (104) | — | — | 1,000 [0,964–1,000] | — | — |
| INJ_yalniz | — (16) | — | — | 1,000 [0,806–1,000] | — | — |
| yas<65 | 897 (156) | 136 / 79 / 662 / 20 | 0,633 [0,566–0,694] | 0,872 [0,810–0,915] | 0,107 [0,086–0,131] | — |
| yas>=65 | 577 (365) | 355 / 59 / 153 / 10 | 0,857 [0,821–0,888] | 0,973 [0,950–0,985] | 0,278 [0,222–0,342] | — |
| erkek(sex=0) | 759 (293) | 277 / 76 / 390 / 16 | 0,785 [0,739–0,824] | 0,945 [0,913–0,966] | 0,163 [0,132–0,199] | — |
| kadin(sex=1) | 715 (228) | 214 / 62 / 425 / 14 | 0,775 [0,723–0,821] | 0,939 [0,900–0,963] | 0,127 [0,101–0,160] | — |

Kaynak: `phase_xxxviii/results/test_subgroups.csv`. Oran GA'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı (sayımlar yoksa kaynak dosyadaki değer).

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

- Zamansal doğrulama ve bağımsız dış doğrulama YAPILMADI.
- Etiket ve feature aynı EKG'den gelir; yüksek AUC klinik MI tanı doğruluğu anlamına gelmez (troponin/görüntüleme referansı yok; MI çoğunlukla eski/evresi belirsiz).
- MI'ya özgüllük sınırlı: STTC/CD/HYP kayıtları negatife eklenince FPR 0,40–0,50; model büyük ölçüde "anormal EKG" ayırıyor. Yaş ≥ 65'te FPR 0,28.
- Kural baseline'ı (B2) geçersiz çıktı (AUC 0,31); geçerli basit kurala göre ML katkısı ÖLÇÜLEMEDİ. Ölçülebilen katkı yaş+cinsiyete göre +0,155 AUC.
- Eşik FPR sınırında (OOF FPR 0,149). İkincil eşik (0,8634) yalnız raporlama içindir, kilitli karar eşiği değildir.
- Feature üretim pipeline'ı YOK (lead bazlı genlikler); dış veride/uygulamada feature üretilemez.
- B2 operasyonel Q kuralı ters yönde çalıştı (AUC 0,31); geçerli kural baseline'ı kurulamadı.

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `registry_only` — feature üretim pipeline'ı yok; yalnız iç test. Modül etiketi: uygulamada değil (registry_only).
- **Uygulanabilirlik:** UYGULAMAYA ALINAMAZ (şimdilik): 168 lead bazlı ECGDeli feature'ını üretecek kilitli pipeline mevcut değil.
- **Kurallar:** Uygulamada YOK (`app_visible = false`, `registry_only`): 168 lead bazlı ECGDeli özniteliğini üretecek kilitli pipeline yok.
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

- `phase_xxxviii/PHASE_XXXVIII_REPORT.md`
- `phase_xxxviii/01_cohort.md`
- `phase_xxxviii/02_dev_cv.md`
- `phase_xxxviii/03_test_results.md`
- `phase_xxxviii/config/model_lock.json`
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

52 madde: karşılandı 22, kısmen 20, yok 8, uygulanamaz 2. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.
