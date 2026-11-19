"""Phase XLV test özetleri: Playwright JSON (senaryo grubu × hastalık), Vitest ve backend pytest JUnit XML.
Kullanım: python -B summarize_tests.py  ->  phase_xlv/results/test_summary.json. Yalnız rapor dosyalarını okur."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P / 'results'
GROUPS = ['@normal', '@eksik', '@birim', '@kapsam', '@gizlilik']


def walk(suite, titles=()):
    t = titles + ((suite.get('title') or ''),)
    for s in suite.get('specs', []):
        for test in s['tests']:
            res = test['results'][-1] if test['results'] else {}
            yield dict(title=' › '.join(x for x in t + (s['title'],) if x), status=res.get('status', 'skipped'),
                       duration_s=round(res.get('duration', 0) / 1000, 1))
    for c in suite.get('suites', []):
        yield from walk(c, t)


def pw(path):
    d = json.loads(path.read_text(encoding='utf8'))
    tests = [x for s in d['suites'] for x in walk(s)]
    out = {}
    for g in GROUPS:
        ts = [t for t in tests if g in t['title']]
        dis = {}
        for t in ts:
            k = 'AF' if re.search(r'\bAF\b', t['title']) else 'fibrozis' if 'fibrozis' in t['title'].lower() else 'genel'
            dd = dis.setdefault(k, dict(passed=0, total=0))
            dd['total'] += 1
            dd['passed'] += t['status'] == 'passed'
        out[g] = dict(passed=sum(t['status'] == 'passed' for t in ts), total=len(ts), by_disease=dis,
                      tests=[(t['title'].split(' › ')[-1], t['status'], t['duration_s']) for t in ts])
    return dict(total=len(tests), passed=sum(t['status'] == 'passed' for t in tests), groups=out)


def junit(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
    n = f = e = s = 0
    for su in suites:
        n += int(su.get('tests', 0)); f += int(su.get('failures', 0)); e += int(su.get('errors', 0)); s += int(su.get('skipped', 0))
    return dict(tests=n, failures=f, errors=e, skipped=s, passed=n - f - e - s)


out = dict(playwright=pw(R / 'playwright_results.json'), vitest=junit(R / 'vitest_junit.xml'),
           backend_pytest=junit(R / 'pytest_backend_full.xml'))
rep = P / 'logs' / 'pw_repeat_run' / 'playwright_results.json'
if rep.exists():
    out['playwright_repeat'] = {k: v for k, v in pw(rep).items() if k != 'groups'}
(R / 'test_summary.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: (v if k != 'playwright' else {g: (x['passed'], x['total'], x['by_disease']) for g, x in v['groups'].items()})
                  for k, v in out.items()}, ensure_ascii=False))
