# Kurulum kılavuzu (Windows)

Araştırma prototipi; klinik karar aracı değildir. Bu kılavuz Phase XLVI'da yazıldı. Her adımın yanında doğrulama durumu
vardır: **[temiz klonda doğrulandı]**, **[bu makinede doğrulandı]** veya **[doğrulanmadı]**. Temiz klon sonucu:
`phase_xlvi/results/clean_clone46.json` ve `phase_xlvi/PHASE_XLVI_REPORT.md`.

## 0. Gereksinimler

| bileşen | sürüm | not |
|---|---|---|
| Windows | 10/11, 64 bit | yalnız Windows'ta denendi |
| Python | **3.13.3** (64 bit) | sunucu, kurulu paket sürümleri kilitli sürümlerden farklıysa tüm modelleri devre dışı bırakır |
| Node.js / npm | 22 (denendi: 22.14.0 / npm 11.2.0) | yalnız arayüz için |
| Git | herhangi güncel sürüm | |
| GNU Octave + ECGDeli | 10.3.0 + ECGDeli v1.1 | **yalnız AF (EKG) modeli için**; depoda yoktur (§4) |

Python paketleri (`app/backend/requirements.lock`, tam sürüm): numpy 2.2.6, pandas 2.3.1, scipy 1.16.3, scikit-learn 1.8.0,
lightgbm 4.7.0, xgboost 3.4.1, catboost 1.2.10, imbalanced-learn 0.14.2, joblib 1.5.3, fastapi, uvicorn ve bağımlılıkları.

## 1. Depoyu klonla [temiz klonda doğrulandı]

```powershell
git clone https://github.com/Huseyinyagmur/disease-risk-prediction.git
cd disease-risk-prediction
```

Depo, registry'deki 13 donmuş model dosyasını registry yollarında ve SHA256'ları registry ile aynı olarak içerir
(`.gitattributes`: `.joblib`, `.dat`, `.mat`, `.png` ikili).

## 2. Backend [temiz klonda doğrulandı]

```powershell
cd app\backend
py -3.13 -m venv .venv
.venv\Scripts\python.exe --version                    # Python 3.13.3 olmalı
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -B run_server.py --port 8000 # http://127.0.0.1:8000 (yalnız localhost)
```

Kontrol (ayrı terminal):

```powershell
curl.exe http://127.0.0.1:8000/health
```

