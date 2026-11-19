# HealthRisk AI Research V2 — arayüz (app/frontend, Phase XLV)

Vite + React + TypeScript + Tailwind CSS (+ Recharts) ile yazılmış araştırma arayüzü. **Klinik karar aracı değildir.**
Her ekranda sabit araştırma uyarısı gösterilir. Metnin tek kaynağı backend'dir (`app/backend/config/app_config.json >
disclaimer_tr`); arayüz metni `/schema` yanıtının `disclaimer` alanından alır ve kendisi tutmaz.

## İlkeler

- Model mantığı, birim dönüşümü, aralık denetimi ve uygunluk kararı **backend'dedir** (`app/backend`). Arayüz değeri ve
  seçilen birimi olduğu gibi gönderir; eşik, olasılık veya dönüşüm kodu içermez. Model olasılığı gösterilmez.
- Form, `/schema`'dan dinamik üretilir (alanlar, birimler, aralıklar, `ask_when_rule` / `required_when_rule`, bölümler,
  kategori etiketleri). Arayüzde elle kopyalanmış alan listesi yoktur.
- Sağlık verisi tarayıcıda kalıcı saklanmaz: localStorage / sessionStorage / IndexedDB / çerez kullanılmaz; durum yalnız
  React belleğindedir, sayfa yenilenince silinir. Analitik yok, harici yazı tipi/istek yok (yalnız localhost).

## Kurulum

Node.js 22 (denendi: 22.14.0, npm 11.2.0). Paket sürümleri `package.json`'da tam sürümle, `package-lock.json`'da kilitli.

```powershell
cd app\frontend
npm ci
npx playwright install chromium     # yalnız uçtan uca testler için
```

## Çalıştırma

1. Backend (ayrı terminal; bkz. `app/backend/README.md`):
   ```powershell
   cd app\backend
   .venv\Scripts\python.exe -B run_server.py --port 8000
   ```
2. Arayüz (geliştirme): `npm run dev` → <http://127.0.0.1:5173>
   veya üretim derlemesi: `npm run build` ardından `npm run preview` → <http://127.0.0.1:4173>

Arayüz istekleri aynı kökenden `/api/...` ile gönderir; Vite vekili öneki kaldırıp `http://127.0.0.1:8000`'e iletir
(farklı port: `HEALTHRISK_API_PORT=8765`). Sunucular yalnız `127.0.0.1`'e bağlanır.

## Ekranlar

