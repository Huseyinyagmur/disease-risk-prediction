"""input_schema.transforms kurallarının uygulaması. Tek kaynak: phase_xliv/registry/input_schema_v2.json (v1'in 46 kuralı
+ v2'nin 5 yeni kuralı; v1 kuralları birim testleri için korunur, v2 model_usage'da kullanılmayanlar işaretlidir).

Her dönüşüm `fn(F, src)` imzalıdır: F doğrulanmış kullanıcı alanları (model birimine çevrilmiş), src registry'deki
`input_field` metni. Eksik alan -> Missing, şemada olmayan kategori -> UnknownCategory, popülasyon dışı -> NotApplicable.
Sessiz tür dönüşümü yapılmaz: string kategoriler buradaki tablolarla üretilir (ör. CAD '1.0').
Yapısal boşluk (osteo age_last_period) STRUCTURAL_NAN döner; eksik sayılmaz (policy.structural_blanks)."""
import math


class Missing(Exception):
    def __init__(self, fields):
        super().__init__(', '.join(fields))
        self.fields = list(fields)


class UnknownCategory(Exception):
    def __init__(self, field, value):
        super().__init__(f'{field}={value!r}')
        self.field, self.value = field, value


class NotApplicable(Exception):
    pass


class Invalid:
    """Şema kategorisinde olmayan ham değer (doğrulama katmanı üretir). Kullanan model ABSTAIN eder."""
    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return f'Invalid({self.raw!r})'


STRUCTURAL_NAN = float('nan')


def need(F, name):
    v = F.get(name)
    if v is None:
        raise Missing([name])
    if isinstance(v, Invalid):
        raise UnknownCategory(name, v.raw)
    return v


def need_all(F, names):
    miss = [n for n in names if F.get(n) is None]
    if miss:
        raise Missing(miss)
    return [need(F, n) for n in names]


def _cat(F, name, table):
    v = need(F, name)
    if v not in table:
        raise UnknownCategory(name, v)
    return table[v]


def _bool(F, name):
    v = need(F, name)
    if not isinstance(v, bool):
        raise UnknownCategory(name, v)
    return v


# ---------------------------------------------------------------- tablolar (şema metinleriyle birebir)
SEX_STR = {'female': 'female', 'male': 'male'}
SEX_MALE01 = {'male': 1.0, 'female': 0.0}
SEX_FEMALE01 = {'female': 1.0, 'male': 0.0}
SEX_PTBXL01 = {'male': 0, 'female': 1}
RACE_CATS = ['mexican_american', 'other_hispanic', 'nh_white', 'nh_black', 'other_incl_multi']
SMOKING_CATS = ['never', 'former', 'current']
CAD_SEX = {'female': '0.0', 'male': '1.0'}
CAD_CP = {'typical_angina': '1.0', 'atypical_angina': '2.0', 'non_anginal': '3.0', 'asymptomatic': '4.0'}
CAD_RESTECG = {'normal': '0.0', 'st_t_abnormality': '1.0', 'lv_hypertrophy': '2.0'}
CAD_EXANG = {True: '1.0', False: '0.0'}
CAD_SLOPE = {'upsloping': '1.0', 'flat': '2.0', 'downsloping': '3.0'}


def _race_ind(code):
    def f(F, src):
        v = _cat(F, 'race_ethnicity', {c: c for c in RACE_CATS})
        return 1.0 if v == code else 0.0
    return f


def _mean(F, names):
    vals = need_all(F, names)
    return float(sum(vals) / len(vals))


def _smoking(F):
    return _cat(F, 'smoking_status', {c: c for c in SMOKING_CATS})


def egfr_ckdepi2021(scr, age, female):
    k, a = (0.7, -0.241) if female else (0.9, -0.302)
    r = scr / k
    return 142.0 * min(r, 1.0) ** a * max(r, 1.0) ** -1.2 * 0.9938 ** age * (1.012 if female else 1.0)


def _age_cap89(F, src):
    a = float(need(F, 'age_years'))
    if a >= 90:
        raise NotApplicable('yaş ≥ 90: PTB-XL eğitiminde >89 yaş gizlilik kodluydu (age_cap89_ptbxl), tahmin üretilmez')
    return a


