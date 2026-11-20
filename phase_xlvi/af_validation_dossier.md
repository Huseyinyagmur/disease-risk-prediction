# Phase XLVI — AF doğrulama belgesi (`af_S4_DEVICE` + AF-ECGDELI-OCTAVE-v1)

Kapsam: danışman isteği — hasta bazlı ayrım, aynı öznitelik çıkarımı, Challenge 2021 kaynakları, kaynaklar arası ve
PTB-XL ile kayıt çakışması, CPSC-Extra, diğer ritimler. **Tüm sayılar önceki faz dosyalarından okunmuştur**; her
tablonun altında kaynak yolu vardır. Belge `scripts/af_dossier.py` ile üretildi (elle sayı yazılmadı). Bu fazda model
yüklenmedi, tahmin üretilmedi, EKG sinyali okunmadı. Tek yeni hesap §1.2'deki PTB-XL metadata kesişim kontrolüdür
(kimlik ve fold sütunları; tahmin veya sonuç verisi değil).

## 0. Sistem kimliği

| öğe | değer | kaynak |
|---|---|---|
| model | `All_Disease_Improvement_Phase21/models/af_S4_DEVICE.joblib` SHA256 `f4a61af71d7fa1dc…`; LightGBM; 12 öznitelik (yaş, cinsiyet + 10 EKG aralığı) | `phase_xliii/registry/models.json` |
| eşik | 0.2360882764 (donmuş; Phase21 validation BALANCED senaryosu, bkz. model kartı) | registry; `All_Disease_Improvement_Phase21/selected_model_registry.json` |
| hedef | PTB-XL kayıtlarında insan-doğrulamalı 12 derivasyonlu EKG ritminin atriyal fibrilasyon mu sinüs ritmi mi olduğu (AF vs SR; mevcut ritim). | registry |
| pipeline | AF-ECGDELI-OCTAVE-v1; `phase_xxviii/pipeline/af_pipeline_v1.py` SHA256 `2bf3c307024711fd…`; kilit 2026-11-12T09:38:34Z | `phase_xxviii/config/af_pipeline_lock.json` |
| ECGDeli | v1.1; kaynak ağacı SHA256 `cfa133de285a1d8f…` (26 .m) | kilit |
| Octave | 10.3.0 (`octave-cli.exe` SHA256 `14891b7697bdb679…`); paketler signal 1.4.6, statistics 1.7.5, image 2.18.1 | kilit |
| WFDB | vendored 4.3.1 | kilit |
| ön işleme | YOK (ham mV sinyal); 500 Hz; 12 lead | kilit |
| agregasyon | medyan; IQR numpy `linear` (25, 75); son RR tekrarlanmaz | kilit (`aggregation`) |

## 1. PTB-XL: hasta bazlı ayrım

### 1.1 Kural (Phase21)

`All_Disease_Improvement_Phase21/src/preprocessing/prepare.py :: af()`:
1. PTB-XL 1.0.3 `ptbxl_database.csv` hasta başına **en küçük `ecg_id`** (ilk EKG) seçilir. Bu seçim etiket ve kalite
   süzgecinden **önce** yapılır.
2. Yalnız `validated_by_human = True` ve SCP kodlarında AFIB **xor** SR olan, yaşı ≥ 18 kayıtlar kalır.
3. Bölme PTB-XL'in resmî `strat_fold` alanıyla yapılır: 1–8 fit, 9 validation, 10 test. PTB-XL fold'ları hasta
   düzeyinde atanmıştır.
4. Kimlik `person_id = "PTB_" + patient_id`; `config/af_splits.json` kişi kimliklerini saklar.

### 1.2 Kişi kesişimi kanıtı (bu fazda metadata ile yeniden hesaplandı)

`results/af_split_check.json`:
- Bölme boyutları: fit 8839, validation 1614, test 1572.
- Kişi kesişimleri: fit∩validation: **0** · fit∩test: **0** · validation∩test: **0**.
- Birden fazla `strat_fold`'a düşen PTB-XL hastası: **0** / 18869 (tüm veri tabanı,
  21799 EKG). Yani bir hastanın EKG'leri hiçbir zaman farklı fold'lara dağılmaz.
