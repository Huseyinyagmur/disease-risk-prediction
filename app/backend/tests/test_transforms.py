"""input_schema (v2) transforms'daki TÜM kurallar için birim testleri (beklenen değerler şema metninden elle türetildi).
v1'in 46 kuralı + v2'nin 5 kuralı (bmi_kgm2_r1/_r2, dm_insulin_train, dm_pills_train, egfr_ckdepi2021_cap80)."""
import json
import math

import pytest

from healthrisk_api import transforms as T
from healthrisk_api.paths import SCHEMA_JSON

SCHEMA = json.loads(SCHEMA_JSON.read_text(encoding='utf8'))
M, FE = 'male', 'female'

# (dönüşüm, F, src, beklenen)
CASES = [
    ('identity', {'waist_cm': 91.5}, 'waist_cm', 91.5),
    ('age_cap80', {'age_years': 45.0}, 'age_years', 45.0),
    ('age_cap80', {'age_years': 87.0}, 'age_years', 80.0),
    ('age_cap80', {'age_years': 80.0}, 'age_years', 80.0),
    ('age_cap89_ptbxl', {'age_years': 89.0}, 'age_years', 89.0),
    ('bmi_kgm2', {'weight_kg': 80.0, 'height_cm': 180.0}, 'height_cm+weight_kg', 80 / 1.8 ** 2),
    ('sex_str', {'sex': FE}, 'sex', 'female'), ('sex_str', {'sex': M}, 'sex', 'male'),
    ('sex_male01', {'sex': M}, 'sex', 1.0), ('sex_male01', {'sex': FE}, 'sex', 0.0),
    ('sex_female01', {'sex': FE}, 'sex', 1.0), ('sex_female01', {'sex': M}, 'sex', 0.0),
    ('sex_ptbxl01', {'sex': M}, 'sex', 0), ('sex_ptbxl01', {'sex': FE}, 'sex', 1),
    ('race_mexam', {'race_ethnicity': 'mexican_american'}, 'race_ethnicity', 1.0),
    ('race_mexam', {'race_ethnicity': 'nh_white'}, 'race_ethnicity', 0.0),
    ('race_othhisp', {'race_ethnicity': 'other_hispanic'}, 'race_ethnicity', 1.0),
    ('race_othhisp', {'race_ethnicity': 'nh_black'}, 'race_ethnicity', 0.0),
    ('race_black', {'race_ethnicity': 'nh_black'}, 'race_ethnicity', 1.0),
    ('race_black', {'race_ethnicity': 'other_incl_multi'}, 'race_ethnicity', 0.0),
    ('race_other', {'race_ethnicity': 'other_incl_multi'}, 'race_ethnicity', 1.0),
    ('race_other', {'race_ethnicity': 'nh_white'}, 'race_ethnicity', 0.0),
    ('race_str', {'race_ethnicity': 'other_hispanic'}, 'race_ethnicity', 'other_hispanic'),
    ('sbp_mean_all', {'sbp_1_mmhg': 120.0, 'sbp_2_mmhg': 130.0, 'sbp_3_mmhg': 125.0}, 'sbp_1..3_mmhg', 125.0),
    ('dbp_mean_all', {'dbp_1_mmhg': 70.0, 'dbp_2_mmhg': 80.0, 'dbp_3_mmhg': 78.0}, 'dbp_1..3_mmhg', 76.0),
    ('sbp_mean_23', {'sbp_1_mmhg': 200.0, 'sbp_2_mmhg': 130.0, 'sbp_3_mmhg': 125.0}, 'sbp_1..3_mmhg', 127.5),
    ('sbp_mean_23', {'sbp_2_mmhg': 130.0, 'sbp_3_mmhg': 125.0}, 'sbp_1..3_mmhg', 127.5),   # 1. okuma gerekmez
    ('dbp_mean_23', {'dbp_1_mmhg': 99.0, 'dbp_2_mmhg': 80.0, 'dbp_3_mmhg': 78.0}, 'dbp_1..3_mmhg', 79.0),
    ('smoke_current01', {'smoking_status': 'current'}, 'smoking_status', 1.0),
    ('smoke_current01', {'smoking_status': 'former'}, 'smoking_status', 0.0),
    ('smoke_former01', {'smoking_status': 'former'}, 'smoking_status', 1.0),
    ('smoke_former01', {'smoking_status': 'never'}, 'smoking_status', 0.0),
    ('smoke_former01', {'smoking_status': 'current'}, 'smoking_status', 0.0),
    ('smoking_str', {'smoking_status': 'never'}, 'smoking_status', 'never'),
    ('smoker_yesno', {'smoking_status': 'current'}, 'smoking_status', 'yes'),
    ('smoker_yesno', {'smoking_status': 'former'}, 'smoking_status', 'no'),
    ('smoker_yesno', {'smoking_status': 'never'}, 'smoking_status', 'no'),
    ('bool01', {'family_hx_diabetes': True}, 'family_hx_diabetes', 1.0),
    ('bool01', {'family_hx_diabetes': False}, 'family_hx_diabetes', 0.0),
    ('bool_yesno', {'fracture_hip': True}, 'fracture_hip', 'yes'),
    ('bool_yesno', {'fracture_hip': False}, 'fracture_hip', 'no'),
    ('htn_dx_med', {'told_hypertension': True}, '', 1.0),
    ('htn_dx_med', {'told_hypertension': False}, '', 0.0),
    ('htn_dx_med', {'told_hypertension': False, 'on_bp_medication': True}, '', 1.0),
    ('gdm_rule', {'sex': M}, '', 0.0),
    ('gdm_rule', {'sex': FE, 'gestational_diabetes_hx': True}, '', 1.0),
    ('gdm_rule', {'sex': FE, 'gestational_diabetes_hx': False}, '', 0.0),
    ('htn_med_rule', {'told_hypertension': False}, '', 0.0),
    ('htn_med_rule', {'told_hypertension': True, 'on_bp_medication': True}, '', 1.0),
    ('htn_med_rule', {'told_hypertension': True, 'on_bp_medication': False}, '', 0.0),
    ('dm_insulin_rule', {'told_diabetes': False}, '', 0.0),
    ('dm_insulin_rule', {'told_diabetes': True, 'on_insulin': True}, '', 1.0),
    ('dm_pills_rule', {'told_diabetes': False}, '', 0.0),
    ('dm_pills_rule', {'told_diabetes': True, 'on_diabetes_pills': False}, '', 0.0),
    ('diabetes_yesno', {'told_diabetes': True}, '', 'yes'),
    ('diabetes_yesno', {'told_diabetes': False}, '', 'no'),
    ('diabetes_yesno', {'told_diabetes': False, 'on_insulin': True}, '', 'yes'),
    ('diabetes_yesno', {'told_diabetes': False, 'on_diabetes_pills': True}, '', 'yes'),
    ('alcohol_ge3_yesno', {'alcohol_drinks_per_day': 3.0}, '', 'yes'),
    ('alcohol_ge3_yesno', {'alcohol_drinks_per_day': 2.99}, '', 'no'),
    ('ln_clip1', {'tg_mgdl': 150.0}, 'tg_mgdl', math.log(150.0)),
    ('ln_clip1', {'alt_ul': 1.0}, 'alt_ul', 0.0),
    ('ln_clip1', {'alt_ul': 0.5}, 'alt_ul', 0.0),                       # max(x, 1)
    # CKD-EPI 2021 elle: kadın, Scr 0.7, 50 y: 142*1*1*0.9938^50*1.012
    ('egfr_ckdepi2021', {'creatinine_mgdl': 0.7, 'age_years': 50.0, 'sex': FE}, '', 142 * 0.9938 ** 50 * 1.012),
    # erkek, Scr 1.8, 60 y: 142*(1.8/0.9)^-1.2*0.9938^60
    ('egfr_ckdepi2021', {'creatinine_mgdl': 1.8, 'age_years': 60.0, 'sex': M}, '', 142 * 2.0 ** -1.2 * 0.9938 ** 60),
    # erkek, Scr 0.6 (<κ): 142*(0.6/0.9)^-0.302*0.9938^40
    ('egfr_ckdepi2021', {'creatinine_mgdl': 0.6, 'age_years': 40.0, 'sex': M}, '', 142 * (0.6 / 0.9) ** -0.302 * 0.9938 ** 40),
    # ham yaş (age_cap80 DEĞİL): 85 yaş
    ('egfr_ckdepi2021', {'creatinine_mgdl': 0.9, 'age_years': 85.0, 'sex': M}, '', 142 * 0.9938 ** 85),
    ('uacr_log1p', {'urine_albumin_mgl': 30.0, 'urine_creatinine_mgdl': 100.0}, '', math.log(1 + 30.0)),
    ('osteo_period_yesno', {'sex': M}, '', 'na_male'),
    ('osteo_period_yesno', {'sex': FE, 'menses_absent_12m': True}, '', 'yes'),
    ('osteo_period_yesno', {'sex': FE, 'menses_absent_12m': False}, '', 'no'),
    ('osteo_hrt', {'sex': M}, '', 'na_male'),
    ('osteo_hrt', {'sex': FE, 'hrt_ever': True}, '', 'yes'),
    ('osteo_age_last_period', {'sex': FE, 'menses_absent_12m': True, 'age_last_period_years': 51.0}, '', 51.0),
    ('alcohol_dpd', {'alcohol_drinks_per_day': 1.25}, '', 1.25),
    ('fasting_gt120_strfloat', {'glucose_fasting_mgdl': 121.0}, '', '1.0'),
    ('fasting_gt120_strfloat', {'glucose_fasting_mgdl': 120.0}, '', '0.0'),   # > 120 katı
    ('cad_sex_strfloat', {'sex': FE}, '', '0.0'), ('cad_sex_strfloat', {'sex': M}, '', '1.0'),
    ('cad_cp_strfloat', {'cad_chest_pain_type': 'typical_angina'}, '', '1.0'),
    ('cad_cp_strfloat', {'cad_chest_pain_type': 'atypical_angina'}, '', '2.0'),
    ('cad_cp_strfloat', {'cad_chest_pain_type': 'non_anginal'}, '', '3.0'),
    ('cad_cp_strfloat', {'cad_chest_pain_type': 'asymptomatic'}, '', '4.0'),
    ('cad_restecg_strfloat', {'cad_resting_ecg': 'normal'}, '', '0.0'),
    ('cad_restecg_strfloat', {'cad_resting_ecg': 'st_t_abnormality'}, '', '1.0'),
    ('cad_restecg_strfloat', {'cad_resting_ecg': 'lv_hypertrophy'}, '', '2.0'),
    ('cad_exang_strfloat', {'cad_exercise_angina': True}, '', '1.0'),
    ('cad_exang_strfloat', {'cad_exercise_angina': False}, '', '0.0'),
    ('cad_slope_strfloat', {'cad_st_slope': 'upsloping'}, '', '1.0'),
    ('cad_slope_strfloat', {'cad_st_slope': 'flat'}, '', '2.0'),
    ('cad_slope_strfloat', {'cad_st_slope': 'downsloping'}, '', '3.0'),
    ('cad_trestbps', {'sbp_1_mmhg': 142.0, 'sbp_2_mmhg': 120.0}, '', 142.0),
    ('ecg_pipeline_output', {'ecg_af_RR_Mean_Global': 812.0}, 'ecg_af_RR_Mean_Global', 812.0),
    # ---- v2
    ('bmi_kgm2_r1', {'weight_kg': 80.0, 'height_cm': 180.0}, '', 24.7),          # 24.691…
    ('bmi_kgm2_r1', {'weight_kg': 70.0, 'height_cm': 175.0}, '', 22.9),          # 22.857…
    ('bmi_kgm2_r1', {'weight_kg': 90.0, 'height_cm': 150.0}, '', 40.0),          # 40.0 tam
    ('bmi_kgm2_r2', {'weight_kg': 80.0, 'height_cm': 180.0}, '', 24.69),         # 24.6913…
    ('bmi_kgm2_r2', {'weight_kg': 70.0, 'height_cm': 175.0}, '', 22.86),         # 22.857… -> yukarı
    ('dm_insulin_train', {'told_diabetes': False}, '', 0.0),                      # yanıtsız + tanı yok -> 0
    ('dm_insulin_train', {'told_diabetes': False, 'on_insulin': True}, '', 1.0),  # eğitim: tanıdan bağımsız
    ('dm_insulin_train', {'told_diabetes': True, 'on_insulin': False}, '', 0.0),
    ('dm_pills_train', {'told_diabetes': False, 'on_diabetes_pills': True}, '', 1.0),
    ('dm_pills_train', {'told_diabetes': True, 'on_diabetes_pills': True}, '', 1.0),
    ('dm_pills_train', {'on_diabetes_pills': False}, '', 0.0),                    # yanıt varsa tanı gerekmez
    ('egfr_ckdepi2021_cap80', {'creatinine_mgdl': 0.9, 'age_years': 85.0, 'sex': M}, '', 142 * 0.9938 ** 80),
    ('egfr_ckdepi2021_cap80', {'creatinine_mgdl': 0.7, 'age_years': 50.0, 'sex': FE}, '', 142 * 0.9938 ** 50 * 1.012),
]

