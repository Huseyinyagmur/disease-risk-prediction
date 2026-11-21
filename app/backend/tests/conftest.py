import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
BACKEND = Path(__file__).resolve().parents[1]
for p in (BACKEND, BACKEND / 'tests'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


V2 = BACKEND.parents[1]

# Phase XLVI kapanış: GitHub deposunda olmayan araştırma ağacı dosyaları (geliştirme verisi, AF kilidi/pipeline/Octave,
# phase_xxviii/xxxiii EKG kayıtları). Bu dosyaları gerektiren testler `requires_research_tree(*yollar)` ile işaretlenir;
# yollardan biri yoksa test açık gerekçeyle SKIP olur (temiz klonda 0 hata). Tam ağaçta hepsi çalışır.
AF_ENV = ('phase_xxviii/config/af_pipeline_lock.json', 'phase_xxviii/config/af_pipeline_lock.sha256',
          'phase_xxviii/pipeline/af_pipeline_v1.py',
          'Clinical_Optimization_Phase25/runtime/octave/octave-10.3.0-w64/mingw64/bin/octave-cli.exe',
          'Clinical_Optimization_Phase25/src/ecg_extraction/native_source')


def research_tree_missing(*paths):
    return [p for p in paths if not (V2 / p).exists()]


def research_tree_skip_reason(missing):
    return ('araştırma ağacı gerekli (GitHub deposunda yok; app/docs/INSTALL.md §5): bulunamadı: ' + ', '.join(missing))


def skip_module_without(*paths):
    """Modül düzeyinde veri okuyan test dosyaları için: toplama (collection) hatası yerine SKIP."""
    miss = research_tree_missing(*paths)
    if miss:
        pytest.skip(research_tree_skip_reason(miss), allow_module_level=True)


def pytest_runtest_setup(item):
    for m in item.iter_markers('requires_research_tree'):
        miss = research_tree_missing(*m.args)
        if miss:
            pytest.skip(research_tree_skip_reason(miss))


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: Octave/ECGDeli çalıştıran uçtan uca testler (≈ 15–30 sn/kayıt)')
    config.addinivalue_line('markers', 'requires_research_tree(*paths): V2 köküne göre bu yollar yoksa SKIP (temiz klon)')
    for m, d in (('scenario_normal', 'Senaryo 1: normal (eksiksiz, kapsam içi) girdi'),
                 ('scenario_missing', 'Senaryo 2: eksik girdi'),
                 ('scenario_unit', 'Senaryo 3: birim hatası'),
                 ('scenario_out_of_scope', 'Senaryo 4: kapsam dışı veri')):
        config.addinivalue_line('markers', f'{m}: {d}')


@pytest.fixture(scope='session')
def service():
    from healthrisk_api.service import Service
    return Service()


@pytest.fixture(scope='session')
def client(service):
    from fastapi.testclient import TestClient
    from healthrisk_api import main
    main._SERVICE = service
    return TestClient(main.app)


def base_person(**over):
    """Sentetik, sınırlar içinde, tüm form alanları dolu bir kişi (gerçek kişi değildir)."""
    f = dict(age_years=55, sex='female', pregnant=False, race_ethnicity='nh_white', height_cm=165, weight_kg=72,
             waist_cm=90, sbp_1_mmhg=128, dbp_1_mmhg=80, sbp_2_mmhg=126, dbp_2_mmhg=78, sbp_3_mmhg=124, dbp_3_mmhg=79,
             smoking_status='never', alcohol_drinks_per_day=0.2, told_hypertension=False, told_diabetes=False,
             family_hx_diabetes=False, gestational_diabetes_hx=False, recreational_activity=True,
             hx_coronary_disease=False, hx_heart_failure=False, hx_stroke=False, told_weak_failing_kidneys=False,
             glucocorticoid_ge1month=False, fracture_hip=False, fracture_wrist=False, fracture_spine=False,
             fracture_after_age20=False, parent_hip_fracture=False, menses_absent_12m=True, age_last_period_years=50,
             hrt_ever=False)
    f.update(over)
    return {k: v for k, v in f.items() if v is not None}


LABS = dict(total_chol_mgdl=190, hdl_mgdl=55, tg_mgdl=120, alt_ul=22, ast_ul=24, ggt_ul=25, alp_ul=70, albumin_gdl=4.3,
            platelets_k_ul=250, uric_acid_mgdl=5.0, glucose_serum_mgdl=95, creatinine_mgdl=0.8,
            urine_albumin_mgl=8.0, urine_creatinine_mgdl=110, wbc_k_ul=6.5, rbc_m_ul=4.6, mcv_fl=90, rdw_pct=13.0)
