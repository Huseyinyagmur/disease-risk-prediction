"""Phase L madde 1: sunucunun ürettiği uygunluk / ret / aralık metinlerinin taranması.
SENTETİK uç durum girdileri /eligibility ve /predict'e gönderilir; dönen tüm gerekçe, ek gerekçe, uyarı ve 422 alan
hatası metinleri toplanır. Çıktı (Vitest fikstürü + rapor girdisi):
  app/frontend/src/test/fixtures/reason_scan.json, phase_l/results/reason_scan.json
Kullanım (V2 kökünden; backend 127.0.0.1:8000):  python -B phase_l/scripts/scan_reasons.py
Gerçek kişi verisi yok; hiçbir test/sealed veri dosyası okunmaz."""
import json
import urllib.error
import urllib.request
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
API = 'http://127.0.0.1:8000'

BASE = dict(
    age_years=55, sex='female', pregnant=False, race_ethnicity='nh_white', height_cm=165, weight_kg=70, waist_cm=88,
    sbp_1_mmhg=130, dbp_1_mmhg=80, sbp_2_mmhg=128, dbp_2_mmhg=79, sbp_3_mmhg=127, dbp_3_mmhg=78,
    smoking_status='never', alcohol_drinks_per_day=0, told_hypertension=False, on_bp_medication=False,
    told_diabetes=False, hx_coronary_disease=False, hx_heart_failure=False, hx_stroke=False, family_hx_diabetes=False,
    gestational_diabetes_hx=False, recreational_activity=True, glucocorticoid_ge1month=False, fracture_hip=False,
    fracture_wrist=False, fracture_spine=False, fracture_after_age20=False, parent_hip_fracture=False,
    menses_absent_12m=True, hrt_ever=False, age_last_period_years=50, hba1c_pct=5.6, glucose_serum_mgdl=95,
    glucose_fasting_mgdl=92, total_chol_mgdl=200, hdl_mgdl=55, tg_mgdl=120, alt_ul=25, ast_ul=24, ggt_ul=30, alp_ul=70,
    albumin_gdl=4.3, platelets_k_ul=250, uric_acid_mgdl=5, creatinine_mgdl=0.8, urine_albumin_mgl=10,
    urine_creatinine_mgdl=100, wbc_k_ul=6.5, rbc_m_ul=4.5, mcv_fl=90, rdw_pct=13, hemoglobin_gdl=13.5,
    fev1_pre_ml=2000, fvc_pre_ml=3200, cad_chest_pain_type='asymptomatic', cad_resting_ecg='normal',
    cad_max_hr_bpm=150, cad_exercise_angina=False, cad_st_depression_mm=0.5, cad_st_slope='flat',
    told_weak_failing_kidneys=False, on_dialysis=False)


