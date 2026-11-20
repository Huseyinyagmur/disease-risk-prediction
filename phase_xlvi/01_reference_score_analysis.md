# Phase XLVI — 01: Fibrozis ve osteoporozda referans skor karşılaştırması

**Etiket: POST-HOC TANIMLAYICI.** Bu analiz kilitli test sonucu değildir ve model, eşik ya da feature seçimi için
kullanılmaz. Model yeniden fit edilmedi; eşik, feature sırası ve test kümesi değişmedi. Birincil (kilitli) sonuçlar
Phase XXXI (fibrozis) ve Phase XXX (osteoporoz) raporlarındaki sonuçlardır.

Üretim: `scripts/ref_score_analysis.py` (Focused venv, Python 3.13.3) → `results/reference_score_analysis.csv`;
bu belge `scripts/render_ref_md.py` ile CSV'den üretildi (elle sayı yazılmadı).

## 0. Yöntem notu: teknik yeniden skorlama ve kapı

Phase XXX/XXXI kişi düzeyi test tahminlerini ve referans skor değerlerini dosyaya kaydetmemişti; yalnız toplu
sonuçlar vardı. McNemar ve paired bootstrap kişi düzeyi veri ister. Kullanıcı kararıyla (2026-11-20) donmuş model ve
kilitli eşik, **önceden açılmış** test dosyası üzerinde deterministik olarak yeniden skorlandı (Phase XXVII "rescore" ve
Phase XXXI 01 ile aynı yöntem). Referans skor formülleri özgün faz betiklerinden salt okunur içe aktarıldı:
`phase_xxxi/scripts/t3_fib_dev.py :: fib4, nfs`, `phase_xxx/scripts/t2_dev.py :: ost`; metrik işlevleri
`phase_xxx/scripts/p30_engine.py`.

**Kapı:** kayıtlı TP/FP/TN/FN, AUC ve ΔAUC (özgün tohum 20261114) değerleri birebir yeniden
üretilmeden analiz yapılmaz. Sonuç: **24/24 birebir** (`results/reference_score_gate.json`;
AUC ve ΔAUC farkı < 1e-12).

| | fibrozis | osteoporoz |
|---|---|---|
| test | NHANES L 2021–23, n = 4714 | NHANES J 2017–18, n = 2275 |
| model SHA256 | `7f349c4a29663e00…` | `2c31bd8770b59975…` |
| kilitli eşik | 0.061497 | 0.060289 |
| test dosyası SHA256 | `534498bd1247f456…` | `df9c8d05037a50de…` |

## 1. Referans skorlar: formül, kaynak eşikleri ve özgün hedef popülasyon

Kaynak: Europe PMC kayıtları (`data/refs/*.json`, PubMed özetleri). Yalnız özette okunabilen bilgi yazıldı; tam metin
okunmadı. Özette doğrulanamayan bilgi BULUNAMADI.

