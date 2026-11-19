"""Birim dönüşümleri (input_schema.unit_conversions) ve alan doğrulaması (422 kuralları)."""
import pytest

from healthrisk_api.transforms import Invalid
from healthrisk_api.validation import ValidationError422, validate_fields

# (alan, kaynak birim, değer, beklenen model birimi değeri) — şemadaki op metinlerinden elle
UNIT_CASES = [
    ('glucose_serum_mgdl', 'mmol/L', 5.5, 5.5 * 18.016), ('glucose_fasting_mgdl', 'mmol/L', 7.0, 7.0 * 18.016),
    ('total_chol_mgdl', 'mmol/L', 5.0, 5.0 * 38.67), ('hdl_mgdl', 'mmol/L', 1.3, 1.3 * 38.67),
    ('tg_mgdl', 'mmol/L', 1.7, 1.7 * 88.57), ('creatinine_mgdl', 'µmol/L', 88.4, 1.0),
    ('uric_acid_mgdl', 'µmol/L', 297.4, 297.4 / 59.48), ('hba1c_pct', 'mmol/mol (IFCC)', 48.0, 48 * 0.09148 + 2.152),
    ('hemoglobin_gdl', 'g/L', 135.0, 13.5), ('albumin_gdl', 'g/L', 42.0, 4.2), ('height_cm', 'inç', 70.0, 177.8),
    ('weight_kg', 'lb', 180.0, 180 * 0.45359237), ('waist_cm', 'inç', 36.0, 91.44), ('fev1_pre_ml', 'L', 2.5, 2500.0),
    ('fvc_pre_ml', 'L', 3.5, 3500.0), ('urine_albumin_mgl', 'mg/dL', 3.0, 30.0), ('wbc_k_ul', '10^9/L', 6.1, 6.1),
    ('platelets_k_ul', '10^9/L', 250.0, 250.0), ('rbc_m_ul', '10^12/L', 4.7, 4.7),
]


def _v(service, raw):
    return validate_fields(raw, service.schema, service.extra_fields, service.conversions)


def test_every_schema_conversion_is_tested(service):
    schema_pairs = set(service.conversions)
    tested = {(f, u) for f, u, _, _ in UNIT_CASES}
    assert schema_pairs == tested, schema_pairs ^ tested


@pytest.mark.parametrize('field,unit,val,expected', UNIT_CASES)
def test_unit_conversion(service, field, unit, val, expected):
    F, notes = _v(service, {field: {'value': val, 'unit': unit}})
    assert abs(F[field] - expected) <= 1e-9 * max(1, abs(expected))
    assert notes


def test_canonical_unit_passthrough(service):
    F, notes = _v(service, {'glucose_serum_mgdl': {'value': 99, 'unit': 'mg/dL'}})
    assert F['glucose_serum_mgdl'] == 99.0 and not notes


def test_ambiguous_unit_out_of_range_rejected(service):
    """Şema notu: glukoz 5.4 birim belirtilmeden mg/dL sayılır ve aralık dışı -> tahmin yok (422)."""
    with pytest.raises(ValidationError422):
        _v(service, {'glucose_serum_mgdl': 5.4})


@pytest.mark.parametrize('raw', [
    {'age_years': 130}, {'age_years': 17}, {'height_cm': 90}, {'sbp_1_mmhg': 300},
    {'hba1c_pct': {'value': 200, 'unit': 'mmol/mol (IFCC)'}},       # dönüşüm sonrası 20.4% > 18
    {'age_years': 'elli'}, {'age_years': True}, {'bilinmeyen_alan': 1},
    {'glucose_serum_mgdl': {'value': 5.5, 'unit': 'mmol/mol'}},     # desteklenmeyen birim
    {'sbp_1_mmhg': 80, 'dbp_1_mmhg': 85},                           # sistolik ≤ diyastolik
    {'fev1_pre_ml': 3000, 'fvc_pre_ml': 2500},                      # FEV1 > FVC
    {'ecg_af_RR_Mean_Global': 800},                                 # pipeline alanı formdan girilemez
    {'ecg_ptbxl_ecgdeli_168': 1},
])
def test_422_cases(service, raw):
    with pytest.raises(ValidationError422):
        _v(service, raw)


def test_unknown_category_is_not_422(service):
    F, _ = _v(service, {'sex': 'diverse', 'smoking_status': 'sometimes', 'fracture_hip': 'yes'})
    assert all(isinstance(F[k], Invalid) for k in ('sex', 'smoking_status', 'fracture_hip'))


def test_null_is_missing(service):
    F, _ = _v(service, {'age_years': None, 'sex': 'male'})
    assert 'age_years' not in F and F['sex'] == 'male'