# (dönüşüm, F, src, beklenen istisna, eksik alanlar)
ERRORS = [
    ('age_cap89_ptbxl', {'age_years': 90.0}, '', T.NotApplicable, None),
    ('ptbxl_group', {}, 'ecg_ptbxl_ecgdeli_168', T.NotApplicable, None),
    ('bmi_kgm2', {'weight_kg': 70.0}, '', T.Missing, ['height_cm']),
    ('sbp_mean_all', {'sbp_1_mmhg': 120.0, 'sbp_2_mmhg': 121.0}, '', T.Missing, ['sbp_3_mmhg']),
    ('gdm_rule', {'sex': FE}, '', T.Missing, ['gestational_diabetes_hx']),
    ('htn_med_rule', {'told_hypertension': True}, '', T.Missing, ['on_bp_medication']),
    ('dm_insulin_rule', {'told_diabetes': True}, '', T.Missing, ['on_insulin']),
    ('diabetes_yesno', {}, '', T.Missing, ['told_diabetes']),
    ('osteo_period_yesno', {'sex': FE}, '', T.Missing, ['menses_absent_12m']),
    ('osteo_age_last_period', {'sex': FE, 'menses_absent_12m': True}, '', T.Missing, ['age_last_period_years']),
    ('race_black', {}, '', T.Missing, ['race_ethnicity']),
    ('sex_str', {'sex': T.Invalid('diverse')}, '', T.UnknownCategory, None),
    ('cad_cp_strfloat', {'cad_chest_pain_type': T.Invalid('1')}, '', T.UnknownCategory, None),
    ('bool01', {'fracture_hip': T.Invalid('yes')}, 'fracture_hip', T.UnknownCategory, None),
    ('smoker_yesno', {'smoking_status': T.Invalid('sometimes')}, '', T.UnknownCategory, None),
    ('bmi_kgm2_r1', {'height_cm': 170.0}, '', T.Missing, ['weight_kg']),
    ('dm_pills_train', {'told_diabetes': True}, '', T.Missing, ['on_diabetes_pills']),
    ('dm_insulin_train', {}, '', T.Missing, ['told_diabetes']),
    ('dm_insulin_train', {'on_insulin': T.Invalid('maybe')}, '', T.UnknownCategory, None),
    ('egfr_ckdepi2021_cap80', {'age_years': 50.0, 'sex': M}, '', T.Missing, ['creatinine_mgdl']),
]


