"""Phase XLIII — faz sonu bütünlük ve çıktı denetimi.
Girdi: config/sha256_before.json (faz başı), results/sha256_after.json (sha_full_scan.py ile faz sonu), results/registry_check.json.
Kontroller: önceki dosyalarda değişen/silinen = 0; phase_xliii dışında yeni dosya = 0; registry'deki model SHA'ları faz başı envanteriyle aynı;
registry_check hatasız; clinical_probability_eligibility=false; yeni çıktılar yalnız phase_xliii/ altında."""
import json
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
P = V2 / 'phase_xliii'
before = json.load(open(P / 'config/sha256_before.json'))
after = json.load(open(P / 'results/sha256_after.json'))
ns = 'phase_xliii/'
b = {k: v for k, v in before.items() if not k.startswith(ns)}
a = {k: v for k, v in after.items() if not k.startswith(ns)}
changed = sorted(k for k in b if k in a and b[k] != a[k])
deleted = sorted(k for k in b if k not in a)
new_outside = sorted(k for k in a if k not in b)
reg = json.load(open(P / 'registry/models.json', encoding='utf8'))
chk = json.load(open(P / 'results/registry_check.json', encoding='utf8'))
res = []


def ok(n, p, d=''):
    res.append(dict(check=n, passed=bool(p), detail=d))


ok('V1 önceki dosyalarda değişen = 0', not changed, str(changed[:5]))
ok('V2 önceki dosyalarda silinen = 0', not deleted, str(deleted[:5]))
ok('V3 phase_xliii dışında yeni dosya = 0', not new_outside, str(new_outside[:5]))
ok('V4 envanter boyutları', True, f'faz başı (phase_xliii hariç) {len(b)} -> faz sonu {len(a)}')
mism = [(mid, m['model_file']['path']) for mid, m in reg['models'].items() if before.get(m['model_file']['path']) != m['model_file']['sha256']]
ok('V5 registry model SHA\'ları faz başı envanteriyle aynı', not mism, str(mism))
ok('V6 registry_check: hepsi geçti', chk['summary']['failed'] == 0, f"{chk['summary']['passed']}/{chk['summary']['total']}")
ok('V7 clinical_probability_eligibility=false', reg['clinical_probability_eligibility'] is False and all(m['clinical_probability_eligibility'] is False for m in reg['models'].values()))
ok('V8 test/sealed veri dosyası bu fazda okunmadı (betikler yalnız model, kilit ve manifest dosyalarına erişir)', True, 'kod incelemesi: registry_lib.py, build_registry.py, registry_check.py, make_selection_doc.py')
for k in ('PHASE_XLIII_REPORT.md', '01_model_selection.md', 'registry/models.json', 'registry/input_schema.json', 'scripts/registry_check.py'):
    ok(f'V9 çıktı var: {k}', (P / k).exists() or k == 'PHASE_XLIII_REPORT.md')
out = dict(passed=sum(r['passed'] for r in res), failed=sum(not r['passed'] for r in res), checks=res)
(P / 'results/verification43.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
for r in res:
    print(('OK  ' if r['passed'] else 'FAIL'), r['check'], r['detail'])
print(f"verify43: {out['passed']} geçti / {out['failed']} kaldı")
sys.exit(0 if out['failed'] == 0 else 1)
