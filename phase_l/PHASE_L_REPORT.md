# PHASE L: Arayüz testi bulguları, anlaşılırlık iyileştirmesi ve büyük asistan paneli

Durum: **TAMAMLANDI** (açık maddeler §11'de).
- Model, eşik, registry, şema ve uygunluk/dönüşüm mantığı değişmedi (bkz. `results/verificationL.json`).
- Olasılık hiçbir ekranda gösterilmiyor. Uyarı bandı, modül etiketleri ve kanıt düzeyi her sayfada görünür.
- Veri saklanmıyor: localStorage, sessionStorage ve çerez yazımı yok (Playwright `privacy.spec.ts`).
- Yeni bağımlılık eklenmedi.
- `clinical_probability_eligibility = false`.

## 0. Kurulu skill'ler ve bu fazda kullanılanlar

Kurulu (CLAUDE.md): grill-with-docs / grill-me, tdd, systematic-debugging, anti-ui-slop, frontend-design,
web-design-guidelines, agent-browser, code-review, improve-codebase-architecture, graphify, handoff, stop-slop, find-skills,
verification-before-completion, token-optimization, cv-*. Bu oturumda listede görünmeyenler: grill-with-docs (yerine
`grilling` var), agent-browser (Playwright kullanıldı), improve-codebase-architecture, handoff.

| skill | adım | ne için |
|---|---|---|
| systematic-debugging | madde 5, 8 | önce yeniden üretim (`probe_stale.cjs`, `asst_probe.py`), sonra kök neden, sonra test ve düzeltme |
| frontend-design | madde 6–7 | durum odaklı görsel plan, kalıp varsayılanlardan kaçınma (tek vurgu rengi, yüzeysel dekor yok) |
| anti-ui-slop | madde 6–7 | tasarım sözleşmesi (`01_design_contract.md`), sayım (`results/count_finish.txt`: 0 hata), ayrı bağlamda bir eleştiri turu |
| tdd | tüm kod | test önce (backend `test_phase_l.py`, Vitest `plain.test.ts`, `phase_l.test.tsx`); kırmızı sonra yeşil |
| web-design-guidelines | UI bitince | değişen 7 dosya incelendi; düzeltilenler: sürüklemede metin seçimi, `overscroll-contain`, `transition-[width]`, azaltılmış hareket |
| stop-slop | metinler | rapor ve app_config sade Türkçe metinleri |
| code-review | kapanış | standart + spec ekseni, iki ayrı alt ajan (§9) |
| verification-before-completion | kapanış | tüm test takımları ve SHA denetimi koşulmadan "tamam" denmedi |

Kullanılamayanlar: görüntü üretme aracı ve UIZZE MCP yok, bu yüzden anti-ui-slop'un hedef görsel ve dış referans adımları
atlandı (`01_design_contract.md` §3).

## 1. Teknik metinlerin sadeleşmesi (madde 1)

Sunucu metinleri değişmedi; arayüz bunları `app_config.json > ui.reason_rules_tr` (31 kural) ve
`ui.field_error_rules_tr` (5 kural) ile sade Türkçeye çevirir (`frontend/src/lib/plain.ts`). Ham metin yalnız "Teknik
ayrıntı" içinde kalır.

- **Tarama:** `scripts/scan_reasons.py` 74 sentetik uç durumu `/eligibility` ve `/predict`'e gönderdi. Toplananlar: 108
  gerekçe, 42 alan hatası, 3 uyarı metni (`results/reason_scan.json`).
- **Denetim:** Vitest, her metnin ana metindeki halinde snake_case, köşeli parantezli aralık, `alan=değer` ve teknik terim
  (pipeline, feature, policy, pre-BD, "model popülasyonu", "makul aralık") olmadığını sınar. 157 test geçti.
- a) "age=30 yıl model girdi aralığı dışında [50, 80]" satırı, sade yaş satırı varken ana listede gösterilmez. Tek nedense
  sade biçimde gösterilir ("Vücut kitle indeksi …: bu analiz yalnız 12–80 kg/m² arasındaki değerlerle geliştirildi").
- b) Gebelik "bilmiyorum" metni görevdeki cümlenin aynısıdır.
- c) "weight_kg=500 kg makul aralık dışında [25, 300]" artık "Kilo 25–300 kg arasında olmalı." olarak görünür. Kalıp
  bütün sayısal alanlarda alan etiketinden kurulur. Yüzde alanında Türkçe biçim kullanılır: "%3,0–18,0".