def test_all_schema_transforms_implemented_and_tested():
    schema_names = set(SCHEMA['transforms'])
    assert schema_names == set(T.TRANSFORMS), schema_names ^ set(T.TRANSFORMS)
    tested = {c[0] for c in CASES} | {c[0] for c in ERRORS}
    assert schema_names <= tested, f'testsiz dönüşüm: {sorted(schema_names - tested)}'
    assert len(schema_names) == 51 and SCHEMA['schema_version'] == '2.0'


@pytest.mark.parametrize('name,F,src,expected', CASES, ids=[f'{c[0]}-{i}' for i, c in enumerate(CASES)])
def test_transform_value(name, F, src, expected):
    got = T.apply(name, F, src)
    if isinstance(expected, str):
        assert isinstance(got, str) and got == expected              # string biçim birebir (sessiz tür dönüşümü yok)
    else:
        assert not isinstance(got, str)
        assert abs(got - expected) <= 1e-12, (got, expected)


@pytest.mark.parametrize('name,F,src,exc,missing', ERRORS, ids=[f'{c[0]}-err{i}' for i, c in enumerate(ERRORS)])
def test_transform_errors(name, F, src, exc, missing):
    with pytest.raises(exc) as ei:
        T.apply(name, F, src)
    if missing is not None:
        assert ei.value.fields == missing