def _gdm(F, src):
    if _cat(F, 'sex', SEX_STR) == 'male':
        return 0.0
    return 1.0 if _bool(F, 'gestational_diabetes_hx') else 0.0


def _htn_dx_med(F, src):
    told = _bool(F, 'told_hypertension')
    med = F.get('on_bp_medication')
    if med is not None and not isinstance(med, bool):
        raise UnknownCategory('on_bp_medication', getattr(med, 'raw', med))
    return 1.0 if (told or med is True) else 0.0


def _skip_rule(parent, child):
    def f(F, src):
        if not _bool(F, parent):
            return 0.0                                  # yapısal atlama (eğitimdeki tanım)
        return 1.0 if _bool(F, child) else 0.0
    return f


def _diabetes_yesno(F, src):
    told = _bool(F, 'told_diabetes')
    extra = []
    for n in ('on_insulin', 'on_diabetes_pills'):
        v = F.get(n)
        if v is not None and not isinstance(v, bool):
            raise UnknownCategory(n, getattr(v, 'raw', v))
        extra.append(v is True)
    return 'yes' if (told or any(extra)) else 'no'


def _egfr(F, src):
    scr, age = need_all(F, ['creatinine_mgdl', 'age_years'])
    female = _cat(F, 'sex', SEX_STR) == 'female'
    return float(egfr_ckdepi2021(float(scr), float(age), female))


def _uacr(F, src):
    alb, ucr = need_all(F, ['urine_albumin_mgl', 'urine_creatinine_mgdl'])
    return float(math.log1p(100.0 * alb / ucr))


def _osteo_period(F, src):
    if _cat(F, 'sex', SEX_STR) == 'male':
        return 'na_male'
    return 'yes' if _bool(F, 'menses_absent_12m') else 'no'


def _osteo_hrt(F, src):
    if _cat(F, 'sex', SEX_STR) == 'male':
        return 'na_male'
    return 'yes' if _bool(F, 'hrt_ever') else 'no'


def _osteo_alp(F, src):
    if _cat(F, 'sex', SEX_STR) == 'female' and _bool(F, 'menses_absent_12m'):
        return float(need(F, 'age_last_period_years'))
    return STRUCTURAL_NAN


def round_half_up(x, nd):
    """Ondalık yarım-yukarı yuvarlama (NHANES BMXBMI ile 0,1 / 0,01 hassasiyetinde birebir; phase_xliv analizi)."""
    from decimal import ROUND_HALF_UP, Decimal
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def _bmi_raw(F):
    w, h = need_all(F, ['weight_kg', 'height_cm'])
    return float(w / (h / 100.0) ** 2)


def _train_med(child):
    """phase_xxxv t1_data: v = yn(soru); v[v.isna() & dm_told==0] = 0 — yanıt varsa tanıdan bağımsız kullanılır."""
    def f(F, src):
        v = F.get(child)
        if isinstance(v, Invalid) or (v is not None and not isinstance(v, bool)):
            raise UnknownCategory(child, getattr(v, 'raw', v))
        if v is not None:
            return 1.0 if v else 0.0
        if not _bool(F, 'told_diabetes'):
            return 0.0
        raise Missing([child])
    return f


def _egfr_cap80(F, src):
    scr, age = need_all(F, ['creatinine_mgdl', 'age_years'])
    female = _cat(F, 'sex', SEX_STR) == 'female'
    return float(egfr_ckdepi2021(float(scr), min(float(age), 80.0), female))


def _ptbxl_group(F, src):
    raise NotApplicable('MI ECGDeli 168 feature pipeline’ı yok (MI-ECGDELI-OCTAVE-v1 yazılmadı); uygulamaya bağlanamaz')


