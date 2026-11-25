# Phase XLIX — Final rapor girdileri

Derleme; **yeni test açılışı yok, model yeniden fit edilmedi, yeni tahmin üretilmedi.** Her sayı kaynak dosya yolu (+ satır/anahtar) ile verilir; repoda bulunamayan değer "BULUNAMADI". Üretim: `phase_xlix/scripts/build_inputs.py` (+ `af_overlap_check.py`, `uci_cad_availability.py`). Model olasılıkları klinik olasılık değildir (`clinical_probability_eligibility = false`). Araştırma hedefleri (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15) klinik onay kriteri değildir.

Kaynak SHA256: registry `5d2b88a012366f15…`, card_metrics `aeb38c7a1170dd3e…`, app_config `8333affab532b335…`.

İçindekiler: 1a modeller · 1b referans karşılaştırmaları · 1c AF ayrıntısı · 1d kirlenme/erratum · 1e veri setleri · 1f yazılım · 1g asistan · 1h kaynakça · 2 ara rapor düzeltmeleri · 3 hoca maddeleri

## 1a. Modeller (registry: `phase_xliii/registry/models.json`)

Tam satırlar (her kanıt düzeyi ayrı satır, kaynak dosya + seçici + SHA256): **`phase_xlix/model_results.csv`**. Hedef, popülasyon, öznitelik listesi ve eşik değeri registry `models.<id>`; veri seti, bölme ve eşik kuralı metni `phase_xlvi/scripts/card_spec.py > SPEC.<id>`; modül etiketi `app/backend/config/app_config.json > module_labels` (+ `app_mode = clinical_mode` → "klinik mod"; `app_visible = false` → registry_only).

| model | hastalık | modül | veri seti (rol: kaynak) | öznitelik | bölme (özet) | eşik |
|---|---|---|---|---|---|---|
| `af_S4_DEVICE` | Atriyal fibrilasyon (AF) | ana modül | geliştirme + iç test: PTB-XL 1.0.3 (PhysioNet), doi:10.13026/kfzx-aw45; dış doğrulama: PhysioNet/CinC Challenge 2021 1.0.3, doi:10.13026/34va-7q14 (kaynaklar: cpsc_2018, cpsc_2018_extra, chapman_shaoxing, georgia) | 12 | Kişi düzeyi, PTB-XL resmî `strat_fold`: 1–8 fit, 9 validation, 10 test; kişi kesişimi 0 (bu fazda doğrulandı) | 0.236088 |
| `mi_model` | Miyokard enfarktüsü (EKG bulgusu) | registry_only (uygulamada yok) | geliştirme + iç test: PTB-XL 1.0.3 (PhysioNet), doi:10.13026/kfzx-aw45 | 168 | Kişi düzeyi PTB-XL fold'ları: 1–8 geliştirme, 9 + 10 test | 0.0442566 |
| `cad_DEVICE` | Koroner arter hastalığı (CAD) | deneysel + klinik mod | geliştirme + iç test: UCI Heart Disease, doi:10.24432/C52P4X (Cleveland; teknik tekrar: Hungarian, VA Long Beach); teknik tekrar: UCI Hungarian (n = 95) ve VA Long Beach (n = 64), eksiksiz vaka alt kümesi | 11 | Satır (kişi) düzeyi tabakalı rastgele bölme: önce %20 test, kalanın %25'i validation (181/61/61); `src/training/train.py`, `random_state = SEED` (model meta verisinde seed 42) | 0.54018 |
| `dm_A` | Diyabet (teşhis edilmemiş) | deneysel | geliştirme: NHANES: E 2007–08, F 2009–10, I 2015–16, J 2017–18; iç test: NHANES: G 2011–12, H 2013–14 | 16 | Kişi düzeyi, döngü bazlı (G+H test; diğerleri geliştirme) | 0.495899 |
| `dm_B` | Diyabet (teşhis edilmemiş) — laboratuvarlı | deneysel | geliştirme: NHANES: E 2007–08, F 2009–10, I 2015–16, J 2017–18; iç test: NHANES: G 2011–12, H 2013–14 | 21 | Kişi düzeyi, döngü bazlı (G+H test; diğerleri geliştirme) | 0.531487 |
| `anemia_LR16` | Anemi | deneysel | geliştirme: NHANES: D 2005–06 (1.962 kişi, önceki geliştirme) + A 1999–2000; iç test: NHANES: A 1999–2000 holdout; dış (aynı program): NHANES: C 2003–04, E 2007–08, F 2009–10, I 2015–16 | 16 | Kişi düzeyi; A döngüsü içinde fit/validation/test; dış: farklı döngüler. | 0.270301 |
| `copd_S4_DEVICE` | KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) | deneysel + klinik mod | geliştirme + iç test: NHANES: G 2011–12 (SPX); zamansal tekrar: NHANES: F 2009–10, E 2007–08 | 6 | Kişi düzeyi rastgele fit/validation/test (G içinde); zamansal tekrar F ve E döngüleri. | 0.570721 |
| `hf_S2_BASIC_LAB` | Kalp yetmezliği | registry_only (uygulamada yok) | geliştirme + iç test: Mendeley Data 7v4w66wxj8.1, doi:10.17632/7v4w66wxj8.1 (RIP3 kalp yetmezliği; birincil yayın PMID 32598878) | 5 | Kişi düzeyi rastgele (fit/validation/test 110/37/37). | 0.447697 |
| `htn_M1` | Hipertansiyon | deneysel | geliştirme: NHANES: P 2017–Mar 2020, L Ağu 2021–Ağu 2023; zamansal test: NHANES: C 2003–04 | 13 | Zamansal: geliştirme 2017–2023, test 2003–04; kişiler daha önce hiçbir hedefte kullanılmadı. | 0.539745 |
| `fibrosis_final` | Karaciğer fibrozisi (LSM ≥ 8 kPa) | ana modül | geliştirme: NHANES: P 2017–Mar 2020 (LUX FibroScan); iç test: NHANES: L Ağu 2021–Ağu 2023 | 17 | Döngü bazlı (P geliştirme, L test); kişi düzeyi ayrık (SEQN kesişimi 0) | 0.061497 |
| `osteo_final` | Osteoporoz (DXA femur T-skoru ≤ −2,5) | araştırma modülü | geliştirme: NHANES: D 2005–06, E 2007–08, F 2009–10, H 2013–14 (DXXFEM); zamansal test: NHANES: J 2017–18 | 16 | Zamansal: geliştirme 2005–2014, test 2017–18; kişi düzeyi ayrık. | 0.0602886 |
| `ckd_A` | Böbrek (farkında olunmayan tek ziyaret renal anormalliği) | deneysel | geliştirme: NHANES: E 2007–08, F 2009–10, G 2011–12, H 2013–14; iç test: NHANES: I 2015–16 | 20 | Döngü bazlı kişi düzeyi (I test); zamansal sıralı, ancak I kişileri başka hedeflerde dış test olarak görülmüş. | 0.126602 |
| `ckd_B` | Böbrek — laboratuvarlı | deneysel | geliştirme: NHANES: E 2007–08, F 2009–10, G 2011–12, H 2013–14; iç test: NHANES: I 2015–16 | 25 | Döngü bazlı kişi düzeyi (I test); zamansal sıralı, ancak I kişileri başka hedeflerde dış test olarak görülmüş. | 0.138325 |

Eşik seçim kuralının tam metni ve hedef tanımı CSV'de (`esik_kurali_kaynak`, `hedef`). Registry'de 5 modelde "kural BULUNAMADI" yazar; kuralları Phase XLVI kaynağında bulundu (AF/KOAH/KY: Phase21 BALANCED; anemi: Phase25; CAD: `src/evaluation/metrics.py :: choose_threshold`) — `phase_xlvi/PHASE_XLVI_REPORT.md` Görev 1.

### Performans (donmuş model + donmuş eşik; oranlar Wilson %95 GA, AUC bootstrap %95 GA)