def test_structural_blank_osteo():
    assert math.isnan(T.apply('osteo_age_last_period', {'sex': M}, ''))
    assert math.isnan(T.apply('osteo_age_last_period', {'sex': FE, 'menses_absent_12m': False}, ''))


def test_cad_strings_are_exact_registry_categories(service):
    """CAD string-float biçimi: dönüşüm çıktısı registry'deki fitted kategorilerle birebir ('1.0', '1' değil)."""
    e = service.registry['models']['cad_DEVICE']
    cats = {f['name']: f['allowed_values'] for f in e['features'] if f['model_dtype'] == 'str'}
    produced = {'sex': set(T.CAD_SEX.values()), 'cp': set(T.CAD_CP.values()), 'restecg': set(T.CAD_RESTECG.values()),
                'exang': set(T.CAD_EXANG.values()), 'slope': set(T.CAD_SLOPE.values()), 'fbs': {'0.0', '1.0'}}
    for k, v in produced.items():
        assert v == set(cats[k]), (k, v, cats[k])


def test_transform_names_match_registry(service):
    """models.json features[].transform == şema v2 model_usage[].transform; farklar YALNIZ changes_from_v1'deki
    gerekçeli değişikliklerdir (15 satır) ve listesiz bir fark tutarlılık hatası verir."""
    from healthrisk_api.features import consistency_problems
    ch = {}
    for c in service.schema['changes_from_v1']:
        ch.setdefault(c['model'], set()).add((c['feature'], c['old_transform'], c['new_transform']))
        assert c['reason'] and c['evidence']
    assert len(service.schema['changes_from_v1']) == 15
    for mid, e in service.registry['models'].items():
        assert consistency_problems(e, service.schema['model_usage'][mid], ch.get(mid, set())) == [], mid
        if ch.get(mid):          # izin listesi olmadan fark yakalanır (negatif kontrol)
            assert consistency_problems(e, service.schema['model_usage'][mid]) != [], mid


def test_v2_effective_transforms(service):
    use = {m: {u['model_feature']: u['transform'] for u in service.models[m]['usage']} for m in service.models}
    assert use['anemia_LR16']['bmi'] == 'bmi_kgm2_r2'
    assert all(use[m]['bmi'] == 'bmi_kgm2_r1' for m in ('dm_A', 'dm_B', 'copd_S4_DEVICE', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_A', 'ckd_B'))
    assert use['ckd_A']['dm_pills'] == 'dm_pills_train' and use['ckd_B']['dm_insulin'] == 'dm_insulin_train'
    assert use['htn_M1']['egfr'] == 'egfr_ckdepi2021_cap80'
    assert use['osteo_final']['age'] == 'age_cap80'          # karar 2: korunur
