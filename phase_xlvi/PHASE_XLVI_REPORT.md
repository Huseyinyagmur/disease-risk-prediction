# PHASE XLVI — Model kartları (TRIPOD+AI), AF doğrulama belgesi, referans skor analizi, mimari ve kurulum belgeleri

Durum: **TAMAMLANDI.** Model eğitilmedi veya yeniden fit edilmedi. Eşik, kalibrasyon, feature sırası, registry, şema ve
önceki faz dosyaları değişmedi. Yeni test açılmadı. Tek kod değişikliği Görev 5'tir (canlı panelde AF satırı).
`clinical_probability_eligibility = false`.

## Çıktılar

| konum | içerik |
|---|---|
| `model_cards/` (+ kopyası `app/docs/model_cards/`) | 13 model kartı (11 uygulamada + MI, KY) ve dizin |
| `tripod_ai_checklist.md` | TRIPOD+AI (BMJ 2024) 52 madde × 13 model |
| `af_validation_dossier.md` | AF doğrulama belgesi |
| `01_reference_score_analysis.md` (+ `results/reference_score_analysis.csv`) | fibrozis ve osteoporoz referans skor analizi (post-hoc) |
| `app/docs/` | `architecture.md` + `img/` (4 diyagram, SVG + PNG), `api.md`, `openapi.json`, `INSTALL.md`, `experiment_tables.md` |
| `scripts/` | `extract_metrics.py`, `card_spec.py`, `build_cards.py`, `af_dossier.py`, `ref_score_analysis.py`, `render_ref_md.py`, `build_api_docs.py`, `build_experiment_tables.py`, `render_diagrams.mjs`, `gen_af_env_fixture.py`, `verify_clean_clone46.py`, `verify46.py`, `sha_full_scan.py` |
| `results/` | `card_metrics.json` (+ `_check`), `reference_score_*.json/csv`, `af_split_check.json`, `diagram_manifest.json`, `clean_clone46.json`, test raporları, `verification46.json` |
| `data/refs/` | TRIPOD+AI tam metni (CC BY) ve tablo 2; FIB-4/NFS/OST kaynak özetleri (Europe PMC; depoya konmadı) |

## Görev 1 — Model kartları ve TRIPOD+AI

- Her kart 18 bölümdür ve TRIPOD+AI maddelerine eşlenmiştir: amaç, veri kaynağı ve sürümü, uygunluk, hedef, öznitelikler,
  örnek sayıları, eksik veri, bölme, model seçimi, eşik, kalibrasyon, performans, baseline ΔAUC, alt gruplar, sınırlılıklar,
  uygulama/ABSTAIN kuralları, etik/gizlilik.
- **Performans her kanıt düzeyinde ayrı tablodadır.** P, R, FPR, NPV ve AUC %95 GA ile, TP/FP/TN/FN birlikte verilir.
- **Kaynak:** sayılar yalnız önceki fazların kayıtlı sonuç dosyalarından okundu (`scripts/extract_metrics.py`, 31 satır).
  - Yeni tahmin üretilmedi. NPV kaynakta yoksa kayıtlı TN/FN'den hesaplandı ve kartta belirtildi.
  - Registry ile çapraz kontrol: **236 kontrol, 0 uyuşmazlık**.
  - 2 yuvarlama farkı var (dm_B FPR ham 0,23548, AUC ham 0,82548). Registry kaynak rapordaki çift yuvarlanmış 0,236 / 0,826
    değerini taşır. Kartta not olarak yazıldı.
- **Bu fazda bulunan eşik kuralları.** XLIII registry'sinde 5 model için "kural BULUNAMADI" yazıyordu. Bunların kuralı
  kaynağında bulundu ve eşik değeriyle eşleştirildi:
  - **AF, KOAH, KY:** Phase21 validation "BALANCED" senaryosu. Eşik değerleri `selected_model_registry.json` ile bit
    düzeyinde aynıdır.
  - **Anemi:** Phase25 kuralı (`development_protocol.json`).
  - **CAD:** kök V2 `src/evaluation/metrics.py :: choose_threshold`. Validation eşik tablosunda seçilen satır registry
    eşiğiyle aynıdır.
  - Registry değiştirilmedi.
