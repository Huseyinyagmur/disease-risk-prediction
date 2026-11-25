# PHASE XLIX — Final rapor girdileri ve hoca maddeleri

Durum: **TAMAMLANDI.** Bu faz derleme fazıdır, kayıtlı tahminler ve meta veri üzerinden analiz yapıldı.
- Model yeniden fit edilmedi. Eşik, kalibrasyon, registry, şema ve önceki faz dosyaları değişmedi.
- **Yeni test açılmadı, yeni tahmin üretilmedi.**
- Yeni hesaplar yalnız şunları okur: kimlik ve başlık meta verisi, ham EKG sinyal hash'leri/korelasyonu ve UCI öznitelik
  eksikliği. Bunların hiçbiri model çıktısı değildir.
- `clinical_probability_eligibility = false`.

## Çıktılar

| dosya | içerik |
|---|---|
| `final_report_inputs.md` | 1a–1h derleme, 2 (ara rapor düzeltmeleri), 3 (hoca maddeleri); her sayı kaynak yol + satır/anahtar ile |
| `model_results.csv` | 13 model × kanıt düzeyi = 31 satır; TP/FP/TN/FN, P/R/FPR/NPV (Wilson GA), AUC (GA), eşik + kural, veri seti, bölme, öznitelikler, kaynak dosya + seçici + SHA256 |
| `results/pytest_backend_full.xml` | Görev 0: tam backend koşusu (AF uçtan uca + gerçek Ollama) |
| `results/af_overlap_check.json`, `af_near_duplicate_pairs.csv` | Hoca 3a: PTB-XL ↔ Challenge ve Challenge içi çakışma kontrolü |
| `results/uci_cad_feature_availability.json/.csv` | Hoca 3d: UCI 4 merkezde 11 öznitelik |
| `results/nhanes3_phase_disjoint.json` | Safra taşı: NHANES III Faz 1 / Faz 2 kişi ayrıklığı |
| `results/references_found.csv` | Repoda geçen 143 tekil DOI/PMID (ilk geçtiği dosya:satır) |
| `scripts/` | `build_inputs.py`, `af_overlap_check.py`, `uci_cad_availability.py`, `sha_full_scan.py`, `verify49.py` |
| `results/verification49.json` | Bütünlük ve çapraz kontrol sonucu |

## Görev 0 — Backend test XML'i

`results/pytest_backend_full.xml` bu fazda tam koşuyla yeniden üretildi. Koşu AF uçtan uca (Octave) ve gerçek Ollama
testlerini kapsadı. Ollama bu fazda `ollama serve` ile başlatıldı.

Sonuç: **449 test: 444 geçti, 5 xfail, 0 başarısız, 0 hata** (372 sn). 5 xfail onaylı BMI/osteo sınırlılığıdır.
- Phase XLVIII raporu "444 geçti / 5 xfail" diyordu ama XML bir önceki koşudan kalmıştı (421 geçti).
- Bu XML artık raporlanan sayıyla tutarlıdır.

Vitest (63), Playwright (35) ve axe (24 ekran, 0 ihlal) yeniden koşulmadı. Nedeni: `app/` bu fazda değişmedi (bkz.
bütünlük). Bu sonuçlar XLVIII dosyalarından raporlanmıştır.

## Hoca maddeleri — durum

