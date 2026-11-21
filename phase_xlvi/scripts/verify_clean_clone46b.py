"""Phase XLVI kapanış — temiz klon doğrulaması (INSTALL.md §1–2, §4, §5). KLONUN venv'iyle çalıştırılır:
    <klon>/app/backend/.venv/Scripts/python.exe -B <bu_betik> <klon_kökü> <çıktı_json> [port]
verify_clean_clone46.py'den farkı: /eligibility AF satırı yeni kurala göre denetlenir (boş form: Eksik + "Ayrıca: ortam yok";
tam form: Karar verilemez: ortam yok); klonda backend pytest (-m "not slow") ve verify_af_env.py çalıştırılır.
(1) 13 model dosyası var mı, SHA256 = registry mi; (2) klonda run_server.py başlatılır; /health ve boş form için
/eligibility okunur (AF satırı ortam yokken "Karar verilemez" olmalı); /predict sentetik form; sunucu kapatılır.
Klona dosya yazılmaz (yalnız çıktı JSON'u)."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
port = int(sys.argv[3]) if len(sys.argv) > 3 else 8791
reg = json.loads((root / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
res = dict(clone_root=str(root), python=sys.version.split()[0], models={})
for mid, e in reg['models'].items():
    p = root / e['model_file']['path']
    res['models'][mid] = dict(exists=p.exists(), sha_ok=p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == e['model_file']['sha256'])


def call(path, body=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=None if body is None else json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, json.loads(r.read().decode('utf8'))


srv = subprocess.Popen([sys.executable, '-B', 'run_server.py', '--port', str(port)], cwd=root / 'app' / 'backend',
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(120):
        try:
            st, h = call('/health')
            break
        except Exception:
            time.sleep(1)
    res['health'] = dict(status=h['status'], disabled_models=h['disabled_models'], n_models=len(h['models']),
                         af_enabled=h['af_pipeline']['enabled'], af_problems=h['af_pipeline']['problems'],
                         packages_ok=h['packages']['ok'], registry_problems=h['registry']['problems'])
    st, el = call('/eligibility', {'fields': {}})
    af = [m for m in el['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
    res['eligibility_af'] = {k: af.get(k) for k in ('state', 'reasons', 'additional_reasons', 'missing_fields', 'af_pipeline_available')}
    full = dict(age_years=55, sex='female', pregnant=False)
    st, el = call('/eligibility', {'fields': full})
    af = [m for m in el['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
    res['eligibility_af_full'] = {k: af.get(k) for k in ('state', 'reasons', 'additional_reasons', 'missing_fields', 'af_pipeline_available')}
    person = dict(age_years=55, sex='female', pregnant=False, race_ethnicity='nh_white', height_cm=165, weight_kg=72,
                  smoking_status='never', glucocorticoid_ge1month=False, fracture_hip=False, fracture_wrist=False,
                  fracture_spine=False, fracture_after_age20=False, parent_hip_fracture=False, menses_absent_12m=True,
                  age_last_period_years=50, hrt_ever=False, alcohol_drinks_per_day=0.2)
    st, pr = call('/predict', {'fields': person})
    res['predict_status'] = st
    res['predict_osteo'] = [r['status'] for r in pr['results'] if r['model_id'] == 'osteo_final']
finally:
    srv.terminate()
    srv.wait(30)
ENV = 'Octave/ECGDeli AF çalışma ortamı yok'
be = root / 'app' / 'backend'
pt = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', 'tests', '-m', 'not slow', '-q', '-rs',
                     '--junitxml', str(out.with_suffix('.pytest.xml'))], cwd=be, capture_output=True, text=True, encoding='utf8',
                    errors='replace')
tail = [l for l in pt.stdout.splitlines() if l.strip()]
res['pytest'] = dict(returncode=pt.returncode, summary=tail[-1] if tail else '',
                     skipped_reasons=sorted({l.split(' ', 2)[-1][:220] for l in tail if l.startswith('SKIPPED')}))
ae = subprocess.run([sys.executable, '-B', str(root / 'phase_xlvi/scripts/verify_af_env.py')], cwd=root, capture_output=True,
                    text=True, encoding='utf8', errors='replace')
res['verify_af_env'] = dict(returncode=ae.returncode, last_lines=ae.stdout.strip().splitlines()[-3:])
ea, ef = res['eligibility_af'], res['eligibility_af_full']
res['ok'] = (all(m['exists'] and m['sha_ok'] for m in res['models'].values()) and res['health']['packages_ok']
             and not res['health']['disabled_models']
             and ea['state'] == 'MISSING' and 'ecg_record' not in ea['missing_fields'] and ea['additional_reasons'] == [ENV]
             and ef['state'] == 'ABSTAIN' and ef['reasons'] == [ENV] and ef['additional_reasons'] == []
             and res['predict_osteo'] == ['OK'] and pt.returncode == 0 and ' failed' not in res['pytest']['summary']
             and 'error' not in res['pytest']['summary'] and ae.returncode == 1)
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps(dict(ok=res['ok'], health=res['health']['status'], af=res['eligibility_af'], af_full=res['eligibility_af_full'],
                      osteo=res['predict_osteo'], pytest=res['pytest']['summary'], af_env=res['verify_af_env']), ensure_ascii=False))