- **TRIPOD+AI:** madde metinleri BMJ tam metninden (Europe PMC, CC BY) otomatik alındı. Model başına karşılanan madde
  sayısı 21–25 / 52. Tüm modellerde ortak eksikler: 3c/14 (eşitsizlik ve adalet yöntemi), 10 (örneklem büyüklüğü
  hesabı), 17/18a/18b/18d/19 (proje etik onayı, fon, çıkar beyanı, kayıt, hasta katılımı: BULUNAMADI), 22 (açık formül
  yok, donmuş nesne).

## Görev 2 — AF doğrulama belgesi

- **Hasta bazlı ayrım:** PTB-XL metadata ile yeniden doğrulandı.
  - fit/validation/test kişi kesişimi **0/0/0**.
  - Birden fazla fold'a düşen hasta: 0 / 18.869.
  - Phase21 kuralı yeniden uygulandı; sayılar XXVII ile aynı: 8.839 / 1.614 / 1.572 kişi; AF 560 / 117 / 114.
- **Öznitelik çıkarımı birebir aynı değildir.**
  - Eğitim ve iç test PTB-XL+ yayımlanmış ECGDeli değerleriyle yapıldı.
  - Dış doğrulama ve uygulama kilitli Octave yeniden uygulamasını kullanır.
  - RR/QRS eşleşir; PR, P ve QT sapar (QT tolerans içi 8/100). Karar uyumu 0,99; GA alt sınırı 0,946 < 0,98.
  - Uygulama ile araştırma pipeline'ı arasında 11/11 kayıtta 10 öznitelik birebir.
- **Tekilleştirme:** pencere hash'iyle kaynak içinde ve kaynaklar arasında yapıldı. 226 kopya dışlandı. CPSC-Extra'daki
  152 AF kaydının 74'ü CPSC 2018 kopyasıydı.
- **PTB-XL ↔ Challenge kayıt düzeyi hash karşılaştırması yapılmadı.** Önceki fazlarda yalnız kaynak düzeyinde dışlama
  vardı. Bu açık kalan bir kontroldür.
- CPSC-Extra'da tekilleştirmeden sonra 4 SR kaldı; A2'de FPR ve AUC yorumlanamaz. B (diğer ritimler), karışım ve AFL
  sonuçları belgede tablolanmıştır.

## Görev 3 — Fibrozis ve osteoporoz referans skor analizi (POST-HOC, tanımlayıcı)

- **Yöntem:** XXX/XXXI kişi düzeyi tahminleri kaydetmemişti. **Kullanıcı kararıyla** önceden açılmış test dosyası
  donmuş model ve kilitli eşikle deterministik olarak yeniden skorlandı.
  - Kapı: kayıtlı TP/FP/TN/FN, AUC ve özgün tohumlu ΔAUC birebir üretilmeden analiz yapılmaz. Sonuç **24/24** (fark < 1e-12).
  - Yeni bootstrap: 2.000 tekrar, seed 20261120. McNemar kesin binom testiyle hesaplandı.
- **Kaynak eşikler** birincil kaynak özetlerinden doğrulandı:
  - FIB-4 formülü ve 1,45/3,25: Sterling 2006, HIV/HCV.
  - FIB-4 1,30/2,67: Shah 2009, NAFLD.
  - NFS −1,455/0,676: Angulo 2007, NAFLD.
  - OST(A): Koh 2001, postmenopozal Asyalı kadınlar.
  - OST erkek ≤ 3: Adler 2003.
  - OST kadın < 2 eşiği ve OST formülü özette doğrulanamadı (BULUNAMADI).
- **Fibrozis:** model üç şemada ve iki cinsiyette FIB-4 ve NFS'den iyi ayırdı.
  - ΔAUC FIB-4'e göre +0,197 [0,168–0,226], NFS'ye göre +0,096 [0,075–0,117].
  - Aynı Recall'da (0,768) yönlendirilen kişi: model 1.881, NFS 2.497, FIB-4 3.155.
  - NFS standart eşiğiyle eşit yönlendirmede FPR farkı anlamlı değil (p = 0,069).
  - Skorlar biyopside ilerlemiş fibrozis için geliştirildi; buradaki hedef LSM ≥ 8 kPa'dır.
