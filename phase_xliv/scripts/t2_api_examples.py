"""Phase XLIV Görev 2 — canlı sunucu denemesi (yalnız 127.0.0.1) ve örnek istek/yanıtlar.
run_server.py ayrı süreçte başlatılır; httpx ile /health, /models, /schema, /predict (sentetik kişiler) ve /ecg/af
(phase_xxviii parity kümesinden 5 kayıt; sentetik yaş/cinsiyet) çağrılır. Yerel ağ adresinden bağlantı denenir
(reddedilmesi beklenir). Çıktı: results/api_examples.json, results/af_e2e.json. Olasılık hiçbir yerde üretilmez/yazılmaz.
Kullanım (app venv): python -B -I t2_api_examples.py"""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pandas as pd

P44 = Path(__file__).resolve().parents[1]
V2 = P44.parent
BACKEND = V2 / 'app' / 'backend'
PY = BACKEND / '.venv' / 'Scripts' / 'python.exe'
PORT = 8765
URL = f'http://127.0.0.1:{PORT}'
AF_FEATURES = ['RR_Mean_Global', 'RR_Mean_Global_iqr', 'QRS_Dur_Global', 'QRS_Dur_Global_iqr', 'PR_Int_Global',
               'PR_Int_Global_iqr', 'P_Dur_Global', 'P_Dur_Global_iqr', 'QT_Int_Global', 'QT_Int_Global_iqr']

PERSON = dict(age_years=55, sex='female', pregnant=False, race_ethnicity='nh_white', height_cm=165, weight_kg=72,
              waist_cm=90, sbp_1_mmhg=128, dbp_1_mmhg=80, sbp_2_mmhg=126, dbp_2_mmhg=78, sbp_3_mmhg=124, dbp_3_mmhg=79,
              smoking_status='never', alcohol_drinks_per_day=0.2, told_hypertension=False, told_diabetes=False,
              family_hx_diabetes=True, gestational_diabetes_hx=False, recreational_activity=True,
              hx_coronary_disease=False, hx_heart_failure=False, hx_stroke=False, told_weak_failing_kidneys=False,
              glucocorticoid_ge1month=False, fracture_hip=False, fracture_wrist=False, fracture_spine=False,
              fracture_after_age20=False, parent_hip_fracture=False, menses_absent_12m=True, age_last_period_years=50,
              hrt_ever=False)
LABS = dict(total_chol_mgdl={'value': 5.2, 'unit': 'mmol/L'}, hdl_mgdl=55, tg_mgdl=120, alt_ul=22, ast_ul=24, ggt_ul=25,
            alp_ul=70, albumin_gdl=4.3, platelets_k_ul=250, uric_acid_mgdl=5.0, glucose_serum_mgdl=95,
            hba1c_pct=5.3, hemoglobin_gdl=13.5, creatinine_mgdl={'value': 70, 'unit': 'µmol/L'},
            urine_albumin_mgl=8.0, urine_creatinine_mgdl=110)


def compact(resp):
    """Örnek yanıtı rapor için kısalt (kanıt/sınırlılık metinleri uzun)."""
    if 'results' in resp:
        out = []
        for r in resp['results']:
            out.append({k: r.get(k) for k in ('model_id', 'module_label', 'status', 'reasons', 'missing_fields', 'unknown_categories',
                                                'decision', 'warnings') if k in r} |
                       ({'fallback_from': {k: r['fallback_from'][k] for k in ('model_id', 'status', 'missing_fields')}}
                        if r.get('fallback_from') else {}))
        return dict(results=out, unit_conversion_notes=resp.get('unit_conversion_notes'), disclaimer=resp.get('disclaimer'),
                    clinical_probability_eligibility=resp.get('clinical_probability_eligibility'))
    return resp


