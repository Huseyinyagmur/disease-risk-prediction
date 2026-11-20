"""Phase XLVI — faz sonu bütünlük denetimi.
Kullanım: python -X utf8 -B -I phase_xlvi/scripts/verify46.py  (önce sha_full_scan.py ile results/sha256_after.json)
V1: phase_xlvi/, app/ ve README.md dışında değişen/silinen/yeni = 0 (README görev gereği; app/ CLAUDE.md istisnası).
V2: 13 model dosyası SHA256 = registry = faz başı = faz sonu.
V3: registry, şema v1/v2, AF kilidi ve pipeline değişmedi.
V4: app/ ve README değişiklik listesi (bilgi).
V5: faz başından sonra yazılmış .pyc yok (tarama .venv/node_modules/.git hariç).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
P46 = V2 / 'phase_xlvi'
b = json.loads((P46 / 'config/sha256_before.json').read_text(encoding='utf8'))
a = json.loads((P46 / 'results/sha256_after.json').read_text(encoding='utf8'))
ALLOWED = ('phase_xlvi/', 'app/')
ALLOWED_FILES = {'README.md'}


def outside(k):
    return not k.startswith(ALLOWED) and k not in ALLOWED_FILES


chg = sorted(k for k in b if k in a and a[k] != b[k] and outside(k))
dele = sorted(k for k in b if k not in a and outside(k))
new = sorted(k for k in a if k not in b and outside(k))
reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))['models']
v2 = {mid: dict(registry=e['model_file']['sha256'], before=b.get(e['model_file']['path']), after=a.get(e['model_file']['path']))
      for mid, e in reg.items()}
v2ok = all(x['registry'] == x['before'] == x['after'] for x in v2.values())
locked = ['phase_xliii/registry/models.json', 'phase_xliii/registry/input_schema.json', 'phase_xliv/registry/input_schema_v2.json',
          'phase_xxviii/config/af_pipeline_lock.json', 'phase_xxviii/pipeline/af_pipeline_v1.py']
v3 = {k: b.get(k) == a.get(k) and b.get(k) is not None for k in locked}
app_chg = sorted(k for k in b if k in a and a[k] != b[k] and not outside(k))
app_new = sorted(k for k in a if k not in b and k.startswith('app/'))
app_del = sorted(k for k in b if k not in a and k.startswith('app/'))
start = (P46 / 'config/sha256_before.json').stat().st_mtime
pyc = []
for root, dirs, files in os.walk(V2):
    dirs[:] = [d for d in dirs if d not in ('.venv', 'node_modules', '.git')]
    for f in files:
        if f.endswith('.pyc') and os.path.getmtime(os.path.join(root, f)) > start:
            pyc.append(os.path.relpath(os.path.join(root, f), V2).replace('\\', '/'))
res = dict(utc=datetime.now(timezone.utc).isoformat(), n_before=len(b), n_after=len(a),
           V1=dict(changed=chg, deleted=dele, new=new, ok=not (chg or dele or new)),
           V2=dict(models=v2, ok=v2ok), V3=dict(files=v3, ok=all(v3.values())),
           V4=dict(changed_allowed=app_chg, new_app=app_new, deleted_app=app_del),
           V5=dict(new_pyc=pyc, ok=not pyc))
res['all_ok'] = all(res[k]['ok'] for k in ('V1', 'V2', 'V3', 'V5'))
(P46 / 'results/verification46.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print('V1', res['V1']['ok'], len(chg), len(dele), len(new), '| V2', v2ok, '| V3', res['V3']['ok'], '| V5', res['V5']['ok'], len(pyc),
      '| app değişen', len(app_chg), 'app yeni', len(app_new), '| all_ok', res['all_ok'])
for k in chg + dele + new + pyc:
    print('  ', k)