| skor | formül (projede) | kaynak eşik | özgün geliştirme popülasyonu ve hedef | kaynak |
|---|---|---|---|---|
| FIB-4 (formül) | yaş × AST / (trombosit × √ALT) | < 1,45 / > 3,25 | HIV/HCV ko-enfeksiyonlu 832 hasta, biyopsi; Ishak 4–6 (ilerlemiş fibrozis) | Sterling ve ark. 2006, Hepatology, PMID 16729309, doi:10.1002/hep.21178 |
| FIB-4 (NAFLD eşikleri) | aynı | ≤ 1,30 (NPV %90) / ≥ 2,67 (PPV %80) | NAFLD'li 541 erişkin (ABD ulusal veri tabanı), biyopsi; ilerlemiş fibrozis | Shah ve ark. 2009, Clin Gastroenterol Hepatol, PMID 19523535, doi:10.1016/j.cgh.2009.05.033 |
| NFS | −1,675 + 0,037·yaş + 0,094·BMI + 1,13·IFG/diyabet + 0,99·AST/ALT − 0,013·trombosit − 0,66·albümin | < −1,455 (dışlama) / > 0,676 (yüksek) | Biyopsiyle kanıtlı NAFLD'li 733 hasta (480 geliştirme, 253 doğrulama); ilerlemiş fibrozis | Angulo ve ark. 2007, Hepatology, PMID 17393509, doi:10.1002/hep.21496 |
| OST(A) | 0,2 × (kilo kg − yaş) | özetten: üç risk kategorisi; sayısal eşik BULUNAMADI | Asya'da 8 ülkeden **postmenopozal Asyalı kadınlar**; femur boynu T ≤ −2,5. Doğrulama: postmenopozal Japon kadınlar | Koh ve ark. 2001, Osteoporos Int, PMID 11580084, doi:10.1007/s001980170070 |
| OST, erkek | aynı | ≤ 3 (duyarlılık %93, özgüllük %66); kategoriler ≥ 4 / −1…3 / ≤ −2 | ABD gaziler hastanesi (göğüs ve romatoloji kliniği) 181 erkek; omurga/total kalça/femur boynu T ≤ −2,5 | Adler ve ark. 2003, Mayo Clin Proc, PMID 12934782, doi:10.4065/78.6.723 |
| OST, kadın eşiği < 2 | aynı | < 2 | Birincil kaynak özetinde BULUNAMADI. Phase XXX protokolü bu eşiği USPSTF kanıt özetinden (model-çıkarımlı özet) almıştır | `phase_xxx/config/protocol_osteo.md` §6 |

**Bu projedeki hedeflerle fark (önemli):**
- Fibrozis hedefi **FibroScan LSM ≥ 8 kPa**dır; FIB-4 ve NFS ise **biyopside ilerlemiş fibrozis** (F3–F4 / Ishak 4–6) için
  geliştirildi. Popülasyon da farklıdır: kaynaklar karaciğer kliniği hastalarıdır (HIV/HCV, NAFLD); burada genel NHANES
  erişkin popülasyonu (≥ 20 yaş, gebe değil) vardır. Skorların bu hedefte düşük performansı kısmen bu uyumsuzluktan
  gelir; skorların kendi amaçları için yetersiz olduğu anlamına gelmez.
- Shah 2009'da düşük eşik "≤ 1,30" olarak verilir. Phase XXXI'de karar `FIB-4 ≥ 1,3` = yönlendir, yani 1,30 tam değerindeki
  kişi yönlendirilir. Kaynakta 1,30 "düşük risk" tarafındadır. Sınır değerdeki kişi sayısı bu analizde ayrıca sayılmadı.
- OST(A) **postmenopozal Asyalı kadınlarda** geliştirildi. NHANES J testi ≥ 50 yaş kadın ve erkekleri, çoğunluğu Asyalı
  olmayan kişileri içerir; menopoz durumu OST kararı için ayrıca kullanılmadı. **Erkekler OST'nin özgün popülasyonu
  dışındadır.** Erkek eşiği (≤ 3) Adler 2003'ün küçük, klinik erkek örneklemine dayanır. Bu yüzden kadın ve erkek ayrı
  değerlendirildi ve erkek sonuçları ayrıca bu notla okunmalıdır.
- Osteoporoz hedefi min(femur boynu, total femur) T ≤ −2,5'tir (NHANES III 20–29 yaş Hispanik olmayan beyaz kadın
  referansı, erkeklerde de kadın referansı). Adler 2003'te omurga da dahildir.

## 2. Karşılaştırma şemaları

Hepsi test verisinde yapılır; bu yüzden **iyimser ve tanımlayıcıdır** (eşleştirme testte seçildi).

1. **Eşit duyarlılık:** model kilitli eşikte. Referans skorun eşiği, testte modelin Recall'una eşit veya üstünde
   Recall veren **en yüksek** eşik olarak seçildi (`p30_engine.threshold_recall` kuralı). Karşılaştırma FPR ve
   yönlendirme üzerinedir.
2. **Eşit yönlendirme (a):** model kilitli eşikte k kişiyi yönlendirir; referans skorun en yüksek k kişisi alınır.
3. **Eşit yönlendirme (b):** referans skor kendi standart eşiğinde (FIB-4 ≥ 1,30; NFS ≥ −1,455; kadında OST < 2,
   erkekte OST ≤ 3) k kişiyi yönlendirir; modelin en yüksek k kişisi alınır.

