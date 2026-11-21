# Kurulum kılavuzu (Windows)

Araştırma prototipi; klinik karar aracı değildir. Bu kılavuz Phase XLVI'da yazıldı. Her adımın yanında doğrulama durumu
vardır: **[temiz klonda doğrulandı]**, **[bu makinede doğrulandı]** veya **[doğrulanmadı]**. Temiz klon sonucu:
`phase_xlvi/results/clean_clone46.json` (kapanış düzeltmesi sonrası: `phase_xlvi/results/clean_clone46b.json`) ve `phase_xlvi/PHASE_XLVI_REPORT.md`.

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
çalışır. Canlı panelde AF satırı form doluyken **"Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok"** gösterir; kişiye
özel neden varsa (ör. yaş 95, boş form) ana satır o nedendir ve altında **"Ayrıca: Octave/ECGDeli AF çalışma ortamı yok"**
yazar (Phase XLVI kapanış) [temiz klonda doğrulandı].

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
| GNU Octave 10.3.0 (Windows, taşınabilir 7z) | `Clinical_Optimization_Phase25/runtime/octave/octave-10.3.0-w64/mingw64/bin/octave-cli.exe` | exe SHA256 `14891b76…f446a2df`; paketler signal 1.4.6, statistics 1.7.5, image 2.18.1 |
| ECGDeli v1.1 kaynak dosyaları (26 `.m`, değiştirilmemiş) | `Clinical_Optimization_Phase25/src/ecg_extraction/native_source/` | ağaç SHA256 `cfa133de…a94c28b`; arşiv SHA256 `5da77e68…ee2d9ad` |
| uyumluluk `.m` dosyaları (9) | `Clinical_Optimization_Phase25/src/ecg_extraction/compat/`, `Strong_Model_External_Validation_Phase26/src/ecg/compat/` | dosya başına SHA256 kilitte |
| vendored WFDB 4.3.1 | `Clinical_Optimization_Phase25/src/ecg_extraction/vendor/` | sürüm kilitte |
| "ilk 10 sn" ön adımının kaynak doğrulaması | `phase_xxix/scripts/t3_extract.py`, `phase_xxxiii/scripts/t3_extract.py` | dosya ve fonksiyon SHA256'sı `app/backend/healthrisk_api/ecg_window.py` içinde |

### 4.1 Kilitli sürümler ve indirme kaynakları (proje kayıtlarından)

| bileşen | kilitli sürüm | projede kullanılan kaynak | arşiv SHA256 (proje kaydı) |
|---|---|---|---|
| GNU Octave (Windows 64 bit, taşınabilir 7z) | **10.3.0**; paketler signal 1.4.6, statistics 1.7.5, image 2.18.1 (Windows 7z paketine dahil; ayrı `pkg install` yapılmadı) | `https://mirrors.nic.funet.fi/pub/gnu/gnu/octave/windows/octave-10.3.0-w64.7z` (GNU aynası; resmî: `https://ftp.gnu.org/gnu/octave/windows/octave-10.3.0-w64.7z`) — `Clinical_Optimization_Phase25/data/metadata/octave_complete_download.json` | `4595b055c73de090839f5b86f289b0ac22b69549676b3452252306fffdc37ac6` (469.597.755 bayt) |
| ECGDeli (KIT-IBT, GPL-3.0) | **v1.1** etiketi = commit **`3c13b1b2ff55152360f3cee992c1d1d66099aa14`** (yayın 2022-10-12) | `https://api.github.com/repos/KIT-IBT/ECGdeli/zipball/v1.1` — `Clinical_Model_Improvement_Phase24/af_source_download.json` | `5da77e68f3170f20ff4f94ef63b069e3aa11b86faddeaf1b093d9c487ee2d9ad` (= kilit `ecgdeli.archive_sha256`) |

