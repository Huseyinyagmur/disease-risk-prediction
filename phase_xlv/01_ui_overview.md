# Phase XLV — Görev 1: Arayüz (app/frontend) ve backend ekleri

Kod: `app/frontend/` (Vite 6.3.5 + React 18.3.1 + TypeScript 5.8.3 + Tailwind 3.4.17 + Recharts 2.15.3; tüm sürümler
`package.json`'da tam sürüm, `package-lock.json` kilitli). Kurulum/çalıştırma: `app/frontend/README.md`.
Ekran görüntüleri: `screenshots/01–10` (sentetik profiller, açık PTB-XL örnek EKG).

## Şema kaynağı

`/schema`, `phase_xliv/registry/input_schema_v2.json`'ı sunar (`app/backend/healthrisk_api/paths.py > SCHEMA_JSON`;
yanıtta `schema_version: "2.0"`, 15 satırlık `changes_from_v1`). v1 kullanılmıyor. Kontrol edildi (faz başı, canlı
sunucu `/health` → `schema_version 2.0`, `status ok`).

## İlkelerin uygulanışı

| ilke | uygulama |
|---|---|
| Model mantığı, birim dönüşümü, uygunluk backend'de | Frontend değeri metin olarak alır, yalnız sayıya ayrıştırır (ondalık virgül kabul) ve seçilen birimle `{value, unit}` olarak gönderir. Aralık denetimi frontend'de **yapılmaz**; sunucunun `/eligibility > field_errors` mesajı alanın altında gösterilir. Kaynak kodda eşik, olasılık veya dönüşüm katsayısı yok (statik tarama + Vitest "aralık dışı değer de gönderilir" testi). |
| Form `/schema`'dan dinamik | Alanlar (`form_input=true`), etiketler, birimler, birim seçenekleri (`unit_conversions`), makul aralık metni, notlar, bölümler (`form_section`), koşullu sorular (`ask_when_rule`), zorunluluk (`required_when_rule`), kategori etiketleri sunucudan gelir. Frontend'de alan listesi yok. Yalnız demo profilleri alan adı içerir (veri; test şemaya karşı denetler). |
| Kalıcı saklama yok, analitik yok | Durum yalnız React context'inde. Storage/IndexedDB/çerez API'si kodda yok; `fetch(..., {cache: 'no-store', credentials: 'omit'})`. Harici yazı tipi/istek yok; CSP `default-src 'self'`. Yenileme → tüm veri silinir (Playwright ile doğrulandı). |
| Türkçe ve sabit uyarı | Tüm metinler Türkçe. Üstte yapışkan bant, her ekranda, talimattaki metin birebir. |
| Olasılık gösterilmez | Karar yalnız `research_class` → "İleri değerlendirme önerilir" / "Eşik altında"; backend zaten olasılık dönmüyor. |

## Ekranlar

1. **Giriş** — amaç (mevcut durum sınıflandırması; gelecek risk tahmini değil), uyarı, gizlilik notu, "Başla" ve
   "EKG ile AF analizi".
2. **Ortak veri girişi** — bölümlü tek sayfa: 1 Temel bilgiler (yaş, cinsiyet, gebelik, ırk) → 2 Ölçümler (boy, kilo,
   bel, 3 tansiyon okuması) → 3 Öykü ve ilaçlar → 4 Laboratuvar ve spirometri (isteğe bağlı) → 5 Klinik değerlendirme ve
   efor testi (isteğe bağlı; yalnız CAD). Birim seçici (ör. mg/dL ↔ mmol/L, mg/dL ↔ µmol/L, g/dL ↔ g/L, cm ↔ inç).
   Koşullu sorular: gebelik ve GDM / adet / HRT (kadın), son adet yaşı (kadın ve adet yok), tansiyon ilacı (tansiyon
   tanısı var). Gebelik kadında ≥ 18 yaşta "* zorunlu" işaretli ve "Bilmiyorum" seçeneği var. Irk sorusu "(isteğe
   bağlı)", "Belirtmek istemiyorum (yanıtsız)" seçeneği ve şema notuyla (yanıtsızsa 5 model ABSTAIN). Gizlenen koşullu
   alanlar gönderilmez.