- Ek olarak: EKG işleme satırı ("ECGDeli delineasyonu → 10 feature" yerine sade metin), birim dönüşüm notları ("42 g/L,
  4,2 g/dL olarak kullanıldı") ve EKG kaydı etiketi (".hea + .dat/.mat" kaldırıldı).

## 2. Kanıt düzeyi rozetleri (madde 2)

Rozetler yalnız registry'deki `evidence.tiers` verisinden gelir. Yapılan düzeyde "✓" görünür. Kaydı olmayan düzey üstü
çizilir; yanında görünür "(kayıt yok)" ibaresi ve kartta şu not yer alır: "Üstü çizili: bu tür test bu model için
yapılmadı veya kayıtlı sonucu yok."

Kart verisi denetimi (`/models`):

| model | iç test | zamansal | dış |
|---|---|---|---|
| AF | ✓ (PTB-XL n=1.572) | yok | ✓ (Challenge 2021 n=7.817) |
| Fibrozis | ✓ (n=4.714) | yok | yok |
| Osteoporoz | **yok** | ✓ (NHANES J n=2.275) | yok |
| Hipertansiyon | **yok** | ✓ (NHANES C n=2.798) | yok |

Osteoporoz ve hipertansiyonda registry'de iç test kaydı yok. Bu modellerde iç testin hiç yapılmadığını gösteren bir kayıt
BULUNAMADI. Bu yüzden metin "yapılmadı" değil, "yapılmadı veya kayıtlı sonucu yok" der. Eleştiri turu üstü çizgiyi
tamamen kaldırmayı önerdi; görev açıkça "üstü çizili rozete görünür kısa not" istediği için uygulanmadı.

## 3. AF eşik üstü kartı (madde 3)

- "Ne yapmalıyım?" metnine şu cümle eklendi: "AF dışındaki bazı ritim bozuklukları (ör. ekstrasistol, flutter, hızlı kalp
  atımı) da bu sonucu verebilir."
- Registry sınırlılığında yalnız 3 ritim vardı. App_config'e (`ui.limitations_extra_tr`; registry salt okunur) iki ek
  satır eklendi. Sayılar `phase_xxxiii/results/b_rhythm_fpr.csv` ve `afl_results.csv` "Havuz (4 kaynak)" satırlarından
  birebir alındı (FP/n, Wilson %95 GA):

| ritim | eşik üstü / n | oran [%95 GA] |
|---|---|---|
| ventrikül kaynaklı ekstrasistol (PVC) | 19/62 | 0,306 [0,206–0,430] |
| kalp pili ritmi | 3/10 | 0,300 [0,108–0,603] |
| sinüs taşikardisi | 43/237 | 0,181 [0,138–0,235] |
| kulakçık kaynaklı ekstrasistol (PAC/SVPB) | 20/131 | 0,153 [0,101–0,224] |
| diğer ritimler | 72/1142 | 0,063 [0,050–0,079] |
| atriyal flutter (AF olarak sınıflanma oranı; birincil metriklere katılmadı) | 420/651 | 0,645 [0,608–0,681] |

Backend testi bu sayıların CSV'yle aynı olduğunu sınar.

## 4. EKG sayfası (madde 4)

- "Örnek kayıtla dene" başlığı altında iki büyük düğme var: "AF kaydı" ve "Sinüs ritmi kaydı". Her düğmede bir satır
  açıklama bulunur.
- Analiz sürerken "Analiz yaklaşık 10–30 sn sürebilir; bu sayfadan ayrılmayın." yazısı ve geçen saniye görünür.
- Görüntüler: `L_desktop_06_ekg_ornek_kayitlar.png`, `L_desktop_07_ekg_sure_gostergesi.png`.

## 5. Boş formda "Hesaplanabilir" (madde 5)

- **Temiz oturum, ilk açılış, boş form, tüm analizler seçili:** sorun YENİDEN ÜRETİLEMEDİ. 1.440 ve 768 px'te
  localStorage boştu; panel önce boştu, 1,5 sn'de 11 modelin tamamı "Eksik bilgi" gösterdi (`screenshots/before/probe_before.json`).
  Sunucu da boş girdiye bütün modeller için MISSING döndürüyor. Uygulama tarayıcı depolaması kullanmadığı için önceki
  oturumdan bir değer taşınamıyor.
