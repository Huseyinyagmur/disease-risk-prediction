"""Phase XLIX doğrulama: SHA256 bütünlüğü + model dosyaları + model_results.csv ↔ registry çapraz kontrolü.
Kullanım (sha256_after.json alındıktan sonra): .venv/Scripts/python.exe -B phase_xlix/scripts/verify49.py
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
P = V2 / 'phase_xlix'
before = json.loads((P / 'results/sha256_before.json').read_text(encoding='utf8'))
after = json.loads((P / 'results/sha256_after.json').read_text(encoding='utf8'))
inphase = lambda k: k.startswith('phase_xlix/')
changed = sorted(k for k in before if k in after and before[k] != after[k] and not inphase(k))
deleted = sorted(k for k in before if k not in after and not inphase(k))
new_out = sorted(k for k in after if k not in before and not inphase(k))
checks = {}
checks['V1_prior_changed_0'] = (len(changed) == 0, changed[:20])
checks['V1_prior_deleted_0'] = (len(deleted) == 0, deleted[:20])
checks['V1_new_outside_phase_0'] = (len(new_out) == 0, new_out[:20])
checks['V1_app_unchanged'] = (not any(k.startswith('app/') for k in changed + deleted + new_out), None)

reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))['models']
bad = []
for mid, m in reg.items():
    p = V2 / m['model_file']['path']
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != m['model_file']['sha256']:
        bad.append(mid)
checks['V2_model_sha_eq_registry_13'] = (len(bad) == 0 and len(reg) == 13, bad)

# model_results.csv ↔ registry evidence (nokta değerleri, 3 basamak; dm_B FPR/AUC çift yuvarlama notu XLVI'da)
mr = pd.read_csv(P / 'model_results.csv')
tiermap = {'internal_test': 'internal_test', 'temporal': 'temporal', 'external': 'external'}
mism, n = [], 0
for _, r in mr.iterrows():
    k = tiermap.get(r.kanit_tier)
    ev = reg[r.model_id]['evidence'].get(k) if k else None
    if not ev or 'recall' not in ev:
        continue
    for col, key in [('R', 'recall'), ('FPR', 'fpr'), ('AUC', 'auc'), ('P', 'precision')]:
        e = ev.get(key)
        if not e or pd.isna(r[col]):
            continue
        n += 1
        if abs(round(r[col], 3) - e['value']) > 0.0015:
            mism.append((r.model_id, r.kanit_tier, col, r[col], e['value']))
checks['V3_model_results_vs_registry'] = (len(mism) == 0, {'compared': n, 'mismatch': mism})
checks['V4_test_xml_backend'] = ('failures="0"' in (P / 'results/pytest_backend_full.xml').read_text(encoding='utf8')
                                 and 'errors="0"' in (P / 'results/pytest_backend_full.xml').read_text(encoding='utf8'), None)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'files_before': len(before), 'files_after': len(after),
       'phase_xlix_new_files': sorted(k for k in after if inphase(k) and k not in before),
       'checks': {k: {'pass': v[0], 'detail': v[1]} for k, v in checks.items()},
       'passed': sum(v[0] for v in checks.values()), 'failed': sum(not v[0] for v in checks.values())}
(P / 'results/verification49.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: v for k, v in out.items() if k != 'phase_xlix_new_files'}, ensure_ascii=False, indent=1))