- **Osteoporoz, kadın:**
  - Eşit duyarlılıkta model 36 daha az yanlış pozitif verdi (FPR 0,388 / 0,426; p < 0,001).
  - Eşit yönlendirmede fark yok.
  - ΔAUC +0,015 [0,002–0,029].
- **Osteoporoz, erkek** (31 pozitif; OST'nin özgün popülasyonu dışında):
  - Modelin kilitli eşiği Recall 0,484 verdi. Bu duyarlılıkta OST daha az yanlış pozitif verdi (FPR 0,066 / 0,102).
  - Eşit yönlendirmede fark yok. ΔAUC +0,015 [−0,008–0,044].
  - Bu veriyle güvenilir üstünlük sonucu çıkarılamaz.

## Görev 4 — Mimari, API, kurulum, deney tabloları

- **Mimari:** 4 Mermaid diyagramı (bileşenler, başlangıç bütünlük denetimi, kanıta duyarlı yönlendirme, AF yolu).
  SVG/PNG çıktıları aynı kaynaktan, yerel Chromium ve mermaid 11.4.1 ile üretildi (`results/diagram_manifest.json`).
  mermaid paketi scratchpad'e kuruldu, depoya eklenmedi.
- **API:** `api.md` gerçek backend yanıtlarından üretildi; `/eligibility` ve AF-ortamı kuralı dahil. `openapi.json`,
  FastAPI `app.openapi()` çıktısıdır (6 yol).
- **Deney tabloları:** betikle üretildi; elle değer yazılmadı. Tabloda **15 hastalık** var (görevde "14" yazıyordu):
  registry'deki 11 hastalık + "ALMA" kararı verilen 4 aday. Lipid ve astım yalnız CV adayıdır ve öyle etiketlidir.
- **INSTALL ve temiz klon** (`results/clean_clone46.json`). Commit `6c5930c` yerel depodan scratchpad'e klonlandı ve
  kılavuz izlendi:
  - Python 3.13.3 venv ve `requirements.lock` kuruldu.
  - 13 model dosyası mevcut ve SHA256'ları registry ile aynı.
  - `/health`: `degraded`, devre dışı model yok, AF pipeline kapalı.
  - `/eligibility` AF satırı: **ABSTAIN, "Octave/ECGDeli AF çalışma ortamı yok"**. `/predict` osteo: OK.
  - `npm ci`, tip denetimi ve derleme başarılı; Vitest 36/36.
  - **Backend pytest klonda tam geçmez:** 2 dosya toplanamadı; kalanlarda 268 geçti, 22 başarısız. Hepsinin nedeni klonda
    olmayan araştırma ağacı dosyalarıdır (parity için geliştirme verisi, AF kilidi, örnek EKG kopyası). Bu XLVI'dan önce
    de böyleydi (XLV temiz klon notu pytest çalıştırmamıştı). INSTALL'da yazılı.
  - **Doğrulanmayan:** Octave/ECGDeli'nin temiz bir makineye kurulumu. Projede kullanılan indirme adresleri BULUNAMADI;
    INSTALL yalnız kilit SHA'larını ve beklenen yolları verir.
  - Klon GitHub'dan değil yerel commit'ten alındı; push sonrası GitHub içeriği aynı commit'tir.
- README'ye `app/docs` belgelerine ve XLVI raporuna bağlantılar eklendi; test tablosu güncellendi.

## Görev 5 — Panel düzeltmesi

- **Değişiklik:** `Service.eligibility` artık AF pipeline'ının çalışır olup olmadığına bakar
  (`app/backend/healthrisk_api/service.py`).
  - Pipeline devre dışıysa AF satırı `state = ABSTAIN` olur.
  - `reasons[0]` kısa gerekçedir: "Octave/ECGDeli AF çalışma ortamı yok". Kilit/SHA hatasında "AF pipeline devre dışı:
    kilit/SHA256 doğrulaması başarısız".
  - `missing_fields = []`. Yeni alanlar: `details` (tam sorun metni) ve `af_pipeline_available`.
  - Arayüz satırı: "Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok". "EKG kaydı yükle" bağlantısı gizlenir; teknik
    ayrıntı açılır-kapanır listededir.
- **Testler:**
  - Backend `tests/test_phase46_af_panel.py` (5): ortam yok, ortam yok + boş form/kapsam dışı yaş, Octave yok, SHA
    uyuşmazlığı, ortam var (önceki davranış korunur), diğer modellerin etkilenmediği.
  - Vitest `RoutingPanel.test.tsx` (3). Fixture gerçek backend yanıtından üretildi (`gen_af_env_fixture.py`).
- **Tasarım kararı (onayınız gerekir):** ortam yokken AF satırı yaş kapsam dışı olsa bile "Karar verilemez" gösterir.
  Ortam yokken hiçbir AF kararı üretilemeyeceği için bu öncelik seçildi.

## Ne doğrulandı

| kontrol | sonuç |
|---|---|
| Backend pytest (tam, AF uçtan uca dahil) | **318 geçti, 5 strict-xfail (onaylı), 0 hata** (`results/pytest_backend_full.xml`) |
| Vitest | **36/36** (`results/vitest_junit.xml`) |
| Playwright (canlı backend, üretim derlemesi) | **20/20** (`results/playwright/`; `PW_OUT` ile XLVI klasörüne yazıldı) |
| Kart sayıları ↔ registry | 236 kontrol, 0 uyuşmazlık, 2 yuvarlama |
| Referans skor kapısı | 24/24 birebir |
| Temiz klon | bkz. Görev 4 |

## Bütünlük (`results/verification46.json`)

- Faz başı envanteri (158.434 dosya) iş başlamadan alındı ve bitmesi beklendi. Hariç tutulanlar: `.git`, `node_modules`,
  `.venv`, `__pycache__`, `dist`.
- **V1:** `phase_xlvi/`, `app/` ve `README.md` dışında **değişen 0, silinen 0, yeni 0** (faz sonu 158.519 dosya).
- **V2:** 13 model SHA256'sı registry = faz başı = faz sonu. **V3:** registry, şema v1/v2, AF kilidi ve pipeline
  değişmedi. **V5:** faz başından sonra yazılmış `.pyc` yok. Önceki faz betikleri `-B` ile içe aktarıldı.
- **V4:** `app/` altında 4 dosya değişti (`service.py`, `types.ts`, `RoutingPanel.tsx`; `README.md` kökte), 30 dosya yeni
  (`app/docs/**`, 1 backend testi, 1 Vitest, 1 fixture).
- İndirilenler: Europe PMC kayıtları (5 özet + TRIPOD+AI tam metni) `data/refs/` altında; mermaid npm paketi scratchpad'de.

## Açık kalanlar

1. **AF panel önceliği:** ortam yokken "Karar verilemez" yaş kapsam dışı durumundan önce gelir. Uygun mu?
2. **PTB-XL ↔ Challenge kayıt düzeyi çakışma kontrolü** yapılmadı. Yapmak için PTB-XL `records500` indirilip pencere
   hash'leri karşılaştırılmalı.
3. **Klonda backend testleri:** araştırma ağacı gerektiren testler klonda başarısız oluyor. İsterseniz bu testler
   dosya yoksa `skip` olacak şekilde işaretlenebilir (test kodu değişikliği; bu fazda yapılmadı).
4. **Octave/ECGDeli kurulum provenance'ı** BULUNAMADI. INSTALL yalnız sürüm ve SHA'ları veriyor.
5. Görev metnindeki "14 hastalık" ile kayıtlardaki 15 hastalık farkı.

## Sınırlılıklar

- Kartlar dergi makalesi değildir; TRIPOD+AI durumları kart + kaynak faz dosyalarına göre kural tabanlı atandı.
- Referans skor analizi post-hoc ve tanımlayıcıdır; eşleştirme eşikleri testte seçildi; çoklu karşılaştırma düzeltmesi yok.
- Kaynak eşik doğrulaması yalnız PubMed özetlerinden yapıldı; tam metinler okunmadı.
- Kararlar "araştırma sınıflaması"dır; model olasılığı klinik olasılık değildir. Klinik onay yoktur.
