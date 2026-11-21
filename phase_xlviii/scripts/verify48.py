"""Phase XLVIII son doğrulama: SHA256 faz başı/sonu karşılaştırması ve "model mantığı değişmedi" denetimi.

1) sha256_before.json ile yeni tarama (sha256_after.json). İzin verilen: app/ (uygulama istisnası) ve phase_xlviii/.
   Önceki faz klasörleri, modeller, registry, ham veri: değişen/silinen = 0; faz dışı yeni dosya = 0.
2) Model/eşik/şema/uygunluk mantığı dosyaları (service, transforms, eligibility, features, model_loader, validation,
   ecg_*, paths) son commit'e göre DEĞİŞMEDİ. main.py farkı yalnız EKLEMEdir (asistan uç noktası, /health anahtarı,
   KNOWN_PATHS); silinen satırlar listelenir.
3) Kilitli registry/şema dosyaları app_config'teki SHA256 ile aynı; app_config'te ui.text_tr dışı değişiklik yok.
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlviii/scripts/verify48.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
R = V2 / 'phase_xlviii/results'
subprocess.run([sys.executable, '-B', str(V2 / 'phase_xlviii/scripts/sha_full_scan.py'), str(R / 'sha256_after.json')], check=True)
before = json.loads((R / 'sha256_before.json').read_text(encoding='utf8'))
after = json.loads((R / 'sha256_after.json').read_text(encoding='utf8'))

ALLOWED = ('app/', 'phase_xlviii/')
changed = sorted(k for k in before if k in after and before[k] != after[k])
deleted = sorted(k for k in before if k not in after)
added = sorted(k for k in after if k not in before)
APPROVED = {'.gitignore', '.gitattributes'}   # .gitignore: kullanıcı onayı (logs, artifacts). .gitattributes: commit sırasında Claude ekledi (yalnız ekleme; kilitli KB/indeks satır sonu korunması), kullanıcıya bildirildi
bad_changed = [k for k in changed if not k.startswith(ALLOWED) and k not in APPROVED]
bad_deleted = [k for k in deleted if not k.startswith('phase_xlviii/')]
bad_added = [k for k in added if not k.startswith(ALLOWED)]

LOGIC = ['service.py', 'transforms.py', 'eligibility.py', 'features.py', 'model_loader.py', 'validation.py', 'ecg_af.py',
         'ecg_window.py', 'paths.py']
logic_diff = {f: subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', f'app/backend/healthrisk_api/{f}'], cwd=V2).returncode
              for f in LOGIC}
md = subprocess.run(['git', 'diff', '-U0', 'HEAD', '--', 'app/backend/healthrisk_api/main.py'], cwd=V2, capture_output=True,
                    text=True, encoding='utf8').stdout
main_removed = [x for x in md.splitlines() if x.startswith('-') and not x.startswith('---')]

cfg = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
old = json.loads(subprocess.run(['git', 'show', 'HEAD:app/backend/config/app_config.json'], cwd=V2, capture_output=True,
                                check=True).stdout.decode('utf8'))
cfg_diff_keys = sorted(k for k in set(cfg) | set(old) if cfg.get(k) != old.get(k))
ui_diff = sorted(k for k in set(cfg['ui']) | set(old['ui']) if cfg['ui'].get(k) != old['ui'].get(k))
text_changed = sorted(k for k in old['ui']['text_tr'] if cfg['ui']['text_tr'].get(k) != old['ui']['text_tr'][k])
text_added = sorted(k for k in cfg['ui']['text_tr'] if k not in old['ui']['text_tr'])
reg = {p: hashlib.sha256((V2 / p).read_bytes()).hexdigest() == h for p, h in cfg['registry_files_sha256'].items()}

res = dict(files_before=len(before), files_after=len(after), changed=changed, deleted=deleted,
           added_outside_phase=[k for k in added if not k.startswith('phase_xlviii/')],
           added_in_phase_count=sum(k.startswith('phase_xlviii/') for k in added),
           violations=dict(changed=bad_changed, deleted=bad_deleted, added=bad_added),
           model_logic_files_changed=[f for f, rc in logic_diff.items() if rc != 0],
           main_py_removed_lines=main_removed,
           app_config=dict(top_level_changed=cfg_diff_keys, ui_changed=ui_diff, text_tr_changed=text_changed,
                           text_tr_added=text_added),
           registry_sha_ok=reg)
res['ok'] = (not bad_changed and not bad_deleted and not bad_added and not res['model_logic_files_changed']
             and cfg_diff_keys == ['ui'] and ui_diff == ['text_tr'] and not text_changed and all(reg.values()))
(R / 'verification48.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: res[k] for k in ('files_before', 'files_after', 'violations', 'model_logic_files_changed',
                                      'main_py_removed_lines', 'app_config', 'registry_sha_ok', 'ok')}, ensure_ascii=False, indent=1))
print('changed:', len(changed), 'deleted:', len(deleted), 'added outside phase:', len(res['added_outside_phase']))
