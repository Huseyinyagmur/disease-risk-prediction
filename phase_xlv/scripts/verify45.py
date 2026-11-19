"""Phase XLV faz sonu bütünlük doğrulaması.
1) sha_full_scan.py ile faz sonu envanteri (results/sha256_after.json; .venv, __pycache__, node_modules hariç).
2) V1: phase_xlv/ ve app/ DIŞINDA faz başı -> faz sonu: değişen / silinen / yeni = 0 olmalı.
3) V2: 13 registry modeli dosya SHA256 = registry = faz başı = faz sonu. V3: registry, v1/v2 şema, AF kilidi, pipeline.
4) V4: app/ altında değişen/yeni dosyalar listelenir (CLAUDE.md istisnası). V5: faz başından sonra yazılmış .pyc yok
   (.venv / node_modules hariç tüm ağaç).
Kullanım: python -B verify45.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
V2 = P.parent
before_p = P / 'config' / 'sha256_before.json'
after_p = P / 'results' / 'sha256_after.json'
subprocess.run([sys.executable, '-B', str(P / 'scripts' / 'sha_full_scan.py'), str(after_p)], check=True)
B = json.loads(before_p.read_text(encoding='utf8'))
A = json.loads(after_p.read_text(encoding='utf8'))
mine = lambda k: k.startswith('phase_xlv/') or k.startswith('app/')
outside_b = {k: v for k, v in B.items() if not mine(k)}
outside_a = {k: v for k, v in A.items() if not mine(k)}
changed = sorted(k for k in outside_b if k in outside_a and outside_a[k] != outside_b[k])
deleted = sorted(k for k in outside_b if k not in outside_a)
new = sorted(k for k in outside_a if k not in outside_b)

reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
models = {}
for mid, e in reg['models'].items():
    p = e['model_file']['path'].replace('\\', '/')
    models[mid] = dict(path=p, registry=e['model_file']['sha256'], before=B.get(p), after=A.get(p))
models_ok = all(m['registry'] == m['before'] == m['after'] for m in models.values())
cfg = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
locked = dict(cfg['registry_files_sha256'])
locked.update({'phase_xxviii/config/af_pipeline_lock.json': (V2 / 'phase_xxviii/config/af_pipeline_lock.sha256').read_text().strip()})
lock = json.loads((V2 / 'phase_xxviii/config/af_pipeline_lock.json').read_text(encoding='utf8'))
locked['phase_xxviii/pipeline/af_pipeline_v1.py'] = lock['pipeline_sha256']
locks = {k: dict(expected=v, before=B.get(k), after=A.get(k), ok=(v == B.get(k) == A.get(k))) for k, v in locked.items()}

app_changed = sorted(k for k in A if k.startswith('app/') and k in B and A[k] != B[k])
app_new = sorted(k for k in A if k.startswith('app/') and k not in B)
app_deleted = sorted(k for k in B if k.startswith('app/') and k not in A)

t0 = before_p.stat().st_mtime
pyc = []
for root, dirs, files in os.walk(V2):
    dirs[:] = [d for d in dirs if d not in ('.venv', 'node_modules')]
    pyc += [str(Path(root, f).relative_to(V2)) for f in files if f.endswith('.pyc') and Path(root, f).stat().st_mtime > t0]

res = dict(
    before_files=len(B), after_files=len(A), scan_scope='V2 tümü; .venv, __pycache__, node_modules hariç',
    V1_outside_phase_and_app=dict(before=len(outside_b), after=len(outside_a), changed=changed, deleted=deleted, new=new,
                                  ok=not (changed or deleted or new)),
    V2_models=dict(ok=models_ok, n=len(models), models=models),
    V3_registry_schema_af_lock=dict(ok=all(x['ok'] for x in locks.values()), files=locks),
    V4_app=dict(changed=app_changed, new_count=len(app_new), new=app_new, deleted=app_deleted),
    V5_pyc_after_phase_start=dict(ok=not pyc, files=pyc[:50], n=len(pyc)),
)
(P / 'results' / 'verification45.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: (v.get('ok') if isinstance(v, dict) and 'ok' in v else v) for k, v in res.items() if k != 'V4_app'}, ensure_ascii=False))
print('V1', len(changed), len(deleted), len(new), '| app changed', app_changed, '| app new', len(app_new), '| app deleted', app_deleted)
