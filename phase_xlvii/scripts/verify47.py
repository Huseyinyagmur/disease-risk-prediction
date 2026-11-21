"""Phase XLVII son doğrulama: SHA256 faz başı/sonu karşılaştırması ve 'yalnız sunum katmanı' denetimi.

1) sha256_before.json ile yeni tarama (sha256_after.json) karşılaştırılır. İzin verilen değişiklikler: app/ (uygulama
   istisnası), README.md (görseller), phase_xlvii/ (faz klasörü). Önceki faz klasörleri, modeller, registry, ham veri:
   değişen/silinen = 0; faz dışı yeni dosya = 0 (app/ ve phase_xlvii hariç).
2) Model mantığı dosyaları (transforms, eligibility, features, model_loader, validation, ecg_*) son commit'e göre
   değişmemiş; service.py farkı yalnız /schema'ya iki metin anahtarı ekler.
3) Kilitli registry dosyaları app_config'teki SHA256 ile aynı.
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlvii/scripts/verify47.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
R = V2 / 'phase_xlvii/results'
subprocess.run([sys.executable, '-B', str(V2 / 'phase_xlvii/scripts/sha_full_scan.py'), str(R / 'sha256_after.json')], check=True)
before = json.loads((R / 'sha256_before.json').read_text(encoding='utf8'))
after = json.loads((R / 'sha256_after.json').read_text(encoding='utf8'))

ALLOWED = ('app/', 'phase_xlvii/')
changed = sorted(k for k in before if k in after and before[k] != after[k])
deleted = sorted(k for k in before if k not in after)
added = sorted(k for k in after if k not in before)
bad_changed = [k for k in changed if not k.startswith(ALLOWED) and k != 'README.md']
bad_deleted = [k for k in deleted if not k.startswith('phase_xlvii/')]
bad_added = [k for k in added if not k.startswith(ALLOWED)]

LOGIC = ['transforms.py', 'eligibility.py', 'features.py', 'model_loader.py', 'validation.py', 'ecg_af.py', 'ecg_window.py', 'main.py', 'paths.py']
logic_diff = {f: subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', f'app/backend/healthrisk_api/{f}'], cwd=V2).returncode for f in LOGIC}
svc = subprocess.run(['git', 'diff', '-U0', 'HEAD', '--', 'app/backend/healthrisk_api/service.py'], cwd=V2, capture_output=True, text=True, encoding='utf8').stdout
svc_added = [l for l in svc.splitlines() if l.startswith('+') and not l.startswith('+++')]
svc_removed = [l for l in svc.splitlines() if l.startswith('-') and not l.startswith('---')]

cfg = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
reg = {p: hashlib.sha256((V2 / p).read_bytes()).hexdigest() == h for p, h in cfg['registry_files_sha256'].items()}

res = dict(
    files_before=len(before), files_after=len(after),
    changed=changed, deleted=deleted, added_outside_phase=[k for k in added if not k.startswith('phase_xlvii/')],
    added_in_phase_count=sum(k.startswith('phase_xlvii/') for k in added),
    violations=dict(changed=bad_changed, deleted=bad_deleted, added=bad_added),
    model_logic_files_changed=[f for f, rc in logic_diff.items() if rc != 0],
    service_py_diff=dict(added=svc_added, removed=svc_removed),
    registry_sha_ok=reg,
)
res['ok'] = (not bad_changed and not bad_deleted and not bad_added and not res['model_logic_files_changed']
             and not svc_removed and len(svc_added) == 2 and all(reg.values()))
(R / 'verification47.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: res[k] for k in ('files_before', 'files_after', 'violations', 'model_logic_files_changed', 'registry_sha_ok', 'ok')}, ensure_ascii=False))
print('changed:', len(changed), 'deleted:', len(deleted), 'added outside phase:', len(res['added_outside_phase']))
