"""Sabit yollar. Uygulama V2 kökündeki dosyaları yalnız OKUR."""
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]          # app/backend
V2 = BACKEND.parents[1]                                 # HealthRisk_AI_Research_V2
REGISTRY_DIR = V2 / 'phase_xliii' / 'registry'
MODELS_JSON = REGISTRY_DIR / 'models.json'
SCHEMA_V1_JSON = REGISTRY_DIR / 'input_schema.json'
# Şema v2 (Phase XLIV kullanıcı kararları; v1 salt okunur kalır). Modeller yine yalnız models.json'dan yüklenir.
SCHEMA_JSON = V2 / 'phase_xliv' / 'registry' / 'input_schema_v2.json'
APP_CONFIG = BACKEND / 'config' / 'app_config.json'
AF_LOCK = V2 / 'phase_xxviii' / 'config' / 'af_pipeline_lock.json'
AF_LOCK_SHA = V2 / 'phase_xxviii' / 'config' / 'af_pipeline_lock.sha256'
AF_PIPELINE = V2 / 'phase_xxviii' / 'pipeline' / 'af_pipeline_v1.py'
