# Mimari

Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Klinik karar aracı değildir.
Bu belge Phase XLVI'da yazıldı; diyagramların SVG/PNG çıktıları `img/` altındadır ve bu dosyadaki Mermaid
kaynaklarından `phase_xlvi/scripts/render_diagrams.mjs` ile üretilmiştir (elle çizilmedi).

İlgili belgeler: [API](api.md) · [OpenAPI](openapi.json) · [Kurulum](INSTALL.md) · [Deney tabloları](experiment_tables.md) ·
[Model kartları](model_cards/README.md)

## 1. Bileşenler

```mermaid
flowchart LR
  subgraph B["Tarayıcı"]
    UI["React + TypeScript + Tailwind<br/>127.0.0.1:4173 (preview) / 5173 (dev)<br/>form şemadan üretilir<br/>durum yalnız bellekte"]
  end
  subgraph S["FastAPI backend (127.0.0.1:8000)"]
    MW["Ara katman<br/>yalnız loopback · gövde loglanmaz<br/>anonim sayaç · sabit uyarı"]
    API["Uç noktalar<br/>/schema /models /eligibility<br/>/predict /ecg/af /health"]
    SVC["Service<br/>birim dönüşümü → doğrulama<br/>→ uygunluk → dönüşümler"]
    REG["Registry + şema v2<br/>SHA256 başlangıçta doğrulanır"]
    LOAD["Model yükleyici<br/>dosya SHA256 = registry<br/>(yüklemeden ÖNCE)"]
    ROUTE["Kanıta duyarlı yönlendirme<br/>OK / ABSTAIN / NOT_APPLICABLE<br/>panel: Çalışabilir / Eksik / Kapsam dışı / Karar verilemez"]
    MOD["13 donmuş model (11 uygulamada)<br/>donmuş eşik → eşik üstü / altı"]
    AF["AF yolu<br/>ilk 10 sn → kilitli Octave/ECGDeli<br/>→ 10 öznitelik"]
  end
  FS[("Salt okunur dosyalar<br/>phase_xliii/registry/models.json<br/>phase_xliv/registry/input_schema_v2.json<br/>model .joblib dosyaları<br/>phase_xxviii AF kilidi")]
  UI -- "/api (Vite vekili)" --> MW --> API --> SVC
  SVC --> ROUTE --> MOD
  API --> AF --> MOD
  REG --> SVC
  LOAD --> MOD
  FS --> REG
  FS --> LOAD
  FS --> AF
```