Eşitlikler kararlı sırayla (veri sırası) kırıldı; sınırdaki eşit skor sayısı tablo notlarındadır.

**İstatistik:**
- Oranlar Wilson %95 GA.
- **McNemar:** aynı kişilerde eşleştirilmiş kararlar. Pozitiflerde (Recall farkı) ve negatiflerde (FPR farkı) ayrı
  ayrı, uyumsuz çiftler üzerinde kesin iki yönlü binom testi. Eşit duyarlılık şemasında Recall farkı tasarım gereği
  ~0'dır; anlamlı olan negatiflerdeki testtir. Eşit yönlendirme şemasında iki test birlikte okunur.
- **ΔAUC:** AUC(model) − AUC(referans), aynı kişilerde pozitif/negatif tabakalı paired bootstrap, 2000 tekrar,
  seed 20261120. OST için skor −OST'dir (düşük OST = yüksek risk). Çoklu karşılaştırma düzeltmesi yapılmadı.

## 3. Fibrozis (LSM ≥ 8 kPa) — model vs FIB-4 ve NFS

### 3.1 Tümü
| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 451/1430/2697/136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,399 (1881) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | FIB-4 ≥ 0,774 (testte eşlenmiş) | 451/2704/1423/136 | 0,143 [0,131–0,156] | 0,768 [0,733–0,801] | 0,655 [0,641–0,670] | 0,669 (3155) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 451/1430/2697/136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,399 (1881) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | FIB-4 en yüksek 1881 | 309/1572/2555/278 | 0,164 [0,148–0,182] | 0,526 [0,486–0,566] | 0,381 [0,366–0,396] | 0,399 (1881) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | model | model en yüksek 1550 | 422/1128/2999/165 | 0,272 [0,251–0,295] | 0,719 [0,681–0,754] | 0,273 [0,260–0,287] | 0,329 (1550) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | referans | FIB-4 ≥ 1,30 | 262/1288/2839/325 | 0,169 [0,151–0,189] | 0,446 [0,407–0,487] | 0,312 [0,298–0,326] | 0,329 (1550) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 451/1430/2697/136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,399 (1881) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | NFS ≥ -1,69 (testte eşlenmiş) | 451/2046/2081/136 | 0,181 [0,166–0,196] | 0,768 [0,733–0,801] | 0,496 [0,481–0,511] | 0,530 (2497) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 451/1430/2697/136 | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,399 (1881) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | NFS en yüksek 1881 | 384/1497/2630/203 | 0,204 [0,187–0,223] | 0,654 [0,615–0,692] | 0,363 [0,348–0,378] | 0,399 (1881) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | model | model en yüksek 2198 | 477/1721/2406/110 | 0,217 [0,200–0,235] | 0,813 [0,779–0,842] | 0,417 [0,402–0,432] | 0,466 (2198) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | referans | NFS ≥ −1,455 | 414/1784/2343/173 | 0,188 [0,173–0,205] | 0,705 [0,667–0,741] | 0,432 [0,417–0,447] | 0,466 (2198) |

| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |
|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — FIB-4 ≥ 0,774 (testte eşlenmiş) | 95 / 95 (p 1,000) | 357 / 1631 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — FIB-4 en yüksek 1881 | 200 / 58 (p < 0,001) | 742 / 884 (p < 0,001) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) — FIB-4 ≥ 1,30 | 219 / 59 (p < 0,001) | 675 / 835 (p < 0,001) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — NFS ≥ -1,69 (testte eşlenmiş) | 71 / 71 (p 1,000) | 359 / 975 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — NFS en yüksek 1881 | 112 / 45 (p < 0,001) | 529 / 596 (p 0,049) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) — NFS ≥ −1,455 | 106 / 43 (p < 0,001) | 550 / 613 (p 0,069) |