def main():
    log = open(P44 / 'logs' / 't2_server.log', 'w', encoding='utf8')
    srv = subprocess.Popen([str(PY), '-B', str(BACKEND / 'run_server.py'), '--port', str(PORT)], cwd=str(BACKEND),
                           stdout=log, stderr=subprocess.STDOUT)
    ex = dict(server=dict(cmd='app/backend/.venv/Scripts/python.exe -B run_server.py --port 8765', bind='127.0.0.1'))
    try:
        c = httpx.Client(base_url=URL, timeout=120)
        for _ in range(120):
            try:
                if c.get('/health').status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.5)
        h = c.get('/health').json()
        ex['GET /health'] = dict(status=h['status'], disclaimer=h['disclaimer'], schema_version=h['schema_version'], disabled_models=h['disabled_models'], packages_ok=h['packages']['ok'],
                                 af_pipeline=h['af_pipeline'], registry_problems=h['registry']['problems'])
        m = c.get('/models').json()
        ex['GET /models'] = dict(n=len(m['models']), first=m['models'][2], ids=[x['model_id'] for x in m['models']])
        s = c.get('/schema').json()
        ex['GET /schema'] = dict(n_fields=len(s['fields']), example_field=s['fields']['glucose_fasting_mgdl'],
                                 example_units=s['unit_conversions']['glucose_fasting_mgdl'],
                                 extra_eligibility=[k for k, v in s['fields'].items() if str(v.get('source', '')).startswith('app_eligibility')])
        reqs = {
            'form_only': dict(fields=PERSON),
            'form_plus_labs_units': dict(fields=PERSON | LABS),
            'race_missing': dict(fields={k: v for k, v in PERSON.items() if k != 'race_ethnicity'}),
            'unknown_category': dict(fields=PERSON | dict(smoking_status='sometimes')),
            'target_defining_inputs': dict(fields=PERSON | dict(hba1c_pct=6.9, sbp_1_mmhg=152, sbp_2_mmhg=150, sbp_3_mmhg=149)),
            'out_of_range_422': dict(fields=PERSON | dict(age_years=150)),
            'pregnancy_unknown': dict(fields=PERSON | dict(pregnant='unknown')),
            'undiagnosed_on_pills': dict(fields=PERSON | dict(on_diabetes_pills=True, on_insulin=False)),
            'ambiguous_unit_422': dict(fields=PERSON | dict(glucose_fasting_mgdl=5.4)),
            'cad_clinical': dict(fields=dict(age_years=58, sex='male', cad_chest_pain_type='asymptomatic', sbp_1_mmhg=140,
                                             total_chol_mgdl=230, glucose_fasting_mgdl=100, cad_resting_ecg='normal',
                                             cad_max_hr_bpm=150, cad_exercise_angina=False, cad_st_depression_mm=1.0,
                                             cad_st_slope='flat')),
        }
        ex['POST /predict'] = {}
        for k, body in reqs.items():
            r = c.post('/predict', json=body)
            ex['POST /predict'][k] = dict(request=body, http_status=r.status_code,
                                          response=compact(r.json()) if r.status_code == 200 else r.json())
        # /ecg/af — parity kümesinden 5 kayıt
        par = pd.read_csv(V2 / 'phase_xxviii/results/tol100_pipeline_features.csv').sort_values('ecg_id')
        rows = []
        for eid in par[par.completed].ecg_id.head(5):
            stem = f'{int(eid):05d}_hr'
            d = V2 / 'phase_xxviii/data/ptbxl500'
            t0 = time.monotonic()
            r = c.post('/ecg/af', files={'header_file': (f'{stem}.hea', (d / f'{stem}.hea').read_bytes()),
                                         'signal_file': (f'{stem}.dat', (d / f'{stem}.dat').read_bytes())},
                       data={'age_years': '60', 'sex': 'male'})
            res = r.json()['result']
            ref = par.set_index('ecg_id').loc[eid]
            feats = res['pipeline']['features_ms'] or {}
            deltas = {k: (abs(feats[k] - float(ref[k])) if k in feats and feats[k] is not None else None) for k in AF_FEATURES}
            rows.append(dict(ecg_id=int(eid), http_status=r.status_code, status=res['status'],
                             decision_present=res['decision'] is not None,
                             max_abs_delta_vs_phase_xxviii=max(v for v in deltas.values() if v is not None) if feats else None,
                             all_10_within_1e6=bool(feats) and all(v is not None and v <= 1e-6 for v in deltas.values()),
                             octave_seconds=res['pipeline']['octave_seconds'], wall_seconds=res['pipeline']['wall_seconds'],
                             http_roundtrip_seconds=time.monotonic() - t0))
            if 'ecg_af_example' not in ex:
                ex['ecg_af_example'] = dict(request=dict(header_file=f'{stem}.hea', signal_file=f'{stem}.dat', age_years=60, sex='male'),
                                            response=dict(status=res['status'], decision=res['decision'], reasons=res['reasons'],
                                                          pipeline=res['pipeline']))
        # /ecg/af — Challenge .hea + .mat (karar 6): phase_xxxiii kayıtları; yalnız kimlik + feature sütunları okunur
        cols = ['rel', 'source', 'origin', 'completed'] + AF_FEATURES
        r33 = pd.read_csv(V2 / 'phase_xxxiii/results/records33.csv', usecols=cols)
        r33 = r33[(r33.origin == 'XXXIII') & (r33.completed == True) & r33[AF_FEATURES].notna().all(axis=1)].sort_values('rel')  # noqa: E712
        raw33 = V2 / 'phase_xxxiii/data/raw'
        mat_rows = []
        for src in ('chapman_shaoxing', 'cpsc_2018', 'georgia'):
            for _, ref in r33[r33.source == src].iterrows():
                h = raw33 / f'{ref.rel}.hea'
                if not ((raw33 / f'{ref.rel}.mat').exists() and int(h.read_text().split()[3]) == 5000):
                    continue
                stem = Path(ref.rel).name
                t0 = time.monotonic()
                r = c.post('/ecg/af', files={'header_file': (f'{stem}.hea', h.read_bytes()),
                                             'signal_file': (f'{stem}.mat', (raw33 / f'{ref.rel}.mat').read_bytes())},
                           data={'age_years': '60', 'sex': 'female'})
                res = r.json()['result']
                feats = res['pipeline']['features_ms'] or {}
                deltas = [abs(feats[k] - float(ref[k])) for k in AF_FEATURES if feats.get(k) is not None]
                mat_rows.append(dict(rel=ref.rel, source=src, http_status=r.status_code, status=res['status'],
                                     n_features=len(deltas), max_abs_delta_vs_phase_xxxiii=max(deltas) if deltas else None,
                                     all_10_within_1e6=len(deltas) == 10 and max(deltas) <= 1e-6,
                                     octave_seconds=res['pipeline']['octave_seconds'], wall_seconds=res['pipeline']['wall_seconds'],
                                     http_roundtrip_seconds=time.monotonic() - t0, module_label=res['module_label']))
                break
        (P44 / 'results' / 'af_mat_e2e.json').write_text(json.dumps(dict(
            note='Karar 6: PhysioNet Challenge .hea + .mat biçimi. phase_xxxiii kayıtları (kaynak başına 10 sn uzunluğundaki ilk '
                 'kayıt). records33.csv dosyasından yalnız rel/source/origin/completed + 10 feature okundu; olasılık/etiket okunmadı. '
                 'Model metriği raporlanmaz. Yaş/cinsiyet sentetik (60, female).', records=mat_rows), indent=1, ensure_ascii=False), encoding='utf8')
        # /ecg/af — 10 sn'den uzun cpsc_2018 kayıtları: 'ilk 10 sn' ön adımı (Phase XXIX/XXXIII birebir kopya)
        long_rows = []
        cand = r33[r33.source == 'cpsc_2018']
        for _, ref in cand.iterrows():
            h = raw33 / f'{ref.rel}.hea'
            if not (raw33 / f'{ref.rel}.mat').exists() or int(h.read_text().split()[3]) <= 5000:
                continue
            stem = Path(ref.rel).name
            t0 = time.monotonic()
            r = c.post('/ecg/af', files={'header_file': (f'{stem}.hea', h.read_bytes()),
                                         'signal_file': (f'{stem}.mat', (raw33 / f'{ref.rel}.mat').read_bytes())},
                       data={'age_years': '60', 'sex': 'female'})
            res = r.json()['result']
            feats = res['pipeline']['features_ms'] or {}
            deltas = [abs(feats[k] - float(ref[k])) for k in AF_FEATURES if feats.get(k) is not None]
            long_rows.append(dict(rel=ref.rel, record_samples=res['pipeline'].get('record_samples'),
                                  window=res['pipeline'].get('window'), http_status=r.status_code, status=res['status'],
                                  n_features=len(deltas), max_abs_delta_vs_phase_xxxiii=max(deltas) if deltas else None,
                                  all_10_within_1e6=len(deltas) == 10 and max(deltas) <= 1e-6,
                                  wall_seconds=res['pipeline']['wall_seconds'], http_roundtrip_seconds=time.monotonic() - t0))
            if len(long_rows) == 3:
                break
        (P44 / 'results' / 'af_long_e2e.json').write_text(json.dumps(dict(
            note='Son karar: ilk 10 sn ön adımı (phase_xxxiii/scripts/t3_extract.py read_first10s birebir kopya; '
                 'app/backend/healthrisk_api/ecg_window.py) kilitli pipeline önünde. cpsc_2018, 10 sn den uzun ilk 3 kayıt '
                 '(rel sırası). Yalnız kimlik + 10 feature okundu; model metriği raporlanmaz.', records=long_rows),
            indent=1, ensure_ascii=False), encoding='utf8')
        ex['GET /health after'] = dict(request_stats=c.get('/health').json()['request_stats'])
        (P44 / 'results' / 'af_e2e.json').write_text(json.dumps(dict(
            note='phase_xxviii tolerans (parity) kümesinden 5 kayıt (en küçük ecg_id). Yaş/cinsiyet sentetik (60, male). '
                 'Karar metrik olarak raporlanmaz; yalnız uç nokta ve feature parity.', records=rows), indent=1), encoding='utf8')
        # yerel ağ adresinden erişim denemesi (yalnız localhost'a bağlı olmalı)
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip = None
        reach = None
        if ip and not ip.startswith('127.'):
            try:
                socket.create_connection((ip, PORT), timeout=2).close()
                reach = 'BAĞLANDI (beklenmeyen)'
            except OSError as e:
                reach = f'bağlantı reddedildi/ulaşılamadı ({type(e).__name__})'
        ex['non_loopback_probe'] = dict(ip=ip, result=reach)
    finally:
        srv.terminate()
        srv.wait(timeout=30)
        log.close()
    (P44 / 'results' / 'api_examples.json').write_text(json.dumps(ex, indent=1, ensure_ascii=False), encoding='utf8')
    print(json.dumps(dict(mat=[(r['rel'], r['status'], r['all_10_within_1e6']) for r in json.loads((P44 / 'results/af_mat_e2e.json').read_text(encoding='utf8'))['records']],
                          health=ex['GET /health']['status'], af=[(r['ecg_id'], r['status'], r['all_10_within_1e6']) for r in rows],
                          probe=ex['non_loopback_probe']), ensure_ascii=False))


if __name__ == '__main__':
    main()