- **Yeniden üretilen hata:** Profil yüklenip "Formu temizle"ye basılınca boş formda fibrozis ve osteoporoz yaklaşık
  300–400 ms boyunca "Hesaplanabilir" kaldı (`results/probe_stale_before.json`). Kök neden: panel son gelen yanıtı, hangi
  girdi için istendiğine bakmadan gösteriyordu. İstek hata verirse eski durum süresiz kalıyordu.
- **Düzeltme:** `DataEntry.tsx` yanıtı istendiği girdinin anahtarıyla saklar. Girdi değişince yeni yanıt gelene dek durum
  rozeti gösterilmez. Sonra: 0–200 ms boyunca panel boş, 400 ms'de MISSING (`results/probe_stale_after.json`).
- **Testler:** Vitest'te iki test var: temizleme ve istek hatası.

## 6. Anlaşılırlık (madde 6)

Sorun listesi ve tasarım sözleşmesi: `01_design_contract.md` (S1–S11).

| alan | önce | sonra |
|---|---|---|
| analiz seçimi | seçim boş; "Tümü" 9 analiz ve 7 adım | açılışta ana modüller + osteoporoz (3 analiz); "Deneysel modüller (isteğe bağlı)" kapalı; her kartta gereksinim etiketi ("Kan tahlili gerekir", "EKG kaydı gerekir", "Tahlil gerekmez") |
| adımlar | "Adım 1 / 7", 12 px düğmeler | "Adım 2 / 6: Temel bilgiler"; 14 px düğmeler, tamamlanan adımlar ayrı renkte; her bölümde "Neden soruluyor?" cümlesi; kontrol adımında atlanan adımlar listelenir |
| gerekmeyen alanlar | seçime göre zaten gizliydi (Phase XLVII) | aynı; atlanan adımlar artık açıkça yazılıyor |
| sonuçlar | özet yok | üstte özet şeridi ("3 analiz: 1 eşik üstü, 1 eşik altı, 1 EKG kaydı bekliyor") ve karta bağlantı; sonuç kutusu 18 px, simgeli; ikincil bilgiler katlanmış |
| durum renkleri | eşik altı ve uygun değil aynı gri; "sonuç üretilmedi" kırmızı | tek kaynak `lib/status.ts`: eşik üstü turuncu ▲, eşik altı mavi ▼ (yeşil değil: negatif sonuç dışlamaz), sonuç üretilmedi kesikli gri ?, EKG bekliyor kesikli gri …, uygun değil taş grisi – |
| okunabilirlik | ana içerikte 11 px metin | ana içerikte en küçük 12 px; 11 px yalnız teknik ayrıntı ve altbilgide |

Ekran görüntüleri:
- Önce: `screenshots/before/` (26 Playwright + 6 yoklama).
- Sonra: `screenshots/after/` (aynı akışlar + `L_*` yeni öğeler).
- Eşleşen çiftler: `desktop_02_analiz_secimi`, `desktop_03_temel_bilgiler`, `desktop_06_kontrol_ve_hesaplama`,
  `desktop_07_sonuclar`, `desktop_10_ekg_af_ornegi`, `tablet768_02…07`, `desktop_p03_asistan_paneli`.

## 7. Açıklama asistanı paneli (madde 7)

- **Masaüstü (≥ 1.024 px):** sağda tam yükseklik yan panel, ekranın yaklaşık %38'i. İçerik ve uyarı bandı panel kadar
  daralır; Playwright içeriğin panelin altında kalmadığını ölçer.
- **Boyut:** panelin sol kenarı sürüklenerek ya da ←/→ tuşlarıyla değişir (en dar 360 px). "Paneli genişlet" ekranın
  yaklaşık %92'sini kaplar.
- **Tablet ve mobil:** panel tam ekran açılır.
- **İçerik:**
  - mesajlar 16 px;
  - acil uyarı kutusu kalın kırmızı kenarlı ve 16 px;
  - kaynaklar katlanabilir liste ("Kaynaklar (n)");
  - örnek sorular büyük düğmeler.
- **Örnek sorular:** sonuç varsa yalnız sonuç ETİKETİNDEN (hastalık + durum) seçilir, ör. "Eşik üstü sonuç ne anlama
  geliyor?" ya da "FibroScan nedir?". Ham değer kullanılmaz; Vitest bunu sınar.
- "Yerel model — veriler bilgisayarınızdan çıkmaz" notu ve araştırma uyarısı panelde görünür kalır. Sohbet yalnız
  bellekte tutulur.

## 8. Asistan yanıt hatası (madde 8)

Ayrıntı: `02_assistant_fix.md`.

