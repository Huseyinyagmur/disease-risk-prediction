"""HealthRisk AI Research V2 — Phase XLIV FastAPI tahmin sunucusu (yalnız localhost, araştırma amaçlı).

Modeller yalnız phase_xliii/registry/models.json üzerinden yüklenir. Model olasılığı hiçbir yanıtta dönülmez
(clinical_probability_eligibility=false); yalnız donmuş eşiğe göre "araştırma sınıflaması" verilir.
"""
import sys

sys.dont_write_bytecode = True          # önceki faz src/ klasörlerine __pycache__ yazılmasın (salt okunur)

__version__ = '0.1.0'
APP_PHASE = 'XLIV'