TRANSFORMS = {
    'identity': lambda F, src: float(need(F, src)),
    'age_cap80': lambda F, src: float(min(float(need(F, 'age_years')), 80.0)),
    'age_cap89_ptbxl': _age_cap89,
    'bmi_kgm2': lambda F, src: (lambda w, h: float(w / (h / 100.0) ** 2))(*need_all(F, ['weight_kg', 'height_cm'])),
    'sex_str': lambda F, src: _cat(F, 'sex', SEX_STR),
    'sex_male01': lambda F, src: _cat(F, 'sex', SEX_MALE01),
    'sex_female01': lambda F, src: _cat(F, 'sex', SEX_FEMALE01),
    'sex_ptbxl01': lambda F, src: _cat(F, 'sex', SEX_PTBXL01),
    'race_mexam': _race_ind('mexican_american'),
    'race_othhisp': _race_ind('other_hispanic'),
    'race_black': _race_ind('nh_black'),
    'race_other': _race_ind('other_incl_multi'),
    'race_str': lambda F, src: _cat(F, 'race_ethnicity', {c: c for c in RACE_CATS}),
    'sbp_mean_all': lambda F, src: _mean(F, ['sbp_1_mmhg', 'sbp_2_mmhg', 'sbp_3_mmhg']),
    'dbp_mean_all': lambda F, src: _mean(F, ['dbp_1_mmhg', 'dbp_2_mmhg', 'dbp_3_mmhg']),
    'sbp_mean_23': lambda F, src: _mean(F, ['sbp_2_mmhg', 'sbp_3_mmhg']),
    'dbp_mean_23': lambda F, src: _mean(F, ['dbp_2_mmhg', 'dbp_3_mmhg']),
    'smoke_current01': lambda F, src: 1.0 if _smoking(F) == 'current' else 0.0,
    'smoke_former01': lambda F, src: 1.0 if _smoking(F) == 'former' else 0.0,
    'smoking_str': lambda F, src: _smoking(F),
    'smoker_yesno': lambda F, src: 'yes' if _smoking(F) == 'current' else 'no',
    'bool01': lambda F, src: 1.0 if _bool(F, src) else 0.0,
    'bool_yesno': lambda F, src: 'yes' if _bool(F, src) else 'no',
    'htn_dx_med': _htn_dx_med,
    'gdm_rule': _gdm,
    'htn_med_rule': _skip_rule('told_hypertension', 'on_bp_medication'),
    'dm_insulin_rule': _skip_rule('told_diabetes', 'on_insulin'),
    'dm_pills_rule': _skip_rule('told_diabetes', 'on_diabetes_pills'),
    'diabetes_yesno': _diabetes_yesno,
    'alcohol_ge3_yesno': lambda F, src: 'yes' if float(need(F, 'alcohol_drinks_per_day')) >= 3 else 'no',
    'ln_clip1': lambda F, src: float(math.log(max(float(need(F, src)), 1.0))),
    'egfr_ckdepi2021': _egfr,
    'uacr_log1p': _uacr,
    'osteo_period_yesno': _osteo_period,
    'osteo_hrt': _osteo_hrt,
    'osteo_age_last_period': _osteo_alp,
    'alcohol_dpd': lambda F, src: float(need(F, 'alcohol_drinks_per_day')),
    'fasting_gt120_strfloat': lambda F, src: '1.0' if float(need(F, 'glucose_fasting_mgdl')) > 120 else '0.0',
    'cad_sex_strfloat': lambda F, src: _cat(F, 'sex', CAD_SEX),
    'cad_cp_strfloat': lambda F, src: _cat(F, 'cad_chest_pain_type', CAD_CP),
    'cad_restecg_strfloat': lambda F, src: _cat(F, 'cad_resting_ecg', CAD_RESTECG),
    'cad_exang_strfloat': lambda F, src: CAD_EXANG[_bool(F, 'cad_exercise_angina')],
    'cad_slope_strfloat': lambda F, src: _cat(F, 'cad_st_slope', CAD_SLOPE),
    'cad_trestbps': lambda F, src: float(need(F, 'sbp_1_mmhg')),
    'ecg_pipeline_output': lambda F, src: float(need(F, src)),
    'ptbxl_group': _ptbxl_group,
    # ---- v2 (phase_xliv/registry/input_schema_v2.json changes_from_v1)
    'bmi_kgm2_r1': lambda F, src: round_half_up(_bmi_raw(F), 1),
    'bmi_kgm2_r2': lambda F, src: round_half_up(_bmi_raw(F), 2),
    'dm_insulin_train': _train_med('on_insulin'),
    'dm_pills_train': _train_med('on_diabetes_pills'),
    'egfr_ckdepi2021_cap80': _egfr_cap80,
}

