"""Parity (en önemli test): geliştirme verisinden 200 kişi; ham alanlar -> şema alanları -> sunucu dönüşümleri (şema v2)
-> geliştirme feature tablosu ile |Δ| ≤ 1e-6 / birebir. Test/mühürlü dosyalar okunmaz (parity_lib._guard).

Şema v2 (kullanıcı kararları, phase_xliv/registry/input_schema_v2.json): BMI 0,1'e (anemide 0,01'e) yuvarlanır;
KBH dm_pills/dm_insulin eğitim tanımıyla; HTN eGFR yaşı 80'de kırpılır.
  * test_parity_strict: tüm feature'lar birebir. Eğitim BMI'si döngüye göre karışık hassasiyetli (≤ 2009–10 döngüleri
    2 ondalık, sonrası 1 ondalık) olan 5 modelde BEKLENEN BAŞARISIZLIK (strict xfail); osteo'da ayrıca yaş farkı.
    CAD, anemi, KOAH, HTN, fibrozis: xfail işareti kaldırıldı, geçer.
  * test_parity_explained: her fark ya (a) 2 ondalıklı kaynak döngüsünden gelen BMI (|Δ| ≤ 0,05) ya da (b) belgelenmiş
    osteo yaş sınırlılığıdır (kullanıcı kararı 2: age_cap80 korunur)."""
import pytest

import parity_lib as PL

MODELS = ['cad_DEVICE', 'dm_A', 'dm_B', 'anemia_LR16', 'copd_S4_DEVICE', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_A', 'ckd_B']
MIXED_BMI_PRECISION = {'dm_A', 'dm_B', 'osteo_final', 'ckd_A', 'ckd_B'}
KNOWN_LIMITATIONS = {
    ('osteo_final', 'age'): 'kullanıcı kararı 2: age_cap80 korunur; NHANES D (2005–06) yaşı 85\'te kodlu, eğitimde kırpılmamış',
}
_CACHE = {}


def _run(service, m):
    if m not in _CACHE:
        _CACHE[m] = PL.run_case(service, m, with_decision=False)
    return _CACHE[m]


def _tree(m):
    return pytest.mark.requires_research_tree(*PL.REQUIRED_FILES[m])


@pytest.mark.parametrize('model', [pytest.param(m, marks=_tree(m)) for m in MODELS])
def test_parity_explained(service, model):
    r, ex = _run(service, model)
    assert r['n_sampled'] == min(200, r['dev_pool_complete'])
    o = r['outcome']
    compared = o['MATCH'] + o['MATCH_EXCEPT_BMI_2DEC_SOURCE_CYCLE'] + o['MISMATCH_OTHER']
    assert compared >= 0.85 * r['n_sampled'], o
    for f in r['features']:
        unexplained = f['n_mismatch'] - f['n_explained_bmi_2dec_source_cycle']
        if unexplained:
            assert (model, f['feature']) in KNOWN_LIMITATIONS, (model, f, [e for e in ex if e['feature'] == f['feature']])
    bmi = next((f for f in r['features'] if f['feature'] == 'bmi'), None)
    if bmi is not None:
        assert bmi['n_mismatch'] == bmi['n_explained_bmi_2dec_source_cycle'] and bmi['max_abs_delta'] <= 0.05 + 1e-9
        if model not in MIXED_BMI_PRECISION:
            assert bmi['n_mismatch'] == 0


@pytest.mark.requires_research_tree(*PL.REQUIRED_FILES['ckd_A'])
def test_ckd_meds_now_match_training(service):
    """Karar 3: dm_pills/dm_insulin eğitim tanımıyla üretilir -> KBH'de bu feature'larda fark kalmaz."""
    for m in ('ckd_A', 'ckd_B'):
        r, _ = _run(service, m)
        feats = {f['feature']: f for f in r['features']}
        assert feats['dm_pills']['n_mismatch'] == 0 and feats['dm_insulin']['n_mismatch'] == 0
        assert feats['dm_pills']['transform'] == 'dm_pills_train'


@pytest.mark.parametrize('model', [pytest.param(m, marks=[_tree(m), pytest.mark.xfail(
    strict=True, reason='eğitim BMI\'si döngüye göre karışık hassasiyetli (≤2009–10: 0,01; sonrası 0,1); tek yuvarlama '
                        'ikisini birden üretemez' + (' + osteo yaş (age_cap80, karar 2)' if m == 'osteo_final' else ''))])
    if m in MIXED_BMI_PRECISION else pytest.param(m, marks=_tree(m)) for m in MODELS])
def test_parity_strict(service, model):
    r, _ = _run(service, model)
    o = r['outcome']
    assert o['MISMATCH_OTHER'] == 0 and o['MATCH_EXCEPT_BMI_2DEC_SOURCE_CYCLE'] == 0, o
    assert o['MATCH'] > 0