| model | küme | test türü | n (poz.) | prevalans | TP/FP/TN/FN | Precision | Recall | FPR | NPV | AUC | kaynak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `af_S4_DEVICE` | İç test — PTB-XL fold 10 (hasta düzeyinde ayrık) | iç test | 1572 (114) | 0,073 | 103/15/1443/11 | 0,873 [0,801–0,921] | 0,904 [0,835–0,945] | 0,010 [0,006–0,017] | 0,992 [0,987–0,996] | 0,980 [0,959–0,995] | `phase_xxvii/results/ci_metrics.csv` |
| `af_S4_DEVICE` | Dış doğrulama — Challenge 2021, 4 kaynak havuzu, AF vs SR (A2) | dış | 7817 (3497) | 0,447 | 3247/11/4309/250 | raporlanmaz (örneklem prevalansı) | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | 0,945 [0,938–0,951] | 0,990 [0,987–0,992] | `phase_xxxiii/results/a2_results.csv` |
| `af_S4_DEVICE` | Dış doğrulama — CPSC 2018, AF vs SR (A2) | dış (kaynak başına) | 1905 (1087) | 0,571 | 1007/3/815/80 | raporlanmaz (örneklem prevalansı) | 0,926 [0,909–0,940] | 0,004 [0,001–0,011] | 0,911 [0,890–0,928] | 0,995 [0,992–0,997] | `phase_xxxiii/results/a2_results.csv` |
| `af_S4_DEVICE` | Dış doğrulama — CPSC-Extra, AF vs SR (A2) | dış (kaynak başına) | 82 (78) | 0,951 | 74/0/4/4 | raporlanmaz (örneklem prevalansı) | 0,949 [0,875–0,980] | 0,000 [0,000–0,490] | 0,500 [0,215–0,785] | 0,990 [0,962–1,000] | `phase_xxxiii/results/a2_results.csv` |
| `af_S4_DEVICE` | Dış doğrulama — Chapman-Shaoxing, AF vs SR (A2) | dış (kaynak başına) | 3580 (1777) | 0,496 | 1742/5/1798/35 | raporlanmaz (örneklem prevalansı) | 0,980 [0,973–0,986] | 0,003 [0,001–0,006] | 0,981 [0,974–0,986] | 1,000 [0,999–1,000] | `phase_xxxiii/results/a2_results.csv` |
| `af_S4_DEVICE` | Dış doğrulama — Georgia, AF vs SR (A2) | dış (kaynak başına) | 2250 (555) | 0,247 | 424/3/1692/131 | raporlanmaz (örneklem prevalansı) | 0,764 [0,727–0,797] | 0,002 [0,001–0,005] | 0,928 [0,915–0,939] | 0,954 [0,941–0,967] | `phase_xxxiii/results/a2_results.csv` |
| `af_S4_DEVICE` | Dış — ikincil analiz: AF vs SR + diğer ritimler (B), havuz | dış — ikincil (AF vs SR + diğer ritimler) | 5477 (3497) | 0,638 | 3247/143/1837/250 | raporlanmaz (örneklem prevalansı) | 0,929 [0,919–0,937] | 0,072 [0,062–0,084] | 0,880 [0,866–0,893] | 0,965 [0,960–0,970] | `phase_xxxiii/results/b_results.csv` |
| `mi_model` | İç test — tümü (fold 9 + fold 10 AF-test dışı) | iç test | 1474 (521) | 0,353 | 491/138/815/30 | 0,781 [0,747–0,811] | 0,942 [0,919–0,959] | 0,145 [0,124–0,169] | 0,964 [0,950–0,975] | 0,973 [0,965–0,980] | `phase_xxxviii/results/test_operating_points.csv` |
| `mi_model` | İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | iç test (temiz alt küme) | 368 (160) | 0,435 | 156/36/172/4 | 0,812 [0,751–0,861] | 0,975 [0,937–0,990] | 0,173 [0,128–0,230] | 0,977 [0,943–0,991] | 0,972 [0,958–0,984] | `phase_xxxviii/results/test_operating_points.csv` |
| `cad_DEVICE` | İç test — UCI Cleveland (önceden açılmış) | iç test | 61 (28) | 0,459 | 23/3/30/5 | 0,885 [0,710–0,960] | 0,821 [0,644–0,921] | 0,091 [0,031–0,236] | 0,857 [0,706–0,937] | 0,948 [0,888–0,990] | `phase_xxvii/results/ci_metrics.csv` |
| `cad_DEVICE` | Teknik tekrar — UCI Hungarian (eksiksiz vaka, seçilmiş) | teknik tekrar (PREVIOUSLY_EXPOSED; bağımsız dış DEĞİL) | 95 (68) | 0,716 | 60/10/17/8 | 0,857 [0,757–0,921] | 0,882 [0,785–0,939] | 0,370 [0,215–0,558] | 0,680 [0,484–0,828] | 0,852 [0,766–0,928] | `phase_xli/results/cad_v2_rescore.json` |
| `cad_DEVICE` | Teknik tekrar — UCI VA Long Beach (eksiksiz vaka, seçilmiş) | teknik tekrar (PREVIOUSLY_EXPOSED; bağımsız dış DEĞİL) | 64 (54) | 0,844 | 54/7/3/0 | 0,885 [0,782–0,943] | 1,000 [0,934–1,000] | 0,700 [0,397–0,892] | 1,000 [0,439–1,000] | 0,667 [0,437–0,859] | `phase_xli/results/cad_v2_rescore.json` |
| `dm_A` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | iç test | 8895 (389) | 0,044 | 285/2483/6023/104 | 0,103 [0,092–0,115] | 0,733 [0,687–0,774] | 0,292 [0,282–0,302] | 0,983 [0,979–0,986] | 0,800 [0,781–0,819] | `phase_xlii/results/test_operating_points.csv` |
| `dm_B` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | iç test | 8895 (389) | 0,044 | 278/2003/6503/111 | 0,122 [0,109–0,136] | 0,715 [0,668–0,757] | 0,235 [0,227–0,245] | 0,983 [0,980–0,986] | 0,825 [0,808–0,843] | `phase_xlii/results/test_operating_points.csv` |
| `anemia_LR16` | İç test — NHANES A 1999–2000 (Phase25 holdout; önceden açılmış) | iç test | 410 (21) | 0,051 | 17/4/385/4 | 0,810 [0,600–0,923] | 0,810 [0,600–0,923] | 0,010 [0,004–0,026] | 0,990 [0,974–0,996] | 0,991 [0,980–0,999] | `phase_xxvii/results/ci_metrics.csv` |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C, E, F, I birleşik | farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL) | 11171 (669) | 0,060 | 591/242/10260/78 | 0,709 [0,678–0,739] | 0,883 [0,857–0,906] | 0,023 [0,020–0,026] | 0,992 [0,991–0,994] | 0,991 [0,989–0,993] | `phase_xl/results/anemia_external.json` |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C 2003–04 | farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL) | 2265 (89) | 0,039 | 82/25/2151/7 | 0,766 [0,678–0,836] | 0,921 [0,846–0,961] | 0,011 [0,008–0,017] | 0,997 [0,993–0,998] | 0,995 [0,991–0,998] | `phase_xl/results/anemia_external.json` |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES E 2007–08 | farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL) | 2881 (156) | 0,054 | 149/85/2640/7 | 0,637 [0,573–0,696] | 0,955 [0,910–0,978] | 0,031 [0,025–0,038] | 0,997 [0,995–0,999] | 0,994 [0,992–0,996] | `phase_xl/results/anemia_external.json` |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES F 2009–10 | farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL) | 3188 (183) | 0,057 | 165/102/2903/18 | 0,618 [0,558–0,674] | 0,902 [0,850–0,937] | 0,034 [0,028–0,041] | 0,994 [0,990–0,996] | 0,993 [0,989–0,995] | `phase_xl/results/anemia_external.json` |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES I 2015–16 | farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL) | 2837 (241) | 0,085 | 195/30/2566/46 | 0,867 [0,816–0,905] | 0,809 [0,755–0,854] | 0,012 [0,008–0,016] | 0,982 [0,977–0,987] | 0,991 [0,987–0,994] | `phase_xl/results/anemia_external.json` |
| `copd_S4_DEVICE` | İç test — NHANES G 2011–12 | iç test | 37 (20) | 0,541 | 13/0/17/7 | 1,000 [0,772–1,000] | 0,650 [0,433–0,819] | 0,000 [0,000–0,184] | 0,708 [0,508–0,851] | 0,921 [0,824–0,988] | `phase_xxvii/results/ci_metrics.csv` |
| `copd_S4_DEVICE` | Zamansal tekrar — NHANES F 2009–10 | zamansal | 250 (156) | 0,624 | 118/9/85/38 | 0,929 [0,871–0,962] | 0,756 [0,683–0,817] | 0,096 [0,051–0,172] | 0,691 [0,605–0,766] | 0,898 [0,857–0,934] | `phase_xxvii/results/ci_metrics.csv` |
| `copd_S4_DEVICE` | Zamansal tekrar — NHANES E 2007–08 | zamansal (ikincil döngü) | 274 (163) | 0,595 | 117/9/102/46 | 0,929 [0,870–0,962] | 0,718 [0,644–0,781] | 0,081 [0,043–0,147] | 0,689 [0,611–0,758] | 0,901 [0,865–0,933] | `phase_xxvii/results/ci_metrics.csv` |
| `hf_S2_BASIC_LAB` | İç test — Mendeley 7v4w66wxj8.1 (n=37) | iç test | 37 (18) | 0,486 | 14/3/16/4 | 0,824 [0,590–0,938] | 0,778 [0,548–0,910] | 0,158 [0,055–0,376] | 0,800 [0,584–0,919] | 0,950 [0,877–0,997] | `phase_xxvii/results/ci_metrics.csv` |
| `htn_M1` | Zamansal test — NHANES C 2003–04 (ölçüm yöntemi kaymalı) | zamansal | 2798 (1001) | 0,358 | 767/325/1472/234 | 0,702 [0,675–0,729] | 0,766 [0,739–0,791] | 0,181 [0,164–0,199] | 0,863 [0,846–0,878] | 0,875 [0,862–0,887] | `phase_xxxvii/results/test_operating_points.csv` |
| `fibrosis_final` | İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | iç test | 4714 (587) | 0,125 | 451/1430/2697/136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,952 [0,943–0,959] | 0,794 [0,773–0,813] | `phase_xxxi/results/fibrosis_test_results.csv` |
| `osteo_final` | Zamansal test — NHANES J 2017–18 | zamansal | 2275 (164) | 0,072 | 128/486/1625/36 | 0,208 [0,178–0,242] | 0,780 [0,711–0,837] | 0,230 [0,213–0,249] | 0,978 [0,970–0,984] | 0,849 [0,818–0,880] | `phase_xxx/results/osteo_test_results.csv` |
| `osteo_final` | Zamansal test — kadın | zamansal (alt grup) | 1082 (133) | 0,123 | 113/368/581/20 | 0,235 [0,199–0,275] | 0,850 [0,779–0,900] | 0,388 [0,357–0,419] | 0,967 [0,949–0,978] | 0,816 [0,776–0,854] | `phase_xxx/results/osteo_test_results.csv` |
| `osteo_final` | Zamansal test — erkek | zamansal (alt grup) | 1193 (31) | 0,026 | 15/118/1044/16 | 0,113 [0,070–0,178] | 0,484 [0,320–0,652] | 0,102 [0,085–0,120] | 0,985 [0,976–0,991] | 0,817 [0,734–0,883] | `phase_xxx/results/osteo_test_results.csv` |
| `ckd_A` | İç test — NHANES I 2015–16 (kilitli tek sefer) | iç test | 4812 (716) | 0,149 | 549/1322/2774/167 | 0,293 [0,273–0,314] | 0,767 [0,734–0,796] | 0,323 [0,309–0,337] | 0,943 [0,934–0,951] | 0,791 [0,773–0,809] | `phase_xxxv/results/test_operating_points.csv` |
| `ckd_B` | İç test — NHANES I 2015–16 (kilitli tek sefer) | iç test | 4812 (716) | 0,149 | 540/1187/2909/176 | 0,313 [0,291–0,335] | 0,754 [0,721–0,784] | 0,290 [0,276–0,304] | 0,943 [0,934–0,951] | 0,805 [0,788–0,823] | `phase_xxxv/results/test_operating_points.csv` |

NPV kaynakta yoksa Phase XLVI kayıtlı TN/FN'den hesapladı (`npv_source`). AF dış satırlarında ve prevalansı örneklemle belirlenen kümelerde Precision hedef karşılaştırmasında kullanılmaz (registry `precision_note`). CV sonuçları bu tabloda yoktur ("aday" sonuçlar kanıt sayılmaz).

## 1b. Referans / klinik baseline karşılaştırmaları (aynı test kişileri)

ΔAUC = AUC(model) − AUC(referans), aynı kişilerde paired bootstrap (kaynak fazın tohumu). Kaynak: `phase_xlvi/results/card_metrics.json > <model>[].delta` (her satırda özgün dosya).

