"""Karar 6: PhysioNet Challenge biçimi (.hea + .mat) ile /ecg/af uçtan uca biçim testi.
Kaynak: phase_xxxiii'te kilitli pipeline ile işlenmiş kayıtlar (records33.csv). YALNIZ kimlik/kaynak ve 10 EKG feature
sütunu okunur (olasılık ve etiket sütunları okunmaz); model metriği raporlanmaz, karar yalnız uç noktanın çalıştığını
gösterir. Seçim: kilitli read_wfdb_500 girdi koşulunu (5000 örnek = 10 sn) sağlayan, eksiksiz feature'lı kayıtlar
arasından kaynak başına (chapman_shaoxing, cpsc_2018, georgia) rel sırasına göre ilk kayıt. Yaş/cinsiyet sentetik."""
import math
from pathlib import Path

import pandas as pd
import pytest

from conftest import AF_ENV, skip_module_without
from healthrisk_api.ecg_af import AF_FEATURES
from healthrisk_api.paths import V2

REQ = ('phase_xxxiii/results/records33.csv', 'phase_xxxiii/data/raw') + AF_ENV
skip_module_without(*REQ)                                           # temiz klon: toplama hatası yerine SKIP
pytestmark = pytest.mark.requires_research_tree(*REQ)
P33 = V2 / 'phase_xxxiii'
RAW = P33 / 'data/raw'
COLS = ['rel', 'source', 'origin', 'completed'] + AF_FEATURES


def _nsamp(rel):
    h, m = RAW / f'{rel}.hea', RAW / f'{rel}.mat'
    return int(h.read_text().split()[3]) if h.exists() and m.exists() else -1


def _select():
    d = pd.read_csv(P33 / 'results/records33.csv', usecols=COLS)          # p / y / dx sütunları okunmaz
    d = d[(d.origin == 'XXXIII') & (d.completed == True) & d[AF_FEATURES].notna().all(axis=1)].sort_values('rel')  # noqa: E712
    out = []
    for src in ('chapman_shaoxing', 'cpsc_2018', 'georgia'):
        for _, r in d[d.source == src].iterrows():
            if _nsamp(r.rel) == 5000:
                out.append(r)
                break
    return pd.DataFrame(out)


SEL = _select()
RECORDS = SEL.rel.tolist()


def _upload(client, rel, age='60', sex='female'):
    stem = Path(rel).name
    return client.post('/ecg/af', files={'header_file': (f'{stem}.hea', (RAW / f'{rel}.hea').read_bytes()),
                                         'signal_file': (f'{stem}.mat', (RAW / f'{rel}.mat').read_bytes())},
                       data={'age_years': age, 'sex': sex})


def test_three_sources_selected():
    assert len(RECORDS) == 3 and set(SEL.source) == {'chapman_shaoxing', 'cpsc_2018', 'georgia'}


@pytest.mark.slow
@pytest.mark.parametrize('rel', RECORDS)
def test_af_mat_end_to_end_feature_parity(client, rel):
    r = _upload(client, rel)
    assert r.status_code == 200, r.text
    res = r.json()['result']
    feats = res['pipeline']['features_ms']
    assert feats is not None, res['reasons']
    ref = SEL.set_index('rel').loc[rel]
    for k in AF_FEATURES:
        a, b = feats[k], float(ref[k])
        assert (math.isnan(b) and a is None) or abs(a - b) <= 1e-6, (rel, k, a, b)
    assert res['status'] in ('OK', 'NOT_APPLICABLE') and res['pipeline']['wall_seconds'] <= 60
    assert r.json()['disclaimer'].startswith('Araştırma prototipidir;') and res['module_label'] == 'ana modül'


def _select_long(n=3):
    """cpsc_2018: tamamlanmış, feature'ları eksiksiz, 10 sn'den UZUN (> 5000 örnek) kayıtlar; rel sırasına göre ilk n."""
    d = pd.read_csv(P33 / 'results/records33.csv', usecols=COLS)          # p / y / dx sütunları okunmaz
    d = d[(d.origin == 'XXXIII') & (d.completed == True) & (d.source == 'cpsc_2018')  # noqa: E712
          & d[AF_FEATURES].notna().all(axis=1)].sort_values('rel')
    rows = [r for _, r in d.iterrows() if _nsamp(r.rel) > 5000][:n]
    return pd.DataFrame(rows)


LONG = _select_long()


def test_three_long_cpsc_selected():
    assert len(LONG) == 3 and all(_nsamp(r) > 5000 for r in LONG.rel)


@pytest.mark.slow
@pytest.mark.parametrize('rel', LONG.rel.tolist())
def test_af_long_record_first10s_feature_parity(client, rel):
    """Karar (Phase XLIV son): 'ilk 10 sn' ön adımı (Phase XXIX/XXXIII kodunun birebir kopyası) kilitli pipeline'ın
    önünde. 10 sn'den uzun Challenge kaydında feature'lar phase_xxxiii kayıtlı çıktısıyla birebir aynı olmalı."""
    r = _upload(client, rel)
    assert r.status_code == 200, r.text
    res = r.json()['result']
    feats = res['pipeline']['features_ms']
    assert feats is not None, res['reasons']
    ref = LONG.set_index('rel').loc[rel]
    for k in AF_FEATURES:
        assert abs(feats[k] - float(ref[k])) <= 1e-6, (rel, k, feats[k], float(ref[k]))
    assert res['pipeline']['record_samples'] == _nsamp(rel) and 'kırpıldı' in res['pipeline']['window']
    assert res['status'] in ('OK', 'NOT_APPLICABLE') and res['pipeline']['wall_seconds'] <= 60


def _hea_with(rel, fs=None, nsamp=None):
    lines = (RAW / f'{rel}.hea').read_text().splitlines()
    head = lines[0].split()
    if fs is not None:
        head[2] = str(fs)
    if nsamp is not None:
        head[3] = str(nsamp)
    return (chr(10).join([' '.join(head)] + lines[1:]) + chr(10)).encode('ascii')


@pytest.mark.parametrize('fs,nsamp,msg', [(250, None, '500 Hz'), (1000, None, '500 Hz'), (None, 4999, '10 sn'),
                                          (None, 3000, '10 sn')], ids=['250Hz', '1000Hz', '4999_ornek', '3000_ornek'])
def test_af_short_or_wrong_fs_abstains(client, fs, nsamp, msg):
    rel = LONG.rel.iloc[0]
    stem = Path(rel).name
    r = client.post('/ecg/af', files={'header_file': (f'{stem}.hea', _hea_with(rel, fs, nsamp)),
                                      'signal_file': (f'{stem}.mat', (RAW / f'{rel}.mat').read_bytes())},
                    data={'age_years': '60', 'sex': 'female'})
    res = r.json()['result']
    assert res['status'] == 'ABSTAIN' and msg in res['reasons'][0], res['reasons']


def test_pre_step_source_verified_and_tamper_detected(monkeypatch):
    from healthrisk_api import ecg_window as W
    assert W.verify_source() == []

    def read_first10s(record_path, pl):           # değiştirilmiş kopya (sampto farklı)
        """x"""
        import wfdb
        sig, f = wfdb.rdsamp(str(record_path), sampto=4000)
        return sig
    monkeypatch.setattr(W, 'read_first10s', read_first10s)
    assert any('birebir değil' in x for x in W.verify_source())
    monkeypatch.setattr(W, 'SOURCE_FILE_SHA256', '0' * 64)
    assert any('SHA256' in x for x in W.verify_source())