| ekran | içerik |
|---|---|
| Giriş | amaç (mevcut durum sınıflandırması), uyarı, "Başla", "EKG ile AF analizi" |
| Veri girişi | bölümlü tek sayfa: Temel bilgiler → Ölçümler → Öykü ve ilaçlar → Laboratuvar (isteğe bağlı) → Klinik değerlendirme (isteğe bağlı, CAD); birim seçici; alan altında sunucu doğrulama hatası; koşullu sorular; sentetik örnek profiller |
| Canlı yönlendirme paneli | `POST /eligibility` (model çalıştırmaz): her model için Çalışabilir / Eksik: … / Kapsam dışı: … / Karar verilemez, modül etiketi, hedefi tanımlayan girdi uyarıları |
| Sonuçlar | `POST /predict`: model kartları (karar, ABSTAIN nedeni, kanıt düzeyi rozetleri, P/R/FPR/AUC ve %95 GA, hedef tanımı, sınırlılıklar); ana modüller üstte, deneyseller ayrı ve gri |
| EKG ile AF | `.hea` + `.dat`/`.mat` sürükle-bırak, ilerleme, sonuç kartı, 10 öznitelik tablosu, lead II grafiği + R tepeleri, RR takogramı; "yalnız ilk 10 sn" bilgisi |
| Model kartları | `/models` |
| Hakkında | yöntem özeti, kanıta duyarlı yönlendirme, model başına veri kaynakları (registry'den) |

## Testler

```powershell
npm run typecheck
npm test                                    # Vitest + React Testing Library (jsdom; backend gerekmez)
npm run build; npx playwright test --grep-invert "@screenshots|@timing"   # uçtan uca; backend 127.0.0.1:8000'de çalışmalı
npx playwright test e2e/screenshots.spec.ts # ekran görüntüleri -> phase_xlv/screenshots
```

Vitest fixture'ları (`src/test/fixtures/*.json`) backend'in sentetik girdilerle verdiği yanıtlardır. Playwright
senaryo grupları: `@normal`, `@eksik`, `@birim`, `@kapsam` (fibrozis ve AF), `@gizlilik`. Raporlar
`phase_xlv/results/` altına yazılır. Sonuçlar: `phase_xlv/02_tests.md`.

## Demo verisi

- **Örnek profiller** (`src/demo/profiles.ts`): elle üretilmiş **sentetik** profiller — fibrozis için çalışabilir, eksik
  alanlı, kapsam dışı (gebe), birim hatalı. Gerçek kişi verisi değildir.
- **Örnek EKG** (`public/samples/`): PTB-XL 1.0.3'ten iki açık kayıt, Phase XXVIII parity (tolerans) kümesinden bayt
  düzeyinde kopya (PhysioNet SHA256SUMS ile doğrulanmış; `phase_xxviii/results/ptbxl_download_manifest.json`):

  | dosya | SHA256 | kayıt etiketi | parity kümesindeki rol |
  |---|---|---|---|
  | `00691_hr.hea` | `6afc10ce…a9f1f75` | AF | fit (geliştirme) |
  | `00691_hr.dat` | `de2745c6…d1809ea9` | | |
  | `00165_hr.hea` | `79c760fb…f0bae477` | SR | validation (geliştirme) |
  | `00165_hr.dat` | `448d01db…f510d229` | | |

  Bu kayıtlar modelin geliştirme verisindendir (test kaydı değildir); üzerlerindeki karar performans kanıtı değildir.
  Arayüzde bu örneklerle gönderilen yaş/cinsiyet sentetiktir (60, erkek).

  **Lisans ve atıf.** PTB-XL 1.0.3, PhysioNet'te *Creative Commons Attribution 4.0 International Public License*
  (CC BY 4.0) ile yayımlanır (<https://physionet.org/content/ptb-xl/1.0.3/>; sayfa 2026-11-19'da kontrol edildi).
  Sayfanın istediği atıflar:
  - Wagner, P., Strodthoff, N., Bousseljot, R., Samek, W., & Schaeffter, T. (2022). PTB-XL, a large publicly available
    electrocardiography dataset (version 1.0.3). *PhysioNet*. RRID:SCR_007345. https://doi.org/10.13026/kfzx-aw45
  - Wagner, P., Strodthoff, N., Bousseljot, R.-D., Kreiseler, D., Lunze, F.I., Samek, W., Schaeffter, T. (2020),
    PTB-XL: A Large Publicly Available ECG Dataset. *Scientific Data*. https://doi.org/10.1038/s41597-020-0495-6
  - PhysioNet standart atfı: Pollard, T., Moody, B. E., Lehman, L., Gow, B., Fernandes, C., Xie, C., Johnson, A.,
    Mark, R. G., & Heldt, T. (2026). PhysioNet as a global platform for biomedical research. *Nature Health*.
    https://doi.org/10.1038/s44360-026-00096-z

  Kopyalarda değişiklik yapılmadı (bayt düzeyinde aynı; `app/backend/tests/test_phase45_ui_support.py` denetler).

## Kurallar (CLAUDE.md — Uygulama)

- Arayüz hiçbir test/mühürlü veri dosyasını okumaz; yalnız backend API'sini, sentetik profilleri ve iki açık örnek EKG
  kaydını kullanır.
- Model olasılığı arayüzde gösterilmez; yalnız "araştırma sınıflaması" (eşik üstü/altı), kanıt düzeyi ve sınırlılıklar.