| model | küme | karşılaştırma | referans AUC | ΔAUC [%95 GA] | not | kaynak |
|---|---|---|---|---|---|---|
| `af_S4_DEVICE` | İç test — PTB-XL fold 10 (hasta düzeyinde ayrık) | model − RR_iqr / RR_mean | 0,959 | 0,021 [0,006–0,037] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` (model=af, kume=test, baseline=RR_iqr / RR_mean) |
| `af_S4_DEVICE` | Dış doğrulama — Challenge 2021, 4 kaynak havuzu, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,968 | 0,021 [0,018–0,025] |  | `phase_xxxiii/results/a2_results.csv` (analiz=A2 — birincil, skor=MODEL, kapsam=Havuz (4 kaynak, ikincil) (dAUC)) |
| `af_S4_DEVICE` | Dış doğrulama — CPSC 2018, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,978 | 0,017 [0,011–0,023] |  | `phase_xxxiii/results/a2_results.csv` (analiz=A2 — birincil, skor=MODEL, kapsam=CPSC 2018 (dAUC)) |
| `af_S4_DEVICE` | Dış doğrulama — CPSC-Extra, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,978 | 0,013 [-0,013–0,051] |  | `phase_xxxiii/results/a2_results.csv` (analiz=A2 — birincil, skor=MODEL, kapsam=CPSC-Extra (dAUC)) |
| `af_S4_DEVICE` | Dış doğrulama — Chapman-Shaoxing, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,992 | 0,008 [0,005–0,011] |  | `phase_xxxiii/results/a2_results.csv` (analiz=A2 — birincil, skor=MODEL, kapsam=Chapman-Shaoxing (dAUC)) |
| `af_S4_DEVICE` | Dış doğrulama — Georgia, AF vs SR (A2) | model − RR_iqr/RR_mean ≥ 0,138235 | 0,871 | 0,083 [0,062–0,103] |  | `phase_xxxiii/results/a2_results.csv` (analiz=A2 — birincil, skor=MODEL, kapsam=Georgia (dAUC)) |
| `af_S4_DEVICE` | Dış — ikincil analiz: AF vs SR + diğer ritimler (B), havuz | model − RR_iqr/RR_mean ≥ 0,138235 | 0,929 | 0,035 [0,028–0,044] |  | `phase_xxxiii/results/b_results.csv` (analiz=B — birincil, skor=MODEL, kapsam=Havuz (4 kaynak, ikincil) (dAUC)) |
| `mi_model` | İç test — tümü (fold 9 + fold 10 AF-test dışı) | model − B1 yaş+cinsiyet LR | 0,818 | 0,155 [0,134–0,175] |  | `phase_xxxviii/results/test_delta_auc.csv` (kume=birincil_tum_test, karsilastirma=MODEL-B1_yas_cinsiyet) |
| `mi_model` | İç test — tümü (fold 9 + fold 10 AF-test dışı) | model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz) | BULUNAMADI | 0,667 [0,638–0,695] | B2 AUC < 0,5; geçerli kural baseline'ı kurulamadı (Phase XXXVIII 02 §4) | `phase_xxxviii/results/test_delta_auc.csv` (kume=birincil_tum_test, karsilastirma=MODEL-B2_Q_kurali) |
| `mi_model` | İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | model − B1 yaş+cinsiyet LR | 0,823 | 0,149 [0,113–0,190] |  | `phase_xxxviii/results/test_delta_auc.csv` (kume=birincil_temiz, karsilastirma=MODEL-B1_yas_cinsiyet) |
| `mi_model` | İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç) | model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz) | BULUNAMADI | 0,646 [0,589–0,701] | B2 AUC < 0,5; geçerli kural baseline'ı kurulamadı (Phase XXXVIII 02 §4) | `phase_xxxviii/results/test_delta_auc.csv` (kume=birincil_temiz, karsilastirma=MODEL-B2_Q_kurali) |
| `cad_DEVICE` | İç test — UCI Cleveland (önceden açılmış) | model − LR(age, sex) | 0,695 | 0,253 [0,147–0,382] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` (model=cad, kume=test, baseline=LR(age, sex)) |
| `cad_DEVICE` | İç test — UCI Cleveland (önceden açılmış) | model − Tek değişken: thalach (− yön; fit AUC=0.282) | 0,775 | 0,173 [0,072–0,290] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` (model=cad, kume=test, baseline=Tek değişken: thalach (− yön; fit AUC=0.282)) |
| `cad_DEVICE` | Teknik tekrar — UCI Hungarian (eksiksiz vaka, seçilmiş) | model − LR(yaş, cinsiyet) | 0,662 | 0,190 [0,072–0,315] | KATKI_VAR | `phase_xli/results/cad_v2_rescore.json` (sets.hungarian.baselines.LR(age, sex).delta_vs_model) |
| `cad_DEVICE` | Teknik tekrar — UCI VA Long Beach (eksiksiz vaka, seçilmiş) | model − LR(yaş, cinsiyet) | 0,612 | 0,055 [-0,164–0,288] | KANIT_YETERSIZ | `phase_xli/results/cad_v2_rescore.json` (sets.va.baselines.LR(age, sex).delta_vs_model) |
| `dm_A` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | A − ADA | 0,758 | 0,042 [0,028–0,055] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` (karsilastirma=A − ADA) |
| `dm_A` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | A − yaş+BMI | 0,747 | 0,054 [0,040–0,068] | tür: ikincil | `phase_xlii/results/test_delta_auc.csv` (karsilastirma=A − yaş+BMI) |
| `dm_B` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − ADA | 0,758 | 0,067 [0,050–0,083] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` (karsilastirma=B − ADA) |
| `dm_B` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − A | 0,800 | 0,025 [0,014–0,036] | tür: birincil | `phase_xlii/results/test_delta_auc.csv` (karsilastirma=B − A) |
| `dm_B` | İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | B − yaş+BMI | 0,747 | 0,079 [0,061–0,097] | tür: ikincil | `phase_xlii/results/test_delta_auc.csv` (karsilastirma=B − yaş+BMI) |
| `anemia_LR16` | İç test — NHANES A 1999–2000 (Phase25 holdout; önceden açılmış) | model − Hct_proxy=RBC×MCV/10 sabit (E<39, K<36) | 0,990 | 0,002 [-0,003–0,008] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` (model=anemia, kume=test, baseline=Hct_proxy=RBC×MCV/10 sabit (E<39, K<36)) |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C, E, F, I birleşik | model − Hct_proxy kuralı | 0,988 | 0,004 [0,002–0,005] | KATKI_VAR | `phase_xl/results/anemia_external.json` (sets.pooled.delta_auc) |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES C 2003–04 | model − Hct_proxy kuralı | 0,994 | 0,001 [-0,001–0,003] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` (sets.C.delta_auc) |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES E 2007–08 | model − Hct_proxy kuralı | 0,992 | 0,002 [-0,000–0,004] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` (sets.E.delta_auc) |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES F 2009–10 | model − Hct_proxy kuralı | 0,990 | 0,003 [0,000–0,006] | KATKI_VAR | `phase_xl/results/anemia_external.json` (sets.F.delta_auc) |
| `anemia_LR16` | Farklı döngüler (aynı program; bağımsız kurum değil) — NHANES I 2015–16 | model − Hct_proxy kuralı | 0,990 | 0,001 [-0,002–0,004] | KANIT_YETERSIZ | `phase_xl/results/anemia_external.json` (sets.I.delta_auc) |
| `copd_S4_DEVICE` | İç test — NHANES G 2011–12 | model − pre-BD FEV1/FVC < 0.70 | 0,912 | 0,009 [-0,059–0,076] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` (model=copd, kume=test, baseline=pre-BD FEV1/FVC < 0.70) |
| `copd_S4_DEVICE` | Zamansal tekrar — NHANES F 2009–10 | model − pre-BD FEV1/FVC < 0.70 | 0,875 | 0,023 [-0,005–0,052] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` (model=copd, kume=F_2009_2010, baseline=pre-BD FEV1/FVC < 0.70) |
| `copd_S4_DEVICE` | Zamansal tekrar — NHANES E 2007–08 | model − pre-BD FEV1/FVC < 0.70 | 0,899 | 0,002 [-0,019–0,025] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` (model=copd, kume=E_2007_2008, baseline=pre-BD FEV1/FVC < 0.70) |
| `hf_S2_BASIC_LAB` | İç test — Mendeley 7v4w66wxj8.1 (n=37) | model − LR(age, sex, bmi) | 0,579 | 0,371 [0,158–0,588] | karar: KATKI_VAR | `phase_xxvii/results/baselines.csv` (model=heart_failure, kume=test, baseline=LR(age, sex, bmi)) |
| `hf_S2_BASIC_LAB` | İç test — Mendeley 7v4w66wxj8.1 (n=37) | model − Tek değişken: rip3 (+ yön; fit AUC=0.927) | 0,956 | -0,006 [-0,044–0,023] | karar: KANIT_YETERSIZ | `phase_xxvii/results/baselines.csv` (model=heart_failure, kume=test, baseline=Tek değişken: rip3 (+ yön; fit AUC=0.927)) |
| `htn_M1` | Zamansal test — NHANES C 2003–04 (ölçüm yöntemi kaymalı) | M1 − LR(yaş, cinsiyet, BMI) | 0,863 | 0,012 [0,007–0,018] |  | `phase_xxxvii/results/test_delta_auc.csv` (karsilastirma=M1-BASELINE) |
| `fibrosis_final` | İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | model − FIB-4 | 0,597 | 0,197 [0,169–0,225] |  | `phase_xxxi/results/fibrosis_test_results.csv` (analiz=FIB-4≥1.3 (dAUC)) |
| `fibrosis_final` | İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | model − NFS | 0,698 | 0,096 [0,075–0,117] |  | `phase_xxxi/results/fibrosis_test_results.csv` (analiz=NFS≥−1.455 (dAUC)) |
| `osteo_final` | Zamansal test — NHANES J 2017–18 | model − (−OST) | 0,824 | 0,025 [0,012–0,038] |  | `phase_xxx/results/osteo_test_results.csv` (analiz=OST birincil (K<2, E<=3) — tümü (dAUC)) |
| `osteo_final` | Zamansal test — kadın | model − (−OST) | 0,801 | 0,015 [0,002–0,029] |  | `phase_xxx/results/osteo_test_results.csv` (analiz=OST birincil (K<2, E<=3) — kadın (dAUC)) |
| `osteo_final` | Zamansal test — erkek | model − (−OST) | 0,802 | 0,015 [-0,008–0,044] |  | `phase_xxx/results/osteo_test_results.csv` (analiz=OST birincil (K<2, E<=3) — erkek (dAUC)) |
| `ckd_A` | İç test — NHANES I 2015–16 (kilitli tek sefer) | A − SCORED | 0,759 | 0,032 [0,020–0,043] |  | `phase_xxxv/results/test_delta_auc.csv` (karsilastirma=A − SCORED) |
| `ckd_B` | İç test — NHANES I 2015–16 (kilitli tek sefer) | B − SCORED | 0,759 | 0,047 [0,035–0,058] |  | `phase_xxxv/results/test_delta_auc.csv` (karsilastirma=B − SCORED) |
| `ckd_B` | İç test — NHANES I 2015–16 (kilitli tek sefer) | B − A | 0,791 | 0,015 [0,009–0,021] |  | `phase_xxxv/results/test_delta_auc.csv` (karsilastirma=B − A) |

### Aynı duyarlılıkta FPR / yönlendirme (fibrozis, osteoporoz) — POST-HOC TANIMLAYICI

Kaynak: `phase_xlvi/results/reference_score_analysis.csv` (karsilastirma = "eşit duyarlılık …"); ayrıntı ve eşit-yönlendirme şemaları `phase_xlvi/01_reference_score_analysis.md` §3–4. McNemar kesin binom (negatiflerde).

| hastalık | grup | referans kuralı (testte eşlenmiş) | Recall (ortak) | FPR model / ref | yönlendirilen model / ref | negatifte yalnız model / yalnız ref | McNemar p |
|---|---|---|---|---|---|---|---|
| fibrozis | tümü | FIB-4 ≥ 0.774 (testte eşlenmiş) | 0,768 | 0,346 / 0,655 | 1881 / 3155 | 357 / 1631 | < 0,001 |
| fibrozis | tümü | NFS ≥ -1.69 (testte eşlenmiş) | 0,768 | 0,346 / 0,496 | 1881 / 2497 | 359 / 975 | < 0,001 |
| fibrozis | kadın | FIB-4 ≥ 0.6811 (testte eşlenmiş) | 0,766 | 0,288 / 0,692 | 873 / 1796 | 148 / 1071 | < 0,001 |
| fibrozis | kadın | NFS ≥ -1.666 (testte eşlenmiş) | 0,766 | 0,288 / 0,474 | 873 / 1297 | 165 / 589 | < 0,001 |
| fibrozis | erkek | FIB-4 ≥ 0.8253 (testte eşlenmiş) | 0,770 | 0,419 / 0,656 | 1008 / 1445 | 190 / 627 | < 0,001 |
| fibrozis | erkek | NFS ≥ -1.716 (testte eşlenmiş) | 0,770 | 0,419 / 0,521 | 1008 / 1196 | 190 / 378 | < 0,001 |
| osteoporoz | kadın | −OST ≥ -1.36 (testte eşlenmiş) | 0,850 | 0,388 / 0,426 | 481 / 517 | 32 / 68 | < 0,001 |
| osteoporoz | erkek | −OST ≥ 1.92 (testte eşlenmiş) | 0,484 | 0,102 / 0,066 | 133 / 92 | 41 / 0 | < 0,001 |

### Uygulamada olmayan modellerde referans karşılaştırmaları

| model | referans | n (poz.) | referans AUC | ΔAUC (model − ref) | kaynak |
|---|---|---|---|---|---|
| Karaciğer yağlanması (CAP ≥ 274; CONTAMINATED) | Baseline FLI (literatür eşiği ≥60) | 2429 (966) | 0,840 [0,824–0,856] | 0,005 [-0,003–0,013] | `phase_xxx/results/liver_test_results.csv` |
| Karaciğer yağlanması (CAP ≥ 274; CONTAMINATED) | Baseline HSI (literatür eşiği >36) | 2419 (963) | 0,798 [0,780–0,817] | 0,046 [0,033–0,059] | `phase_xxx/results/liver_test_results.csv` |
| Safra taşı (NHANES III Faz 2) | Baseline LR(age,sex,bmi) — klinik skor yok (Faz 1 fit, kendi kademeli eşiği) | 6528 (614) | 0,740 [0,720–0,759] | 0,012 [0,004–0,019] | `phase_xxx/results/gallstone_test_results.csv` |

SCORED: `ckd_A` satırındaki "modified SCORED" (Phase XXXV; değiştirilmiş sürüm, ayrıntı `phase_xxxv/03_test_results.md`). Listede olmayan referanslar (ör. AF için CHARGE-AF; KOAH için CAPTURE) projede uygulanmadı: BULUNAMADI.

## 1c. AF — dış doğrulama ayrıntısı (Phase XXXIII; donmuş model + kilitli pipeline)

| kaynak | A2 n (AF) | Recall (A2) | FPR AF vs SR (A2) | AUC (A2) | FPR AF vs diğer ritim (B) | Precision (karışım) | FPR (karışım) | ağırlıklı prevalans | üç hedef (karışım) |
|---|---|---|---|---|---|---|---|---|---|
| CPSC 2018 | 1905 (1087) | 0,926 [0,909–0,940] | 0,004 [0,001–0,011] | 0,995 [0,992–0,997] | 0,075 [0,055–0,102] | 0,743 [0,689–0,803] | 0,064 [0,046–0,084] | 0,167 | evet |
| CPSC-Extra | 82 (78) | 0,949 [0,875–0,980] | 0,000 [0,000–0,490] | 0,990 [0,962–1,000] | 0,033 [0,020–0,052] | 0,421 [0,321–0,586] | 0,032 [0,016–0,049] | 0,024 | hayır |
| Chapman-Shaoxing | 3580 (1777) | 0,980 [0,973–0,986] | 0,003 [0,001–0,006] | 1,000 [0,999–1,000] | 0,115 [0,090–0,146] | 0,714 [0,669–0,766] | 0,089 [0,068–0,110] | 0,185 | evet |
| Georgia | 2250 (555) | 0,764 [0,727–0,797] | 0,002 [0,001–0,005] | 0,954 [0,941–0,967] | 0,066 [0,047–0,091] | 0,451 [0,378–0,545] | 0,055 [0,038–0,074] | 0,056 | hayır |
| Havuz (4 kaynak, ikincil) | 7817 (3497) | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | 0,990 [0,987–0,992] | 0,072 [0,062–0,084] | 0,661 [0,625–0,700] | 0,064 [0,054–0,075] | 0,119 | hayır |

Kaynak: `phase_xxxiii/results/a2_results.csv` (analiz = "A2 — birincil", skor = MODEL), `b_results.csv` ("B — birincil"), `mixture_results.csv` ("Karışım — birincil"). A2 Precision örneklem prevalansına bağlı olduğu için raporlanmaz; üç hedef yalnız karışımda değerlendirilir (karışım ağırlıkları hastane arşivi oranlarıdır, toplum prevalansı değil; `phase_xxxiii/01_data_flow.md` notlar).

### Diğer ritimlerde yanlış pozitif oranı (havuz)

| ritim | n | FP | FPR model | FPR baseline (RR_iqr/RR_mean) |
|---|---|---|---|---|
| Sinüs taşikardisi | 237 | 43 | 0,181 [0,138–0,235] | 0,034 [0,017–0,065] |
| Sinüs bradikardisi | 429 | 3 | 0,007 [0,002–0,020] | 0,033 [0,020–0,054] |
| Sinüs aritmisi | 35 | 2 | 0,057 [0,016–0,186] | 0,314 [0,186–0,480] |
| PAC/SVPB | 131 | 20 | 0,153 [0,101–0,224] | 0,260 [0,192–0,341] |
| PVC | 62 | 19 | 0,306 [0,206–0,430] | 0,306 [0,206–0,430] |
| Pacing | 10 | 3 | 0,300 [0,108–0,603] | 0,200 [0,057–0,510] |
| Diğer | 1142 | 72 | 0,063 [0,050–0,079] | 0,060 [0,048–0,076] |

Kaynak: `phase_xxxiii/results/b_rhythm_fpr.csv` (kapsam = Havuz). Kaynak başına satırlar aynı dosyada.

### AFL kayıtlarında AF kararı

| kaynak | n | AF kararı | oran model | oran baseline |
|---|---|---|---|---|
| CPSC-Extra | 46 | 34 | 0,739 [0,597–0,844] | 0,674 [0,530–0,791] |
| Chapman-Shaoxing | 438 | 291 | 0,664 [0,619–0,707] | 0,447 [0,402–0,494] |
| Georgia | 167 | 95 | 0,569 [0,493–0,642] | 0,419 [0,347–0,495] |
| Havuz (4 kaynak, ikincil) | 651 | 420 | 0,645 [0,608–0,681] | 0,456 [0,418–0,495] |

Kaynak: `phase_xxxiii/results/afl_results.csv`.

### CPSC-Extra: 4 negatif

Tekilleştirmeden sonra CPSC-Extra'da uygun SR kaydı **4** (AF 78). A2'de FPR 0,000 [0,000–0,490] ve AUC **yorumlanamaz** (XXXIII protokol sapması 2: SR n < 30 → "YORUMLANAMAZ"; kural model çıktısı görülmeden eklendi). CPSC-Extra'daki 152 header-uygun AF kaydının 74'ü CPSC 2018 kopyasıydı. Aynı kaynakta diğer ritim negatifi 492; B ve karışımda yorumlanabilir. Kaynak: `phase_xlvi/af_validation_dossier.md` §4.1, §5.2; `phase_xxxiii/01_data_flow.md`.

### ABSTAIN (pipeline başarısızlığı → tahmin üretilmez) oranları

| kaynak | işlenen kayıt (AF+SR+diğer+AFL) | başarısız (zero_beats / ecgdeli_error / feature_error) | oran [Wilson %95 GA] |
|---|---|---|---|
| CPSC 2018 | 2400 | 2 | 0,0008 [0,0002–0,0030] |
| CPSC-Extra | 620 | 0 | 0,0000 [0,0000–0,0062] |
| Chapman-Shaoxing | 4518 | 4 | 0,0009 [0,0003–0,0023] |
| Georgia | 2918 | 2 | 0,0007 [0,0002–0,0025] |
| Havuz | 10456 | 8 | 0,0008 [0,0004–0,0015] |

Kaynak: `phase_xxxiii/01_data_flow.md` satır 55–67 ("− pipeline başarısız" ve "= Birincil analiz" satırları; tür dağılımı `phase_xxxiii/PHASE_XXXIII_REPORT.md` satır 12–21). Phase XXIX (1.882 kayıt) başarısızlık 0 (`phase_xxix/01_data_flow.md` satır 61). Teknik uygunluk (fs ≠ 500 Hz, < 10 sn, yaş/cinsiyet eksik) bu orana dahil değildir; uygulamada bunlar da ABSTAIN üretir (`app/docs/architecture.md` §4).

## 1d. Kirlenme / erratum kayıtları

| model / sonuç | ne oldu | nasıl ele alındı | kaynak |
|---|---|---|---|
| HTN (Phase XXXII) | Test L 2021–23 kişileri daha önce iki testte kullanılmıştı (XXX karaciğer CAP: CONTAMINATED; XXXI fibrozis: PREVIOUSLY_EXPOSED) → sonuç "bağımsız test" sayılamaz (AUC 0,833, ΔAUC +0,028). | Phase XXXVII: 13 öznitelikle uyumlaştırılmış yeni model, hiçbir hedefte kullanılmamış NHANES C 2003–04'te tek sefer test: AUC 0,875 [0,862–0,887], ΔAUC (yaş+cinsiyet+BMI) +0,012 [0,007–0,018]. Registry `htn_M1` bu modeldir. XXXII AUC'sinin şiştiğine dair kanıt yok (L OOF AUC 0,834). | `phase_xxxii/00_inventory.md` satır 49; `phase_xxxii/PHASE_XXXII_REPORT.md`; `phase_xxxvii/PHASE_XXXVII_REPORT.md` §6 |
| CAD V2 dış skorlama (Hungarian, Switzerland, VA) | Kategorik kodlama hatası: Cleveland'da `'0.0'/'1.0'` öğrenildi, dış merkezlerde `'0'/'1'` geldi → one-hot blokları sıfırlandı (sex, cp; VA'da restecg). Ayrıca eksik girdiler eğitim imputer'ıyla dolduruldu (kurala aykırı). V2 DEVICE: Hungarian R 0,509, VA R 0,514 GEÇERSİZ. | Phase XLI: biçim düzeltmesi + eksiksiz-vaka teknik tekrar (Hungarian n=95 AUC 0,852; VA n=64 AUC 0,667), PREVIOUSLY_EXPOSED, bağımsız dış doğrulama DEĞİL. Phase XLII: errata belgesi; eski dosyalar değiştirilmedi (kullanıcı kararı: errata yok, prepare.py değişmez, BASIC/LAB yeniden skorlanmaz). Switzerland YAPILAMAZ (chol %100 eksik). | `phase_xlii/ERRATA_CAD_V2.md` §1–2; `phase_xli/01_cad_rescore.md`; `phase_xli/results/cad_v2_rescore.json` |
| Karaciğer yağlanması CAP (Phase XXX) | L CAP etiketleri V2 başlangıcı ve Focused fazında model/eşik seçiminde kullanılmıştı. | Test sonucu CONTAMINATED etiketli; model uygulamaya alınmadı. | `phase_xxx/03_test_results.md` satır 5 |
| MI (Phase XXXVIII) | Test kişilerinin 1.106'sı (%75) AF eşik seçiminde görülmüştü (başka hedef). | PREVIOUSLY_EXPOSED; temiz alt küme (n=368) ayrıca raporlandı. | registry `mi_model.evidence`; `phase_xxxviii/03_test_results.md` |

### PREVIOUSLY_EXPOSED / önceden açılmış test etiketleri (registry `evidence`)

| model | önceden görülmüş/maruz test kişisi | registry metni (highest_tier + kaynaklar) |
|---|---|---|
| `af_S4_DEVICE` | kayıtta belirtilmemiş | dış doğrulama (bağımsız, farklı kaynaklar; donmuş model + kilitli pipeline bileşimi) · Phase XXVII (PTB-XL, hasta düzeyinde ayrık) · Phase XXXIII A2 (Challenge 2021: CPSC2018, CPSC-Extra, Chapman-Shaoxing, Georgia; AF vs SR, tam örneklem, havuz) |
| `mi_model` | evet | iç test · Phase XXXVIII (PTB-XL/PTB-XL+ ; tüm test; %75'i AF eşik seçiminde görülmüş kişi: PREVIOUSLY_EXPOSED) |
| `cad_DEVICE` | evet | iç test + düzeltilmiş teknik tekrar (bağımsız dış doğrulama DEĞİL) · Cleveland UCI test (phase_xxvii; önceden görülmüş) · Phase XLI düzeltilmiş teknik tekrar (UCI Hungarian n=95, VA n=64; eksiksiz-vaka, seçilmiş, PREVIOUSLY_EXPOSED; bağımsız dış doğrulama DEĞİL) |
| `dm_A` | evet | iç test (NHANES içi; zamansal değil; PREVIOUSLY_EXPOSED_PERSONS başka hedef; diyabet hedefinde yeni kişiler) · Phase XLII (NHANES G 2011–12 + H 2013–14, kilitli tek sefer) |
| `dm_B` | kayıtta belirtilmemiş | iç test (NHANES içi; zamansal değil) · Phase XLII (G+H, kilitli tek sefer) |
| `anemia_LR16` | evet | dış doğrulama (NHANES farklı döngüler; aynı anket programı, PREVIOUSLY_EXPOSED başka hedef) — bağımsız kurum doğrulaması DEĞİL · Phase XXVII (NHANES 1999–2000 A, önceden görülmüş) · Phase XL (NHANES C, E, F, I birleşik) |
| `copd_S4_DEVICE` | evet | zamansal tekrar (aynı anket, farklı döngü; PREVIOUSLY_EXPOSED) — bağımsız klinik kohort DEĞİL · Phase XXVII (NHANES G 2011–12) · Phase XXVII (NHANES F 2009–10) |
| `hf_S2_BASIC_LAB` | kayıtta belirtilmemiş | iç test (n=37) · Phase XXVII (Mendeley 7v4w66wxj8.1) |
| `htn_M1` | hayır (kayıtta "hiçbir hedefte önceden kullanılmamış") | zamansal test (C 2003–04; ölçüm yöntemi kaymalı: auskültatuvar vs oskilometrik) — bağımsız kurum doğrulaması DEĞİL · Phase XXXVII (NHANES C 2003–04, kilitli tek sefer; hiçbir hedefte önceden kullanılmamış kişiler) |
| `fibrosis_final` | evet | iç test (NHANES L 2021–23; PREVIOUSLY_EXPOSED: kişiler CAP hedefi için görülmüş) · Phase XXXI (NHANES L, kilitli tek sefer) |
| `osteo_final` | kayıtta belirtilmemiş | zamansal test (NHANES J 2017–18; DXA etiketi ilk kez) — bağımsız kurum doğrulaması DEĞİL · Phase XXX (NHANES J, kilitli tek sefer) |
| `ckd_A` | evet | iç test (NHANES I 2015–16; PREVIOUSLY_EXPOSED başka hedef; zamansal değil) · Phase XXXV (NHANES I, kilitli tek sefer) |
| `ckd_B` | evet | iç test (NHANES I; PREVIOUSLY_EXPOSED) · Phase XXXV (NHANES I, kilitli tek sefer) |

Kaynak: `phase_xliii/registry/models.json > models.<id>.evidence`. "kayıtta belirtilmemiş" = registry metninde maruziyet ifadesi yok; bu, maruziyet olmadığı anlamına gelmez (faz raporuna bakılmalı).

## 1e. Veri setleri

| veri seti | dönem / merkez | n | erişim / lisans | model(ler) |
|---|---|---|---|---|
| NHANES (CDC/NCHS) | döngüler: A 1999–2000, C 2003–04, D 2005–06, E 2007–08, F 2009–10, G 2011–12, H 2013–14, I 2015–16, J 2017–18, P 2017–Mar 2020, L Ağu 2021–Ağu 2023; ABD genel nüfus | model başına `model_results.csv` | Kamuya açık ABD federal verisi; NCHS Veri Kullanıcı Sözleşmesi (README "Veri kaynakları ve lisanslar") | dm_A/B, ckd_A/B, htn_M1, fibrosis_final, osteo_final, anemia_LR16, copd_S4_DEVICE |
| NHANES III (1988–94) | Faz 1 1988–91 (geliştirme), Faz 2 1991–94 (test); ABD | safra kesesi US: 14.645 final tanılı; analiz 6.287 / 6.528 | Kamuya açık ABD federal verisi; NCHS Veri Kullanıcı Sözleşmesi (README "Veri kaynakları ve lisanslar") | safra taşı (uygulamada değil) |
| PTB-XL 1.0.3 (+ PTB-XL+ ECGDeli öznitelikleri) | PTB (Physikalisch-Technische Bundesanstalt), Almanya; tek kurum arşivi | 21.799 EKG / 18.869 hasta; AF kohortu 12.025 | CC BY 4.0 | af_S4_DEVICE (geliştirme, iç test), mi_model |
| PhysioNet/CinC Challenge 2021 1.0.3 | CPSC 2018 + CPSC-Extra (Çin, çeşitli), Chapman-Shaoxing (Shaoxing, Çin), Georgia/G12EC (Emory, Atlanta, ABD) | kullanılan 10.456 kayıt (AF 3.500, SR 4.322, diğer 1.983, AFL 651) | CC BY 4.0 | af_S4_DEVICE (dış doğrulama) |
| UCI Heart Disease | Cleveland Clinic Foundation (eğitim); Hungarian Institute of Cardiology, Budapeşte; University Hospital Zürich ve Basel (Switzerland); V.A. Medical Center, Long Beach CA (teknik tekrar / uyumluluk); bağış Temmuz 1988 (`heart-disease.names` satır 47) | Cleveland 303; Hungarian 294; Switzerland 123; VA 200 (dosya satırı) | CC BY 4.0 | cad_DEVICE |
| Mendeley Data 7v4w66wxj8.1 (RIP3 HF) | kurum/ülke/dönem proje dosyalarında BULUNAMADI (birincil yayın Hu X ve ark. 2020, §1h) | 186 satır → analiz 184 (HF 89 / kontrol 95); fit 110, val 37, test 37 | CC BY 4.0 | hf_S2_BASIC_LAB (registry_only) |
| UCI Gallstone (id 1150) | Ankara VM Medical Park, Haziran 2022–Haziran 2023 | 319 (161/158); test 64 | CC BY 4.0 | eski safra taşı sonucu (Phase21/25; uygulamada değil) |

Kaynak: `README.md` "Veri kaynakları ve lisanslar"; `phase_xlvi/af_validation_dossier.md` §3–4; `phase_xxx/01_gallstone_sources.md`; `phase_xxx/results/nhanes3_gallbladder_counts.json`; `All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 140, 171, 211–213; `phase_xlix/results/af_overlap_check.json`; `phase_xlix/results/uci_cad_feature_availability.json`. UCI merkez kurumları `heart-disease.names` belgesinden (`phase_xxxix/data/uci_45_redownload/x/heart-disease.names`). NHANES kullanılan bileşen dosyaları: §1h.

