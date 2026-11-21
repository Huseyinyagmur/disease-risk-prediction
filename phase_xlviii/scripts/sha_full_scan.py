"""V2 altındaki tüm dosyaların SHA256 envanteri (.venv ve __pycache__ hariç; hiçbir faz klasörü hariç tutulmaz).
Kullanım: python sha_full_scan.py <çıktı_json>. Phase XLVI kopyası (XLVIII); .git, node_modules, .venv, __pycache__, dist hariç; hash paralel."""
import hashlib, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
V2 = Path(__file__).resolve().parents[2]
SKIP = {'.venv', '__pycache__', 'node_modules', '.git', 'dist'}
def sha256(p, bs=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b: break
            h.update(b)
    return h.hexdigest()
paths = []
for root, dirs, files in os.walk(V2):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        p = Path(root) / fn
        paths.append((p.relative_to(V2).as_posix(), p))
out = Path(sys.argv[1]).resolve()
with ThreadPoolExecutor(16) as ex:
    hs = list(ex.map(lambda t: sha256(t[1]), paths))
inv = {rel: h for (rel, _), h in zip(paths, hs) if Path(V2 / rel).resolve() != out}
out.write_text(json.dumps(inv, indent=0, sort_keys=True), encoding='utf8')
print('files', len(inv), flush=True)