Doğrulama durumu (Phase XLVI kapanış, 2026-11-21): ECGDeli zipball adresi bugün de kilitteki arşiv SHA256'sını verdi;
arşiv yorumu ve `git rev-parse v1.1` commit'i `3c13b1b…` olarak doğruladı; zipball'dan çıkarılan ve `git checkout v1.1`
ile alınan `.m` dosyaları kilitteki ağaç SHA256'sını (`cfa133de…`, 26 dosya) verdi **[doğrulandı]**. Octave arşivi bu
fazda yeniden indirilmedi; projedeki kopyanın SHA256'sı yukarıdaki kayıtla aynı **[bu makinede doğrulandı]**. GNU, Octave
arşivleri için SHA256 değil GPG imzası (`.sig`) yayımlar; resmî imza denetimi proje kayıtlarında BULUNAMADI.
`https://github.com/KIT-IBT/ECGdeli/archive/refs/tags/v1.1.zip` adresi farklı üst klasör adı nedeniyle **farklı** arşiv
SHA256'sı verir; belirleyici kontrol arşiv değil kaynak ağacı SHA256'sıdır.

Kurulum (depo kökünden, PowerShell; 7-Zip gerekir):

```powershell
# Octave 10.3.0 -> Clinical_Optimization_Phase25/runtime/octave/octave-10.3.0-w64/...
New-Item -ItemType Directory -Force Clinical_Optimization_Phase25\runtime\octave
7z x octave-10.3.0-w64.7z -oClinical_Optimization_Phase25\runtime\octave

# ECGDeli v1.1: yalnız .m dosyaları, üst klasör (KIT-IBT-ECGdeli-3c13b1b/) atılarak, DEĞİŞTİRİLMEDEN
git -c core.autocrlf=false clone https://github.com/KIT-IBT/ECGdeli.git ecgdeli_src
git -C ecgdeli_src -c core.autocrlf=false checkout 3c13b1b2ff55152360f3cee992c1d1d66099aa14
robocopy ecgdeli_src Clinical_Optimization_Phase25\src\ecg_extraction\native_source *.m /S /XD .git
```

`core.autocrlf=false` önemlidir: satır sonu dönüşümü `.m` SHA256'larını değiştirir ve AF devre dışı kalır.

### 4.2 Kurulumdan sonra SHA eşleştirmesi (betik)

```powershell
app\backend\.venv\Scripts\python.exe -B phase_xlvi\scripts\verify_af_env.py
# isteğe bağlı: indirilen arşivleri de denetle
app\backend\.venv\Scripts\python.exe -B phase_xlvi\scripts\verify_af_env.py --ecgdeli-zip ECGdeli_v1.1.zip --octave-7z octave-10.3.0-w64.7z
```

Betik, sunucunun başlangıç denetimiyle aynı tanımlarla şunları `phase_xxviii/config/af_pipeline_lock.json` ile karşılaştırır
ve her satır için `OK`/`HATA` (beklenen/bulunan SHA) yazar: kilit dosyası ↔ `.sha256` sidecar, `af_pipeline_v1.py`,
`octave-cli.exe`, üç Octave paket klasörü, ECGDeli kaynak ağacı SHA256'sı (26 `.m`; `healthrisk_api.ecg_af._tree_hash`),
9 uyumluluk `.m` dosyası, vendored WFDB sürümü, "ilk 10 sn" ön adımının kaynak SHA'sı; sonda sunucunun kendi denetimini
(`AFPipeline`) çalıştırır. Çıkış kodu 0 = hepsi kilitle aynı ve AF etkin; 1 = uyuşmazlık/eksik. Dosya değiştirmez.
Tam ağaçta çıktı: `phase_xlvi/results/af_env_check.json` (21/21 OK, çıkış 0) **[bu makinede doğrulandı]**; temiz klonda
beklenen çıkış 1 (kilit yok) **[temiz klonda doğrulandı]**.

