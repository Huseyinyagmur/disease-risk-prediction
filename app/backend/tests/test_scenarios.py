"""Danışman isteği 7d: testler dört senaryo grubunda ayrı raporlanır (pytest -m scenario_*). Tüm kişiler sentetiktir.
Her yanıtta sabit araştırma uyarısı ve modül etiketi de kontrol edilir."""
import pytest

from conftest import LABS, base_person

# Phase XLV: tek kaynak backend (app_config.json > disclaimer_tr); metin kullanıcı kararıyla güncellendi
DISCLAIMER = ('Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir; negatif sonuç '
              'hastalığı dışlamaz; tanı ve tedavi için hekime başvurun.')
LABELS = {'af_S4_DEVICE': 'ana modül', 'fibrosis_final': 'ana modül', 'osteo_final': 'araştırma modülü'}
FULL_LABS = dict(LABS, hba1c_pct=5.3, hemoglobin_gdl=13.5)
MALE_DROP = dict(pregnant=None, gestational_diabetes_hx=None, menses_absent_12m=None, age_last_period_years=None, hrt_ever=None)


def post(client, fields, code=200):
    r = client.post('/predict', json={'fields': fields})
    assert r.status_code == code, r.text
    body = r.json()
    assert body['disclaimer'] == DISCLAIMER
    return body


def by_model(body):
    out = {}
    for r in body['results']:
        out[r['model_id']] = r
        assert r['module_label'] == LABELS.get(r['model_id'], 'deneysel')
        if r.get('fallback_from'):
            out[r['fallback_from']['model_id']] = dict(r['fallback_from'], via_fallback=True)
    return out


# =========================================================== 1. normal girdi
N = pytest.mark.scenario_normal


@N
def test_normal_form_only_woman(client):
    res = by_model(post(client, base_person()))
    for m in ('dm_A', 'osteo_final', 'ckd_A'):
        assert res[m]['status'] == 'OK' and res[m]['decision']['research_class'] in ('ESIK_USTU', 'ESIK_ALTI')


