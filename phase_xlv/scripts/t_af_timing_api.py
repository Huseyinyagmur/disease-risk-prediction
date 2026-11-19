"""AF süre ölçümü — doğrudan API (tarayıcı yok). Canlı backend (varsayılan 127.0.0.1:8000) gerekir.
Her örnek kayıt için N istek sırayla: istemci gidiş-dönüş, sunucu wall_seconds / octave_seconds, yanıt boyutu
(toplam ve display bloğu), JSON ayrıştırma süresi. Yalnız app/frontend/public/samples altındaki iki açık PTB-XL kaydı;
yaş/cinsiyet sentetik. Kullanım: python -B t_af_timing_api.py [çıktı_json] [etiket] [N]"""
import json
import sys
import time
from pathlib import Path

import httpx

P = Path(__file__).resolve().parents[1]
S = P.parent / 'app' / 'frontend' / 'public' / 'samples'
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'results' / 'af_timing_api.json'
label = sys.argv[2] if len(sys.argv) > 2 else 'api'
N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
c = httpx.Client(base_url='http://127.0.0.1:8000', timeout=120)
rows = []
for i in range(N):
    for stem in ('00691_hr', '00165_hr'):
        files = {'header_file': (f'{stem}.hea', (S / f'{stem}.hea').read_bytes()),
                 'signal_file': (f'{stem}.dat', (S / f'{stem}.dat').read_bytes())}
        t0 = time.perf_counter()
        r = c.post('/ecg/af', files=files, data={'age_years': '60', 'sex': 'male'})
        t1 = time.perf_counter()
        body = r.content
        j = json.loads(body)
        t2 = time.perf_counter()
        res = j['result']
        rows.append(dict(label=label, run=i, record=stem, http=r.status_code, status=res['status'],
                         roundtrip_s=round(t1 - t0, 3), json_parse_s=round(t2 - t1, 4),
                         server_wall_s=round(res['pipeline']['wall_seconds'], 3),
                         octave_s=round(res['pipeline']['octave_seconds'], 3),
                         response_bytes=len(body), display_bytes=len(json.dumps(res.get('display'))),
                         upload_bytes=sum(len(v[1]) for v in files.values())))
        print(rows[-1], flush=True)
prev = json.loads(out.read_text(encoding='utf8')) if out.exists() else []
out.write_text(json.dumps(prev + rows, indent=1), encoding='utf8')
