"""Phase XLV backend ekleri: POST /eligibility, /schema form sunumu (ask_when_rule vb.), /ecg/af görüntüleme verisi.
Tüm girdiler sentetiktir; EKG örnekleri app/frontend/public/samples altındaki iki açık PTB-XL kaydıdır (phase_xxviii
parity kümesinin bayt düzeyinde kopyası)."""
import hashlib
import math

import numpy as np
import pandas as pd
import pytest

from conftest import LABS, base_person
from healthrisk_api.ecg_af import AF_FEATURES
from healthrisk_api.paths import V2
from healthrisk_api.service import parse_condition

SAMPLES = V2 / 'app' / 'frontend' / 'public' / 'samples'
P28 = V2 / 'phase_xxviii'
STATE_OF = {'OK': 'READY', 'NOT_APPLICABLE': 'OUT_OF_SCOPE'}


def _elig(client, fields):
    r = client.post('/eligibility', json={'fields': fields})
    assert r.status_code == 200, r.text
    return r.json()


def _states(resp):
    return {m['model_id']: m for m in resp['models']}


def test_eligibility_never_runs_models(client, service, monkeypatch):
    """predict_proba çağrılırsa test başarısız olur."""
    def boom(*a, **k):
        raise AssertionError('eligibility model çalıştırdı')
    for st in service.models.values():
        if st['obj'] is not None:
            monkeypatch.setattr(st['obj'], 'predict_proba', boom, raising=False)
    resp = _elig(client, dict(base_person(), **LABS, hba1c_pct=5.4))
    assert {m['state'] for m in resp['models']} >= {'READY'}
    text = str(resp).lower().replace('clinical_probability_eligibility', '')
    assert 'prob' not in text and 'threshold' not in text and 'esik_' not in text
    assert resp['disclaimer'].startswith('Araştırma prototipidir')


def test_eligibility_lists_all_app_visible_models(client, service):
    resp = _elig(client, {})
    assert {m['model_id'] for m in resp['models']} == set(service.models)
    assert all(m['state'] == 'MISSING' for m in resp['models'])
    af = _states(resp)['af_S4_DEVICE']
    assert 'ecg_record' in af['missing_fields'] and af['endpoint'] == '/ecg/af'


@pytest.mark.parametrize('extra', [{}, LABS, dict(LABS, hba1c_pct=5.4, hemoglobin_gdl=13.5),
                                   {'race_ethnicity': None}, {'pregnant': 'unknown'}, {'age_years': 19},
                                   {'smoking_status': 'sometimes'}, {'pregnant': True}])
def test_eligibility_consistent_with_predict(client, extra):
    """Panel durumu ile /predict sonucu aynı karar öncesi mantıktan gelir (ortak precheck)."""
    f = base_person(**extra)                                     # None = alan gönderilmez
    el = _states(_elig(client, f))
    pr = client.post('/predict', json={'fields': f}).json()['results']
    seen = {}
    for r in pr:
        seen[r['model_id']] = r['status']
        if r.get('fallback_from'):
            seen[r['fallback_from']['model_id']] = r['fallback_from']['status']
    for mid, status in seen.items():
        if mid == 'af_S4_DEVICE':
            continue
        st = el[mid]['state']
        if status in STATE_OF:
            assert st == STATE_OF[status], (mid, status, st, el[mid])
        else:
            assert st in ('MISSING', 'ABSTAIN'), (mid, status, st)


def test_eligibility_field_errors_instead_of_422(client):
    f = dict(base_person(), age_years=150, sbp_2_mmhg=70, total_chol_mgdl={'value': 5.2, 'unit': 'mmol/L'},
             glucose_serum_mgdl={'value': 5.4, 'unit': 'kg'})
    resp = _elig(client, f)
    errs = {e['field']: e['msg'] for e in resp['field_errors']}
    assert set(errs) == {'age_years', 'sbp_2_mmhg', 'glucose_serum_mgdl'}
    assert 'makul aralık dışında [18, 120]' in errs['age_years'] and 'desteklenmeyen birim' in errs['glucose_serum_mgdl']
    assert any(n.startswith('total_chol_mgdl: 5.2 mmol/L') for n in resp['unit_conversion_notes'])
    assert '150' not in str(resp['models'])                      # hatalı değer modele gitmez
    # /predict aynı girdide 422 vermeye devam eder (davranış değişmedi)
    assert client.post('/predict', json={'fields': f}).status_code == 422


def test_eligibility_states_examples(client):
    s = _states(_elig(client, dict(base_person(), **LABS, hba1c_pct=5.4)))
    assert s['fibrosis_final']['state'] == 'READY'
    assert s['anemia_LR16']['state'] == 'OUT_OF_SCOPE'                 # kadın 55
    assert s['copd_S4_DEVICE']['state'] == 'MISSING' and set(s['copd_S4_DEVICE']['missing_fields']) == {'fev1_pre_ml', 'fvc_pre_ml'}
    s = _states(_elig(client, base_person(pregnant='unknown')))
    assert s['osteo_final']['state'] == 'READY'
    assert any('bilmiyorum' in x for x in s['dm_A']['reasons'])
    s = _states(_elig(client, base_person(age_years=95)))
    assert s['af_S4_DEVICE']['state'] == 'OUT_OF_SCOPE'


def test_eligibility_target_warnings(client):
    resp = _elig(client, dict(base_person(), hba1c_pct=6.9, sbp_1_mmhg=152, sbp_2_mmhg=150, sbp_3_mmhg=149))
    keys = {w['disease_key'] for w in resp['warnings']}
    assert {'diabetes', 'hypertension'} <= keys


