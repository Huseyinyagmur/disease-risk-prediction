"""Model SHA256'sı yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı ve /health'te raporlanır."""
import json

from conftest import base_person


def _svc_with_fake_sha(monkeypatch, target_suffix):
    import healthrisk_api.service as S
    real = S.sha256_file
    loaded = []
    monkeypatch.setattr(S, 'sha256_file', lambda p: '0' * 64 if str(p).replace('\\', '/').endswith(target_suffix) else real(p))
    real_load = S.load_model
    monkeypatch.setattr(S, 'load_model', lambda path, extra: loaded.append(path) or real_load(path, extra))
    return S.Service(), loaded


def test_model_sha_mismatch_disables_model(monkeypatch):
    svc, loaded = _svc_with_fake_sha(monkeypatch, 'phase_xlii/models/dm_A_final.joblib')
    assert not svc.models['dm_A']['enabled']
    assert 'phase_xlii/models/dm_A_final.joblib' not in loaded          # SHA uyuşmazsa YÜKLENMEZ
    h = svc.health()
    assert h['status'] == 'degraded' and 'dm_A' in h['disabled_models']
    assert svc.models['dm_B']['enabled']
    from healthrisk_api.validation import validate_fields
    F, _ = validate_fields(base_person(), svc.schema, svc.extra_fields, svc.conversions)
    r = svc.predict_model('dm_A', F)
    assert r['status'] == 'ABSTAIN' and 'devre dışı' in r['reasons'][0]


def test_registry_sha_mismatch_disables_all(monkeypatch):
    svc, loaded = _svc_with_fake_sha(monkeypatch, 'phase_xliii/registry/models.json')
    assert all(not s['enabled'] for s in svc.models.values()) and not loaded
    assert svc.health()['status'] == 'degraded'


def test_package_version_mismatch_disables_all(monkeypatch, tmp_path):
    import healthrisk_api.service as S
    cfg = json.loads(S.APP_CONFIG.read_text(encoding='utf8'))
    cfg['expected_packages']['lightgbm'] = '4.6.0'
    p = tmp_path / 'app_config.json'
    p.write_text(json.dumps(cfg), encoding='utf8')
    monkeypatch.setattr(S, 'APP_CONFIG', p)
    svc = S.Service(load_models=False)
    assert not svc.packages['ok'] and all(not s['enabled'] for s in svc.models.values())


def test_af_pipeline_lock_verified(service):
    st = service.af.status()
    assert st['enabled'] and st['pipeline_version'] == 'AF-ECGDELI-OCTAVE-v1' and st['problems'] == []


def test_af_pipeline_sha_mismatch_disables(monkeypatch):
    import healthrisk_api.ecg_af as A
    real = A.sha256_file
    monkeypatch.setattr(A, 'sha256_file', lambda p: '0' * 64 if str(p).endswith('af_pipeline_v1.py') else real(p))
    af = A.AFPipeline()
    assert not af.enabled and any('af_pipeline_v1.py' in x for x in af.problems)
    feats, info = af.extract('x.hea', b'', 'x.dat', b'')
    assert feats is None and 'devre dışı' in info['abstain_reason']