def variants():
    yield 'bos', {}
    yield 'tam', dict(BASE)
    for age in (19, 30, 45, 70, 85, 95, 110):
        yield f'yas_{age}', {**BASE, 'age_years': age}
        yield f'yas_{age}_erkek', {**BASE, 'age_years': age, 'sex': 'male'}
    yield 'gebe_bilmiyorum', {**BASE, 'age_years': 30, 'pregnant': 'unknown'}
    yield 'gebe_evet', {**BASE, 'age_years': 30, 'pregnant': True}
    yield 'gebe_yanitsiz', {k: v for k, v in {**BASE, 'age_years': 30}.items() if k != 'pregnant'}
    yield 'irk_yanitsiz', {k: v for k, v in BASE.items() if k != 'race_ethnicity'}
    yield 'cinsiyet_yanitsiz', {k: v for k, v in BASE.items() if k != 'sex'}
    yield 'yas_yanitsiz', {k: v for k, v in BASE.items() if k != 'age_years'}
    yield 'diyabet_tanili', {**BASE, 'told_diabetes': True, 'on_insulin': True}
    yield 'diyabet_ilac', {**BASE, 'told_diabetes': True, 'on_diabetes_pills': True}
    yield 'diyabet_yanitsiz', {k: v for k, v in BASE.items() if k != 'told_diabetes'}
    yield 'bobrek_tanili', {**BASE, 'told_weak_failing_kidneys': True, 'on_dialysis': True}
    yield 'bobrek_yanitsiz', {k: v for k, v in BASE.items() if k != 'told_weak_failing_kidneys'}
    yield 'koah_oran_normal', {**BASE, 'fev1_pre_ml': 3000, 'fvc_pre_ml': 3500}
    yield 'bmi_uc_dusuk', {**BASE, 'weight_kg': 30, 'height_cm': 200}
    yield 'bmi_uc_yuksek', {**BASE, 'weight_kg': 250, 'height_cm': 150}
    yield 'tahlil_uc', {**BASE, 'alt_ul': 900, 'ast_ul': 900, 'ggt_ul': 1900, 'platelets_k_ul': 1400, 'hba1c_pct': 17,
                        'creatinine_mgdl': 14, 'urine_albumin_mgl': 9000, 'tg_mgdl': 4900, 'hemoglobin_gdl': 21}
    yield 'kategori_gecersiz', {**BASE, 'smoking_status': 'sometimes', 'race_ethnicity': 'xyz', 'pregnant': 'maybe'}
    yield 'son_adet_yok', {k: v for k, v in {**BASE, 'menses_absent_12m': False}.items() if k != 'age_last_period_years'}
    # 422 alan hataları: her sayısal alan için makul aralık dışı değer + tutarlılık + birim
    yield '422_tutarsiz', {**BASE, 'sbp_1_mmhg': 80, 'dbp_1_mmhg': 90, 'fev1_pre_ml': 4000, 'fvc_pre_ml': 3000}
    yield '422_birim', {**BASE, 'weight_kg': {'value': 70, 'unit': 'stone'}}
    yield '422_metin', {**BASE, 'weight_kg': 'yetmiş'}


def post(path, fields):
    req = urllib.request.Request(API + path, data=json.dumps(dict(fields=fields)).encode(), method='POST',
                                 headers={'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    schema = json.loads(urllib.request.urlopen(API + '/schema', timeout=30).read())
    nums = [n for n, f in schema['fields'].items() if f.get('form_input') and f['type'] == 'numeric']
    cases = list(variants())
    for n in nums:
        lo, hi = schema['fields'][n]['plausible_range']
        cases.append((f'422_aralik_{n}', {**BASE, n: hi * 2 + 10 if hi > 0 else 10}))
    reasons, field_errors, warnings = {}, {}, {}
    for name, fields in cases:
        for path in ('/eligibility', '/predict'):
            code, body = post(path, fields)
            if code == 422:
                for e in body.get('detail', []) if isinstance(body.get('detail'), list) else []:
                    loc = e.get('loc', [])
                    field_errors.setdefault(e['msg'], dict(field=loc[-1] if loc else None, case=name))
                continue
            for e in body.get('field_errors', []) or []:
                field_errors.setdefault(e['msg'], dict(field=e.get('field'), case=name))
            items = body.get('models') or body.get('results') or []
            for m in items:
                for x in (m.get('reasons') or []) + (m.get('additional_reasons') or []):
                    reasons.setdefault(x, dict(model_id=m['model_id'], case=name, path=path))
                for w in m.get('warnings') or []:
                    warnings.setdefault(w['message_tr'], dict(model_id=m['model_id'], case=name))
            for w in body.get('warnings', []) or []:
                warnings.setdefault(w['message_tr'], dict(case=name))
    out = dict(note='Phase L sentetik tarama (scan_reasons.py). Gerçek kişi verisi değildir.', n_cases=len(cases),
               reasons=reasons, field_errors=field_errors, warnings=warnings)
    txt = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    for p in (V2 / 'app/frontend/src/test/fixtures/reason_scan.json', V2 / 'phase_l/results/reason_scan.json'):
        p.write_text(txt + '\n', encoding='utf8')
    print('vaka', len(cases), 'gerekçe', len(reasons), 'alan hatası', len(field_errors), 'uyarı', len(warnings))


if __name__ == '__main__':
    main()