def test_schema_form_presentation(client):
    s = client.get('/schema').json()
    f = s['fields']
    assert f['pregnant']['ask_when_rule'] == [dict(field='sex', op='eq', value='female')]
    assert f['pregnant']['required_when_rule'] == [dict(field='sex', op='eq', value='female'),
                                                   dict(field='age_years', op='gte', value=18.0)]
    assert f['age_last_period_years']['ask_when_rule'][1] == dict(field='menses_absent_12m', op='eq', value=True)
    assert f['on_bp_medication']['ask_when_rule'] == [dict(field='told_hypertension', op='eq', value=True)]
    sec = {x['id'] for x in s['form']['sections']}
    for k, v in f.items():
        assert (v['form_section'] in sec) if v['form_input'] else v['form_section'] is None, k
    assert f['sbp_1_mmhg']['form_section'] == 'olcumler' and f['alt_ul']['form_section'] == 'laboratuvar'
    assert f['cad_st_slope']['form_section'] == 'klinik' and f['race_ethnicity']['form_section'] == 'temel'
    for k, v in f.items():                                         # her kategorinin Türkçe etiketi var
        if v['type'] == 'categorical':
            assert set(map(str, v['categories'])) <= set(s['form']['category_labels_tr'][k]), k


APPROVED_DISCLAIMER = ('Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir; '
                       'negatif sonuç hastalığı dışlamaz; tanı ve tedavi için hekime başvurun.')


def test_disclaimer_single_source(client, service):
    """Uyarı metninin tek kaynağı app_config.json > disclaimer_tr; arayüz metni /schema yanıtından alır."""
    assert service.config['disclaimer_tr'] == APPROVED_DISCLAIMER
    rs = [client.get('/schema'), client.get('/models'), client.get('/health'),
          client.post('/eligibility', json={'fields': {}}), client.post('/predict', json={'fields': {'age_years': 150}})]
    assert [r.json()['disclaimer'] for r in rs] == [APPROVED_DISCLAIMER] * len(rs)


def test_af_missing_environment_reason(monkeypatch, tmp_path):
    """Yalnız depo klonlandığında (kilit/pipeline/Octave yok): AF açık gerekçeyle devre dışı, istisna yok."""
    import healthrisk_api.ecg_af as A
    monkeypatch.setattr(A, 'AF_LOCK', A.V2 / 'yok' / 'af_pipeline_lock.json')
    af = A.AFPipeline()
    assert not af.enabled and len(af.problems) == 1
    assert 'Octave/ECGDeli AF çalışma ortamı yok' in af.problems[0] and 'beklenmeyen' not in af.problems[0]
    feats, info = af.extract('x.hea', b'', 'x.dat', b'')
    assert feats is None and 'devre dışı' in info['abstain_reason']


def test_af_missing_octave_reason(monkeypatch):
    import json as _json
    import healthrisk_api.ecg_af as A
    real = _json.loads(A.AF_LOCK.read_text(encoding='utf8'))
    real['octave']['exe'] = 'yok/octave-cli.exe'
    monkeypatch.setattr(A.json, 'loads', lambda s, *a, **k: real)
    af = A.AFPipeline()
    assert not af.enabled and any(p.startswith('Octave yok:') for p in af.problems)


def test_parse_condition_rejects_unknown():
    fields = {'sex': {}, 'age_years': {}}
    assert parse_condition('sex = female ve age_years ≥ 18', fields)[1]['op'] == 'gte'
    with pytest.raises(ValueError):
        parse_condition('sex != female', fields)
    with pytest.raises(ValueError):
        parse_condition('unknown_field = 1', fields)


def test_frontend_samples_are_byte_copies():
    for n in ('00165_hr.hea', '00165_hr.dat', '00691_hr.hea', '00691_hr.dat'):
        a, b = (SAMPLES / n).read_bytes(), (P28 / 'data' / 'ptbxl500' / n).read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest(), n


@pytest.mark.slow
@pytest.mark.parametrize('stem', ['00691_hr', '00165_hr'])
def test_ecg_display_payload(client, stem):
    hea, dat = (SAMPLES / f'{stem}.hea').read_bytes(), (SAMPLES / f'{stem}.dat').read_bytes()
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', hea), 'signal_file': (f'{stem}.dat', dat)},
                    data={'age_years': '60', 'sex': 'male'})
    assert r.status_code == 200, r.text
    res = r.json()['result']
    # feature'lar ekten etkilenmedi: phase_xxviii parity çıktısıyla birebir
    ref = pd.read_csv(P28 / 'results/tol100_pipeline_features.csv').set_index('ecg_id').loc[int(stem[:5])]
    for k in AF_FEATURES:
        assert abs(res['pipeline']['features_ms'][k] - float(ref[k])) <= 1e-6, k
    d = res['display']
    assert d['lead'] == 'II' and d['fs_hz'] == 250 and len(d['signal_mv']) == 2500 and d['duration_s'] == 10
    rp, rr = d['r_peaks_s'], d['rr_ms']
    assert len(rp) >= 5 and len(rr) == len(rp) - 1 and all(0 <= t < 10 for t in rp)
    assert np.allclose(np.diff(rp) * 1000, rr, atol=0.11)
    # gösterilen RR'lerin medyanı, modele giren RR_Mean_Global feature'ına eşit (aynı FPT sütunu)
    assert math.isclose(float(np.median(rr)), res['pipeline']['features_ms']['RR_Mean_Global'], abs_tol=0.11)
    assert 'prob' not in r.text.lower().replace('clinical_probability_eligibility', '')
