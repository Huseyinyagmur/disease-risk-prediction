"""Phase XLVI — Görev 5: AF çalışma ortamı yokken /eligibility AF satırı.

Önce: panel AF için "Eksik: EKG kaydı" gösteriyordu; oysa ortam yokken EKG yüklense de karar üretilemez.
Şimdi: state = ABSTAIN, gerekçe "Octave/ECGDeli AF çalışma ortamı yok" (arayüz: "Karar verilemez: …"),
missing_fields boş, af_pipeline_available = false, ayrıntı `details` alanında. Diğer modeller etkilenmez.
Model çalıştırılmaz (eligibility); gerçek Octave çalıştırılmaz.
"""
import json

import pytest

from conftest import base_person


def _af_row(resp):
    rows = [m for m in resp['models'] if m['model_id'] == 'af_S4_DEVICE']
    assert len(rows) == 1
    return rows[0]


def _pipeline_without_env(monkeypatch):
    import healthrisk_api.ecg_af as A
    monkeypatch.setattr(A, 'AF_LOCK', A.V2 / 'yok' / 'af_pipeline_lock.json')
    af = A.AFPipeline()
    assert not af.enabled
    return af


def test_af_env_missing_eligibility_says_cannot_decide(client, service, monkeypatch):
    before = {m['model_id']: m for m in client.post('/eligibility', json={'fields': base_person(sex='male', pregnant=None)}).json()['models']}
    monkeypatch.setattr(service, 'af', _pipeline_without_env(monkeypatch))
    resp = client.post('/eligibility', json={'fields': base_person(sex='male', pregnant=None)})
    assert resp.status_code == 200
    body = resp.json()
    af = _af_row(body)
    assert af['state'] == 'ABSTAIN'
    assert af['reasons'][0] == 'Octave/ECGDeli AF çalışma ortamı yok'
    assert af['missing_fields'] == [] and 'ecg_record' not in af['missing_fields']
    assert af['af_pipeline_available'] is False
    assert af['details'] and af['details'][0].startswith('Octave/ECGDeli AF çalışma ortamı yok')
    assert not any('EKG kaydı' in r for r in af['reasons'])
    # diğer modeller etkilenmez
    after = {m['model_id']: m for m in body['models']}
    for mid, m in after.items():
        if mid == 'af_S4_DEVICE':
            continue
        assert (m['state'], m['missing_fields'], m['reasons']) == (before[mid]['state'], before[mid]['missing_fields'],
                                                                     before[mid]['reasons']), mid


def test_af_env_missing_overrides_out_of_scope_and_empty_form(client, service, monkeypatch):
    monkeypatch.setattr(service, 'af', _pipeline_without_env(monkeypatch))
    for fields in ({}, {'age_years': 95, 'sex': 'female', 'pregnant': False}):
        af = _af_row(client.post('/eligibility', json={'fields': fields}).json())
        assert af['state'] == 'ABSTAIN' and af['reasons'][0] == 'Octave/ECGDeli AF çalışma ortamı yok'


def test_af_octave_missing_same_reason(service, monkeypatch):
    import healthrisk_api.ecg_af as A
    real = json.loads(A.AF_LOCK.read_text(encoding='utf8')) if A.AF_LOCK.exists() else None
    if real is None:
        pytest.skip('kilit dosyası yok (temiz klon); ortam-yok yolu ayrı testte')
    real['octave']['exe'] = 'yok/octave-cli.exe'
    monkeypatch.setattr(A.json, 'loads', lambda s, *a, **k: real)
    af = A.AFPipeline()
    monkeypatch.undo()
    assert not af.enabled
    monkeypatch.setattr(service, 'af', af)
    row = _af_row(service.eligibility(base_person()))
    assert row['state'] == 'ABSTAIN' and row['reasons'][0] == 'Octave/ECGDeli AF çalışma ortamı yok'


def test_af_sha_mismatch_reason_is_not_env_missing(service, monkeypatch):
    import healthrisk_api.ecg_af as A
    if not A.AF_LOCK.exists():
        pytest.skip('kilit dosyası yok (temiz klon)')
    real = A.sha256_file
    monkeypatch.setattr(A, 'sha256_file', lambda p: '0' * 64 if str(p).endswith('af_pipeline_v1.py') else real(p))
    af = A.AFPipeline()
    monkeypatch.undo()
    assert not af.enabled
    monkeypatch.setattr(service, 'af', af)
    row = _af_row(service.eligibility(base_person()))
    assert row['state'] == 'ABSTAIN'
    assert row['reasons'][0] == 'AF pipeline devre dışı: kilit/SHA256 doğrulaması başarısız'
    assert any('af_pipeline_v1.py' in d for d in row['details'])


def test_af_env_present_keeps_missing_ecg_record(client, service):
    if not service.af.enabled:
        pytest.skip('AF çalışma ortamı bu makinede etkin değil')
    af = _af_row(client.post('/eligibility', json={'fields': base_person()}).json())
    assert af['state'] == 'MISSING' and af['missing_fields'] == ['ecg_record']
    assert af['af_pipeline_available'] is True and af['details'] == []