- Phase21 kuralı metadata ile yeniden uygulandı; rol ile `strat_fold` tutarlı: **evet**;
  bölmede olup kurala uymayan kişi: 0.

| rol | n | AF | SR |
|---|---|---|---|
| fit | 8839 | 560 | 8279 |
| validation | 1614 | 117 | 1497 |
| test | 1572 | 114 | 1458 |

Test (fold 10) 114 AF / 1.458 SR ile Phase XXVII'deki iç test sayısıyla aynıdır.

### 1.3 İç test sonucu (Phase XXVII, kilitli eşik)

| n (AF) | TP/FP/TN/FN | P | R | FPR | AUC |
|---|---|---|---|---|---|
| 1572 (114) | 103/15/1443/11 | 0,873 [0,801–0,921] | 0,904 [0,835–0,945] | 0,010 [0,006–0,017] | 0,980 [0,959–0,995] |

Kaynak: `phase_xxvii/results/ci_metrics.csv` (model=af, kume=test). Etiket: İÇ TEST (held-out, daha önce açılmış).

## 2. Öznitelik çıkarımı: eğitim ile dış doğrulama aynı mı?

**Kısa yanıt: birebir aynı değil; farkı ölçüldü ve kilitlendi.**

- **Eğitim ve iç test** (Phase21, XXVII): PhysioNet'in PTB-XL+ veri setindeki hazır ECGDeli öznitelikleri
  (`ecgdeli_features.csv`, "golden"). Bu öznitelikleri üreten yazılım ve ayarlar PTB-XL+ yayıncılarınındır.
- **Dış doğrulama ve uygulama** (XXIX, XXXIII, XLIV): aynı ECGDeli v1.1 kaynağını Octave 10.3.0'da çalıştıran ve
  agregasyonu PTB-XL+ ile eşleştirmek için yeniden yazılan **kilitli** AF-ECGDELI-OCTAVE-v1 pipeline'ı. Agregasyon
  kuralları (son RR tekrarsız, `linear` IQR) Phase XXVII'de 30 kayıtta **post-hoc** bulundu.
- Bağımsız doğrulama Phase XXVIII'de yapıldı: fit/validation'dan 100 PTB-XL kaydı (test hastası 0), kilitli
  tolerans ve kriter (karar uyumu ≥ 0,98 ve medyan |Δp| ≤ 0,02) sonuçtan önce yazıldı.

### 2.1 Öznitelik uyumu (pipeline − golden, 100 kayıt)

| öznitelik | tolerans içinde | tam eşit oranı | medyan |Δ| (ms) | Bland–Altman yanlılık [LoA] (ms) |
|---|---|---|---|---|
| RR_Mean_Global | 98/100 | 0,980 | 0,000 | -0,090 [-4,583; 4,403] |
| RR_Mean_Global_iqr | 98/100 | 0,980 | 0,000 | -0,025 [-3,178; 3,128] |
| QRS_Dur_Global | 100/100 | 0,980 | 0,000 | 0,030 [-0,406; 0,466] |
| QRS_Dur_Global_iqr | 99/100 | 0,970 | 0,000 | 0,030 [-0,871; 0,931] |
| PR_Int_Global | 29/100 | 0,190 | 10,000 | 15,030 [-14,263; 44,323] |
| PR_Int_Global_iqr | 24/100 | 0,090 | 6,500 | -1,220 [-23,998; 21,558] |
| P_Dur_Global | 27/100 | 0,190 | 8,500 | 14,400 [-13,225; 42,025] |
| P_Dur_Global_iqr | 26/100 | 0,060 | 7,000 | 1,035 [-23,024; 25,094] |
| QT_Int_Global | 8/100 | 0,020 | 30,000 | -31,530 [-144,485; 81,425] |
| QT_Int_Global_iqr | 3/100 | 0,010 | 26,000 | -27,395 [-122,655; 67,865] |

Kaynak: `phase_xxviii/results/tol100_feature_parity.csv` (grup = tümü). RR ve QRS ailesi eşleşir. PR, P süresi ve
özellikle QT sapar (QT tolerans içi 8/100).