3. **Canlı model yönlendirme paneli** — formun yanında; her değişiklikte 300 ms gecikmeli `POST /eligibility`; eski
   yanıtlar iptal edilir. 11 app_visible model için rozet: **Çalışabilir** / **Eksik: …** (alan etiketleri) /
   **Kapsam dışı: …** (gerekçe) / **Karar verilemez: …** (ör. gebelik "bilmiyorum", şemada olmayan kategori) ve modül
   etiketi. Ana modüller (AF, fibrozis) üstte, sonra araştırma modülü (osteoporoz), deneyseller gri. AF satırında
   "Eksik: EKG kaydı" ve EKG sayfasına bağlantı. Hedefi tanımlayan girdi uyarıları panelin altında.
4. **Sonuç ekranı** — `POST /predict`. Model kartı: karar, ABSTAIN/kapsam dışı ise neden ve eksik alanlar, B → A geri
   düşüşü (`fallback_from`) veya laboratuvarlı model seçimi, hedefi tanımlayan girdi uyarısı, kanıt düzeyi rozetleri
   (iç test / zamansal / dış doğrulama; olmayan düzey üstü çizili), test metrikleri tablosu (n, n_pos, P, R, FPR, AUC ve
   %95 GA; değer yoksa "—"), araştırma hedefi notu, hedef tanımı (`/models`), sınırlılıklar. Ana modüller ve araştırma
   modülü üstte; deneyseller ayrı bölümde, gri tonda. Sunucudaki birim dönüşümleri ayrıca listelenir.
