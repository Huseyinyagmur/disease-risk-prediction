"""AF süre ayrıştırması — sunucusuz, kilitli pipeline işlevleriyle (değiştirilmeden; dosya yolundan içe aktarılır).
Ölçülen: (a) Octave çıplak başlatma (--eval "1"), (b) Octave + pkg load (signal, statistics, image), (c) read_first10s,
run_ecgdeli (wall ve Octave içi toc), features_from_mat. DENEY: aynı ölçüm OPENBLAS/OMP iş parçacığı = 1 ortamıyla da
yapılır ve 10 feature'ın varsayılanla birebir olup olmadığı kontrol edilir (uygulamaya ALINMAZ; yalnız teşhis).
Geçici dosyalar sistem temp'inde, sonunda silinir. Kullanım: python -B t_af_timing_octave.py [çıktı_json] [N]"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

P = Path(__file__).resolve().parents[1]
V2 = P.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(V2 / 'app' / 'backend'))
from healthrisk_api.ecg_window import read_first10s  # noqa: E402

spec = importlib.util.spec_from_file_location('af_pipeline_v1_locked', V2 / 'phase_xxviii/pipeline/af_pipeline_v1.py')
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)
sys.path.insert(0, str(pl.WFDB_VENDOR))
S = V2 / 'app' / 'frontend' / 'public' / 'samples'
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'results' / 'af_timing_octave.json'
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2
ENV0 = dict(os.environ)
MODES = {'default': {}, 'blas_1thread': {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}}


def octave_start(code):
    env = dict(os.environ, OCTAVE_HOME=str(pl.OCTAVE_EXE.parent.parent))
    t = time.perf_counter()
    subprocess.run([str(pl.OCTAVE_EXE), '--no-history', '--no-init-file', '--no-site-file', '--quiet', '--eval', code],
                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000, check=False)
    return round(time.perf_counter() - t, 3)


rows, feats_by = [], {}
for i in range(N):
    for mode, extra in MODES.items():
        os.environ.clear(); os.environ.update(ENV0); os.environ.update(extra)
        row = dict(run=i, mode=mode, octave_bare_s=octave_start('1'),
                   octave_pkgload_s=octave_start('pkg load signal;pkg load statistics;pkg load image;'))
        for stem in ('00691_hr', '00165_hr'):
            tmp = Path(tempfile.mkdtemp(prefix='hr_t45_'))
            try:
                shutil.copy(S / f'{stem}.hea', tmp); shutil.copy(S / f'{stem}.dat', tmp)
                t0 = time.perf_counter()
                sig = read_first10s(tmp / stem, pl)
                t1 = time.perf_counter()
                st = pl.run_ecgdeli(sig, tmp / 'work', 'rec', timeout=300)
                t2 = time.perf_counter()
                f = pl.features_from_mat(tmp / 'work' / 'rec.mat')
                t3 = time.perf_counter()
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            feats = {k: f[k] for k in pl.FEATURES}
            feats_by.setdefault((stem, mode), feats)
            row[stem] = dict(read_s=round(t1 - t0, 3), ecgdeli_wall_s=round(t2 - t1, 3), octave_toc_s=round(st['seconds'], 3),
                             features_s=round(t3 - t2, 3), total_s=round(t3 - t0, 3),
                             features_equal_default=feats == feats_by.get((stem, 'default')))
        rows.append(row)
        print(json.dumps(row), flush=True)
os.environ.clear(); os.environ.update(ENV0)
out.write_text(json.dumps(dict(rows=rows, note='Teşhis ölçümü; blas_1thread uygulamaya alınmadı.'), indent=1), encoding='utf8')
