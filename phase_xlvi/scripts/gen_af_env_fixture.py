"""Phase XLVI — Görev 5: Vitest fixture'ı gerçek backend yanıtından üretir (elle yazılmaz).

AF kilit dosyası yolu var olmayan bir yola çevrilerek (yalnız bu süreçte; dosya sistemi değişmez) "temiz klon" durumu
taklit edilir; boş form için POST /eligibility yanıtı yazılır.
Çıktı: app/frontend/src/test/fixtures/eligibility_af_env_missing.json
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlvi/scripts/gen_af_env_fixture.py
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))

import healthrisk_api.ecg_af as A  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from healthrisk_api import main  # noqa: E402
from healthrisk_api.service import Service  # noqa: E402

A.AF_LOCK = A.V2 / 'yok' / 'af_pipeline_lock.json'
svc = Service()
assert not svc.af.enabled
main._SERVICE = svc
r = TestClient(main.app).post('/eligibility', json={'fields': {}})
assert r.status_code == 200
body = r.json()
af = [m for m in body['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
assert af['state'] == 'ABSTAIN' and af['reasons'][0] == 'Octave/ECGDeli AF çalışma ortamı yok'
out = V2 / 'app/frontend/src/test/fixtures/eligibility_af_env_missing.json'
out.write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('yazıldı', out.relative_to(V2), af['state'], af['reasons'])