# Dönüşümün okuyabileceği kullanıcı alanları (koşullu olanlar dahil) — /models "gerekli alanlar" listesi için.
_SRC = lambda src: [src]
TRANSFORM_FIELDS = {
    'identity': _SRC, 'age_cap80': lambda s: ['age_years'], 'age_cap89_ptbxl': lambda s: ['age_years'],
    'bmi_kgm2': lambda s: ['height_cm', 'weight_kg'], 'sex_str': lambda s: ['sex'], 'sex_male01': lambda s: ['sex'],
    'sex_female01': lambda s: ['sex'], 'sex_ptbxl01': lambda s: ['sex'],
    'race_mexam': lambda s: ['race_ethnicity'], 'race_othhisp': lambda s: ['race_ethnicity'],
    'race_black': lambda s: ['race_ethnicity'], 'race_other': lambda s: ['race_ethnicity'],
    'race_str': lambda s: ['race_ethnicity'],
    'sbp_mean_all': lambda s: ['sbp_1_mmhg', 'sbp_2_mmhg', 'sbp_3_mmhg'],
    'dbp_mean_all': lambda s: ['dbp_1_mmhg', 'dbp_2_mmhg', 'dbp_3_mmhg'],
    'sbp_mean_23': lambda s: ['sbp_2_mmhg', 'sbp_3_mmhg'], 'dbp_mean_23': lambda s: ['dbp_2_mmhg', 'dbp_3_mmhg'],
    'smoke_current01': lambda s: ['smoking_status'], 'smoke_former01': lambda s: ['smoking_status'],
    'smoking_str': lambda s: ['smoking_status'], 'smoker_yesno': lambda s: ['smoking_status'],
    'bool01': _SRC, 'bool_yesno': _SRC,
    'htn_dx_med': lambda s: ['told_hypertension', 'on_bp_medication?'],
    'gdm_rule': lambda s: ['sex', 'gestational_diabetes_hx?'],
    'htn_med_rule': lambda s: ['told_hypertension', 'on_bp_medication?'],
    'dm_insulin_rule': lambda s: ['told_diabetes', 'on_insulin?'],
    'dm_pills_rule': lambda s: ['told_diabetes', 'on_diabetes_pills?'],
    'diabetes_yesno': lambda s: ['told_diabetes', 'on_insulin?', 'on_diabetes_pills?'],
    'alcohol_ge3_yesno': lambda s: ['alcohol_drinks_per_day'], 'ln_clip1': _SRC,
    'egfr_ckdepi2021': lambda s: ['creatinine_mgdl', 'age_years', 'sex'],
    'uacr_log1p': lambda s: ['urine_albumin_mgl', 'urine_creatinine_mgdl'],
    'osteo_period_yesno': lambda s: ['sex', 'menses_absent_12m?'], 'osteo_hrt': lambda s: ['sex', 'hrt_ever?'],
    'osteo_age_last_period': lambda s: ['sex', 'menses_absent_12m?', 'age_last_period_years?'],
    'alcohol_dpd': lambda s: ['alcohol_drinks_per_day'],
    'fasting_gt120_strfloat': lambda s: ['glucose_fasting_mgdl'],
    'cad_sex_strfloat': lambda s: ['sex'], 'cad_cp_strfloat': lambda s: ['cad_chest_pain_type'],
    'cad_restecg_strfloat': lambda s: ['cad_resting_ecg'], 'cad_exang_strfloat': lambda s: ['cad_exercise_angina'],
    'cad_slope_strfloat': lambda s: ['cad_st_slope'], 'cad_trestbps': lambda s: ['sbp_1_mmhg'],
    'ecg_pipeline_output': _SRC, 'ptbxl_group': lambda s: ['ecg_ptbxl_ecgdeli_168'],
    'bmi_kgm2_r1': lambda s: ['height_cm', 'weight_kg'], 'bmi_kgm2_r2': lambda s: ['height_cm', 'weight_kg'],
    'dm_insulin_train': lambda s: ['told_diabetes', 'on_insulin'],
    'dm_pills_train': lambda s: ['told_diabetes', 'on_diabetes_pills'],
    'egfr_ckdepi2021_cap80': lambda s: ['creatinine_mgdl', 'age_years', 'sex'],
}


def apply(name, F, src):
    return TRANSFORMS[name](F, src)