Not: hedef Recall 0.768; sınırdaki eşit referans skoru: 2 kişi; sınırdaki eşit model skoru: 1 kişi; sınırdaki eşit referans skoru: 1 kişi

### 3.2 Kadın
| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 216/657/1625/66 | 0,247 [0,220–0,277] | 0,766 [0,713–0,812] | 0,288 [0,270–0,307] | 0,340 (873) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | FIB-4 ≥ 0,6811 (testte eşlenmiş) | 216/1580/702/66 | 0,120 [0,106–0,136] | 0,766 [0,713–0,812] | 0,692 [0,673–0,711] | 0,700 (1796) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 216/657/1625/66 | 0,247 [0,220–0,277] | 0,766 [0,713–0,812] | 0,288 [0,270–0,307] | 0,340 (873) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | FIB-4 en yüksek 873 | 125/748/1534/157 | 0,143 [0,122–0,168] | 0,443 [0,386–0,502] | 0,328 [0,309–0,347] | 0,340 (873) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | model | model en yüksek 761 | 201/560/1722/81 | 0,264 [0,234–0,297] | 0,713 [0,657–0,762] | 0,245 [0,228–0,263] | 0,297 (761) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | referans | FIB-4 ≥ 1,30 | 115/646/1636/167 | 0,151 [0,127–0,178] | 0,408 [0,352–0,466] | 0,283 [0,265–0,302] | 0,297 (761) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 216/657/1625/66 | 0,247 [0,220–0,277] | 0,766 [0,713–0,812] | 0,288 [0,270–0,307] | 0,340 (873) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | NFS ≥ -1,666 (testte eşlenmiş) | 216/1081/1201/66 | 0,167 [0,147–0,188] | 0,766 [0,713–0,812] | 0,474 [0,453–0,494] | 0,506 (1297) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 216/657/1625/66 | 0,247 [0,220–0,277] | 0,766 [0,713–0,812] | 0,288 [0,270–0,307] | 0,340 (873) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | NFS en yüksek 873 | 174/699/1583/108 | 0,199 [0,174–0,227] | 0,617 [0,559–0,672] | 0,306 [0,288–0,326] | 0,340 (873) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | model | model en yüksek 1144 | 230/914/1368/52 | 0,201 [0,179–0,225] | 0,816 [0,766–0,857] | 0,401 [0,381–0,421] | 0,446 (1144) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | referans | NFS ≥ −1,455 | 199/945/1337/83 | 0,174 [0,153–0,197] | 0,706 [0,650–0,756] | 0,414 [0,394–0,434] | 0,446 (1144) |

| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |
|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — FIB-4 ≥ 0,6811 (testte eşlenmiş) | 52 / 52 (p 1,000) | 148 / 1071 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — FIB-4 en yüksek 873 | 114 / 23 (p < 0,001) | 406 / 497 (p 0,003) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) — FIB-4 ≥ 1,30 | 114 / 28 (p < 0,001) | 371 / 457 (p 0,003) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — NFS ≥ -1,666 (testte eşlenmiş) | 35 / 35 (p 1,000) | 165 / 589 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — NFS en yüksek 873 | 63 / 21 (p < 0,001) | 272 / 314 (p 0,090) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) — NFS ≥ −1,455 | 52 / 21 (p < 0,001) | 300 / 331 (p 0,232) |

Not: hedef Recall 0.766; sınırdaki eşit referans skoru: 1 kişi; sınırdaki eşit model skoru: 1 kişi

