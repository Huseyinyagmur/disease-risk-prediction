"""Uç noktalar ve negatif testler (yalnız sentetik girdi)."""
import json

import pytest

from conftest import AF_ENV, LABS, base_person

RACE_MODELS = {'dm_A', 'dm_B', 'ckd_A', 'ckd_B', 'htn_M1'}
FORBIDDEN_KEYS = ('prob', 'proba', 'probability', 'score', 'risk_percent', 'olasilik', 'olasılık')


def _post(client, fields):
    return client.post('/predict', json={'fields': fields})


def _by_model(resp):
    out = {}
    for r in resp.json()['results']:
        out[r['model_id']] = r
        if r.get('fallback_from'):
            out[r['fallback_from']['model_id']] = dict(status=r['fallback_from']['status'], reasons=r['fallback_from']['reasons'],
                                                       missing_fields=r['fallback_from']['missing_fields'], via_fallback=True)
    return out


def _walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk_keys(v)


def _walk_items(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k, v
            yield from _walk_items(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk_items(v)


@pytest.mark.requires_research_tree(*AF_ENV)
def test_health(client):
    h = client.get('/health').json()
    assert h['status'] == 'ok', h
    assert h['disabled_models'] == [] and h['packages']['ok'] and h['af_pipeline']['enabled']
    assert h['clinical_probability_eligibility'] is False


def test_models_only_app_visible(client, service):
    ms = client.get('/models').json()['models']
    ids = {m['model_id'] for m in ms}
    vis = {k for k, v in service.registry['models'].items() if v['app_visible']}
    assert ids == vis and 'mi_model' not in ids and 'hf_S2_BASIC_LAB' not in ids
    for m in ms:
        assert m['fields']['required'] and m['limitations'] and m['evidence']['tiers'] is not None
        assert m['clinical_probability_eligibility'] is False


def test_schema(client):
    s = client.get('/schema').json()
    assert 'age_years' in s['fields'] and s['fields']['ecg_af_RR_Mean_Global']['form_input'] is False
    assert s['schema_version'] == '2.0' and len(s['changes_from_v1']) == 15
    assert s['fields']['pregnant']['categories'] == [True, False, 'unknown']
    assert s['fields']['pregnant']['required_when'].startswith('sex = female')
    assert 'ask_when' not in s['fields']['on_insulin'] and 'ask_when' not in s['fields']['on_diabetes_pills']
    assert ('mmol/L' in [u['from_unit'] for u in s['unit_conversions']['glucose_serum_mgdl']])


def test_full_person_ok_and_no_probability(client):
    f = base_person(**LABS, hba1c_pct=5.3, hemoglobin_gdl=13.5)
    r = _post(client, f)
    assert r.status_code == 200
    body = r.json()
    res = _by_model(r)
    for mid in ('dm_B', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_B'):
        assert res[mid]['status'] == 'OK', (mid, res[mid]['reasons'])
        assert res[mid]['decision']['research_class'] in ('ESIK_USTU', 'ESIK_ALTI')
    # olasılık hiçbir yerde dönülmez
    keys = [k.lower() for k in _walk_keys(body) if k != 'clinical_probability_eligibility']
    assert not [k for k in keys if any(b in k for b in FORBIDDEN_KEYS)], keys
    assert all(v is False for k, v in _walk_items(body) if k == 'clinical_probability_eligibility')
    for r_ in body['results']:
        if r_['decision']:
            assert set(r_['decision']) == {'research_class', 'label_tr', 'threshold', 'threshold_rule'}
            assert all(isinstance(v, str) for v in r_['decision'].values())


def test_missing_field_abstain(client):
    f = base_person()
    del f['waist_cm']
    res = _by_model(_post(client, f))
    assert res['dm_A']['status'] == 'ABSTAIN' and 'waist_cm' in res['dm_A']['missing_fields']
    assert res['ckd_A']['status'] == 'ABSTAIN' and 'waist_cm' in res['ckd_A']['missing_fields']


def test_out_of_range_422(client):
    r = _post(client, base_person(age_years=150))
    assert r.status_code == 422
    r = _post(client, base_person(weight_kg={'value': 900, 'unit': 'lb'}))
    assert r.status_code == 422


def test_unknown_category_abstain(client):
    res = _by_model(_post(client, base_person(smoking_status='sometimes')))
    for mid in ('dm_A', 'ckd_A', 'osteo_final'):
        assert res[mid]['status'] == 'ABSTAIN', mid
        assert any(u['field'] == 'smoking_status' for u in res[mid]['unknown_categories'])


def test_cad_unknown_string_category_abstain(client):
    """V2 CAD hatası biçimi ('1' yerine '1.0'): şema kategorisi değilse ABSTAIN; sessiz dönüşüm yok."""
    f = dict(age_years=58, sex='male', cad_chest_pain_type='1', sbp_1_mmhg=140, total_chol_mgdl=230,
             glucose_fasting_mgdl=100, cad_resting_ecg='normal', cad_max_hr_bpm=150, cad_exercise_angina=False,
             cad_st_depression_mm=1.0, cad_st_slope='flat')
    res = _by_model(_post(client, f))
    assert res['cad_DEVICE']['status'] == 'ABSTAIN'
    f['cad_chest_pain_type'] = 'typical_angina'
    res = _by_model(_post(client, f))
    assert res['cad_DEVICE']['status'] == 'OK'


def test_race_missing_abstains_exactly_five_models(client):
    f = base_person(**LABS, hba1c_pct=5.3, hemoglobin_gdl=13.5)
    del f['race_ethnicity']
    res = _by_model(_post(client, f))
    abst = {m for m, r in res.items() if r['status'] == 'ABSTAIN' and 'race_ethnicity' in r.get('missing_fields', [])}
    assert abst == RACE_MODELS, abst
    assert res['osteo_final']['status'] == 'OK' and res['fibrosis_final']['status'] == 'OK'


def test_b_model_falls_back_to_a_without_labs(client):
    body = _post(client, base_person()).json()
    dm = next(r for r in body['results'] if r['disease_key'] == 'diabetes')
    assert dm['model_id'] == 'dm_A' and dm['status'] == 'OK' and dm['fallback_from']['model_id'] == 'dm_B'
    ck = next(r for r in body['results'] if r['disease_key'] == 'kidney')
    assert ck['model_id'] == 'ckd_A' and ck['fallback_from']['model_id'] == 'ckd_B'


def test_b_model_used_with_labs(client):
    body = _post(client, base_person(**LABS, hba1c_pct=5.3, hemoglobin_gdl=13.5)).json()
    dm = next(r for r in body['results'] if r['disease_key'] == 'diabetes')
    ck = next(r for r in body['results'] if r['disease_key'] == 'kidney')
    assert dm['model_id'] == 'dm_B' and ck['model_id'] == 'ckd_B'


@pytest.mark.parametrize('extra,disease', [
    (dict(hba1c_pct=6.8), 'diabetes'), (dict(glucose_fasting_mgdl=130), 'diabetes'),
    (dict(sbp_1_mmhg=150, sbp_2_mmhg=148, sbp_3_mmhg=146), 'hypertension'),
    (dict(told_hypertension=True, on_bp_medication=True), 'hypertension'),
    (dict(hemoglobin_gdl=11.0), 'anemia'), (dict(creatinine_mgdl=1.4), 'kidney'),
])
def test_target_defining_warning(client, extra, disease):
    body = _post(client, base_person(**extra)).json()
    r = next(x for x in body['results'] if x['disease_key'] == disease)
    assert any(w['code'] == 'TARGET_DEFINING_INPUT' for w in r['warnings']), r['warnings']
    assert 'doğrudan klinik eşik' in r['warnings'][0]['message_tr']


def test_no_warning_without_target_inputs(client):
    body = _post(client, base_person()).json()
    assert all(not r['warnings'] for r in body['results'])


@pytest.mark.parametrize('over,model,status', [
    (dict(age_years=45), 'osteo_final', 'NOT_APPLICABLE'),
    (dict(told_diabetes=True, on_insulin=False, on_diabetes_pills=True), 'dm_A', 'NOT_APPLICABLE'),
    (dict(pregnant=True), 'dm_A', 'NOT_APPLICABLE'),
    (dict(pregnant=None), 'dm_A', 'ABSTAIN'),
    (dict(told_weak_failing_kidneys=True), 'ckd_A', 'NOT_APPLICABLE'),
    (dict(told_weak_failing_kidneys=None), 'ckd_A', 'ABSTAIN'),
    (dict(on_dialysis=True), 'ckd_A', 'NOT_APPLICABLE'),
    (dict(age_years=50), 'anemia_LR16', 'NOT_APPLICABLE'),
])
def test_population_eligibility(client, over, model, status):
    res = _by_model(_post(client, base_person(**over)))
    assert res[model]['status'] == status, res[model]['reasons']


def test_copd_ratio_not_applicable_and_ok(client):
    f = dict(age_years=60, sex='male', height_cm=175, weight_kg=80, smoking_status='current')
    res = _by_model(_post(client, dict(f, fev1_pre_ml=3000, fvc_pre_ml=4000)))
    assert res['copd_S4_DEVICE']['status'] == 'NOT_APPLICABLE'
    res = _by_model(_post(client, dict(f, fev1_pre_ml={'value': 2.0, 'unit': 'L'}, fvc_pre_ml={'value': 3.5, 'unit': 'L'})))
    assert res['copd_S4_DEVICE']['status'] == 'OK'


def test_af_not_in_predict(client):
    res = _by_model(_post(client, base_person()))
    assert res['af_S4_DEVICE']['status'] == 'NOT_APPLICABLE' and '/ecg/af' in res['af_S4_DEVICE']['reasons'][0]


def test_non_localhost_rejected(service):
    from fastapi.testclient import TestClient
    from healthrisk_api import main
    main._SERVICE = service
    c = TestClient(main.app, client=('203.0.113.7', 5000))
    assert c.get('/health').status_code == 403


def test_threshold_decision_consistency(service):
    """Karar = birincil donmuş eşik ile kıyas; eşik registry'den, değiştirilmemiş (olasılık testte bile dışarı verilmez)."""
    from healthrisk_api import features as FT
    from healthrisk_api.validation import validate_fields
    F, _ = validate_fields(base_person(), service.schema, service.extra_fields, service.conversions)
    st = service.models['dm_A']
    fr = FT.build(st['entry'], F)
    above = st['obj'].predict_proba(FT.to_frame(st['entry'], fr.values))[0, 1] >= st['entry']['thresholds']['primary']['value']
    r = service.predict_model('dm_A', F)
    assert r['decision']['research_class'] == ('ESIK_USTU' if above else 'ESIK_ALTI')
    assert json.dumps(r).count('0.4958988256379918') == 0           # eşik sayısı bile yanıtta yok
