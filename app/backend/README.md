# HealthRisk AI Research V2 — tahmin sunucusu (app/backend, Phase XLIV)

Araştırma amaçlı FastAPI sunucusu. **Klinik karar aracı değildir.** Model olasılığı hiçbir uç noktada dönülmez
(`clinical_probability_eligibility=false`); her model için yalnız donmuş birincil eşiğe göre "araştırma sınıflaması"
(`ESIK_USTU` / `ESIK_ALTI`), kanıt düzeyi ve sınırlılıklar verilir. Sunucu yalnız `127.0.0.1`'e bağlanır ve loopback
dışı istemcileri 403 ile reddeder.

## Kurulum (Windows, Python 3.13.3)

```powershell
cd app\backend
C:\Users\<kullanıcı>\AppData\Local\Programs\Python\Python313\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
```

`requirements.lock` tam sürüm listesidir (sklearn 1.8.0, lightgbm 4.7.0, xgboost 3.4.1, catboost 1.2.10, numpy 2.2.6,
pandas 2.3.1, scipy 1.16.3; Focused venv ile aynı). `requirements.in` doğrudan bağımlılıklardır. Sürüm farklıysa sunucu
tüm modelleri devre dışı bırakır (`/health` → `degraded`); eşdeğerlik yalnız bu sürümlerde gösterildi
(`phase_xliv/01_env_equivalence.md`).

## Çalıştırma

```powershell
.venv\Scripts\python.exe -B run_server.py            # http://127.0.0.1:8000
.venv\Scripts\python.exe -B run_server.py --port 8765
```

Başlangıçta: registry/şema SHA256 (app_config.json), paket sürümleri, her model dosyasının SHA256'sı (yüklemeden önce),
AF pipeline kilidi (pipeline, Octave exe, ECGDeli ağacı, compat dosyaları) doğrulanır. Uyuşmazlıkta ilgili model devre
dışıdır ve `/health`'te listelenir.

## Uç noktalar

| uç nokta | açıklama |
|---|---|
| `GET /health` | durum, devre dışı modeller ve nedenleri, paket sürümleri, AF pipeline kilidi |
| `GET /models` | yalnız `app_visible` modeller: kimlik, hastalık, mod, gerekli/koşullu alanlar, kanıt özeti, sınırlılıklar |
| `GET /schema` | form tanımı (input_schema alanları + uygulama uygunluk soruları), birim dönüşümleri |
| `POST /predict` | `{"fields": {...}}` → hastalık başına sonuç (`OK` / `ABSTAIN` / `NOT_APPLICABLE`) |
| `POST /eligibility` | (Phase XLV) aynı gövde → her app_visible model için `READY` / `MISSING` / `OUT_OF_SCOPE` / `ABSTAIN`, eksik alanlar, gerekçe, hedef-tanımlayan girdi uyarıları; alan hataları 422 yerine `field_errors` listesinde. **Model çalıştırmaz** (`/predict` ile ortak `Service.precheck`) |
| `POST /ecg/af` | multipart: `header_file` (.hea), `signal_file` (.dat/.mat), `age_years`, `sex` → kilitli AF-ECGDELI-OCTAVE-v1 → af_S4_DEVICE (60 sn zaman aşımı) |

Alan değeri doğrudan (`"age_years": 55`) veya birimle (`"glucose_fasting_mgdl": {"value": 5.6, "unit": "mmol/L"}`)
verilir. Bilinmeyen alan, sayısal olmayan değer, desteklenmeyen birim, makul aralık dışı değer, tutarsız tansiyon/
spirometri → **422**. Şemada olmayan kategori 422 değildir: o alanı kullanan model **ABSTAIN** eder.

Ayrıntılı örnekler: `phase_xliv/02_api.md`.