### 3.3 Erkek
| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 235/773/1072/70 | 0,233 [0,208–0,260] | 0,770 [0,720–0,814] | 0,419 [0,397–0,442] | 0,469 (1008) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | FIB-4 ≥ 0,8253 (testte eşlenmiş) | 235/1210/635/70 | 0,163 [0,145–0,183] | 0,770 [0,720–0,814] | 0,656 [0,634–0,677] | 0,672 (1445) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 235/773/1072/70 | 0,233 [0,208–0,260] | 0,770 [0,720–0,814] | 0,419 [0,397–0,442] | 0,469 (1008) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | FIB-4 en yüksek 1008 | 179/829/1016/126 | 0,178 [0,155–0,202] | 0,587 [0,531–0,641] | 0,449 [0,427–0,472] | 0,469 (1008) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | model | model en yüksek 789 | 220/569/1276/85 | 0,279 [0,249–0,311] | 0,721 [0,668–0,769] | 0,308 [0,288–0,330] | 0,367 (789) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) | referans | FIB-4 ≥ 1,30 | 147/642/1203/158 | 0,186 [0,161–0,215] | 0,482 [0,426–0,538] | 0,348 [0,327–0,370] | 0,367 (789) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 235/773/1072/70 | 0,233 [0,208–0,260] | 0,770 [0,720–0,814] | 0,419 [0,397–0,442] | 0,469 (1008) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | NFS ≥ -1,716 (testte eşlenmiş) | 235/961/884/70 | 0,196 [0,175–0,220] | 0,770 [0,720–0,814] | 0,521 [0,498–0,544] | 0,556 (1196) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 235/773/1072/70 | 0,233 [0,208–0,260] | 0,770 [0,720–0,814] | 0,419 [0,397–0,442] | 0,469 (1008) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | NFS en yüksek 1008 | 210/798/1047/95 | 0,208 [0,184–0,234] | 0,689 [0,634–0,738] | 0,433 [0,410–0,455] | 0,469 (1008) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | model | model en yüksek 1054 | 239/815/1030/66 | 0,227 [0,202–0,253] | 0,784 [0,734–0,826] | 0,442 [0,419–0,464] | 0,490 (1054) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) | referans | NFS ≥ −1,455 | 215/839/1006/90 | 0,204 [0,181–0,229] | 0,705 [0,651–0,753] | 0,455 [0,432–0,478] | 0,490 (1054) |

| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |
|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — FIB-4 ≥ 0,8253 (testte eşlenmiş) | 44 / 44 (p 1,000) | 190 / 627 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — FIB-4 en yüksek 1008 | 90 / 34 (p < 0,001) | 332 / 388 (p 0,040) |
| eşit yönlendirme (model en yüksek k; k = FIB-4 ≥ 1,30 yönlendirmesi) — FIB-4 ≥ 1,30 | 107 / 34 (p < 0,001) | 311 / 384 (p 0,006) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — NFS ≥ -1,716 (testte eşlenmiş) | 35 / 35 (p 1,000) | 190 / 378 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — NFS en yüksek 1008 | 50 / 25 (p 0,005) | 251 / 276 (p 0,296) |
| eşit yönlendirme (model en yüksek k; k = NFS ≥ −1,455 yönlendirmesi) — NFS ≥ −1,455 | 49 / 25 (p 0,007) | 252 / 276 (p 0,317) |

Not: hedef Recall 0.770; sınırdaki eşit referans skoru: 1 kişi; sınırdaki eşit model skoru: 1 kişi

### 3.4 Yüksek eşikler (tek başına; karşılaştırma şeması yok)
| grup | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|
| tümü | FIB-4 ≥ 2,67 | 50/109/4018/537 | 0,314 [0,247–0,390] | 0,085 [0,065–0,111] | 0,026 [0,022–0,032] | 0,034 |
| tümü | NFS > 0,676 | 132/251/3876/455 | 0,345 [0,299–0,394] | 0,225 [0,193–0,260] | 0,061 [0,054–0,069] | 0,081 |
| kadın | FIB-4 ≥ 2,67 | 24/45/2237/258 | 0,348 [0,246–0,466] | 0,085 [0,058–0,124] | 0,020 [0,015–0,026] | 0,027 |
| kadın | NFS > 0,676 | 62/130/2152/220 | 0,323 [0,261–0,392] | 0,220 [0,175–0,272] | 0,057 [0,048–0,067] | 0,075 |
| erkek | FIB-4 ≥ 2,67 | 26/64/1781/279 | 0,289 [0,205–0,390] | 0,085 [0,059–0,122] | 0,035 [0,027–0,044] | 0,042 |
| erkek | NFS > 0,676 | 70/121/1724/235 | 0,366 [0,301–0,437] | 0,230 [0,186–0,280] | 0,066 [0,055–0,078] | 0,089 |

