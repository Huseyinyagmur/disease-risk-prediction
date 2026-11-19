"""POST /ecg/af uçtan uca: yalnız phase_xxviii pipeline parity (tolerans) kayıtlarından 5 örnek.
Beklenen: sunucunun ürettiği 10 EKG feature'ı phase_xxviii/results/tol100_pipeline_features.csv ile aynı (|Δ| ≤ 1e-6).
Yaş/cinsiyet SENTETİKTİR (60, male); karar yalnız uç noktanın çalıştığını gösterir, metrik olarak raporlanmaz."""
import math
from pathlib import Path

import pandas as pd
import pytest

from healthrisk_api.ecg_af import AF_FEATURES
from healthrisk_api.paths import V2

P28 = V2 / 'phase_xxviii'
PARITY = pd.read_csv(P28 / 'results/tol100_pipeline_features.csv').sort_values('ecg_id')
RECORDS = PARITY[PARITY.completed].ecg_id.head(5).tolist()          # sabit: en küçük 5 ecg_id


def _files(ecg_id):
    stem = f'{int(ecg_id):05d}_hr'
    d = P28 / 'data/ptbxl500'
    return stem, (d / f'{stem}.hea').read_bytes(), (d / f'{stem}.dat').read_bytes()


@pytest.mark.slow
@pytest.mark.parametrize('ecg_id', RECORDS)
def test_af_end_to_end_feature_parity(client, ecg_id):
    stem, hea, dat = _files(ecg_id)
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', hea), 'signal_file': (f'{stem}.dat', dat)},
                    data={'age_years': '60', 'sex': 'male'})
    assert r.status_code == 200, r.text
    res = r.json()['result']
    feats = res['pipeline']['features_ms']
    assert feats is not None, res['reasons']
    ref = PARITY.set_index('ecg_id').loc[ecg_id]
    for k in AF_FEATURES:
        a, b = feats[k], float(ref[k])
        assert (math.isnan(b) and (a is None or math.isnan(a))) or abs(a - b) <= 1e-6, (k, a, b)
    assert res['pipeline']['wall_seconds'] <= 60
    assert res['status'] in ('OK', 'NOT_APPLICABLE'), res['reasons']
    if res['status'] == 'OK':
        assert res['decision']['research_class'] in ('ESIK_USTU', 'ESIK_ALTI')
    assert 'prob' not in r.text.lower().replace('clinical_probability_eligibility', '')


def test_af_mismatched_files_abstain(client):
    stem, hea, dat = _files(RECORDS[0])
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', hea), 'signal_file': ('other.dat', dat)},
                    data={'age_years': '60', 'sex': 'male'})
    res = r.json()['result']
    assert res['status'] == 'ABSTAIN' and 'uyuşmuyor' in res['reasons'][0]


def test_af_garbage_header_abstain(client):
    r = client.post('/ecg/af', files={'header_file': ('rec.hea', b'\x00\x01garbage'), 'signal_file': ('rec.dat', b'1234')},
                    data={'age_years': '60', 'sex': 'male'})
    assert r.json()['result']['status'] == 'ABSTAIN'


def test_af_wrong_format_abstain(client):
    """Girdi koşulu: 500 Hz. 250 Hz başlıklı kayıt -> ABSTAIN (başlık ön kontrolü; pipeline çalıştırılmaz)."""
    stem, hea, dat = _files(RECORDS[0])
    lines = hea.decode('ascii').splitlines()
    first = lines[0].split()
    first[2] = '250'
    hea2 = ('\n'.join([' '.join(first)] + lines[1:]) + '\n').encode('ascii')
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', hea2), 'signal_file': (f'{stem}.dat', dat)},
                    data={'age_years': '60', 'sex': 'male'})
    res = r.json()['result']
    assert res['status'] == 'ABSTAIN' and '500 Hz' in res['reasons'][0]


def test_af_out_of_range_age_422(client):
    stem, hea, dat = _files(RECORDS[0])
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', hea), 'signal_file': (f'{stem}.dat', dat)},
                    data={'age_years': '150', 'sex': 'male'})
    assert r.status_code == 422


@pytest.mark.slow
def test_af_timeout_abstain(service):
    stem, hea, dat = _files(RECORDS[0])
    feats, info = service.af.extract(f'{stem}.hea', hea, f'{stem}.dat', dat, timeout=3)
    assert feats is None and 'zaman aşımı' in info['abstain_reason']