5. **AF EKG analizi** — `.hea` + `.dat`/`.mat` sürükle-bırak veya dosya seçici; yaş/cinsiyet (şemadan); yükleme yüzdesi
   ve sunucu işleme süresi göstergesi; sonuç kartı; değerlendirilen pencere ("ilk 10 sn (5000 örnek) — kayıt daha uzun,
   kırpıldı" sunucudan) ve kalıcı "yalnız ilk 10 saniye değerlendirilir" bilgisi; 10 EKG özniteliği tablosu; lead II
   grafiği (R tepeleri dikey çizgi) ve RR takogramı (ardışık RR aralıkları; AF örneğinde düzensiz zikzak, SR örneğinde
   düz çizgi). İki örnek kayıt düğmesi.
6. **Model kartları** — `/models`: hastalık, modül, rol/mod/uç nokta, hedef, veri/popülasyon, eksik girdi kuralı, kanıt
   ve metrikler, zorunlu/koşullu girdiler, sınırlılıklar, şema v2 değişiklikleri.
7. **Hakkında** — yöntem özeti, "kanıta duyarlı yönlendirme" açıklaması, model başına veri/kanıt kaynakları (registry'den
   dinamik), gizlilik.

## Backend ekleri (app/backend; model, eşik, registry, şema dosyaları değişmedi)

| ek | ayrıntı |
|---|---|
| `POST /eligibility` | Gövde `/predict` ile aynı. `Service.precheck` (yeni): `/predict`'teki tahmin öncesi adımların (devre dışı kontrolü → `eligibility.check` → `features.build` → NA/ABSTAIN kararı) ayrılmış hâli; `predict_model` artık bunu çağırıyor, davranış aynı (XLIV testlerinin tamamı geçti). `/eligibility` yalnız `precheck` çalıştırır, `predict_proba` çağrılmaz (testte `predict_proba` patlatılarak doğrulandı). Alan hataları 422 yerine `field_errors` listesinde (hatalı alan dışarıda bırakılıp kalanı yine aynı `validate_fields` ile doğrulanır). Durumlar `READY / MISSING / OUT_OF_SCOPE / ABSTAIN`; AF için `ecg_record` sanal eksik alanı. Hedef-tanımlayan girdi uyarıları da döner. |
| `/schema` sunum alanları | `form_section`, `ask_when_rule`, `required_when_rule` (şema metninden sunucuda ayrıştırılır: `"sex = female ve age_years ≥ 18"` → `[{sex eq female}, {age_years gte 18}]`; tanınmayan biçim → başlangıçta hata), `form` (bölümler, Türkçe kategori etiketleri, sanal alan etiketleri; `app_config.json > form`). Model mantığını etkilemez. |
| `/ecg/af` `display` | Lead II, ilk 10 sn, 500 → 250 Hz (her 2. örnek, filtresiz), mV; R tepe zamanları = kilitli `load_fpt` çıktısında `FPT_MultiChannel` 6. sütun (RR_Mean_Global feature'ının hesaplandığı sütun), zaman = (1 tabanlı indeks − 1)/500; `rr_ms`. Kilitli pipeline kodu çağrılır, değiştirilmez; gösterim hatası sonucu etkilemez. Testte: feature'lar phase_xxviii parity çıktısıyla birebir, `median(rr_ms)` = `RR_Mean_Global` (|Δ| ≤ 0,1 ms; yuvarlama). |
| gizlilik | `/eligibility` anonim sayaçlarda ayrı yol anahtarı; istek gövdesi loglanmaz (XLIV gizlilik testlerine `/eligibility` istekleri eklendi, süreç içi ve gerçek sunucu logunda işaret yok). |

## Demo verisi

- Sentetik profiller (`app/frontend/src/demo/profiles.ts`, arayüzde "SENTETİK … gerçek kişi verisi değildir"):
  `fibrosis_ready` (58 E, form + karaciğer laboratuvarları → fibrozis Çalışabilir), `missing` (47 K, yalnız temel +
  boy/kilo), `out_of_scope` (30 K gebe → dm/ckd/htn/fibrozis/anemi kapsam dışı, osteo yaş < 50), `unit_error` (glukoz
  5,4 ve kreatinin 80 mg/dL biriminde → alan altı aralık hatası; birim düzeltilince kaybolur).
- Örnek EKG: `app/frontend/public/samples/` — PTB-XL `00691_hr` (etiket AF, parity kümesinde *fit*) ve `00165_hr`
  (etiket SR, *validation*); phase_xxviii'den bayt düzeyinde kopya, SHA256 PhysioNet SHA256SUMS değerleriyle aynı.
  Lisans CC BY 4.0 (PhysioNet sayfası 2026-11-19'da kontrol edildi), atıflar README'de. Geliştirme kayıtlarıdır; bu
  kayıtlardaki karar performans kanıtı değildir. Örneklerle gönderilen yaş/cinsiyet sentetik (60, erkek).

## Talimattan ayrılan / karar gerektiren noktalar

1. **Panelde dördüncü durum "Karar verilemez".** Talimat üç rozet tanımlıyor; ancak gebelik "bilmiyorum", şemada olmayan
   kategori veya devre dışı model ne "eksik" ne "kapsam dışı"dır. Bunlar için gerekçeli ayrı rozet eklendi. Eksik alan
   da varsa durum "Eksik" kalır ve gerekçe altında listelenir.
2. **Aralık denetimi yalnız sunucuda.** İlke gereği frontend dönüşüm yapmadığından, başka birim seçildiğinde aralığı
   bilemez; tutarlılık için tüm aralık hataları sunucudan (≈ 300 ms gecikmeyle) gelir. Hatalı alan panel hesabından
   çıkarıldığı için panel o alanı ayrıca "Eksik" olarak da gösterir.
3. **Bölüm ataması ve Türkçe kategori etiketleri** şemada yok; backend `app_config.json > form` içinde tanımlandı
   (ör. `nh_white` → "Hispanik olmayan beyaz", `non_anginal` → "Anjinal olmayan ağrı"). Etiketler benim çevirimdir;
   gözden geçirmenizi öneririm.
4. **Sabit uyarı metni.** Arayüz talimattaki metni ("…sınıflandırması yapar…") birebir gösterir; backend'in her
   yanıttaki `disclaimer` metni ("…sınıflandırmasıdır…") değiştirilmedi. İki metin anlamca aynı, kelimece farklı.
5. **XLIV test dosyası değişti:** `app/backend/tests/test_privacy.py` — izinli yol kümesine `/eligibility` eklendi ve
   log gizliliği isteklerine üç `/eligibility` çağrısı eklendi (aksi hâlde yeni uç nokta nedeniyle kırılıyordu).


---

## Güncelleme (2026-11-19)

- Madde 1 ("Karar verilemez") ve madde 5 (`test_privacy.py`) onaylandı.
- Madde 4 kapandı. Uyarı metninin tek kaynağı backend'dir (`app_config.json > disclaimer_tr`, metin "…sınıflandırması
  yapar…"). Arayüz metni `/schema > disclaimer` alanından alır; kaynak kodda uyarı metni yok.
- Madde 3 için `phase_xlv/app_config_review.json` (kaynağın birebir kopyası) gözden geçirmenize hazır.
- EKG ekranındaki işlem süresi metni: "bu makinede ölçülen ≈ 7–30 sn, makine yüküne bağlı; üst sınır 60 sn"
  (`03_af_timing.md`).