### 3.5 ΔAUC
| grup | n (pozitif) | karşılaştırma | AUC model [%95 GA] | AUC referans [%95 GA] | ΔAUC [%95 GA] |
|---|---|---|---|---|---|
| tümü | 4714 (587) | model vs FIB-4 | 0,794 [0,772–0,814] | 0,597 [0,573–0,621] | 0,197 [0,168–0,226] |
| tümü | 4714 (587) | model vs NFS | 0,794 [0,772–0,814] | 0,698 [0,674–0,720] | 0,096 [0,075–0,117] |
| kadın | 2564 (282) | model vs FIB-4 | 0,804 [0,773–0,832] | 0,595 [0,560–0,630] | 0,209 [0,168–0,253] |
| kadın | 2564 (282) | model vs NFS | 0,804 [0,773–0,832] | 0,706 [0,673–0,737] | 0,098 [0,068–0,128] |
| erkek | 2150 (305) | model vs FIB-4 | 0,777 [0,747–0,807] | 0,590 [0,557–0,624] | 0,187 [0,144–0,226] |
| erkek | 2150 (305) | model vs NFS | 0,777 [0,747–0,807] | 0,687 [0,656–0,719] | 0,090 [0,060–0,120] |

## 4. Osteoporoz (DXA T ≤ −2,5) — model vs OST, kadın ve erkek ayrı

### 4.1 Kadın
| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 113/368/581/20 | 0,235 [0,199–0,275] | 0,850 [0,779–0,900] | 0,388 [0,357–0,419] | 0,445 (481) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | −OST ≥ -1,36 (testte eşlenmiş) | 113/404/545/20 | 0,219 [0,185–0,256] | 0,850 [0,779–0,900] | 0,426 [0,395–0,457] | 0,478 (517) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 113/368/581/20 | 0,235 [0,199–0,275] | 0,850 [0,779–0,900] | 0,388 [0,357–0,419] | 0,445 (481) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | −OST en yüksek 481 | 110/371/578/23 | 0,229 [0,193–0,268] | 0,827 [0,754–0,882] | 0,391 [0,360–0,422] | 0,445 (481) |
| eşit yönlendirme (model en yüksek k; k = OST < 2 (kadın) yönlendirmesi) | model | model en yüksek 586 | 118/468/481/15 | 0,201 [0,171–0,236] | 0,887 [0,822–0,930] | 0,493 [0,461–0,525] | 0,542 (586) |
| eşit yönlendirme (model en yüksek k; k = OST < 2 (kadın) yönlendirmesi) | referans | OST < 2 (kadın) | 115/471/478/18 | 0,196 [0,166–0,230] | 0,865 [0,796–0,913] | 0,496 [0,465–0,528] | 0,542 (586) |

| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |
|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — −OST ≥ -1,36 (testte eşlenmiş) | 2 / 2 (p 1,000) | 32 / 68 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — −OST en yüksek 481 | 4 / 1 (p 0,375) | 39 / 42 (p 0,824) |
| eşit yönlendirme (model en yüksek k; k = OST < 2 (kadın) yönlendirmesi) — OST < 2 (kadın) | 5 / 2 (p 0,453) | 45 / 48 (p 0,836) |

Not: hedef Recall 0.850; sınırdaki eşit referans skoru: 5 kişi; sınırdaki eşit model skoru: 1 kişi

