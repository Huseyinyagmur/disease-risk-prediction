"""Phase XLIV güncellemesi — tüm pytest paketi + dört senaryo grubunun ayrı raporu (danışman isteği 7d).
Çıktılar: results/pytest_junit.xml (tam paket), results/pytest_<grup>.xml, results/test_scenarios.json, logs/pytest_*.log.
Kullanım (app venv): python -B -I t5_run_tests.py"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

P44 = Path(__file__).resolve().parents[1]
BACKEND = P44.parent / 'app' / 'backend'
GROUPS = [('scenario_normal', 'Normal girdi'), ('scenario_missing', 'Eksik girdi'), ('scenario_unit', 'Birim hatası'),
          ('scenario_out_of_scope', 'Kapsam dışı veri')]


def run(args, name):
    xml = P44 / 'results' / f'pytest_{name}.xml'
    r = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '-q', '-rxX', *args,
                        f'--junitxml={xml}'], cwd=str(BACKEND), capture_output=True, text=True, encoding='utf8', errors='replace')
    (P44 / 'logs' / f'pytest_{name}.log').write_text(r.stdout + r.stderr, encoding='utf8')
    root = ET.parse(xml).getroot()
    cases = []
    for tc in root.iter('testcase'):
        st = 'passed'
        for ch in tc:
            if ch.tag in ('failure', 'error'):
                st = 'failed'
            elif ch.tag == 'skipped':
                st = 'xfailed' if 'xfail' in (ch.get('type', '') + ch.get('message', '')).lower() or ch.get('type') == 'pytest.xfail' else 'skipped'
        cases.append(dict(test=f"{tc.get('classname').split('.')[-1]}::{tc.get('name')}", status=st))
    summ = {k: sum(c['status'] == k for c in cases) for k in ('passed', 'failed', 'xfailed', 'skipped')}
    return dict(returncode=r.returncode, summary=summ, n=len(cases), tail=r.stdout.strip().splitlines()[-1], cases=cases)


def main():
    out = dict(full=run(['tests'], 'full'), groups={})
    for m, label in GROUPS:
        out['groups'][m] = dict(label=label, **run(['tests', '-m', m], m))
    out['full'].pop('cases')
    (P44 / 'results' / 'test_scenarios.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf8')
    print('TAM:', out['full']['tail'])
    for m, g in out['groups'].items():
        print(g['label'], g['summary'], g['n'])


if __name__ == '__main__':
    main()