### 2.2 Model düzeyinde karar uyumu (aynı 100 kayıt, kilitli eşik)

| senaryo | grup | uyumlu | karar uyumu [Wilson %95 GA] | medyan |Δp| | p95 |Δp| |
|---|---|---|---|---|---|
| Tam pipeline (10 feature) | tümü | 99/100 | 0,990 [0,946–0,998] | 0,001 | 0,152 |
| Tam pipeline (10 feature) | AF | 50/50 | 1,000 [0,929–1,000] | 0,012 | 0,237 |
| Tam pipeline (10 feature) | SR | 49/50 | 0,980 [0,895–0,996] | 0,000 | 0,007 |

Kriter sağlandı: **evet** (nokta tahmini). GA alt sınırı kriterin üstünde:
**hayır** (0,946 < 0,98). Yani %98 eşdeğerlik istatistiksel olarak
kanıtlanmadı. Dış doğrulama sonucu "donmuş model + kilitli pipeline" **bileşiminin** performansıdır. AF kayıtlarında
olasılık kayabilir (p95 |Δp| 0,24). Bu yüzden yalnız sabit eşikte karar raporlanır. Kaynak:
`phase_xxviii/results/tol100_model_agreement.csv`, `tol100_verdict.json`.

### 2.3 Uygulama ile araştırma pipeline'ının birebirliği (Phase XLIV)

Uygulama (`app/backend`) kilitli `af_pipeline_v1.py` dosyasını kopyalamadan, SHA256 doğrulamasından sonra çağırır.
10 öznitelik, araştırma fazlarının kayıtlı çıktısıyla karşılaştırıldı:

| test | kayıt | HTTP | durum | max |Δ| (10 öznitelik) | örnek sayısı |
|---|---|---|---|---|---|
| af_e2e | 165 | 200 | OK | 0.0 |  |
| af_e2e | 254 | 200 | OK | 0.0 |  |
| af_e2e | 480 | 200 | OK | 0.0 |  |
| af_e2e | 691 | 200 | OK | 0.0 |  |
| af_e2e | 1039 | 200 | OK | 0.0 |  |
| af_mat_e2e | training/chapman_shaoxing/g1/JS00005 | 200 | OK | 0.0 |  |
| af_mat_e2e | training/cpsc_2018/g1/A0034 | 200 | OK | 0.0 |  |
| af_mat_e2e | training/georgia/g1/E00011 | 200 | OK | 0.0 |  |
| af_long_e2e | training/cpsc_2018/g1/A0005 | 200 | OK | 0.0 | 12500 |
| af_long_e2e | training/cpsc_2018/g1/A0036 | 200 | OK | 0.0 | 15687 |
| af_long_e2e | training/cpsc_2018/g1/A0048 | 200 | OK | 0.0 | 5807 |