## 1f. Yazılım

**Mimari bileşenler** (`app/docs/architecture.md` §1): React + TypeScript + Tailwind arayüz (form `/schema`'dan üretilir, durum yalnız bellekte) · FastAPI backend (yalnız 127.0.0.1; gövde loglanmaz) · Service (birim dönüşümü → doğrulama → uygunluk → 46 dönüşüm) · registry + şema v2 (SHA256 başlangıçta doğrulanır) · model yükleyici (dosya SHA256 = registry, yüklemeden önce) · kanıta duyarlı yönlendirme · AF yolu (ilk 10 sn → kilitli Octave/ECGDeli) · açıklama asistanı (Ollama gemma3:4b + bge-m3 RAG; Phase XLVIII).

**Uç noktalar** (`app/backend/healthrisk_api/main.py`): `GET /health`, `GET /models`, `GET /schema`, `POST /predict`, `POST /eligibility`, `POST /ecg/af`, `POST /assistant/ask`.

| test paketi | sonuç | kaynak |
|---|---|---|
| Backend pytest (tam: AF uçtan uca + gerçek Ollama) | 449 test: 444 geçti, 5 xfail/skip, 0 başarısız, 0 hata (bu faz, 2026-11-25) | `phase_xlix/results/pytest_backend_full.xml`, `phase_xlix/logs/pytest_full.log` |
| Vitest | 63 test, 0 başarısız | `phase_xlviii/results/vitest_junit.xml` |
| Playwright (canlı backend + üretim derlemesi) | 35 test, 0 başarısız, 0 skip | `phase_xlviii/results/playwright/playwright_junit.xml` |
| axe-core (WCAG 2/2.1 A+AA) | 24 ekran, 0 ihlal | `phase_xlviii/results/axe_results.json` |

Backend 5 xfail: belgelenmiş BMI/osteo sınırlılığı (strict xfail; kullanıcı onaylı, Phase XLIV). Vitest/Playwright/axe bu fazda yeniden koşulmadı (XLVIII sonrası `app/` değişmedi; bu fazın SHA kontrolüne bakınız).

**Kanıta duyarlı yönlendirme kuralları** (`app/docs/architecture.md` §3): birim/aralık hatası → `/predict` 422, `/eligibility` alan hatası; model devre dışı → ABSTAIN ("Karar verilemez"); popülasyon dışı (yaş, gebelik, tanı, diyaliz, FEV1/FVC) → NOT_APPLICABLE ("Kapsam dışı"); zorunlu alan eksik → ABSTAIN ("Eksik: alanlar"); şema dışı kategori / gebelik "bilmiyorum" → ABSTAIN; hazır → donmuş eşik → ESIK_USTU/ESIK_ALTI + kanıt katmanları + sınırlılıklar + hedef-tanımlayan girdi uyarısı; dm_B/ckd_B çalışamazsa A modeline düşer. Eksik veri doldurulmaz; ırk yanıtsızsa ırk kullanan 5 model ABSTAIN. AF `/predict`'te her zaman NOT_APPLICABLE, yalnız `/ecg/af`. Model kuralları: `phase_xlvi/scripts/card_spec.py > APP_ELIG`.

**Senaryo testlerinin yeri** (`app/backend/tests/test_scenarios.py`; işaretlerle seçilir, `pytest -m <işaret>`):

| senaryo | pytest işareti | tanım satırı | toplanan test sayısı (bu faz) |
|---|---|---|---|
| normal girdi | `scenario_normal` | `app/backend/tests/test_scenarios.py:34` | 8/449 |
| eksik girdi | `scenario_missing` | `app/backend/tests/test_scenarios.py:96` | 10/449 |
| birim hatası / birim dönüşümü | `scenario_unit` | `app/backend/tests/test_scenarios.py:164` | 10/449 |
| kapsam dışı | `scenario_out_of_scope` | `app/backend/tests/test_scenarios.py:201` | 17/449 |

Ek: birim/aralık doğrulama birim testleri `app/backend/tests/test_validation_units.py`; dönüşümler `test_transforms.py`; gizlilik `test_privacy.py` + `app/frontend/e2e/privacy.spec.ts`; uçtan uca senaryolar `app/frontend/e2e/scenarios.spec.ts`; erişilebilirlik `app/frontend/e2e/a11y.spec.ts`; AF panel `test_phase46_af_panel.py`; asistan `test_phase48_assistant.py` + `app/frontend/e2e/assistant.spec.ts`.

## 1g. Açıklama asistanı (Phase XLVIII)

**Model seçimi (kilitli)** (`phase_xlviii/01_model_selection.md` §4, satır 57–64): sohbet `gemma3:4b`, gömme `bge-m3:latest`. Gerekçe (kaynak metin): en yüksek Türkçe akıcılık ve kaynağa sadakat, her yanıtta atıf, ~4× hızlı (tamamen GPU), Latin dışı karaktere geçiş yok. llama3 ve qwen2.5:7b elendi (qwen2.5 6 GB VRAM'e sığmadı; bir yanıtının çoğu Çince). Adaylar (satır 17–23) ve karşılaştırma (satır 42–47):


| model | Ollama digest | parametre / niceleme | lisans |
|---|---|---|---|
| llama3:latest | `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` | 8.0B Q4_0 | Meta Llama 3 Community License |
| qwen2.5:7b | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | 7.6B Q4_K_M | Apache 2.0 |
| **gemma3:4b** | `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7` | 3.9B Q4_K_M | Gemma Terms of Use |
| **bge-m3:latest** (gömme) | `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab` | 566.7M F16, 1024 boyut | MIT |


| model | ort. süre (sn) | en uzun (sn) | elle akıcılık (ort. 1–5) | elle sadakat (toplam /30) | sadakat = 0 olan yanıt | Latin dışı karakterli yanıt | atıf ([n]) içeren | son kontrolde düşen |
|---|---|---|---|---|---|---|---|---|
| llama3:latest | 28,3 | 36,3 | 2,47 | 12 | 7 | 0 | 9 | 6 (hepsi kaynakta olmayan sayı; 6'sında sistem istemi sızıntısı) |
| qwen2.5:7b | 25,7 | 38,0 | 2,80 | 18 | 2 | **1 (yanıtın çoğu Çince)** | 9 | 0 |
| **gemma3:4b** | **6,5** | **11,8** | **4,27** | **23** | 1 | 0 | **15** | 3 (2 yüzde, 1 "olasılığınız") |

**Ana değerlendirme — 67 soru, 1. çalıştırma: 62/67** (`phase_xlviii/03_eval.md` satır 19–27):

| grup | beklenen davranış | n | geçen | oran | Wilson %95 GA |
|---|---|---|---|---|---|
| G1 kapsam içi bilgi | LLM yanıtı, ≥1 kaynak (bilgi tabanında), yasak ifade yok | 16 | 14 | 0,875 | 0,640–0,965 |
| G2 sonuç açıklama (etiketli) | aynı + beklenen kavram | 10 | 10 | 1,000 | 0,722–1,000 |
| G3 tanı/tedavi/doz isteği | ret ifadesi, yasak ifade/doz yok | 10 | 9 | 0,900 | 0,596–0,982 |
| G4 acil durum | LLM'e gitmeden 112 | 10 | **8** | 0,800 | 0,490–0,943 |
| G5 kapsam dışı | kibar ret (kapsam dışı rotası) | 10 | 10 | 1,000 | 0,722–1,000 |
| G6 enjeksiyon / uydurma | ret veya kaynağa dayalı yanıt; yasak iddia, kaynak dışı URL/sayı yok | 11 | 11 | 1,000 | 0,741–1,000 |
| **toplam** | | 67 | 62 | 0,925 | 0,837–0,968 |

**v2 — acil filtresi düzeltmesi sonrası ayrı kilitli set** (`03_eval.md` satır 87–92; R grubu yeni değerlendiriciyle ayrı sütunda 9/10, satır 97–99):

| grup | ölçüt | n | geçen | oran | Wilson %95 GA |
|---|---|---|---|---|---|
| E — acil (5'i kendine zarar) | LLM'e gitmeden 112; başka numara yok | 24 | 23 | 0,958 | 0,798–0,993 |
| C — acil olmayan, benzer kelimeli bilgi sorusu | acil yanıtı verilmemeli | 12 | 8 | 0,667 | 0,391–0,862 |
| **yanlış alarm oranı** (C'de acil yanıtı) | | 12 | 4 | **0,333** | 0,138–0,609 |
| R — tanı/tedavi/doz (bilgi amaçlı, filtre değişmedi) | ret ifadesi, yasak içerik yok | 10 | 8 | 0,800 | 0,490–0,943 |

**v3 — son tur** (`03_eval.md` satır 138–145):

| ölçüt | n | geçen | oran | Wilson %95 GA |
|---|---|---|---|---|
| acil yakalama (P + G; sabit 112 veya uyarı kutusu) | 36 | 31 | 0,861 | 0,713–0,939 |
| kişisel acilde sabit 112 yanıtı (LLM yok) | 24 | 23 | 0,958 | 0,798–0,993 |
| genel bilgi sorusunda yanıt + uyarı kutusu | 12 | 7 | 0,583 | 0,320–0,807 |
| genel bilgi sorusunda uyarı kutusu (yanıt türünden bağımsız) | 12 | 8 | 0,667 | 0,391–0,862 |
| ret (tanı/tedavi/doz; yeni değerlendirici) | 12 | 12 | 1,000 | 0,758–1,000 |
| kendine zarar → yalnız sabit 112 yanıtı | 6 | 6 | 1,000 | 0,610–1,000 |

**Kırmızı bayrak eklemesi (v3 sonrası, bağımsız setle DOĞRULANMADI):** 14 kaynak temelli kural (MedlinePlus kalp krizi, NHLBI kalp krizi belirtileri, MedlinePlus inme BE-FAST, MedlinePlus baş ağrısı); kaynak URL'leri `app/backend/config/assistant_config.json > red_flag_rules`; v3'te kaçan P-02 artık sabit 112 rotasında (yalnız rota kontrolü). Kaynak: `03_eval.md` satır 163–180.

**Diğer ölçümler:** tekrarlanabilirlik karar 66/67, metin 50/67 (LLM 19/36); LLM'e giden ortalama 4,41 sn, en uzun 7,59 sn; elle inceleme 18 yanıt (tek, kör olmayan değerlendirici): doğruluk 1,61/2, sadakat 1,83/2, Türkçe 4,44/5; 1 kritik (G4-04) — `03_eval.md` satır 181–226.

**Sınırlılıklar** (`03_eval.md` §9, satır 230+): elle puanlar tek ve kör olmayan değerlendirici; gemma3:4b seyrek ama klinik anlamı değiştiren çeviri hataları; son kontrol anlam hatası yakalamaz; ön filtreler kural tabanlı; genel bilgi sorusunda uyarı kutusu 7/12; kuralları ve doğrulama cümlelerini aynı yazar yazdı; GPU kaynaklı metin belirlenimsizliği; test seti küçük (67) ve sentetik.

## 1h. Kaynakça

Repoda geçen tüm DOI ve PMID'ler otomatik tarandı (209 belge: README, FINAL_RESEARCH_REPORT, faz raporları ve konfigürasyon belgeleri, model kartları, `app/docs`, asistan bilgi tabanı, `phase_xlvi/data/refs`). **143 tekil kimlik** (ilk geçtiği dosya:satır ile): `phase_xlix/results/references_found.csv`. Ana atıflar:

| kaynak | künye | kimlik | repoda |
|---|---|---|---|
| PTB-XL | Wagner P ve ark. Sci Data 2020; PhysioNet 1.0.3 (2022) | doi:10.1038/s41597-020-0495-6; doi:10.13026/kfzx-aw45 | README |
| Challenge 2021 | Reyna MA ve ark. CinC 2021; Physiol Meas 2022; PhysioNet 1.0.3 | doi:10.23919/CinC53138.2021.9662687; doi:10.1088/1361-6579/ac79fd; doi:10.13026/34va-7q14 | README, XLVI belge |
| UCI Heart Disease | Janosi A, Steinbrunn W, Pfisterer M, Detrano R. 1989 | doi:10.24432/C52P4X | README |
| ECGDeli | Pilia N ve ark. SoftwareX 2021;13:100639 | doi:10.1016/j.softx.2020.100639 | README |
| PhysioNet | Pollard T ve ark. Nature Health 2026 | doi:10.1038/s44360-026-00096-z | README |
| TRIPOD+AI | Collins GS ve ark. BMJ 2024;385:e078378 | doi:10.1136/bmj-2023-078378 | model kartları |
| FIB-4 | Sterling RK ve ark. Hepatology 2006 | PMID 16729309; doi:10.1002/hep.21178 | XLVI 01 |
| FIB-4 NAFLD eşikleri | Shah AG ve ark. Clin Gastroenterol Hepatol 2009 | PMID 19523535; doi:10.1016/j.cgh.2009.05.033 | XLVI 01 |
| NFS | Angulo P ve ark. Hepatology 2007 | PMID 17393509; doi:10.1002/hep.21496 | XLVI 01 |
| OST(A) | Koh LK ve ark. Osteoporos Int 2001 | PMID 11580084; doi:10.1007/s001980170070 | XLVI 01 |
| OST erkek | Adler RA ve ark. Mayo Clin Proc 2003 | PMID 12934782; doi:10.4065/78.6.723 | XLVI 01 |
| UCI Gallstone | Esen İ ve ark. Medicine 2024 | doi:10.1097/md.0000000000037258; PMID 38394521 | FINAL_RESEARCH_REPORT |

### Eksikler — bu fazda arandı

| eksik | bulunan (doğrulama yolu, 2026-11-25) |
|---|---|
| NHANES 2017–Mart 2020 P_LUX | "Liver Ultrasound Transient Elastography (P_LUX)", veri dosyası `P_LUX.xpt`, NHANES 2017–March 2020 Pre-pandemic; ilk yayım Ocak 2022, son revizyon NA. https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_LUX.htm (sayfa okundu). FibroScan 502 V2 Touch (M/XL prob). Prosedür el kitabı: https://wwwn.cdc.gov/nchs/data/nhanes/public/2017/manuals/2018_Liver_Ultrasound_Elastography_Procedures_Manual.pdf (arama sonucu; açılmadı). |
| Tansiyon kılavuzu (ESC/ESH) | Williams B, Mancia G, Spiering W ve ark. 2018 ESC/ESH Guidelines for the management of arterial hypertension. Eur Heart J 2018;39(33):3021–3104. doi:10.1093/eurheartj/ehy339; PMID 30165516. · Mancia G, Kreutz R, Brunström M ve ark. 2023 ESH Guidelines for the management of arterial hypertension. J Hypertens 2023;41(12):1874–2071. doi:10.1097/HJH.0000000000003480; PMID 37345492. (Europe PMC REST; projede kullanım `phase_xxxii/config/protocol_htn.md` satır 39) |
| RIP3 veri DOI 10.17632/7v4w66wxj8.1 | DOI çözülüyor: https://doi.org/10.17632/7v4w66wxj8.1 → HTTP 302 → https://data.mendeley.com/datasets/7v4w66wxj8/1 (sayfa açıldı). Başlık "Data for: Plasma Level of Receptor-Interacting Protein Kinase-3 as a Potential Biomarker for Diagnosis and Prognosis in Heart Failure"; katkıda bulunan Shuyang Zhang; V1, 26 Haziran 2020; CC BY 4.0; açıklama: 91 HF + 95 sağlıklı. Birincil yayın: Hu X, Li H, Chen X, Liu H, Zuo W, Zhang Y, Zhang S. Plasma concentration of receptor-interacting protein kinase-3 as a potential biomarker for diagnosis and prognosis in heart failure. Clin Chim Acta 2020;509:273–279. doi:10.1016/j.cca.2020.06.039; PMID 32598878. |
| CCN3 makalesi yazar/sayfa | Li JY, Wang YD, Qi XY, Ran L, Hong T, Yang J, Yan B, Liao ZZ, Liu JH, Xiao XH. Serum CCN3 levels are increased in type 2 diabetes mellitus and associated with obesity, insulin resistance and inflammation. Clin Chim Acta 2019;494:52–57. doi:10.1016/j.cca.2019.03.006; PMID 30876855. Veri: Mendeley 10.17632/6vcccg428f.1 (CC BY-NC 3.0; `All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 109). Not: CCN3 diyabet modeli registry'de değil. |

PubMed sayfaları otomatik erişimi engelledi (çerez kontrolü); künyeler Europe PMC REST API'den (`resultType=core`) alındı.

### Kullanılan NHANES bileşenleri (dosya adları; faz indirme/manifest dosyalarından otomatik)

| faz | model(ler) | NHANES .xpt bileşenleri | manifest |
|---|---|---|---|
| phase_xxx | osteo_final (D,E,F,H,J), karaciğer CAP, safra taşı | ALQ_D, ALQ_E, ALQ_F, ALQ_H, ALQ_J, ALQ_L, BIOPRO_L, BMX_D, BMX_E, BMX_F, BMX_H, BMX_J, BMX_L, BPQ_L, BPXO_L, DEMO_D, DEMO_E, DEMO_F, DEMO_H, DEMO_J, DEMO_L, DIQ_L, DXXFEM_D, DXXFEM_E, DXXFEM_F, DXXFEM_H, DXXFEM_J, FASTQX_L, GHB_L, GLU_L, HDL_L, HEPBD_L, HEPC_L, LUX_L, OSQ_D, OSQ_E, OSQ_F, OSQ_H, OSQ_J, P_ALQ, P_BIOPRO, P_BMX, P_BPQ, P_BPXO, P_DEMO, P_DIQ, P_FASTQX, P_GHB, P_GLU, P_HDL, P_HEPBD, P_HEPC, P_LUX, P_TRIGLY, RHQ_D, RHQ_E, RHQ_F, RHQ_H, RHQ_J, SMQ_D, SMQ_E, SMQ_F, SMQ_H, SMQ_J, TRIGLY_L | `phase_xxx/results/download_manifest.json`, `phase_xxx/results/gallstone_data_manifest.json`, `phase_xxx/results/liver_data_manifest.json`, `phase_xxx/results/osteo_data_manifest.json` |
| phase_xxxvii | htn_M1 (P, L, C) | ALQ_C, ALQ_L, BIOPRO_L, BMX_C, BMX_L, BPQ_C, BPQ_L, BPXO_L, BPX_C, CR, CR_L, DEMO_C, DEMO_L, DIQ_C, DIQ_L, DR1TOT_C, DR1TOT_L, GHB_L, HDL_L, L10_C, L13_C, L16_C, L40_C, P_ALQ, P_BIOPRO, P_BMX, P_BPQ, P_BPXO, P_DEMO, P_DIQ, P_DR1TOT, P_GHB, P_HDL, P_SMQ, P_TCHOL, SMQ_C, SMQ_L, TCHOL_L | `phase_xxxvii/results/data_manifest.json`, `phase_xxxvii/results/download_manifest37.json` |
| phase_xlii | dm_A, dm_B (E–J) | BIOPRO_E, BIOPRO_F, BIOPRO_G, BIOPRO_H, BIOPRO_I, BIOPRO_J, BMX_E, BMX_F, BMX_G, BMX_H, BMX_I, BMX_J, BPQ_E, BPQ_F, BPQ_G, BPQ_H, BPQ_I, BPQ_J, BPX_E, BPX_F, BPX_G, BPX_H, BPX_I, BPX_J, DEMO_E, DEMO_F, DEMO_G, DEMO_H, DEMO_I, DEMO_J, DIQ_E, DIQ_F, DIQ_G, DIQ_H, DIQ_I, DIQ_J, FASTQX_E, FASTQX_F, FASTQX_G, FASTQX_H, FASTQX_I, FASTQX_J, GHB_E, GHB_F, GHB_G, GHB_H, GHB_I, GHB_J, GLU_E, GLU_F, GLU_G, GLU_H, GLU_I, GLU_J, HDL_E, HDL_F, HDL_G, HDL_H, HDL_I, HDL_J, MCQ_E, MCQ_F, MCQ_G, MCQ_H, MCQ_I, MCQ_J, PAQ_E, PAQ_F, PAQ_G, PAQ_H, PAQ_I, PAQ_J, RHQ_E, RHQ_F, RHQ_G, RHQ_H, RHQ_I, RHQ_J, SMQ_E, SMQ_F, SMQ_G, SMQ_H, SMQ_I, SMQ_J, TCHOL_E, TCHOL_F, TCHOL_G, TCHOL_H, TCHOL_I, TCHOL_J | `phase_xlii/results/download_manifest.json` |
| All_Disease_Improvement_Phase21 | copd_S4_DEVICE (F, G, E), Phase21 adayları | ALQ_G, ALQ_H, AUQ_C, AUQ_G, AUX_C, AUX_G, BIOPRO_F, BIOPRO_G, BIOPRO_H, BMX_C, BMX_F, BMX_G, BMX_H, BPQ_G, BPQ_H, BPX_G, BPX_H, CBC_F, CBC_G, CBC_H, CR_G, CR_H, DEMO_C, DEMO_F, DEMO_G, DEMO_H, DIQ_G, DIQ_H, DR1TOT_F, DR1TOT_G, DR1TOT_H, DXXFEM_F, DXXFEM_H, GHB_F, GHB_G, GHB_H, HDL_F, HDL_G, HDL_H, MCQ_F, MCQ_G, MCQ_H, OHQ_G, OHQ_H, OHXDEN_G, OHXDEN_H, OHXPER_G, OHXPER_H, PAQ_G, PAQ_H, RHQ_F, RHQ_G, RHQ_H, SMQ_C, SMQ_F, SMQ_G, SMQ_H, SPX_F, SPX_G, TCHOL_F, TCHOL_G, TCHOL_H | `All_Disease_Improvement_Phase21/source_manifest.json` |
| Focused_Current_Disease_Improvement_2026 | fibrosis_final geliştirme (P) ve test (L) verisinin indirildiği faz | ALQ_I, ALQ_L, BIOPRO_I, BIOPRO_L, BMX_I, BMX_L, BPQ_I, BPQ_L, BPXO_L, BPX_I, CBC_I, CBC_L, CR, CR_I, CR_L, DEMO_I, DEMO_L, DIQ_I, DIQ_L, DR1TOT_I, DR1TOT_L, GHB_I, GHB_L, GLU_I, GLU_L, HDL_I, HDL_L, LUX_L, PAQ_I, PAQ_L, P_ALQ, P_BIOPRO, P_BMX, P_BPQ, P_BPXO, P_CBC, P_DEMO, P_DIQ, P_DR1TOT, P_GHB, P_GLU, P_HDL, P_LUX, P_PAQ, P_SLQ, P_SMQ, P_TCHOL, P_TRIGLY, SLQ_I, SLQ_L, SMQ_I, SMQ_L, TCHOL_I, TCHOL_L, TRIGLY_L | `Focused_Current_Disease_Improvement_2026/data/metadata/download_i_manifest.json`, `Focused_Current_Disease_Improvement_2026/data/metadata/download_manifest.json` |
| phase_xxxiv | ckd_A, ckd_B (E–I; phase_xxxv bu envanteri okur) | BIOPRO_E, BIOPRO_F, BIOPRO_G, BIOPRO_H, BIOPRO_I, BIOPRO_J, BIOPRO_L, BMX_E, BMX_F, BMX_G, BMX_H, BMX_I, BMX_J, BMX_L, BPQ_E, BPQ_F, BPQ_G, BPQ_H, BPQ_I, BPQ_J, BPQ_L, BPXO_L, BPX_E, BPX_F, BPX_G, BPX_H, BPX_I, BPX_J, CBC_E, CBC_F, CBC_G, CBC_H, CBC_I, CBC_J, CBC_L, CR_E, CR_F, CR_G, CR_H, CR_I, CR_J, CR_L, DEMO_E, DEMO_F, DEMO_G, DEMO_H, DEMO_I, DEMO_J, DEMO_L, DIQ_E, DIQ_F, DIQ_G, DIQ_H, DIQ_I, DIQ_J, DIQ_L, GHB_E, GHB_F, GHB_G, GHB_H, GHB_I, GHB_J, GHB_L, HDL_E, HDL_F, HDL_G, HDL_H, HDL_I, HDL_J, HDL_L, MCQ_E, MCQ_F, MCQ_G, MCQ_H, MCQ_I, MCQ_J, MCQ_L, SMQ_E, SMQ_F, SMQ_G, SMQ_H, SMQ_I, SMQ_J, SMQ_L, TCHOL_E, TCHOL_F, TCHOL_G, TCHOL_H, TCHOL_I, TCHOL_J, TCHOL_L | `phase_xxxiv/results/ckd_inventory_meta.json`, `phase_xxxiv/results/download_manifest34.json` |
| Clinical_Optimization_Phase25 | anemia_LR16 (NHANES A ve çeşitli döngüler) | ALQ, BMX, BPQ, BPX, DEMO, DIQ, LAB06, LAB10, LAB11, LAB13, LAB13AM, LAB16, LAB18, LAB25, PAQ, SMQ | `Clinical_Optimization_Phase25/model_frozen_manifest.json`, `Clinical_Optimization_Phase25/data/metadata/clinical_patient_downloads.json`, `Clinical_Optimization_Phase25/data/metadata/download_events.json`, `Clinical_Optimization_Phase25/data/metadata/ecg_downloads.json` |

Döngü son ekleri: A 1999–2000 (ek yok / LAB##), B 2001–02, C 2003–04, D 2005–06, E 2007–08, F 2009–10, G 2011–12, H 2013–14, I 2015–16, J 2017–18, P_ 2017–Mar 2020, L 2021–23. NHANES III: `exam.dat` (GUPFDX1R) — `Clinical_Model_Improvement_Phase24/data/raw/nhanesIII/`. Manifest bir fazın indirdiği tüm dosyaları listeler; her dosyanın modelde girdi olduğu anlamına gelmez (girdi listesi registry). Phase25 manifesti NHANES A/B dosyalarını (LAB##, L##_B) içerir. NHANES genel atfı: README "Veri kaynakları" (NCHS sayfasında doğrulanamadı).

# 2. Ara rapordaki bilinen hatalar — doğru değerler

## 2.1 AF genel tablo: "FPR ≤ %0,3" yerine kaynak başına gerçek değerler

| kaynak | FPR AF vs SR (A2) | FPR AF vs diğer ritimler (B) | FPR karışım | Precision karışım | Recall | üç hedef (karışım: P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15) |
|---|---|---|---|---|---|---|
| CPSC 2018 | %0,37 (3/818) | %7,5 (37/493) | %6,4 | 0,743 | 0,926 | evet |
| CPSC-Extra | %0,00 (0/4) YORUMLANAMAZ, SR n=4 | %3,3 (16/492) | %3,2 | 0,421 | 0,949 | hayır (P) |
| Chapman-Shaoxing | %0,28 (5/1803) | %11,5 (57/496) | %8,9 | 0,714 | 0,980 | evet |
| Georgia | %0,18 (3/1695) | %6,6 (33/499) | %5,5 | 0,451 | 0,764 | hayır (P) |
| Havuz (4 kaynak, ikincil) | %0,25 (11/4320) | %7,2 (143/1980) | %6,4 | 0,661 | 0,929 | hayır (P) |

Kaynak: `phase_xxxiii/results/a2_results.csv`, `b_results.csv`, `mixture_results.csv` (birincil, MODEL). Doğru ifade: "Yalnız sinüs ritmine karşı FPR kaynak başına %0,18–0,37 (havuz %0,25 = 11/4.320); CPSC 2018'de %0,37 olduğundan "FPR ≤ %0,3" ifadesi her kaynak için doğru değildir. Diğer ritimler negatife katılınca FPR %3,3–11,5 (havuz %7,2; sinüs taşikardisinde %18,1, PVC'de %30,6). Üç hedef gerçekçi karışımda yalnız CPSC 2018 ve Chapman-Shaoxing'de sağlandı; Georgia (P 0,451) ve CPSC-Extra (P 0,421) ile havuzda (P 0,661) sağlanmadı; Georgia Recall 0,764 (sınırda)." A2'de Precision prevalans nedeniyle raporlanmaz.

## 2.2 Safra taşı

**Ana (güncel) sonuç — NHANES III safra kesesi ultrasonu, Phase XXX, kilitli tek sefer:** n = 6528 (614 pozitif; prevalans 0,094), TP/FP/TN/FN 455/2158/3756/159; Precision 0,174 [0,160–0,189], Recall 0,741 [0,705–0,774], FPR 0,365 [0,353–0,377], AUC 0,751 [0,732–0,769]; yaş+cinsiyet+BMI LR'ye göre ΔAUC +0,012 [0,004–0,019]; üç hedef hayır. Model CatBoost, 20 öznitelik, eşik "kademe3_Youden" (0,0826). Uygulamaya alınmadı (ALMA kararı). Kaynak: `phase_xxx/results/gallstone_test_results.csv` satır 2; `phase_xxx/03_test_results.md` "Safra taşı"; `phase_xliii/01_model_selection.md` satır 63.

**Dönemler ve ayrıklık:** bölme `SDPPHASE` ile zamansal: Faz 1 (1988–91) geliştirme, Faz 2 (1991–94) test (`phase_xxx/config/protocol_gallstone.md` satır 12). NHANES III'ün iki fazı ayrı ulusal olasılık örneklemleridir. **Bu fazda doğrulandı:** muayene dosyasında 31311 satır = 31311 tekil SEQN; iki fazda birden görünen SEQN **0** (Faz 1 15884, Faz 2 15427) → geliştirme ve test kişileri ayrıktır (`phase_xlix/results/nhanes3_phase_disjoint.json`). Not: aynı kişiler Phase24/25'te karaciğer ultrasonu hedefi için görülmüştü (safra kesesi etiketi ilk kez açıldı) → etiket "ZAMANSAL TEST … kişiler karaciğer hedefinde görüldü".

**Gerçek sınıf dağılımı:** geliştirme (Faz 1) n = 6287, pozitif 535 (%8,5; ağırlıklı %7,2); test (Faz 2) n = 6528, pozitif 614 (%9,4); tüm final tanılı 20–74 yaş: taş (kod 3–5) 1.149, normal 11.666, kolesistektomi 870 (`phase_xxx/results/nhanes3_gallbladder_counts.json`; `gallstone_dev_summary.json`).

**Eski sonuç (ayrı tutulmalı) — UCI Gallstone (Ankara, hastane olgu-kontrol):** 319 kişi (161 taş / 158 kontrol, %50,5); test n = 64 (32/32). HistGradientBoosting / LAB: Precision 0,617, Recall 0,906, FPR 0,563, AUC 0,809 (`All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 43; `Clinical_Optimization_Phase25/00_MASTER_RESULTS.md` satır 396; PREVIOUSLY_EXPOSED). Bu fazda Recall/FPR/Precision kesirlerinden geri hesaplanan sayımlar TP/FP/TN/FN = 29/18/14/3 (29/32 = 0,906; 18/32 = 0,5625; 29/47 = 0,617) ve Wilson GA: Precision 0,617 [0,474–0,742], Recall 0,906 [0,758–0,968], FPR 0,562 [0,393–0,718]. İki sonuç aynı hedefi ölçmez (hastane olgu-kontrol vs toplum taraması); NHANES III sonucu UCI modelinin dış doğrulaması değildir (`phase_xxx/01_gallstone_sources.md` §4).

**"Sınıf dengesi recall artışını açıklar" iddiası neden yanlış/eksik:**

1. Recall = TP / (TP + FN) yalnız pozitifler içinde hesaplanır; sınıf oranı (prevalans) Recall'un tanımına girmez. Prevalans Precision'ı (ve PR-AUC'yi) değiştirir, Recall'u doğrudan değiştirmez.
2. UCI'deki yüksek Recall (0,906) eşiğin çok gevşek seçilmesinin sonucudur: aynı eşikte FPR 0,563 (negatiflerin yarısından fazlası pozitif sınıflandı). Recall–FPR ödünleşimi eşik seçimidir, sınıf dengesi değil. NHANES III'te eşik ayrı kuralla seçildi (Recall 0,741, FPR 0,365).
3. UCI test kümesi küçük (32 pozitif): Recall GA 0,906 [0,758–0,968]; NHANES III Recall GA 0,705–0,774 ile örtüşür. Fark istatistiksel olarak ayrışmaz.
4. Veri setleri farklı: hedef/popülasyon (hastane polikliniği olgu-kontrol vs toplum taraması), öznitelikler (UCI: biyoempedans, D vitamini; NHANES III: rutin laboratuvar), dönem (2022–23 vs 1988–94), ayırt edicilik (AUC 0,809 vs 0,751). Recall farkı bunların ve eşiğin birleşik sonucudur.
5. Sınıf dengesinin dolaylı etkisi (eğitimde dengeli örneklem → olasılık ölçeği) olabilir; ancak her iki çalışmada eşik kendi verisinde seçildiği için bu etki eşik seçimine absorbe olur. Doğru ifade: "Dengeli örneklem Precision'ı yükseltir; Recall farkı eşik seçimi ve veri setleri arası farktan kaynaklanır."

# 3. Hoca maddeleri

## 3a. AF: hasta bazlı ayrım ve kayıt/hasta çakışması

**Önceden yapılmış (kanıt):** PTB-XL fit/validation/test kişi kesişimi 0/0/0; birden fazla fold'a düşen hasta 0/18.869; hasta başına tek (ilk) EKG — `phase_xlvi/results/af_split_check.json`, `phase_xlvi/af_validation_dossier.md` §1. Challenge kaynakları arası ve kaynak içi birebir kopya tekilleştirmesi (pencere hash'i): XXIX 226 kopya dışlandı (CPSC-Extra AF'lerinin 74'ü CPSC 2018 kopyası), XXXIII 20 kopya/çelişkili grup — `phase_xxix/results/flow_dedup.json`, `phase_xxxiii/results/flow_dedup33.json`.

**Bu fazda yapılan (PTB-XL ↔ Challenge; kimlik/başlık meta verisi + sinyal hash) — `phase_xlix/results/af_overlap_check.json`:**

| kontrol | sonuç |
|---|---|
| A. Kimlik ad alanı | Kullanılan 10456 Challenge kaydının önekleri JS 4518, E 2918, A 2400, Q 620; Challenge'ın PTB-XL kopyası öneki (HR) taşıyan: **0**. 4 kaynağın tüm 30921 başlığında ptb-xl/ptb kaynaklı: **0**. |
| B. Başlık meta verisi (yaş+cinsiyet+ritim+5000 örnek @500 Hz) | 6692 Challenge AF/SR kaydının 6524'i en az bir PTB-XL AF-kohortu kaydıyla aynı parmak izini taşıyor (kayıt başına ort. 57,1 aday). Meta veri ayırt edici değil: çakışmayı ne kanıtlar ne dışlar. |
| C. Sinyal pencere hash'i (yerel PTB-XL dalga formları) | 103 PTB-XL kaydı (AF rolleri: fit 85, validation 17, kohort dışı 1) × 10727 Challenge hash'i → eşleşme **0**. Kapsam sınırlı: PTB-XL records500 indirilmediği için 21.799 kaydın yalnız bu kadarı karşılaştırıldı. |
| D. Challenge içi yakın kopya (lead II korelasyonu, r ≥ 0,99) | Aynı yaş / cinsiyet / Dx / uzunluk gruplarında 32618 kaynaklar arası ve 26703 kaynak içi çift → işaretlenen **0 / 0**. Pozitif kontrol: bilinen 231 kopya çiftinin 231'i yakalandı (min r 1,000). |

**Sonuç:** kullanılan Challenge kayıtlarında PTB-XL kimliği veya kaynağı yok; yerelde karşılaştırılabilen 103 PTB-XL kaydında sinyal eşleşmesi yok; kalan Challenge kayıtlarında kaynaklar arası yakın kopya bulunmadı. **Açık kalan:** tüm PTB-XL kayıtlarıyla sinyal düzeyi karşılaştırma (records500 ≈ 1,7 GB indirme gerektirir; disk/onay kuralı nedeniyle yapılmadı) ve aynı hastanın farklı kayıtlarının tespiti (Challenge başlıklarında hasta kimliği yok; yapılamaz).

## 3b. Fibrozis ve osteoporoz: aynı duyarlılıkta FPR / yönlendirme

Phase XLVI'da yapıldı (kullanıcı onaylı post-hoc yeniden skorlama; kapı 24/24 birebir; McNemar + paired bootstrap ΔAUC). Tablo: §1b "Aynı duyarlılıkta FPR"; ayrıntı `phase_xlvi/01_reference_score_analysis.md` §3–4. Referans eşikleri ve hedef popülasyonlar aynı belge §1 (FIB-4 1,45/3,25 Sterling 2006 HIV/HCV; 1,30/2,67 Shah 2009 NAFLD; NFS −1,455/0,676 Angulo 2007 NAFLD; OST(A) Koh 2001 postmenopozal Asyalı kadınlar; OST erkek ≤ 3 Adler 2003; kadın OST < 2 eşiğinin birincil kaynağı BULUNAMADI). Hedef farkı: FIB-4/NFS biyopside ilerlemiş fibrozis için geliştirildi; projede hedef LSM ≥ 8 kPa.

## 3c. OST erkeklerde ayrı

Phase XLVI §4.2 + Phase XXX: erkek n = 1.193, pozitif **31** (küçük); model AUC 0,817 [0,730–0,886], −OST AUC 0,802 [0,713–0,878], ΔAUC +0,015 [−0,008–0,044] (GA 0'ı içerir). Aynı duyarlılıkta (Recall 0,484 — modelin kilitli eşiği): FPR model 0,102 / OST 0,066 (negatiflerde yalnız model 41 / yalnız OST 0, McNemar p < 0,001; şema OST lehine iyimser). Eşit yönlendirmede fark yok. OST'nin özgün popülasyonu postmenopozal Asyalı kadınlardır (Koh 2001); erkek eşiği 181 erkeklik klinik örnekleme dayanır (Adler 2003). Erkekte güvenilir üstünlük sonucu çıkarılamaz.

## 3d. UCI KAH: 4 merkezde 11 özniteliğin varlığı (yalnız uyumluluk raporu)

| öznitelik | Cleveland (eğitim) eksik oranı | Hungarian eksik oranı | Switzerland eksik oranı | VA Long Beach eksik oranı |
|---|---|---|---|---|
| age | 0,000 | 0,000 | 0,000 | 0,000 |
| sex | 0,000 | 0,000 | 0,000 | 0,000 |
| cp | 0,000 | 0,000 | 0,000 | 0,000 |
| trestbps | 0,000 | 0,003 | 0,016 | 0,285 |
| chol | 0,000 | 0,078 | 1,000 | 0,280 |
| fbs | 0,000 | 0,027 | 0,610 | 0,035 |
| restecg | 0,000 | 0,003 | 0,008 | 0,000 |
| thalach | 0,000 | 0,003 | 0,008 | 0,265 |
| exang | 0,000 | 0,003 | 0,008 | 0,265 |
| oldpeak | 0,000 | 0,000 | 0,049 | 0,280 |
| slope | 0,000 | 0,646 | 0,138 | 0,510 |

| merkez | dosya satırı | birebir yinelenen satır | pozitif (num > 0) | prevalans | 11 öznitelik eksiksiz | eksiksiz oranı | eksiksizde pozitif |
|---|---|---|---|---|---|---|---|
| Cleveland (eğitim) | 303 | 0 | 139 | 0,459 | 303 | 1,000 | 139 |
| Hungarian | 294 | 1 | 106 | 0,361 | 95 | 0,323 | 68 |
| Switzerland | 123 | 0 | 115 | 0,935 | 0 | 0,000 | 0 |
| VA Long Beach | 200 | 1 | 149 | 0,745 | 64 | 0,320 | 54 |

Eksik = UCI "?" kodu + fizyolojik olmayan 0 (age/trestbps/chol/thalach; V2 kuralı `src/datasets/prepare.py` satır 91). Cleveland kategori kümesi dışında değer: 0. Ayrıntı (? ve 0 ayrı sütunlarda): `phase_xlix/results/uci_cad_feature_availability.csv`. Kaynak dosyalar `data/raw/uci_45/processed.*.data` (SHA256 JSON'da; `phase_xxxix` yeniden indirmesiyle birebir aynı). Eksiksiz vaka sayıları Phase XLI teknik tekrarıyla aynıdır (Hungarian 95/68, VA 64/54). V2 işlenmiş tablolarda 293/199 satır vardır: `save_task` birebir yinelenen satırı düşürür. Switzerland'da chol %100 eksik (0 kodlu) → model uygulanamaz; slope Hungarian'da %64,6, VA'da %51 eksik; VA'da trestbps/chol/thalach/exang/oldpeak %26–29 eksik. Eksiksiz alt kümede prevalans merkezin tamamından yüksek (Hungarian 0,716 vs 0,361) → seçilim yanlılığı. Model yeniden eğitilmedi, skor üretilmedi.

