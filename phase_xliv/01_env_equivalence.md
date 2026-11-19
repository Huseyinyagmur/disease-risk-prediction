# Phase XLIV — Görev 1: tek app venv'i ve eşdeğerlik testi

## Ortam

- Konum: `app/backend/.venv` (Python 3.13.3, `include-system-site-packages = false`, yalıtılmış).
- Doğrudan bağımlılıklar `app/backend/requirements.in`; tam liste `app/backend/requirements.lock` (`pip freeze`).
- Model paketleri Focused venv (`Focused_Current_Disease_Improvement_2026/.venv`) ile aynı sürümdedir:

| paket | app venv | Focused venv | kök .venv |
|---|---|---|---|
| numpy | 2.2.6 | 2.2.6 | 2.2.6 |
| pandas | 2.3.1 | 2.3.1 | 2.3.1 |
| scipy | 1.16.3 | 1.16.3 | 1.16.3 |
| scikit-learn | 1.8.0 | 1.8.0 | 1.8.0 |
| imbalanced-learn | 0.14.2 | 0.14.2 | 0.14.2 |
| joblib | 1.5.3 | 1.5.3 | 1.5.3 |
| lightgbm | **4.7.0** | 4.7.0 | **4.6.0** |
| xgboost | 3.4.1 | 3.4.1 | yok |
| catboost | 1.2.10 | 1.2.10 | yok |
| pytz / tzdata | 2025.2 / 2025.2 | 2025.2 / 2025.2 | — |

Sunucu ek olarak fastapi 0.128.0, starlette 0.50.0, uvicorn 0.40.0, pydantic 2.12.5, python-multipart 0.0.21
(Focused venv sürümleri) ve kilitli AF pipeline'ının vendored wfdb 4.3.1 bağımlılıklarını (fsspec, python-dateutil,
requests) içerir. Test için pytest 8.4.1, httpx 0.28.1, pyreadstat 1.3.8. Bazı dolaylı paketler (anyio 4.16.0, certifi,
pillow vb.) PyPI'nin çözdüğü sürümlerdedir ve Focused venv'den farklıdır; model hesaplamasına girmezler.

## Eşdeğerlik testi

Betik: `scripts/t1_env_equivalence.py` (log: `logs/t1_env_equivalence.log`, sonuç: `results/env_equivalence.json`).

- Her registry modeli için 200 **sentetik** girdi (seed 20261119 + model sırası): sayısal feature'lar registry
  `allowed_range` içinde düzgün dağılımlı, kategorikler `allowed_values` içinden; osteo `age_last_period` için %25
  yapısal boşluk (eğitimdeki imputer yolu da sınansın diye). Girdiler `results/env_equiv_inputs/*.json`.
- Aynı girdi, modelin **registry'de kayıtlı venv'inde** ve **app venv'inde** iki ayrı süreçte (`-B -I`), app'in kendi
  yükleyicisiyle (`healthrisk_api.model_loader.load_model`; sürüm uyuşmazlığı uyarısı hata sayılır) yüklenip
  `predict_proba[:,1]` hesaplandı. Ham olasılıklar yalnız geçici klasörde tutuldu, faz klasörüne yazılmadı.
- Ölçüt: tüm satırlarda |Δ| ≤ 1e-9.

| model | kayıtlı venv | lightgbm (kayıtlı → app) | 200 satırda bit düzeyinde eşit | max \|Δ\| | sonuç |
|---|---|---|---|---|---|
| cad_DEVICE | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| dm_A | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| dm_B | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| anemia_LR16 | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| osteo_final | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| ckd_A (LightGBM) | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| ckd_B (LightGBM) | kök .venv | 4.6.0 → 4.7.0 | 200 | 0 | EŞDEĞER |
| af_S4_DEVICE | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |
| mi_model | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |
| copd_S4_DEVICE | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |
| hf_S2_BASIC_LAB | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |
| htn_M1 | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |
| fibrosis_final | Focused | 4.7.0 → 4.7.0 | 200 | 0 | EŞDEĞER (ek kontrol) |

Her iki süreçte model dosyası SHA256'sı registry ile aynıydı. app venv'inde yükleme sırasında uyarı çıkmadı.

## Karar

Kök `.venv`'e kayıtlı 7 modelin tamamı (LightGBM 4.6.0 ile fit edilmiş KBH A/B dahil) app venv'inde bit düzeyinde aynı
sonucu verdi. **Ayrı süreç/venv gerekmedi**; tüm modeller app venv'inde tek süreçte çalışır
(`app/backend/config/app_config.json > runtime.mode = in_process_app_venv`). Bu eşdeğerlik yalnız bu paket sürümlerinde
gösterildi: sunucu başlangıçta kurulu sürümleri `expected_packages` ile karşılaştırır, fark varsa tüm modelleri devre
dışı bırakır (test: `tests/test_integrity.py::test_package_version_mismatch_disables_all`).

## Sınırlılıklar

- Sentetik girdi gerçek dağılımı değil, registry aralıklarını kapsar. Gerçek kişilerle çalışma yolu Görev 3 parity
  testinde ayrıca denetlendi (`03_tests.md`).
- Eşdeğerlik bu makinede (Windows 11, aynı CPU) gösterildi. Başka işletim sistemi veya CPU'da tekrar edilmedi.