**Kök neden:** sözlükte eşik üstü ve eşik altı tek parçadaydı. "Ne yapmalıyım?" parçaları tüm durumları birlikte
içeriyordu. Etiket sabitleme, AF eşik üstü etiketinde de "Bu sonuç AF'yi dışlamaz" metnini bağlama ekliyordu.

**Düzeltme:**
- parçalar ayrıldı;
- sabitleme yalnız etiketin kendi durumuna bağlandı;
- son kontrole `threshold_polarity` ve `probability_claim` eklendi;
- atıf temizliği eklendi (tek başına atıf ve "[3], [3]" yığını).

İndeks ve kilit v2 olarak yeniden üretildi: manifest `19ef65c2…`, iki üretim aynı. Düzeltme sonrası yoklamada
"dışlamaz" hiçbir yanıtta eşik üstüne bağlanmadı.

### Ana test seti: yalnız regresyon (bir kez; iyileşme iddiası yok)

`03_eval.md`'deki 62/67, v2 ve v3 sonuçları ESKİ sürüme aittir ve değişmedi. Yeni sürümle koşu: **60/67** (Wilson %95 GA
0,800–0,948). Eski 1. koşu 62/67 idi.

| grup | eski | yeni |
|---|---|---|
| G1 bilgi | 14/16 | 13/16 |
| **G2 sonuç etiketi** | **10/10** | **7/10** |
| G3 tıbbi ret | 9/10 | 10/10 |
| G4 acil | 8/10 | 10/10 |
| G5 kapsam dışı | 10/10 | 10/10 |
| G6 enjeksiyon | 11/11 | 10/11 |

**Bu bir gerilemedir.**
- **G2 düşüşü Phase L kaynaklıdır.** İki yanıtı son kontrol attı: birinde "reçete", birinde olumsuz cümlede "kesin
  olarak" geçti. İki yanıtta model "kaynaklarımda bilgi yok" ekledi ve kaynak listesi boşaldı. Hiçbiri yanlış tanı, doz
  ya da uydurma kaynak değil.
- G3 ve G4 artışı Phase XLVIII v2/v3 ön filtresinden gelir, Phase L'den değil.
- G6-08, kilitli değerlendiricinin "Japonya" sözcüğünü eşleştirmesinden gelir. Yanıtın kendisi "doğrulandığına dair bilgi
  bulunmamaktadır" diyor.

Sonuca bakılarak hiçbir kural, istem veya parça değiştirilmedi.

## 9. Kod incelemesi (code-review, iki eksen)

**Standart ekseni:**
- 2 kesin ihlal bulundu ve düzeltildi: EKG örnek notunda ve altbilgide `.tsx` içine yazılmış metin; ikisi de app_config'e
  taşındı.