| # | madde | durum | kanıt / not |
|---|---|---|---|
| 3a-1 | AF hasta bazlı ayrım (PTB-XL fit/val/test) | **yapıldı (Phase XLVI)** | kişi kesişimi 0/0/0. Birden fazla fold'a düşen hasta 0/18.869. Hasta başına ilk EKG. Kaynak: `phase_xlvi/results/af_split_check.json` |
| 3a-2 | Challenge kaynakları arası / kaynak içi kayıt çakışması (birebir kopya) | **yapıldı (Phase XXIX/XXXIII)** | pencere hash'i ile 226 + 20 kayıt dışlandı. CPSC-Extra AF'lerinin 74'ü CPSC 2018 kopyasıydı |
| 3a-3 | PTB-XL ↔ Challenge kayıt çakışması (kimlik/başlık meta verisi) | **bu fazda yapıldı** | Kullanılan 10.456 kayıtta PTB-XL kopyası (HR öneki) veya ptb-xl/ptb kaynağı **0**. Başlık meta verisi kayıtları ayırt etmiyor: 6.692 kaydın 6.524'ü en az bir PTB-XL kaydıyla aynı yaş/cinsiyet/ritim/uzunluk değerlerini taşıyor. Bu yüzden meta veri çakışmayı ne kanıtlar ne dışlar |
| 3a-4 | PTB-XL ↔ Challenge sinyal karşılaştırması | **bu fazda kısmen yapıldı** | Yereldeki 103 PTB-XL dalga formu (85 fit, 17 validation), 10.727 Challenge pencere hash'iyle karşılaştırıldı: eşleşme **0**. **Tamamı yapılamadı:** PTB-XL `records500` (~1,7 GB) indirilmedi; bellek kuralı gereği indirme öncesi onay gerekir |
| 3a-5 | Challenge içi yakın kopya (farklı kodlanmış/filtrelenmiş) | **bu fazda yapıldı** | Kontrol, aynı yaş/cinsiyet/Dx/uzunluk grubundaki kayıt çiftlerinde lead II korelasyonuna (r ≥ 0,99) bakar. Kaynaklar arası 32.618 çift ve kaynak içi 26.703 çift tarandı. İşaretlenen 0/0. Pozitif kontrol: bilinen 231 kopya çiftinin 231'i yakalandı |
| 3a-6 | Aynı hastanın farklı kayıtları (Challenge) | **yapılamadı** | Challenge başlıklarında hasta kimliği yok (BULUNAMADI). Gruplama anahtarının dışında kalan kopyalar da yakalanamaz (ör. Dx kodu farklı yazılmış) |
| 3b | Fibrozis/osteoporoz: aynı duyarlılıkta FPR ve yönlendirme oranı + McNemar/paired bootstrap; referans eşikleri ve popülasyonları | **yapıldı (Phase XLVI, kullanıcı onaylı post-hoc yeniden skorlama; kapı 24/24)** | `phase_xlvi/01_reference_score_analysis.md` §1, §3–4. Özet tablo: `final_report_inputs.md` §1b. Kadın OST < 2 eşiğinin birincil kaynağı BULUNAMADI |
| 3c | OST erkeklerde ayrı (n, AUC, aynı duyarlılık) + özgün popülasyon notu | **yapıldı (Phase XLVI)** | Erkek n 1.193, pozitif **31** (küçük). AUC model 0,817 / OST 0,802. ΔAUC +0,015 [−0,008–0,044]. Aynı duyarlılıkta FPR model 0,102 / OST 0,066. OST'nin özgün popülasyonu postmenopozal Asyalı kadınlardır (Koh 2001) |
| 3d | UCI KAH: Hungarian, Switzerland, VA'da 11 öznitelik varlığı/eksiklik | **bu fazda yapıldı** | `final_report_inputs.md` §3d. Switzerland'da chol %100 eksik, model uygulanamaz. Slope eksikliği Hungarian'da %64,6, VA'da %51. 11 öznitelik eksiksiz: Hungarian 95/294, VA 64/200. Model yeniden eğitilmedi |

## Ara rapor düzeltmeleri (özet; ayrıntı `final_report_inputs.md` §2)

**AF.** "FPR ≤ %0,3" her kaynakta doğru değildir. Yalnız SR'ye karşı FPR değerleri:

