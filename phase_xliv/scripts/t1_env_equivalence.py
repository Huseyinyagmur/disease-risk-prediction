"""Phase XLIV Görev 1 — app venv eşdeğerlik testi.

Her registry modeli için 200 SENTETİK (registry sınırları/izinli kategorileri içinde) girdi üretilir (sabit seed).
Model, (a) registry'de kayıtlı venv'inde ve (b) app venv'inde (app/backend/.venv) AYRI süreçte, app'in kendi
yükleyicisiyle (healthrisk_api.model_loader) yüklenip predict_proba[:,1] hesaplanır. Ölçüt: |Δ| ≤ 1e-9 (tüm satırlar).

Olasılık değerleri raporlanmaz ve faz klasörüne yazılmaz: ham diziler yalnız geçici klasörde (argv) tutulur;
faz klasörüne yalnız fark istatistikleri yazılır. Test/mühürlü veri okunmaz.

Kullanım (app venv ile):  python -B -I t1_env_equivalence.py <geçici_klasör>
Worker modu (iç kullanım): python -B -I t1_env_equivalence.py worker <model_id> <girdi.json> <çıktı.npy>
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P44 = HERE.parent
V2 = P44.parent
BACKEND = V2 / 'app' / 'backend'
APP_PY = BACKEND / '.venv' / 'Scripts' / 'python.exe'
SEED = 20261119
N = 200
TOL = 1e-9
ROOT_VENV_MODELS = ['cad_DEVICE', 'dm_A', 'dm_B', 'anemia_LR16', 'osteo_final', 'ckd_A', 'ckd_B']


def venv_python(rel):
    return V2 / rel / 'Scripts' / 'python.exe'


def synth(entry, idx):
    import numpy as np
    rng = np.random.default_rng(SEED + idx)
    rows = []
    for _ in range(N):
        r = {}
        for f in entry['features']:
            if f['type'] == 'numeric':
                lo, hi = f['allowed_range']
                v = float(rng.uniform(lo, hi))
                # osteo age_last_period: eğitimdeki yapısal boşluk yolunu da sına (%25 null)
                if f['transform'] == 'osteo_age_last_period' and rng.random() < 0.25:
                    v = None
                r[f['name']] = v
            else:
                vals = f['allowed_values']
                v = vals[int(rng.integers(0, len(vals)))]
                r[f['name']] = float(v) if f['model_dtype'] == 'float' else str(v)
        rows.append(r)
    return rows


def worker(mid, inp, out):
    sys.path.insert(0, str(BACKEND))
    import importlib
    import numpy as np
    import pandas as pd
    from healthrisk_api.model_loader import load_model, sha256_file
    reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
    e = reg['models'][mid]
    mp = V2 / e['model_file']['path']
    sha_ok = sha256_file(mp) == e['model_file']['sha256']
    m = load_model(e['model_file']['path'], e['runtime']['extra_sys_path_for_pickle'])
    names = [f['name'] for f in e['features']]
    rows = json.loads(Path(inp).read_text(encoding='utf8'))
    df = pd.DataFrame(rows, columns=names)
    for f in e['features']:
        if f['model_dtype'] == 'float':
            df[f['name']] = df[f['name']].astype(float)
        else:
            df[f['name']] = df[f['name']].astype(object)
    p = np.asarray(m.predict_proba(df))[:, 1].astype(float)
    np.save(out, p)
    vers = {}
    for k in ['numpy', 'pandas', 'scipy', 'sklearn', 'joblib', 'lightgbm', 'xgboost', 'catboost', 'imblearn']:
        try:
            vers[k] = importlib.import_module(k).__version__
        except Exception:
            vers[k] = None
    print(json.dumps(dict(model=mid, sha_ok=sha_ok, python=sys.version.split()[0], executable=sys.executable,
                          versions=vers, n=int(len(p)), finite=bool(np.isfinite(p).all()))))


def run_worker(py, mid, inp, out):
    r = subprocess.run([str(py), '-B', '-I', str(Path(__file__).resolve()), 'worker', mid, str(inp), str(out)],
                       capture_output=True, text=True, encoding='utf8', errors='replace', timeout=600)
    if r.returncode != 0:
        return None, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1]), r.stderr[-500:]


def main(tmp):
    import numpy as np
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
    out_dir = P44 / 'results' / 'env_equiv_inputs'
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for idx, (mid, e) in enumerate(reg['models'].items()):
        data = synth(e, idx)
        inp = out_dir / f'{mid}_synthetic200.json'
        inp.write_text(json.dumps(data, allow_nan=False), encoding='utf8')
        reg_py = venv_python(e['runtime']['required_venv'])
        a, err_a = run_worker(reg_py, mid, inp, tmp / f'{mid}_registered.npy')
        b, err_b = run_worker(APP_PY, mid, inp, tmp / f'{mid}_app.npy')
        row = dict(model=mid, scope='kok_.venv (görev kapsamı)' if mid in ROOT_VENV_MODELS else 'Focused venv (ek kontrol)',
                   registered_venv=e['runtime']['required_venv'], n=N)
        if a is None or b is None:
            row.update(status='HATA', error_registered=err_a if a is None else '', error_app=err_b if b is None else '')
        else:
            pa, pb = np.load(tmp / f'{mid}_registered.npy'), np.load(tmp / f'{mid}_app.npy')
            d = np.abs(pa - pb)
            row.update(sha_ok_registered=a['sha_ok'], sha_ok_app=b['sha_ok'],
                       versions_registered=a['versions'], versions_app=b['versions'],
                       finite=a['finite'] and b['finite'], max_abs_delta=float(d.max()), mean_abs_delta=float(d.mean()),
                       n_bitwise_equal=int((pa == pb).sum()), n_le_tol=int((d <= TOL).sum()),
                       status='ESDEGER' if bool((d <= TOL).all()) and a['sha_ok'] and b['sha_ok'] else 'ESDEGER_DEGIL',
                       stderr_app_tail=err_b.strip()[-300:])
        rows.append(row)
        print(mid, row['status'], row.get('max_abs_delta'), flush=True)
    res = dict(seed=SEED, n_per_model=N, tolerance=TOL, app_python=str(APP_PY.relative_to(V2)),
               note='Sentetik girdi (registry allowed_range/allowed_values içinde, düzgün dağılım). Olasılıklar raporlanmaz; '
                    'yalnız iki venv arasındaki fark istatistikleri.', models=rows)
    (P44 / 'results' / 'env_equivalence.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf8')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        worker(*sys.argv[2:5])
    else:
        main(sys.argv[1])