- Kanaat bulguları:
  - **düzeltildi:** `lib/status.ts` ile `ResultCard` arasındaki döngüsel bağımlılık (`needsEcg` lib'e taşındı), kullanılmayan
    `_always` okuması, iki küçük tekrar;
  - **bırakıldı:** `RESULT_LOOK.chip` ile `box` aynı; `patch_app_config.py` metinleri app_config'e yazan betik olduğu için
    metinleri ikinci kez tutuyor; `TECH` denetim kalıbı kodda.

**Spec ekseni:**
- **düzeltildi:** EKG işleme satırındaki teknik metin, birim notları, yüzde biçimi, rozette görünür not;
- **raporlandı:** regresyon (§8);
- **açık (§11):** soru biçimli etiketlerde aralık cümlesi ("Son adetinizi kaç yaşında gördünüz? 10–70 yıl arasında
  olmalı.") ve tam ekran panelde `aria-modal="false"`.

## 10. Testler (bu fazda koşuldu)

| takım | sonuç | dosya |
|---|---|---|
| Backend pytest (tam; AF uçtan uca Octave + gerçek Ollama dahil) | 461 test: 456 geçti, 5 xfail (onaylı BMI/osteo sınırlılıkları), 0 başarısız (152 sn) | `results/pytest_backend_full.xml`, `logs/pytest_backend_full.log` |
| Vitest | 234 geçti / 234 (10 dosya) | `npx vitest run` |
| Playwright (masaüstü 1.440 + tablet 768 + mobil 375) | 36 geçti / 36 | `results/playwright/playwright_junit.xml`, `logs/playwright.log` |
| axe (WCAG 2.1 A/AA) | 30 ekran (1.440 ve 375 px), **0 ihlal** | `results/axe_results.json` |
| anti-ui-slop sayım | 0 hata, 1 uyarı (EKG örnek dosyası getirmede yükleniyor işareti yok; yerel dosya, anlık) | `results/count_finish.txt` |
| Asistan regresyonu | 60/67 (§8) | `eval_regression/` |

Pytest'in ilk tam koşusunda 1 test başarısız oldu: `test_privacy::test_stats_are_anonymous`. Kök neden: yeni
`test_phase_l.py` API testi `/assistant/ask` sayacını geri yüklemiyordu. Phase XLVIII'deki geri yükleme fikstürü
eklenerek düzeltildi ve tam koşu yinelendi.

## 11. Açık maddeler ve sınırlılıklar

- **Asistan regresyonu:** G2 10/10'dan 7/10'a düştü (§8). Düzeltmek için test setine bakmadan yazılmış ayrı bir
  geliştirme seti gerekir; bu fazda yapılmadı.
- **Küçük modelin kalan hataları:** bozuk Türkçe ("dışlamadığı anlamına gelir"), yanlış parçaya atıf, "EKG kaydı
  gerekiyor" etiketine eşik üstü yönlendirmesi. Son kontrol yalnız kural tanımlı iki kalıbı yakalar.
- **Soru biçimli etiketler:** aralık hatası kalıbı görevdeki örneği ("Kilo 25–300 kg arasında olmalı.") izler. Soru
  biçimli etiketlerde cümle akıcı değil.
- **Tam ekran asistan paneli:** `aria-modal="false"` kaldı (odak tuzağı yok). axe ihlal bulmadı.
- **EKG dosya kontrolü metinleri** (".hea başlık dosyası yok" vb.) `EcgPage.tsx` içinde kaldı (Phase XLVI'dan beri).
  Teknik dosya adlarıdır, app_config'e taşınmadı.
- **app_config.json** `json.dumps(indent=1)` ile yeniden yazıldı. Diff büyük görünür; içerik değişiklikleri
  `03_text_changes.md`'de (4 değişen, 3 kaldırılan, 75+ eklenen anahtar).
- **Uyarı bandı:** 640 px altında sabit değil (Phase XLVII kararı). Tam ekran asistanda bant görünmez; panelin kendi
  uyarı satırı vardır.

## 12. Bütünlük

`scripts/sha_full_scan.py` (.git, node_modules, .venv, __pycache__, dist hariç) faz başında ve sonunda koşuldu;
`scripts/verifyL.py` → `results/verificationL.json`: **ok = true**.

| denetim | sonuç |
|---|---|
| dosya sayısı (önce / sonra) | 158.783 / 158.913 |
| app/ ve phase_l/ dışında değişen / silinen / yeni dosya | 0 / 0 / 0 |
| önceki faz dosyalarında değişen veya silinen | 0 |
| registry (phase_xliii, phase_xliv) değişen | 0 |
| uygunluk/feature/doğrulama/dönüşüm/servis/model yükleme/EKG mantık dosyaları değişen | 0 |
| app_config registry SHA'ları ve modül etiketleri | değişmedi |
| app/ içinde değişen / yeni / silinen | 41 / 6 / 0 (kod, testler, app_config metinleri, asistan KB v2 ve kilit) |

Son taramadan SONRA yalnız şu iki dosya değişti: bu rapor (yer tutucular dolduruldu) ve kökteki `.gitignore` (commit için 5 satır eklendi: `phase_l/results/sha_*.json` (2×23 MB) ve Playwright artefaktları izlenmez; önceki fazlarla aynı uygulama).

## Çıktılar

| dosya | içerik |
|---|---|
| `00_task.md` | görev metni (kayıt) |
| `01_design_contract.md` | sorun listesi + tasarım sözleşmesi |
| `02_assistant_fix.md` | asistan kök neden, düzeltme, regresyon tablosu |
| `03_text_changes.md` | değişen app_config metinleri (otomatik) |
| `scripts/` | `sha_full_scan.py`, `scan_reasons.py`, `patch_app_config.py`, `gen_schema_fixture.py`, `asst_probe.py`, `probe_ui.cjs`, `probe_stale.cjs`, `text_changes.py`, `verifyL.py` |
| `results/` | SHA envanterleri, tarama, yoklamalar, pytest XML, Playwright, axe, sayım, doğrulama |
| `eval_regression/` | ana test seti regresyon koşusu |
| `screenshots/before`, `screenshots/after` | önce/sonra görüntüleri |
