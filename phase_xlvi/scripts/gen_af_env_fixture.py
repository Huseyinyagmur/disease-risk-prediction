"""Phase XLVI — Görev 5 (+ kapanış düzeltmesi): Vitest fixture'larını gerçek backend yanıtından üretir (elle yazılmaz).

AF kilit dosyası yolu var olmayan bir yola çevrilerek (yalnız bu süreçte; dosya sistemi değişmez) "temiz klon" durumu
taklit edilir; üç form için POST /eligibility yanıtı yazılır: boş form (ana: Eksik yaş; Ayrıca: ortam yok), tam form
(ana: Karar verilemez: ortam yok), yaş 95 (ana: Kapsam dışı: yaş; Ayrıca: ortam yok).
Çıktı: app/frontend/src/test/fixtures/eligibility_af_env_missing*.json
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
client = TestClient(main.app)
sys.path.insert(0, str(V2 / 'app/backend/tests'))
from conftest import base_person  # noqa: E402

ENV = 'Octave/ECGDeli AF çalışma ortamı yok'
# (dosya, form, beklenen AF durumu, beklenen ana gerekçe öneki, beklenen additional_reasons)
CASES = [('eligibility_af_env_missing.json', {}, 'MISSING', 'yaş yanıtsız', [ENV]),
         ('eligibility_af_env_missing_full_form.json', base_person(), 'ABSTAIN', ENV, []),
         ('eligibility_af_env_missing_age95.json', {'age_years': 95, 'sex': 'female', 'pregnant': False}, 'OUT_OF_SCOPE',
          'yaş 95', [ENV])]
for name, fields, state, first, extra in CASES:
    r = client.post('/eligibility', json={'fields': fields})
    assert r.status_code == 200
    body = r.json()
    af = [m for m in body['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
    assert af['state'] == state and af['reasons'][0].startswith(first) and af['additional_reasons'] == extra, af
    out = V2 / 'app/frontend/src/test/fixtures' / name
    out.write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('yazıldı', out.relative_to(V2), af['state'], af['reasons'][:1], af['additional_reasons'])