### 4.2 Erkek (OST'nin özgün popülasyonu dışında)
| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |
|---|---|---|---|---|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | model | model (kilitli eşik) | 15/118/1044/16 | 0,113 [0,070–0,178] | 0,484 [0,320–0,652] | 0,102 [0,085–0,120] | 0,111 (133) |
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) | referans | −OST ≥ 1,92 (testte eşlenmiş) | 15/77/1085/16 | 0,163 [0,101–0,252] | 0,484 [0,320–0,652] | 0,066 [0,053–0,082] | 0,077 (92) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | model | model (kilitli eşik) | 15/118/1044/16 | 0,113 [0,070–0,178] | 0,484 [0,320–0,652] | 0,102 [0,085–0,120] | 0,111 (133) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) | referans | −OST en yüksek 133 | 16/117/1045/15 | 0,120 [0,075–0,186] | 0,516 [0,348–0,680] | 0,101 [0,085–0,119] | 0,111 (133) |
| eşit yönlendirme (model en yüksek k; k = OST ≤ 3 (erkek) yönlendirmesi) | model | model en yüksek 507 | 28/479/683/3 | 0,055 [0,038–0,079] | 0,903 [0,751–0,967] | 0,412 [0,384–0,441] | 0,425 (507) |
| eşit yönlendirme (model en yüksek k; k = OST ≤ 3 (erkek) yönlendirmesi) | referans | OST ≤ 3 (erkek) | 27/480/682/4 | 0,053 [0,037–0,076] | 0,871 [0,711–0,949] | 0,413 [0,385–0,442] | 0,425 (507) |

| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |
|---|---|---|
| eşit duyarlılık (referans eşiği testte model Recall'una eşlendi) — −OST ≥ 1,92 (testte eşlenmiş) | 1 / 1 (p 1,000) | 41 / 0 (p < 0,001) |
| eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi) — −OST en yüksek 133 | 1 / 2 (p 1,000) | 22 / 21 (p 1,000) |
| eşit yönlendirme (model en yüksek k; k = OST ≤ 3 (erkek) yönlendirmesi) — OST ≤ 3 (erkek) | 1 / 0 (p 1,000) | 47 / 48 (p 1,000) |

Not: hedef Recall 0.484; sınırdaki eşit referans skoru: 1 kişi; sınırdaki eşit model skoru: 1 kişi

### 4.3 ΔAUC
| grup | n (pozitif) | karşılaştırma | AUC model [%95 GA] | AUC referans [%95 GA] | ΔAUC [%95 GA] |
|---|---|---|---|---|---|
| kadın | 1082 (133) | model vs −OST | 0,816 [0,775–0,855] | 0,801 [0,758–0,841] | 0,015 [0,002–0,029] |
| erkek | 1193 (31) | model vs −OST | 0,817 [0,730–0,886] | 0,802 [0,713–0,878] | 0,015 [-0,008–0,044] |
| tümü (bağlam; cinsiyete özgü OST eşikleri) | 2275 (164) | model vs −OST | 0,849 [0,817–0,878] | 0,824 [0,790–0,857] | 0,025 [0,012–0,038] |

"Tümü" satırı yalnız bağlam içindir: cinsiyete özgü eşiklerin birleşimidir ve tek bir OST eşiğine karşılık gelmez.

## 5. Yorum (tanımlayıcı)

Şema yanlılığı: eşit duyarlılık şemasında referans skorun eşiği testte seçilir, modelin eşiği ise geliştirmede
kilitlidir; bu şema **referans lehine** iyimserdir. Eşit yönlendirme (b) şemasında modelin en yüksek k kişisi testte
seçilir; bu şema **model lehine** iyimserdir. Eşit yönlendirme (a) her iki tarafta da test sıralamasını kullanır.

**Fibrozis (LSM ≥ 8 kPa).**
- Üç şemada ve iki cinsiyette model, FIB-4 ve NFS'den daha iyi ayırdı. Aynı duyarlılıkta (Recall 0,768) model 1.881 kişiyi
  yönlendirdi. Aynı Recall için FIB-4'ün 3.155, NFS'nin 2.497 kişiyi yönlendirmesi gerekti (negatiflerde McNemar
  p < 0,001).
- FIB-4 ≥ 1,30 ile aynı sayıda kişi (1.550) yönlendirildiğinde model 422, FIB-4 262 pozitif yakaladı (Recall 0,719 / 0,446).
- NFS ≥ −1,455 ile eşit yönlendirmede modelin kazancı pozitiflerdedir (Recall 0,813 / 0,705; p < 0,001). Negatiflerde
  FPR farkı küçüktür ve anlamlı değildir (0,417 / 0,432; p = 0,069; kadında 0,232, erkekte 0,317).