Phase XLV ekleri (arayüz için; model/eşik/registry değişmedi): `/schema` alanlarında `form_section`,
`ask_when_rule` / `required_when_rule` (şema metninden sunucuda ayrıştırılmış koşul listesi) ve `form` (bölümler,
Türkçe kategori etiketleri; `app_config.json > form`). `/ecg/af` sonucunda `display`: lead II (ilk 10 sn, 250 Hz'e
seyreltilmiş, filtresiz) ve kilitli `load_fpt` çıktısındaki R tepe zamanları / RR dizisi — yalnız gösterim içindir,
feature ve kararı etkilemez. Ayrıntı: `phase_xlv/01_ui_overview.md`.

## Testler

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests -m "not slow"   # ≈ 15 sn
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests                   # + AF uçtan uca (Octave, ≈ 1 dk)
```

Parity testleri yalnız geliştirme verisini okur (`tests/parity_lib.py`, mühürlü dosya yolu koruması). Sonuçlar:
`phase_xliv/03_tests.md`.

## Kurallar (CLAUDE.md — Uygulama)

- Modeller yalnız `phase_xliii/registry/models.json` üzerinden yüklenir; model, eşik, registry ve önceki faz dosyaları
  salt okunurdur (sunucu bunlara yazmaz; `sys.dont_write_bytecode=True`).
- Uygulama hiçbir test/mühürlü veri dosyasını okumaz.
- Eksik zorunlu alan tahminle doldurulmaz (ABSTAIN). Irk yanıtsızsa ırk kullanan 5 model ABSTAIN eder.
- Hedefi tanımlayan değer girilmişse (HbA1c/açlık glukozu, ölçülen tansiyon ≥140/90 veya tansiyon ilacı, hemoglobin,
  kreatinin/UACR) yanıt "doğrudan klinik eşik kullanın" uyarısı taşır.

## Güncelleme (Phase XLIV, kullanıcı kararları)

- **Şema v2:** dönüşüm tanımları `phase_xliv/registry/input_schema_v2.json` dosyasından gelir (v1 salt okunur kalır;
  modeller yine yalnız `phase_xliii/registry/models.json` üzerinden yüklenir). İlke: şema metni ile eğitim kodu
  ayrışırsa eğitim kodu kazanır. Değişiklikler ve gerekçeleri `changes_from_v1` içindedir; `/schema` ve `/models`
  bunları döndürür. Sunucu, models.json ile v2 arasındaki her dönüşüm farkının bu listede olmasını zorunlu tutar.
- **Gebelik:** kadında (≥ 18) zorunlu soru; `true` / `false` / `"unknown"`. `"unknown"` veya yanıtsız → ilgili modeller
  ABSTAIN.
- **Diyabet ilaç soruları** (`on_insulin`, `on_diabetes_pills`) herkese sorulur.
- **Her yanıt** `disclaimer` alanını taşır (hata yanıtları dahil). Her model sonucu `module_label` taşır
  (AF ve fibrozis "ana modül", osteoporoz "araştırma modülü", diğerleri "deneysel").
- **Gizlilik:** istek gövdeleri ve sağlık verileri log'a yazılmaz, diske saklanmaz. Uvicorn erişim logu kapalıdır;
  beklenmeyen hatada yalnız hata türü loglanır. `/health > request_stats` yalnız uç nokta bazında anonim sayaç ve
  süre içerir. `/ecg/af` yüklemeleri işlem süresince geçici klasörde durur ve yanıt öncesi silinir.
- **AF girdisi:** `.hea + .dat` (PTB-XL) ve `.hea + .mat` (PhysioNet Challenge) denendi. Kilitli pipeline'ın önünde
  "ilk 10 sn" ön adımı var (`healthrisk_api/ecg_window.py`; Phase XXIX/XXXIII `read_first10s` birebir kopyası, kaynak
  SHA'ları başlangıçta doğrulanır). fs ≠ 500 Hz veya kayıt 10 sn'den kısaysa ABSTAIN; uzun kayıtta ilk 10 sn kullanılır.
- Senaryo grupları: `pytest -m scenario_normal | scenario_missing | scenario_unit | scenario_out_of_scope`.