AF ortamı kurulmamış temiz klonda beklenen: `status = "degraded"`, `disabled_models = []` (uygulamada görünen 11 modelin
11'i etkin), `af_pipeline.enabled = false` ve gerekçe "Octave/ECGDeli AF çalışma ortamı yok: …". Form tabanlı tüm modeller
çalışır. Canlı panelde AF satırı **"Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok"** gösterir (Phase XLVI).

`-B` bayrağı `.pyc` yazımını kapatır (proje kuralı: salt okunur klasörlere yazılmaz).

## 3. Arayüz [temiz klonda doğrulandı: `npm ci`, `npm run build`]

```powershell
cd app\frontend
npm ci
npm run build
npm run preview          # http://127.0.0.1:4173  (geliştirme için: npm run dev → 5173)
```

Arayüz istekleri `/api` önekiyle gönderir; Vite vekili `http://127.0.0.1:8000`'e iletir. Backend başka porttaysa:
`$env:HEALTHRISK_API_PORT = "8765"; npm run preview`.

## 4. AF (EKG) için ek kurulum [bu makinede doğrulandı; temiz makinede doğrulanmadı]

AF modeli yalnız kilitli `AF-ECGDELI-OCTAVE-v1` pipeline'ıyla çalışır. Sunucu başlangıçta aşağıdakilerin hepsinin
SHA256'sını `phase_xxviii/config/af_pipeline_lock.json` ile karşılaştırır; biri bile uymazsa AF devre dışı kalır ve panel
"Karar verilemez" gösterir. Bunlar GitHub deposunda **yoktur**; tam araştırma ağacında bulunur.

| öğe | beklenen konum (depo köküne göre) | kilit |
|---|---|---|
| kilit dosyası + sidecar | `phase_xxviii/config/af_pipeline_lock.json`, `af_pipeline_lock.sha256` | kendi SHA256'sı sidecar'da |
| pipeline kodu | `phase_xxviii/pipeline/af_pipeline_v1.py` | SHA256 `2bf3c307…ede08a6` |
| GNU Octave 10.3.0 (Windows, taşınabilir) | `Clinical_Optimization_Phase25/runtime/octave/octave-10.3.0-w64/mingw64/bin/octave-cli.exe` | exe SHA256 `14891b76…f446a2df`; paketler signal 1.4.6, statistics 1.7.5, image 2.18.1 |
| ECGDeli v1.1 kaynak dosyaları (26 `.m`, değiştirilmemiş) | `Clinical_Optimization_Phase25/src/ecg_extraction/native_source/` | ağaç SHA256 `cfa133de…a94c28b`; arşiv SHA256 `5da77e68…ee2d9ad` |
| uyumluluk `.m` dosyaları (9) | `Clinical_Optimization_Phase25/src/ecg_extraction/compat/`, `Strong_Model_External_Validation_Phase26/src/ecg/compat/` | dosya başına SHA256 kilitte |
| vendored WFDB 4.3.1 | `Clinical_Optimization_Phase25/src/ecg_extraction/vendor/` | sürüm kilitte |
| "ilk 10 sn" ön adımının kaynak doğrulaması | `phase_xxix/scripts/t3_extract.py`, `phase_xxxiii/scripts/t3_extract.py` | dosya ve fonksiyon SHA256'sı `app/backend/healthrisk_api/ecg_window.py` içinde |

- Resmî kaynaklar: GNU Octave (<https://octave.org/download>), ECGDeli (<https://github.com/KIT-IBT/ECGdeli>, GPL-3.0).
  **Projede kullanılan indirme adresleri ve Octave paket kurulum komutları proje kayıtlarında BULUNAMADI.** Bu yüzden
  dosyaları başka bir kaynaktan edinen kullanıcı, kilit SHA256'larının tutup tutmadığını `/health > af_pipeline.problems`
  ile görür. SHA uyuşmazsa AF bilerek çalışmaz (donmuş pipeline dışı öznitelik üretilmez).
- Doğrulama: `GET /health` → `af_pipeline.enabled = true`; panelde AF satırı "Eksik: EKG kaydı"; arayüzde "EKG ile AF
  analizi" → `app/frontend/public/samples/00691_hr.hea` + `.dat` (PTB-XL, AF). Süre makine yüküne bağlı ≈ 7–30 sn.

## 5. Testler

| paket | komut | gereksinim | durum |
|---|---|---|---|
| Backend (hızlı) | `cd app\backend; .venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests -m "not slow"` | parity testleri geliştirme verisi ister (tam araştırma ağacı); klonda bu testler atlanır/başarısız olabilir | [bu makinede doğrulandı] |
| Backend (tam, AF uçtan uca) | `… -m pytest -p no:cacheprovider tests` | §4 AF ortamı | [bu makinede doğrulandı] |
| Vitest | `cd app\frontend; npm test` | yok (backend gerekmez) | [temiz klonda doğrulandı] |
| Tip denetimi | `npm run typecheck` | yok | [temiz klonda doğrulandı] |
| Playwright | `npx playwright install chromium; npm run build; $env:PW_OUT="<çıktı klasörü>"; npx playwright test --grep-invert "@screenshots\|@timing"` | backend 127.0.0.1:8000'de çalışıyor; AF testleri için §4 | [bu makinede doğrulandı] |

`PW_OUT` verilmezse Playwright raporları `phase_xlv/results` altına yazılır; proje kuralı gereği her fazda kendi klasörünü
verin.

## 6. Sık hatalar

| belirti | neden | çözüm |
|---|---|---|
| `/health` → `degraded`, tüm modeller devre dışı, "paket sürümleri beklenenden farklı" | farklı Python veya paket sürümü | Python 3.13.3 ile yeni venv; `pip install -r requirements.lock` |
| tek bir model devre dışı, "model dosyası SHA256 registry ile uyuşmuyor" | dosya değişmiş / Git satır sonu dönüşümü | `git checkout -- <dosya>`; `.gitattributes`'ın `*.joblib binary` kuralını koruyun |
| AF satırı "Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok" | §4 dosyaları yok (temiz klonda beklenen) | yalnız AF gerekiyorsa §4 |
| AF satırı "AF pipeline devre dışı: kilit/SHA256 doğrulaması başarısız" | Octave/ECGDeli/pipeline dosyası kilitten farklı | `/health > af_pipeline.problems` hangi dosya olduğunu söyler |
| EKG yüklemesi ABSTAIN "500 Hz değil" / "10 sn'den kısa" | kayıt biçimi | 500 Hz, 12 lead, ≥ 10 sn WFDB kaydı |
| EKG yüklemesinde 413 / 429 | dosya > 2 MB / pipeline meşgul | küçük dosya / önceki analizin bitmesini bekleyin |
| arayüz "araştırma uyarısı yüklenemedi" | backend kapalı veya yanlış port | backend'i başlatın; `HEALTHRISK_API_PORT` |
| `npm run preview` port hatası | 4173 kullanımda (`strictPort`) | diğer süreci kapatın |
| `py -3.13` bulunamadı | Python 3.13 kurulu değil | python.org'dan 3.13.3 (64 bit) |
| 403 | istek localhost dışından | yalnız 127.0.0.1 desteklenir |