| bileşen | konum | görev |
|---|---|---|
| Arayüz | `app/frontend/src/` | form (`/schema`'dan), canlı panel (`/eligibility`), sonuçlar (`/predict`), EKG sayfası (`/ecg/af`), model kartları, hakkında. Olasılık göstermez; uyarı metni backend'den gelir. |
| Ara katman | `app/backend/healthrisk_api/main.py` | loopback dışı → 403; istek gövdesi/sağlık verisi loglanmaz; beklenmeyen hatada yalnız hata türü; her yanıtta `disclaimer`. |
| Service | `service.py`, `validation.py`, `eligibility.py`, `transforms.py`, `features.py` | birim dönüşümü ve aralık (422), popülasyon uygunluğu, 46 dönüşüm (şema v2), registry feature sırası, `precheck` (`/predict` ve `/eligibility` ortak). |
| Registry ve şema | `phase_xliii/registry/models.json`, `phase_xliv/registry/input_schema_v2.json` | model, eşik, feature sırası, kanıt, sınırlılık; alanlar, birimler, dönüşümler. SHA256'ları `app_config.json` ile doğrulanır. |
| Model yükleyici | `model_loader.py` | model dosyasının SHA256'sı **yüklemeden önce** registry ile karşılaştırılır; uyuşmazlıkta model devre dışı (`/health`). |
| AF yolu | `ecg_af.py`, `ecg_window.py` | kilitli `phase_xxviii/pipeline/af_pipeline_v1.py` kopyalanmadan çağrılır; kilit, Octave exe, ECGDeli kaynak ağacı ve compat dosyaları SHA ile doğrulanır. |

## 2. Başlangıç bütünlük denetimi

```mermaid
flowchart TD
  A["run_server.py<br/>bind_host localhost değilse başlamaz"] --> B{"Paket sürümleri =<br/>expected_packages?"}
  B -- hayır --> X1["tüm modeller devre dışı<br/>/health: degraded"]
  B -- evet --> C{"registry + şema SHA256<br/>= app_config?"}
  C -- hayır --> X1
  C -- evet --> D["her model: dosya var mı,<br/>SHA256 = registry?"]
  D -- hayır --> X2["yalnız o model devre dışı"]
  D -- evet --> E["joblib.load (registry venv eşdeğeri)"]
  A --> F{"AF kilidi, pipeline, Octave,<br/>ECGDeli, compat, ilk-10-sn kaynağı<br/>SHA256 doğru mu?"}
  F -- "dosya yok" --> X3["AF pipeline devre dışı<br/>gerekçe: Octave/ECGDeli AF çalışma ortamı yok"]
  F -- "SHA uyuşmaz" --> X4["AF pipeline devre dışı<br/>gerekçe: kilit/SHA256 doğrulaması başarısız"]
  F -- evet --> G["AF pipeline etkin"]
```

## 3. Kanıta duyarlı yönlendirme (/predict ve /eligibility)

```mermaid
flowchart TD
  I["İstek: fields (değer veya value+unit)"] --> V{"Birim dönüşümü ve<br/>makul aralık doğrulaması"}
  V -- "hata (/predict)" --> E422["HTTP 422"]
  V -- "hata (/eligibility)" --> FE["field_errors listesi;<br/>kalan alanlarla devam"]
  V -- geçerli --> M["Her app_visible model için precheck"]
  FE --> M
  M --> D1{"Model etkin mi?"}
  D1 -- hayır --> AB1["ABSTAIN<br/>panel: Karar verilemez"]
  D1 -- evet --> D2{"Popülasyon içinde mi?<br/>(yaş, gebelik, tanı, diyaliz,<br/>FEV1/FVC, girdi aralığı)"}
  D2 -- hayır --> NA["NOT_APPLICABLE<br/>panel: Kapsam dışı"]
  D2 -- "doğrulanamıyor / zorunlu alan eksik" --> AB2["ABSTAIN<br/>panel: Eksik: alanlar"]
  D2 -- "şema dışı kategori / gebelik 'bilmiyorum'" --> AB3["ABSTAIN<br/>panel: Karar verilemez"]
  D2 -- evet --> R["READY (panel: Çalışabilir)"]
  R -- "/predict" --> P["registry feature sırası → predict_proba<br/>→ donmuş eşik (olasılık saklanmaz)"]
  P --> OUT["OK: ESIK_USTU / ESIK_ALTI<br/>+ kanıt katmanları + sınırlılıklar<br/>+ hedef-tanımlayan girdi uyarısı"]
  R -. "dm_B / ckd_B çalışamazsa" .-> FB["A modeline düş<br/>(fallback_from)"]
```

- **Eksik veri doldurulmaz.** Zorunlu alan eksikse ABSTAIN; dondurulmuş imputer kullanılmaz. Yapısal boşluklar (ör. erkekte
  menopoz) eğitimdeki kuralla işlenir.
- **Irk isteğe bağlıdır.** Yanıtsızsa ırk kullanan 5 model (dm A/B, ckd A/B, htn) ABSTAIN eder; varsayılan sınıf atanmaz.
- **AF satırı** `/predict`'te her zaman NOT_APPLICABLE'dır (yalnız `/ecg/af`). `/eligibility`'de: ortam varken
  "Eksik: EKG kaydı", **ortam yoksa "Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok"** (Phase XLVI).
  Kişiye özel neden de varsa (kapsam dışı yaş, eksik alan) ana satır o nedendir; ortam nedeni altında "Ayrıca: …"
  (`additional_reasons`; Phase XLVI kapanış düzeltmesi).
- **Arayüzde sade metin (Phase L).** Sunucu gerekçe ve alan hatası metinleri DEĞİŞMEZ; arayüz bunları
  `app_config.json > ui.reason_rules_tr` / `ui.field_error_rules_tr` kurallarıyla sade Türkçeye çevirir
  (`frontend/src/lib/plain.ts`; ör. `weight_kg=500 kg makul aralık dışında [25, 300]` → "Kilo 25–300 kg arasında olmalı.").
  Ham metin yalnız "Teknik ayrıntı" içinde kalır. Kurallar, sunucunun ürettiği tüm metinlerin sentetik taramasıyla
  (`phase_l/scripts/scan_reasons.py`) Vitest'te denetlenir.
- **Canlı panel eski yanıtı göstermez (Phase L).** `/eligibility` yanıtı istendiği girdinin anahtarıyla saklanır; girdi
  değişince yeni yanıt gelene dek durum rozeti gösterilmez (önceden "Formu temizle" sonrası kısa süre, istek hatasında
  süresiz eski "Hesaplanabilir" görünüyordu).
- **Kompakt durum paneli (Phase L2).** Her analiz tek satırda: ad, durum rozeti ve "x/y bilgi girildi" ilerlemesi.
  İlerleme, modelin formdan girilen zorunlu alanlarından hesaplanır.
  - Eksikler katlıdır ("Eksikleri göster").
  - Hiç bilgi girilmemişse nötr "Henüz bilgi girilmedi" görünür. Sunucu durumu yine `MISSING`'dir; değişen yalnız
    gösterimdir.
  - Birden çok analizde aynı olan sade gerekçe, panelin üstünde bir kez yazılır.

## 4. AF yolu (/ecg/af)

```mermaid
flowchart LR
  U["Yükleme<br/>.hea + .dat/.mat<br/>yaş, cinsiyet"] --> L{"≤ 2 MB?"}
  L -- hayır --> H413["413"]
  L -- evet --> E{"AF pipeline etkin?"}
  E -- hayır --> AB0["ABSTAIN<br/>ortam yok / SHA hatası"]
  E -- evet --> HD{"Başlık: fs = 500 Hz,<br/>12 lead, ≥ 5000 örnek?"}
  HD -- hayır --> AB1["ABSTAIN"]
  HD -- evet --> W["İlk 10 sn<br/>read_first10s (XXIX/XXXIII birebir)<br/>ecg_window.py"]
  W --> O["Kilitli run_ecgdeli<br/>Octave 10.3.0 + ECGDeli v1.1<br/>(ayrı süreç, 60 sn sınırı)"]
  O --> F["Kilitli features_from_mat<br/>10 global aralık (ms)"]
  F --> N{"Öznitelik NaN /<br/>zero_beats?"}
  N -- evet --> AB2["ABSTAIN"]
  N -- hayır --> MD["af_S4_DEVICE<br/>12 öznitelik (+ yaş, cinsiyet)<br/>donmuş eşik"]
  MD --> R["Eşik üstü / altı<br/>+ 10 öznitelik + lead II ve RR (yalnız gösterim)"]
```

- Kilit: `phase_xxviii/config/af_pipeline_lock.json` (AF-ECGDELI-OCTAVE-v1). Pipeline dosyası değiştirilmez ve kopyalanmaz.
- Aynı anda tek kayıt işlenir (ikinci istek 429). Geçici dosyalar yanıttan önce silinir.
- Eğitim öznitelikleri PTB-XL+ yayımlanmış ECGDeli değerleridir; uygulama ve dış doğrulama kilitli Octave yeniden
  uygulamasını kullanır. Fark ve doğrulaması: `phase_xlvi/af_validation_dossier.md` §2.

## 5. Gizlilik ve güvenlik

- Sunucu yalnız `127.0.0.1`; loopback dışı istemci 403. Kimlik doğrulama yok (tek kullanıcı, yerel kullanım).
- İstek gövdesi ve sağlık verisi loglanmaz, diske yazılmaz. 422 ayrıntısı girdi değerini yansıtmaz.
- Tarayıcıda kalıcı saklama yok (localStorage, sessionStorage, IndexedDB kullanılmaz); analitik yok; istekler yalnız
  aynı köken `/api`.
- Testler: `app/backend/tests/test_privacy.py`, `app/frontend/e2e/privacy.spec.ts`.

## 6. Diyagram dosyaları

| diyagram | SVG | PNG |
|---|---|---|
| 1. Bileşenler | [img/01_components.svg](img/01_components.svg) | [img/01_components.png](img/01_components.png) |
| 2. Başlangıç bütünlük denetimi | [img/02_startup.svg](img/02_startup.svg) | [img/02_startup.png](img/02_startup.png) |
| 3. Kanıta duyarlı yönlendirme | [img/03_routing.svg](img/03_routing.svg) | [img/03_routing.png](img/03_routing.png) |
| 4. AF yolu | [img/04_af_path.svg](img/04_af_path.svg) | [img/04_af_path.png](img/04_af_path.png) |