@N
def test_normal_full_labs_woman_b_models(client):
    res = by_model(post(client, base_person(**FULL_LABS)))
    for m in ('dm_B', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_B'):
        assert res[m]['status'] == 'OK', (m, res[m]['reasons'])


@N
def test_normal_man_with_labs(client):
    res = by_model(post(client, base_person(sex='male', age_years=62, **MALE_DROP, **FULL_LABS)))
    for m in ('dm_B', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_B'):
        assert res[m]['status'] == 'OK', (m, res[m]['reasons'])


@N
def test_normal_young_woman_anemia(client):
    f = base_person(age_years=30, menses_absent_12m=False, age_last_period_years=None, **FULL_LABS)
    assert by_model(post(client, f))['anemia_LR16']['status'] == 'OK'


@N
def test_normal_cad_clinical(client):
    f = dict(age_years=58, sex='male', cad_chest_pain_type='atypical_angina', sbp_1_mmhg=135, total_chol_mgdl=210,
             glucose_fasting_mgdl=95, cad_resting_ecg='normal', cad_max_hr_bpm=160, cad_exercise_angina=False,
             cad_st_depression_mm=0.5, cad_st_slope='upsloping')
    assert by_model(post(client, f))['cad_DEVICE']['status'] == 'OK'


@N
def test_normal_copd_obstructed(client):
    f = dict(age_years=66, sex='female', height_cm=160, weight_kg=60, smoking_status='former', fev1_pre_ml=1400, fvc_pre_ml=2400)
    assert by_model(post(client, f))['copd_S4_DEVICE']['status'] == 'OK'


@N
def test_normal_meds_answered_no(client):
    res = by_model(post(client, base_person(on_insulin=False, on_diabetes_pills=False)))
    assert res['dm_A']['status'] == 'OK' and res['ckd_A']['status'] == 'OK'


@N
def test_normal_ckd_meds_training_definition(service):
    """Karar 3: tanısız ama hap kullanan kişide KBH dm_pills = 1 (eğitim tanımı); dm_A ise popülasyon dışı (tutarlı)."""
    from healthrisk_api.validation import validate_fields
    F, _ = validate_fields(base_person(on_diabetes_pills=True), service.schema, {}, service.conversions)
    fr = service.feature_vector('ckd_A', F)
    assert fr.values['dm_pills'] == 1.0 and fr.values['dm_told'] == 0.0
    assert service.predict_model('dm_A', F)['status'] == 'NOT_APPLICABLE'
    assert service.predict_model('ckd_A', F)['status'] == 'OK'


# =========================================================== 2. eksik girdi
M = pytest.mark.scenario_missing


@M
def test_missing_waist(client):
    res = by_model(post(client, {k: v for k, v in base_person().items() if k != 'waist_cm'}))
    assert res['dm_A']['status'] == 'ABSTAIN' and 'waist_cm' in res['dm_A']['missing_fields']


@M
def test_missing_race_five_models(client):
    f = base_person(**FULL_LABS)
    del f['race_ethnicity']
    res = by_model(post(client, f))
    abst = {m for m, r in res.items() if r['status'] == 'ABSTAIN' and 'race_ethnicity' in r.get('missing_fields', [])}
    assert abst == {'dm_A', 'dm_B', 'ckd_A', 'ckd_B', 'htn_M1'}


@M
@pytest.mark.parametrize('preg', [None, 'unknown'])
def test_missing_or_unknown_pregnancy(client, preg):
    f = base_person(**FULL_LABS)
    f.pop('pregnant')
    if preg is not None:
        f['pregnant'] = preg
    res = by_model(post(client, f))
    for m in ('dm_A', 'ckd_A', 'htn_M1', 'fibrosis_final'):
        assert res[m]['status'] == 'ABSTAIN' and any('gebelik' in x for x in res[m]['reasons']), m
    assert res['osteo_final']['status'] == 'OK'


@M
def test_missing_pregnancy_irrelevant_for_men(client):
    res = by_model(post(client, base_person(sex='male', **MALE_DROP)))
    assert res['dm_A']['status'] == 'OK' and res['ckd_A']['status'] == 'OK'


@M
def test_missing_partial_labs_fallback(client):
    body = post(client, base_person(total_chol_mgdl=190, hdl_mgdl=55))
    dm = next(r for r in body['results'] if r['disease_key'] == 'diabetes')
    assert dm['model_id'] == 'dm_A' and 'tg_mgdl' in dm['fallback_from']['missing_fields']


@M
def test_missing_ckd_pills_when_diagnosed(client):
    res = by_model(post(client, base_person(told_diabetes=True, on_insulin=False)))
    assert res['ckd_A']['status'] == 'ABSTAIN' and 'on_diabetes_pills' in res['ckd_A']['missing_fields']


@M
def test_missing_kidney_question(client):
    assert by_model(post(client, base_person(told_weak_failing_kidneys=None)))['ckd_A']['status'] == 'ABSTAIN'


@M
def test_missing_age_last_period(client):
    res = by_model(post(client, base_person(age_last_period_years=None)))
    assert res['osteo_final']['status'] == 'ABSTAIN' and 'age_last_period_years' in res['osteo_final']['missing_fields']


@M
def test_missing_everything(client):
    body = post(client, {})
    assert all(r['status'] in ('ABSTAIN', 'NOT_APPLICABLE') for r in body['results'])


# =========================================================== 3. birim hatası
U = pytest.mark.scenario_unit


@U
@pytest.mark.parametrize('over', [
    dict(glucose_fasting_mgdl=5.4),                                  # mmol/L değeri birimsiz
    dict(creatinine_mgdl=70),                                        # µmol/L değeri birimsiz
    dict(height_cm=1.65),                                            # metre
    dict(fev1_pre_ml=2.5, fvc_pre_ml=3.5),                           # litre
    dict(weight_kg={'value': 72, 'unit': 'stone'}),                  # desteklenmeyen birim
    dict(glucose_serum_mgdl={'value': 5.4, 'unit': 'mg/mL'}),
    dict(sex={'value': 'female', 'unit': 'kg'}),                     # kategoriye birim
    dict(hba1c_pct={'value': 200, 'unit': 'mmol/mol (IFCC)'}),       # dönüşüm sonrası > 18 %
], ids=['glukoz_mmol_birimsiz', 'kreatinin_umol_birimsiz', 'boy_metre', 'spirometri_litre', 'stone',
        'mg_mL', 'kategoriye_birim', 'ifcc_aralik_disi'])
def test_unit_errors_422(client, over):
    assert post(client, base_person(**over), code=422)['detail']


@U
def test_unit_conversion_equivalence(client):
    a = by_model(post(client, base_person(weight_kg=72, height_cm=165, **FULL_LABS)))
    labs_b = dict(FULL_LABS, total_chol_mgdl={'value': 190 / 38.67, 'unit': 'mmol/L'},
                  hba1c_pct={'value': (5.3 - 2.152) / 0.09148, 'unit': 'mmol/mol (IFCC)'})
    b = by_model(post(client, base_person(weight_kg={'value': 72 / 0.45359237, 'unit': 'lb'},
                                          height_cm={'value': 165 / 2.54, 'unit': 'inç'}, **labs_b)))
    for m in ('dm_B', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_B'):
        assert a[m]['status'] == b[m]['status'] == 'OK' and a[m]['decision'] == b[m]['decision'], m


@U
def test_unit_notes_reported(client):
    body = post(client, base_person(creatinine_mgdl={'value': 70, 'unit': 'µmol/L'}))
    assert any('creatinine_mgdl' in n for n in body['unit_conversion_notes'])


# =========================================================== 4. kapsam dışı veri
O = pytest.mark.scenario_out_of_scope


@O
@pytest.mark.parametrize('over,model', [
    (dict(age_years=45), 'osteo_final'), (dict(age_years=50), 'anemia_LR16'),
    (dict(sex='male', age_years=70, **MALE_DROP), 'anemia_LR16'),
    (dict(pregnant=True), 'dm_A'), (dict(pregnant=True), 'ckd_A'),
    (dict(told_diabetes=True, on_insulin=True, on_diabetes_pills=False), 'dm_A'),
    (dict(told_diabetes=False, on_insulin=True), 'dm_A'),
    (dict(told_weak_failing_kidneys=True), 'ckd_A'), (dict(on_dialysis=True), 'ckd_A'),
], ids=['osteo_yas45', 'anemi_kadin50', 'anemi_erkek70', 'dm_gebe', 'ckd_gebe', 'dm_tanili', 'dm_tanisiz_insulin',
        'ckd_bobrek_tanisi', 'ckd_diyaliz'])
def test_out_of_population(client, over, model):
    res = by_model(post(client, base_person(**over)))
    assert res[model]['status'] == 'NOT_APPLICABLE', res[model]['reasons']


@O
def test_out_of_scope_copd(client):
    f = dict(age_years=66, sex='female', height_cm=160, weight_kg=60, smoking_status='former')
    assert by_model(post(client, dict(f, fev1_pre_ml=2000, fvc_pre_ml=2600)))['copd_S4_DEVICE']['status'] == 'NOT_APPLICABLE'
    assert by_model(post(client, dict(f, age_years=85, fev1_pre_ml=1400, fvc_pre_ml=2400)))['copd_S4_DEVICE']['status'] == 'NOT_APPLICABLE'


@O
def test_out_of_model_input_range(client):
    res = by_model(post(client, base_person(**dict(FULL_LABS, urine_albumin_mgl=10000, urine_creatinine_mgdl=5))))
    assert res['htn_M1']['status'] == 'NOT_APPLICABLE' and 'uacr_log' in res['htn_M1']['reasons'][0]


@O
def test_out_of_scope_af_age(service):
    from healthrisk_api.validation import validate_fields
    F, _ = validate_fields(dict(age_years=92, sex='male'), service.schema, {}, service.conversions)
    ecg = dict(RR_Mean_Global=800, RR_Mean_Global_iqr=30, QRS_Dur_Global=100, QRS_Dur_Global_iqr=10, PR_Int_Global=160,
               PR_Int_Global_iqr=10, P_Dur_Global=110, P_Dur_Global_iqr=10, QT_Int_Global=400, QT_Int_Global_iqr=10)
    F.update({f'ecg_af_{k}': float(v) for k, v in ecg.items()})
    assert service.predict_model('af_S4_DEVICE', F)['status'] == 'NOT_APPLICABLE'


@O
@pytest.mark.parametrize('over', [dict(age_years=150), dict(age_years=17), dict(sbp_1_mmhg=300), dict(waist_cm=10)],
                         ids=['yas150', 'yas17', 'sbp300', 'bel10'])
def test_out_of_plausible_range_422(client, over):
    post(client, base_person(**over), code=422)


@O
def test_out_of_schema_category(client):
    res = by_model(post(client, base_person(sex='diverse')))
    assert res['dm_A']['status'] == 'ABSTAIN' and res['dm_A']['unknown_categories']
