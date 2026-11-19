"""Temiz klon doğrulaması: GitHub deposu boş bir klasöre klonlanmış ve app/backend/.venv requirements.lock ile kurulmuş
olmalı. Bu betik KLONUN İÇİNDEN, klonun venv'iyle çalıştırılır:
    <klon>/app/backend/.venv/Scripts/python.exe -B <bu_betik> <klon_kökü> <çıktı_json> [port]
Yapılanlar: (1) registry'deki 13 model dosyası klonda var mı ve SHA256 registry ile aynı mı; (2) 13 modelin tamamı klonun
kendi model_loader'ı ile yüklenebiliyor mu (tahmin yok); (3) klonda run_server.py başlatılır, /health okunur, sunucu
kapatılır. Hiçbir dosya yazılmaz (yalnız çıktı JSON'u)."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
port = int(sys.argv[3]) if len(sys.argv) > 3 else 8790
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / 'app' / 'backend'))

reg = json.loads((root / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
res = dict(clone_root=str(root), models={})
from healthrisk_api.model_loader import load_model  # noqa: E402  (klonun kodu)

for mid, e in reg['models'].items():
    p = root / e['model_file']['path']
    r = dict(path=e['model_file']['path'], app_visible=bool(e.get('app_visible')), exists=p.exists())
    if p.exists():
        r['sha256_matches_registry'] = hashlib.sha256(p.read_bytes()).hexdigest() == e['model_file']['sha256']
        try:
            obj = load_model(e['model_file']['path'], e['runtime'].get('extra_sys_path_for_pickle'))
            r['loads'] = True
            r['type'] = type(obj).__name__
        except Exception as ex:  # yükleme hatası raporlanır
            r['loads'] = False
            r['error'] = f'{type(ex).__name__}: {ex}'[:300]
    res['models'][mid] = r

srv = subprocess.Popen([sys.executable, '-B', 'run_server.py', '--port', str(port)], cwd=root / 'app' / 'backend',
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    h = None
    for _ in range(240):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as resp:
                h = json.loads(resp.read().decode('utf8'))
                break
        except Exception:
            time.sleep(0.5)
    res['health'] = None if h is None else dict(
        status=h['status'], schema_version=h['schema_version'], packages_ok=h['packages']['ok'],
        registry_problems=h['registry']['problems'],
        models={m['model_id']: dict(enabled=m['enabled'], problems=m['problems']) for m in h['models']},
        disabled_models=h['disabled_models'], af_pipeline=dict(enabled=h['af_pipeline']['enabled'],
                                                               problems=h['af_pipeline']['problems']))
finally:
    srv.terminate()
    srv.wait(timeout=30)

m = res['models']
res['summary'] = dict(n_registry=len(m), n_files_present=sum(x['exists'] for x in m.values()),
                      n_sha_match=sum(bool(x.get('sha256_matches_registry')) for x in m.values()),
                      n_loadable=sum(bool(x.get('loads')) for x in m.values()))
if res['health']:
    hm = res['health']['models']
    res['summary'].update(health_app_visible=len(hm), health_enabled=sum(v['enabled'] for v in hm.values()),
                          health_disabled=res['health']['disabled_models'])
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps(res['summary'], ensure_ascii=False))
print('AF:', res['health']['af_pipeline'] if res['health'] else 'health alınamadı')