Kaynak: `phase_xliv/results/af_e2e.json` (PTB-XL `.hea/.dat`, phase_xxviii ile), `af_mat_e2e.json` (Challenge `.mat`,
phase_xxxiii ile), `af_long_e2e.json` (10 sn'den uzun kayıtlar, "ilk 10 sn" ön adımıyla, phase_xxxiii ile).

### 2.4 "İlk 10 saniye" ön adımı

Kilitli `read_wfdb_500` tam 5.000 örnek (10 sn, 500 Hz) ister. Challenge kayıtlarının bir kısmı 10 sn'den uzundur.
Phase XXIX ve XXXIII bu kayıtlarda kilit dışında bir sarmalayıcı (`read_first10s`, `sampto=5000`) kullandı. Uygulama
aynı fonksiyonu birebir kopyalar (`app/backend/healthrisk_api/ecg_window.py`); kaynak dosya ve fonksiyon gövdesi
SHA256'sı başlangıçta doğrulanır (Phase XLIV kapanış, karar 3). Kilit dosyası değişmedi. Sınırlılık: uzun kayıtta yalnız
ilk 10 sn değerlendirilir; kaydın geri kalanındaki ritim görülmez. Örnek sayısı < 5.000 veya fs ≠ 500 Hz → ABSTAIN.

## 3. Dış doğrulama verisi: PhysioNet/CinC Challenge 2021

| öğe | değer | kaynak |
|---|---|---|
| sürüm | 1.0.3 (`https://physionet.org/files/challenge-2021/1.0.3/`), doi:10.13026/34va-7q14 | `phase_xxix/01_data_flow.md`; README |
| bütünlük | resmî `SHA256SUMS.txt`; header 30.921/30.921, `.mat` (XXIX) 8.059/8.059, (XXXIII B/AFL) 2.668/2.668 SHA ile doğrulandı | `phase_xxix/01_data_flow.md`, `phase_xxxiii/01_data_flow.md` |
| kullanılan kaynaklar | `cpsc_2018`, `cpsc_2018_extra`, `chapman_shaoxing`, `georgia` | XXIX protokol v2 §2 |
| **kullanılmayan** | Ningbo, **PTB-XL kopyası (`training/ptb-xl`, modelin eğitim verisi)**, INCART, PTB (1000 Hz) — indirilmedi | `phase_xxix/config/external_protocol_v2.md` |
| etiket | header Dx (SNOMED CT) kodları: AF 164889003, SR 426783006, AFL 164890007. Pozitif = AF var ve SR yok (AF+AFL pozitif kalır); negatif (A) = SR var, AF ve AFL yok; AF+SR, yalnız AFL, SR+AFL dışlanır | XXIX protokol §4 |
| teknik süzgeç | fs = 500 Hz, 12 lead (sıra/birim), süre ≥ 10 sn, yaş ≥ 18, cinsiyet geçerli | XXIX/XXXIII akış tabloları |

Header-uygun kayıt sayıları (XXXIII): chapman_shaoxing|AF 1780, chapman_shaoxing|AFL 445, chapman_shaoxing|OTHER 6075, chapman_shaoxing|SR 1803, cpsc_2018|AF 1218, cpsc_2018|OTHER 4675, cpsc_2018|SR 821, cpsc_2018_extra|AF 152, cpsc_2018_extra|AFL 53, cpsc_2018_extra|OTHER 3178, cpsc_2018_extra|SR 4, georgia|AF 566, georgia|AFL 170, georgia|OTHER 7761, georgia|SR 1715.

## 4. Kayıt çakışması ve tekilleştirme

### 4.1 Kaynaklar arası ve kaynak içi (yapıldı)

- **Yöntem** (Phase XXIX protokol §3): ilk 5.000 örnek × 12 lead'in ham int16 değerlerinin hash'i ("pencere hash'i").
  Aynı hash'e sahip kayıtlar kopya grubudur. Grup içinde etiketler çelişirse grubun tamamı dışlanır; değilse bir kayıt
  tutulur.
- **AF/SR adaylarında (XXIX):** 8059 aday; sinyal hatası 11; kopya olarak dışlanan
  226; çelişkili etiket 0. Kaynak çiftine göre kopya grupları:
  cpsc_2018: 121, cpsc_2018+cpsc_2018_extra: 74, georgia: 24, chapman_shaoxing: 2. **CPSC-Extra'daki 152 header-uygun AF kaydının
  74'ü CPSC 2018'deki bir kaydın birebir kopyasıydı.** Tam sinyal hash'i aynı kayıt (aday kümesi): 449.
- **Diğer ritim (B) ve AFL kayıtlarında (XXXIII):** XXIX kayıtlarıyla ve kendi içinde aynı yöntem. Dışlananlar:
  cpsc_2018|B|kopya: dışlandı: 2, cpsc_2018|B|çelişkili grup: dışlandı: 1, cpsc_2018_extra|AFL|Phase XXIX kaydının kopyası: dışlandı: 1, cpsc_2018_extra|AFL|kopya: dışlandı: 4, cpsc_2018_extra|AFL|çelişkili grup: dışlandı: 1, cpsc_2018_extra|B|Phase XXIX kaydının kopyası: dışlandı: 2, cpsc_2018_extra|B|kopya: dışlandı: 5, georgia|AFL|kopya: dışlandı: 3, georgia|B|kopya: dışlandı: 1.
- Kaynak: `phase_xxix/results/flow_dedup.json`, `phase_xxxiii/results/flow_dedup33.json`, `phase_xxix/01_data_flow.md`.

### 4.2 PTB-XL ile çakışma

- **Kaynak düzeyinde dışlama yapıldı:** Challenge 2021'in PTB-XL kopyası (`training/ptb-xl`) ve PTB indirilmedi
  (XXIX protokol §1). Kullanılan dört kaynağın kurum/ülke bilgisi proje dosyalarında doğrulanmadı (BULUNAMADI); XXIX
  raporu bu kaynakları "farklı kurum ve ülke" olarak etiketler.
- **Kayıt düzeyinde PTB-XL ↔ Challenge hash karşılaştırması: YAPILMADI** (önceki faz dosyalarında BULUNAMADI). Yerelde
  yalnız 100 civarı PTB-XL dalga formu vardır (`phase_xxviii/data/ptbxl500/`); tam karşılaştırma için PTB-XL
  `records500` indirilmelidir. Bu, açık kalan bir kontroldür.
- **Hasta düzeyinde tekilleştirme yapılamaz:** Challenge header'larında hasta kimliği yoktur (BULUNAMADI). Birebir kopya
  olmayan aynı-hasta kayıtları (ör. aynı hastanın farklı günlerdeki EKG'leri) tespit edilemez.

## 5. Dış doğrulama sonuçları (Phase XXXIII; donmuş model + kilitli pipeline)

Pipeline başarısızları birincil analizde dışlandı (AF 3, SR 2, diğer ritim 3; `phase_xxxiii/01_data_flow.md`).
Yeniden denenen: 0. Baseline: RR_iqr/RR_mean ≥ 0,138235 (PTB-XL validation'da seçilmiş kural).

### 5.1 A2 — AF ve SR, tam örneklem (birincil)

| kaynak | skor | n (AF) | TP/FP/TN/FN | Recall | FPR | AUC | ΔAUC (model − baseline) | not |
|---|---|---|---|---|---|---|---|---|
| CPSC 2018 | MODEL | 1905 (1087) | 1007/3/815/80 | 0,926 [0,909–0,940] | 0,004 [0,001–0,011] | 0,995 [0,992–0,997] | 0,017 [0,011–0,023] |  |
| CPSC 2018 | BASELINE | 1905 (1087) | 935/5/813/152 | 0,860 [0,838–0,880] | 0,006 [0,003–0,014] | 0,978 [0,971–0,985] | — |  |
| CPSC-Extra | MODEL | 82 (78) | 74/0/4/4 | 0,949 [0,875–0,980] | 0,000 [0,000–0,490] | 0,990 [0,962–1,000] | 0,013 [-0,013–0,051] | YORUMLANAMAZ (SR n=4) |
| CPSC-Extra | BASELINE | 82 (78) | 66/0/4/12 | 0,846 [0,750–0,910] | 0,000 [0,000–0,490] | 0,978 [0,936–1,000] | — | YORUMLANAMAZ (SR n=4) |
| Chapman-Shaoxing | MODEL | 3580 (1777) | 1742/5/1798/35 | 0,980 [0,973–0,986] | 0,003 [0,001–0,006] | 1,000 [0,999–1,000] | 0,008 [0,005–0,011] |  |
| Chapman-Shaoxing | BASELINE | 3580 (1777) | 1560/14/1789/217 | 0,878 [0,862–0,892] | 0,008 [0,005–0,013] | 0,992 [0,988–0,995] | — |  |
| Georgia | MODEL | 2250 (555) | 424/3/1692/131 | 0,764 [0,727–0,797] | 0,002 [0,001–0,005] | 0,954 [0,941–0,967] | 0,083 [0,062–0,103] |  |
| Georgia | BASELINE | 2250 (555) | 363/5/1690/192 | 0,654 [0,614–0,692] | 0,003 [0,001–0,007] | 0,871 [0,848–0,895] | — |  |
| Havuz (4 kaynak, ikincil) | MODEL | 7817 (3497) | 3247/11/4309/250 | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | 0,990 [0,987–0,992] | 0,021 [0,018–0,025] |  |
| Havuz (4 kaynak, ikincil) | BASELINE | 7817 (3497) | 2924/24/4296/573 | 0,836 [0,824–0,848] | 0,006 [0,004–0,008] | 0,968 [0,964–0,973] | — |  |

Kaynak: `phase_xxxiii/results/a2_results.csv`. **Precision raporlanmaz**: A2 örneklemindeki AF oranı (havuzda
3497/7817) gerçek kullanım prevalansını temsil etmez (registry `precision_note`).

### 5.2 CPSC-Extra: yalnız 4 negatif

CPSC-Extra'da tekilleştirmeden sonra uygun SR kaydı **4**'tür (AF 78). Bu kaynakta FPR
(0,000, GA 0,000–0,490) ve AUC **yorumlanamaz**. Satır tabloda yine gösterilir ve havuza
katılır; tek başına yorum dışıdır (XXXIII protokol sapması 2: SR n < 30 → "YORUMLANAMAZ"; kural model çıktısı görülmeden
eklendi). Aynı kaynakta diğer ritim negatifi 492'dir; B analizinde bu kaynak yorumlanabilir.

### 5.3 B — AF ve diğer ritimler (ikincil analiz)

Negatif sınıf: SR dışındaki ritimler (kaynak başına 500 kayıt çekildi, tekilleştirildi). Eğitimde bu ritimler negatif
değildi.

| kaynak | skor | n (AF) | TP/FP/TN/FN | Recall | FPR | AUC | ΔAUC | not |
|---|---|---|---|---|---|---|---|---|
| CPSC 2018 | MODEL | 1580 (1087) | 1007/37/456/80 | 0,926 [0,909–0,940] | 0,075 [0,055–0,102] | 0,965 [0,954–0,974] | 0,060 [0,040–0,079] |  |
| CPSC 2018 | BASELINE | 1580 (1087) | 935/54/439/152 | 0,860 [0,838–0,880] | 0,110 [0,085–0,140] | 0,905 [0,883–0,926] | — |  |
| CPSC-Extra | MODEL | 570 (78) | 74/16/476/4 | 0,949 [0,875–0,980] | 0,033 [0,020–0,052] | 0,977 [0,950–0,994] | 0,024 [0,003–0,046] |  |
| CPSC-Extra | BASELINE | 570 (78) | 66/23/469/12 | 0,846 [0,750–0,910] | 0,047 [0,031–0,069] | 0,953 [0,926–0,976] | — |  |
| Chapman-Shaoxing | MODEL | 2273 (1777) | 1742/57/439/35 | 0,980 [0,973–0,986] | 0,115 [0,090–0,146] | 0,978 [0,969–0,986] | 0,018 [0,005–0,033] |  |
| Chapman-Shaoxing | BASELINE | 2273 (1777) | 1560/24/472/217 | 0,878 [0,862–0,892] | 0,048 [0,033–0,071] | 0,961 [0,944–0,975] | — |  |
| Georgia | MODEL | 1054 (555) | 424/33/466/131 | 0,764 [0,727–0,797] | 0,066 [0,047–0,091] | 0,900 [0,880–0,919] | 0,045 [0,025–0,066] |  |
| Georgia | BASELINE | 1054 (555) | 363/36/463/192 | 0,654 [0,614–0,692] | 0,072 [0,053–0,098] | 0,855 [0,831–0,878] | — |  |
| Havuz (4 kaynak, ikincil) | MODEL | 5477 (3497) | 3247/143/1837/250 | 0,929 [0,919–0,937] | 0,072 [0,062–0,084] | 0,965 [0,960–0,970] | 0,035 [0,028–0,044] |  |
| Havuz (4 kaynak, ikincil) | BASELINE | 5477 (3497) | 2924/137/1843/573 | 0,836 [0,824–0,848] | 0,069 [0,059–0,081] | 0,929 [0,920–0,938] | — |  |

Ritim alt gruplarında FPR (`phase_xxxiii/results/b_rhythm_fpr.csv`):

| ritim | n | FP model | FPR model | FPR baseline |
|---|---|---|---|---|
| Sinüs taşikardisi | 237 | 43 | 0,181 [0,138–0,235] | 0,034 [0,017–0,065] |
| Sinüs bradikardisi | 429 | 3 | 0,007 [0,002–0,020] | 0,033 [0,020–0,054] |
| Sinüs aritmisi | 35 | 2 | 0,057 [0,016–0,186] | 0,314 [0,186–0,480] |
| PAC/SVPB | 131 | 20 | 0,153 [0,101–0,224] | 0,260 [0,192–0,341] |
| PVC | 62 | 19 | 0,306 [0,206–0,430] | 0,306 [0,206–0,430] |
| Pacing | 10 | 3 | 0,300 [0,108–0,603] | 0,200 [0,057–0,510] |
| Diğer | 1142 | 72 | 0,063 [0,050–0,079] | 0,060 [0,048–0,076] |

### 5.4 Gerçekçi karışım ve AFL (ikincil)

Ağırlıklı karışım (hastane arşivi oranları; toplum prevalansı değil), `phase_xxxiii/results/mixture_results.csv`:

| kaynak | n (AF/SR/diğer) | ağırlıklı prevalans | Precision | Recall | FPR | üç hedef |
|---|---|---|---|---|---|---|
| CPSC 2018 | 2398 (1087/818/493) | 0,167 | 0,743 [0,689–0,803] | 0,926 [0,911–0,943] | 0,064 [0,046–0,084] | evet |
| CPSC-Extra | 574 (78/4/492) | 0,024 | 0,421 [0,321–0,586] | 0,949 [0,897–0,987] | 0,032 [0,016–0,049] | hayır |
| Chapman-Shaoxing | 4076 (1777/1803/496) | 0,185 | 0,714 [0,669–0,766] | 0,980 [0,973–0,987] | 0,089 [0,068–0,110] | evet |
| Georgia | 2749 (555/1695/499) | 0,056 | 0,451 [0,378–0,545] | 0,764 [0,728–0,800] | 0,055 [0,038–0,074] | hayır |
| Havuz (4 kaynak, ikincil) | 9797 (3497/4320/1980) | 0,119 | 0,661 [0,625–0,700] | 0,929 [0,921–0,937] | 0,064 [0,054–0,075] | hayır |

AFL kayıtlarının AF olarak sınıflandırılma oranı, `phase_xxxiii/results/afl_results.csv`:

| kaynak | n | AF kararı (model) | oran model | oran baseline |
|---|---|---|---|---|
| CPSC-Extra | 46 | 34 | 0,739 [0,597–0,844] | 0,674 [0,530–0,791] |
| Chapman-Shaoxing | 438 | 291 | 0,664 [0,619–0,707] | 0,447 [0,402–0,494] |
| Georgia | 167 | 95 | 0,569 [0,493–0,642] | 0,419 [0,347–0,495] |
| Havuz (4 kaynak, ikincil) | 651 | 420 | 0,645 [0,608–0,681] | 0,456 [0,418–0,495] |

## 6. Özet ve açık noktalar

- **Hasta bazlı ayrım:** PTB-XL'de kişi kesişimi 0; hasta başına tek EKG; resmî hasta-düzeyi fold'lar. Kanıt §1.2.
- **Öznitelik çıkarımı:** eğitim PTB-XL+ golden öznitelikleriyle, dış doğrulama ve uygulama kilitli Octave
  pipeline'ıyla yapıldı. RR/QRS eşleşir; PR/P/QT sapar. Karar uyumu 0,99 (GA alt sınırı 0,946). Uygulama ile araştırma
  pipeline'ı arasında 10 öznitelik 11/11 kayıtta birebir.
- **Tekilleştirme:** pencere hash'iyle kaynak içi ve kaynaklar arası yapıldı; CPSC-Extra'nın AF kayıtlarının yarısı
  CPSC 2018 kopyasıydı.
- **Açık:** PTB-XL ↔ Challenge kayıt düzeyi hash karşılaştırması yapılmadı; hasta kimliği olmadığı için aynı-hasta
  tekrarları dışlanamaz; Challenge etiketleri insan doğrulaması bilgisi taşımaz; yalnız ilk 10 sn kullanılır.
- **Yorum sınırı:** model AF'yi sinüs ritminden iyi ayırır; diğer ritimlerde (sinüs taşikardisi, PVC, PAC, pacing) ve
  AFL'de yanlış pozitifler artar. Klinik tanı aracı değildir.