- ΔAUC: FIB-4'e göre +0,197 [0,168–0,226], NFS'ye göre +0,096 [0,075–0,117]. Kadın ve erkekte benzer.
- Bu fark skorların kendi amaçlarında yetersiz olduğunu göstermez. FIB-4 ve NFS biyopside **ilerlemiş** fibrozis için
  geliştirildi. Buradaki hedef (LSM ≥ 8 kPa) daha erken evreleri de içerir. FIB-4'ün yüksek eşiği (≥ 2,67) testte yalnız
  0,085 Recall verdi.
- Modelin mutlak performansı yine sınırlıdır: kilitli eşikte P 0,240, FPR 0,346. Üç araştırma hedefi sağlanmadı.

**Osteoporoz — kadın** (133 pozitif / 1.082):
- Aynı duyarlılıkta (Recall 0,850) model, OST'den 36 daha az yanlış pozitif yönlendirdi (FPR 0,388 / 0,426). Negatiflerde
  uyumsuz çiftler 32 / 68'dir (p < 0,001).
- Eşit yönlendirmede iki şemada da Recall ve FPR farkları küçüktür ve anlamlı değildir (p 0,375–0,836). Örneğin OST < 2
  ile aynı sayıda kişi (586) yönlendirildiğinde Recall 0,887 / 0,865 oldu.
- ΔAUC +0,015 [0,002–0,029]: istatistiksel olarak sıfırdan farklı ama küçük.
- Pratik sonuç: kadınlarda OST, yalnız yaş ve kiloyla modele yakın bir yönlendirme sağlıyor. Model ek girdiler ister
  (kırık öyküsü, glukokortikoid, menopoz soruları vb.). Phase XXXI 01'in eşit-Recall bulgusuyla tutarlıdır.

**Osteoporoz — erkek** (31 pozitif / 1.193; OST'nin özgün popülasyonu dışında):
- Modelin kilitli eşiği erkekte yalnız 0,484 Recall verdi (Phase XXX ile aynı).
- Bu duyarlılıkta OST daha az yanlış pozitif verdi (FPR 0,066 / 0,102; negatiflerde 0 / 41, p < 0,001). Testte eşlenen
  OST eşiği (OST ≤ −1,92) Adler 2003'ün "yüksek risk" kategorisine (≤ −2) yakındır. Bu sonuç model aleyhinedir; ancak
  şema referans lehine iyimserdir.
- Eşit yönlendirmede fark yoktur. ΔAUC +0,015 [−0,008–0,044]; GA 0'ı içerir.
- Pozitif sayısı küçüktür ve OST'nin erkek eşiği küçük bir klinik örnekleme dayanır. Erkeklerde ne model ne OST için bu
  veriyle güvenilir bir üstünlük sonucu çıkarılamaz.


## 6. Sınırlılıklar

- Post-hoc ve tanımlayıcıdır. Eşleştirme eşikleri test verisinde seçildi; bu yüzden iki tarafa da iyimser.
- Önceki fazlarda aynı testler ve benzer eşit-Recall analizleri (Phase XXXI 01) raporlandı; bu analiz yeni bir test
  değildir. Fibrozis testi PREVIOUSLY_EXPOSED etiketlidir.
- Çoklu karşılaştırma (2 hastalık × 3 grup × 3 şema × 2 test) için p değerleri düzeltilmedi. p değerleri karar kuralı
  olarak kullanılmamalı.
- NHANES tasarım ağırlıkları kullanılmadı (ağırlıksız; birincil analizlerle aynı).
- Referans skorların hedefi ve popülasyonu bu projeninkinden farklıdır (§1).
- Erkeklerde osteoporoz pozitif sayısı küçüktür; GA'lar geniştir.
- OST formülü ve kadın eşiği (< 2) birincil kaynak özetinde doğrulanamadı (BULUNAMADI); Phase XXX protokolündeki tanım
  kullanıldı.
- Model skorları klinik olasılık değildir (`clinical_probability_eligibility = false`).