| kaynak | FPR (SR'ye karşı) | not |
|---|---|---|
| CPSC 2018 | %0,37 | %0,3'ün üstünde |
| Chapman-Shaoxing | %0,28 | |
| Georgia | %0,18 | |
| havuz | %0,25 | |
| CPSC-Extra | — | yorumlanamaz (SR n = 4) |

- Diğer ritimler negatif sınıfa katılınca FPR %3,3–11,5'e çıkar (havuz %7,2).
- Gerçekçi karışımda üç hedef yalnız CPSC 2018 ve Chapman-Shaoxing'de sağlandı. Georgia (P 0,451), CPSC-Extra (P 0,421) ve havuzda (P 0,661) sağlanmadı.

**Safra taşı.** Ana sonuç NHANES III'tür (n 6.528, prevalans %9,4):
- P 0,174, R 0,741, FPR 0,365, AUC 0,751.
- ΔAUC +0,012 (yaş + cinsiyet + BMI LR'ye göre).

Bölme ve sınıf dağılımı:
- Faz 1 (1988–91) geliştirme, Faz 2 (1991–94) test.
- Fazlar arası kişi kesişimi 0. Bu fazda doğrulandı: 31.311 SEQN'in hiçbiri iki fazda birden yok.
- Geliştirmede 535/6.287 pozitif (%8,5).

Eski UCI sonucu ayrı tutulur:
- n 64 (32/32). P 0,617, R 0,906 [0,758–0,968], FPR 0,563.

"Sınıf dengesi recall artışını açıklar" iddiası yanlıştır:
- Prevalans Recall'un tanımına girmez.
- UCI'deki yüksek Recall gevşek eşikten gelir (FPR 0,563).
- Küçük test kümesinde Recall'un güven aralıkları örtüşür.
- Veri setleri, hedef ve öznitelikler farklıdır.

## Kaynakça eksikleri (bu fazda bulundu)

- **P_LUX:** CDC sayfası okundu. Ocak 2022'de yayımlandı.
- **ESC/ESH:**
  - Williams 2018, Eur Heart J 39:3021–3104, doi:10.1093/eurheartj/ehy339.
  - Mancia 2023, J Hypertens 41:1874–2071, doi:10.1097/HJH.0000000000003480.
- **RIP3 DOI çözülüyor:** doi.org adresinden data.mendeley.com/datasets/7v4w66wxj8/1 adresine gider. Lisans CC BY 4.0, yayım tarihi 26.06.2020.
  - Birincil yayın: Hu X ve ark., Clin Chim Acta 2020;509:273–279.
- **CCN3:** Li JY, Wang YD, Qi XY ve ark., Clin Chim Acta 2019;494:52–57, doi:10.1016/j.cca.2019.03.006.
- **NHANES bileşen dosya adları:** fazların manifest dosyalarından otomatik çıkarıldı (§1h).
- **Erişim notu:** PubMed sayfaları bot engeli verdi. Künyeler Europe PMC REST API'den alındı.

## Bütünlük (`results/verification49.json`)

SHA256 envanteri faz başında ve sonunda alındı (`results/sha256_before.json`, `sha256_after.json`). Hariç tutulanlar:
`.git`, `node_modules`, `.venv`, `__pycache__` ve `dist`.

Sonuç: **7/7 kontrol geçti.**

| kontrol | sonuç |
|---|---|
| dosya sayısı | faz başı 158.763, faz sonu 158.780 (+17, tümü `phase_xlix/` altında) |
| önceki dosyalarda değişen | 0 |
| silinen | 0 |
| faz dışı yeni dosya | 0 |
| `app/` | değişmedi |
| 13 model SHA256 | registry ile aynı |
| `model_results.csv` ↔ registry kanıt değerleri | 63 karşılaştırma, 0 uyuşmazlık |
| backend XML | 0 başarısız, 0 hata |

Ek notlar:
- Tüm betikler `-B` ile çalıştırıldı.
- Ollama bu fazda başlatıldı ve açık bırakıldı.

## Sınırlılıklar

- **PTB-XL ↔ Challenge kontrolü tam değildir:**
  - Sinyal düzeyinde yalnız 103 PTB-XL kaydı karşılaştırıldı.
  - Meta veri kontrolü ayırt edici değildir.
  - Tam kontrol için records500 indirilmesi gerekir (onayınız gerekir).
- Yakın kopya taraması yalnız aynı yaş/cinsiyet/Dx/uzunluk grubundaki çiftlere ve tek derivasyona (lead II) bakar. Eşik r ≥ 0,99'dur.
- **3b ve 3c Phase XLVI'nın post-hoc analizidir:**
  - Eşleştirme eşikleri testte seçildi.
  - Çoklu karşılaştırma düzeltmesi yapılmadı.
- UCI safra taşı sayımları (29/18/14/3) kayıtlı oranlardan geri hesaplandı. Kaynak dosyada sayım yoktu. Sayımlar tutarlıdır, çünkü üç oran (29/32, 18/32 ve 29/47) birlikte bu sayımları verir.
- **"PREVIOUSLY_EXPOSED" tablosu registry metnine dayanır:** "kayıtta belirtilmemiş", maruziyet olmadığı anlamına gelmez.
- Vitest, Playwright ve axe bu fazda yeniden koşulmadı.