**Önemli sınır:** kilit dosyası, pipeline kodu (`phase_xxviii/`), 9 uyumluluk `.m` dosyası (Phase25/26) ve vendored WFDB
GitHub deposunda **yoktur**; yalnız tam araştırma ağacında bulunur. Octave ve ECGDeli'yi resmî kaynaktan kurmak tek başına
temiz klonda AF'yi etkinleştirmez. SHA uyuşmazsa AF bilerek çalışmaz (donmuş pipeline dışı öznitelik üretilmez).

- Doğrulama: `GET /health` → `af_pipeline.enabled = true`; panelde AF satırı "Eksik: EKG kaydı"; arayüzde "EKG ile AF
  analizi" → `app/frontend/public/samples/00691_hr.hea` + `.dat` (PTB-XL, AF). Süre makine yüküne bağlı ≈ 7–30 sn.

## 4b. Açıklama asistanı (Phase XLVIII, isteğe bağlı) [bu makinede doğrulandı]

Ollama'yı kurun (0.40.16 ile denendi; yalnız `127.0.0.1:11434`), sonra `ollama pull gemma3:4b` ve `ollama pull bge-m3`
(≈ 4,6 GB). Digest'ler `app/backend/assistant/assistant_lock.json` ile aynı olmalıdır; değilse veya Ollama çalışmıyorsa
yalnız asistan devre dışı kalır (`GET /health > assistant.reason`), uygulamanın geri kalanı etkilenmez. Bilgi tabanı ve
indeks depodadır; yeniden üretim ve atıf: `app/backend/assistant/README.md`; kullanım: [assistant.md](assistant.md).

## 5. Testler

| paket | komut | gereksinim | durum |
|---|---|---|---|
| Backend (hızlı) | `cd app\backend; .venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests -m "not slow"` | yok; araştırma ağacı gerektiren testler `requires_research_tree` ile işaretli ve dosya yoksa gerekçeli SKIP | **GitHub klonunda: 271 geçti, 31 SKIP, 0 başarısız, 0 hata** (2 `slow` seçilmedi) [temiz klonda doğrulandı, Phase XLVI kapanış; `phase_xlvi/results/clean_clone46b.json`]. SKIP gerekçesi eksik yolları listeler: geliştirme verisi (parity), AF kilidi/pipeline/Octave, phase_xxviii/xxxiii EKG kayıtları. Tam ağaçta tüm testler çalışır [bu makinede doğrulandı] |
| Backend (tam, AF uçtan uca) | `… -m pytest -p no:cacheprovider tests` | tam araştırma ağacı + §4 AF ortamı | 320 geçti, 5 xfail (belgelenmiş BMI/osteo sınırlılığı), 0 başarısız [bu makinede doğrulandı, Phase XLVI kapanış] |
| Vitest | `cd app\frontend; npm test` | yok (backend gerekmez) | 38/38 [temiz klonda doğrulandı, Phase XLVI kapanış] |
| Tip denetimi | `npm run typecheck` | yok | [temiz klonda doğrulandı] |
| Playwright | `npx playwright install chromium; npm run build; $env:PW_OUT="<çıktı klasörü>"; npx playwright test --grep-invert "@screenshots\|@timing"` | backend 127.0.0.1:8000'de çalışıyor; AF testleri için §4 | 20/20 [bu makinede doğrulandı, Phase XLVI kapanış; `phase_xlvi/results/playwright_closure/`] |

Yalnız depodaki dosyalarla çalışan testler için: `-m "not slow and not requires_research_tree"`.

`PW_OUT` verilmezse Playwright raporları `phase_xlviii/results/playwright` altına yazılır (Phase XLVIII; ekran görüntüsü, axe ve
zamanlama çıktılarının varsayılanları da `phase_xlviii/`); proje kuralı gereği her fazda kendi klasörünü verin.

Asistan testleri (Phase XLVIII): backend `tests/test_phase48_assistant.py` (Ollama gerektirmeyenler sahte Ollama ile; gerçek
Ollama testi `ollama` işaretli, yoksa SKIP), Vitest `src/components/AssistantPanel.test.tsx`, Playwright `e2e/assistant.spec.ts`
(asistan devre dışıysa gerekçeli SKIP).

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
