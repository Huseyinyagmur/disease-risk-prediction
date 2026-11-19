"""Phase XLIII registry_check'in yeniden çalıştırılması (Phase XLIV) + şema v2 kontrolleri.

phase_xliii/scripts/registry_check.py SALT OKUNUR kullanılır: kayıt kontrolleri (R1–R13) içe aktarılan record_checks ile,
model kontrolleri (C1–C8) orijinal betiğin --worker modunda, modelin kayıtlı venv'inde ayrı süreçte çalışır (worker dosya
yazmaz). Orijinal main() ÇAĞRILMAZ (phase_xliii/results ve logs'a yazardı). Çıktı yalnız phase_xliv/results ve logs.
Ek S1–S6: şema v2'nin v1'e ve models.json'a göre tutarlılığı, app dönüşümleriyle eşleşmesi.
Kullanım (app venv): python -B -I registry_check44.py"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
P44 = Path(__file__).resolve().parents[1]
V2 = P44.parent
RC = V2 / 'phase_xliii/scripts/registry_check.py'


def load_rc():
    sys.path.insert(0, str(RC.parent))
    spec = importlib.util.spec_from_file_location('registry_check_xliii', RC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ok(name, passed, detail=''):
    return dict(check=name, passed=bool(passed), detail=detail)


def schema_v2_checks(reg, v1, v2):
    sys.path.insert(0, str(V2 / 'app/backend'))
    from healthrisk_api import transforms as T
    res = []
    v1sha = hashlib.sha256((V2 / 'phase_xliii/registry/input_schema.json').read_bytes()).hexdigest()
    res.append(ok('S1 v2.base_schema SHA == v1 dosyası', v2['base_schema']['sha256'] == v1sha, v1sha[:16]))
    v2sha = hashlib.sha256((P44 / 'registry/input_schema_v2.json').read_bytes()).hexdigest()
    res.append(ok('S2 input_schema_v2.sha256 == dosya', (P44 / 'registry/input_schema_v2.sha256').read_text().strip() == v2sha, v2sha[:16]))
    diffs = set()
    for mid, m in reg['models'].items():
        u = {x['model_feature']: x for x in v2['model_usage'][mid]}
        assert [f['name'] for f in m['features']] == [x['model_feature'] for x in v2['model_usage'][mid]], mid
        for f in m['features']:
            if u[f['name']]['transform'] != f['transform']:
                diffs.add((mid, f['name'], f['transform'], u[f['name']]['transform']))
            assert u[f['name']]['input_field'] == f['input_field']
    listed = {(c['model'], c['feature'], c['old_transform'], c['new_transform']) for c in v2['changes_from_v1']}
    res.append(ok('S3 v2 model_usage ↔ models.json farkları == changes_from_v1 (birebir; feature sırası/input_field aynı)',
                  diffs == listed and all(c['reason'] and c['evidence'] for c in v2['changes_from_v1']), f'{len(diffs)} fark'))
    res.append(ok('S4 v2 dönüşüm kümesi == app TRANSFORMS', set(v2['transforms']) == set(T.TRANSFORMS),
                  str(sorted(set(v2['transforms']) ^ set(T.TRANSFORMS)))))
    newf = set(v2['fields']) - set(v1['fields'])
    res.append(ok('S5 v2 alanları v1 ⊇ ve yeni alanlar yalnız 3 uygunluk sorusu', set(v1['fields']) <= set(v2['fields'])
                  and newf == {'pregnant', 'told_weak_failing_kidneys', 'on_dialysis'}, str(sorted(newf))))
    res.append(ok('S6 v2 policy: clinical_probability_eligibility=false, v2_principle ve pregnancy maddeleri',
                  v2['policy']['clinical_probability_eligibility'] is False and 'v2_principle' in v2['policy'] and 'pregnancy' in v2['policy'], ''))
    return res


def main():
    rc = load_rc()
    L = rc.L
    reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
    v1 = json.loads((V2 / 'phase_xliii/registry/input_schema.json').read_text(encoding='utf8'))
    v2 = json.loads((P44 / 'registry/input_schema_v2.json').read_text(encoding='utf8'))
    out = dict(phase='XLIV', source_script='phase_xliii/scripts/registry_check.py (salt okunur; worker modu + record_checks)',
               record_checks_v1=rc.record_checks(reg, v1), schema_v2_checks=schema_v2_checks(reg, v1, v2), models={})
    for mid, e in reg['models'].items():
        py = L.VENVS[rc.venv_of(e)]
        r = subprocess.run([str(py), '-B', '-I', str(RC), '--worker', mid], capture_output=True, text=True, encoding='utf-8')
        out['models'][mid] = (json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0
                              else [ok('WORKER başarısız', False, (r.stderr or '')[-800:])])
    allc = out['record_checks_v1'] + out['schema_v2_checks'] + [c for v in out['models'].values() for c in v]
    n_pass = sum(c['passed'] for c in allc)
    out['summary'] = dict(passed=n_pass, failed=len(allc) - n_pass, total=len(allc),
                          xliii_equivalent=dict(passed=sum(c['passed'] for c in out['record_checks_v1']) + sum(c['passed'] for v in out['models'].values() for c in v),
                                                total=len(out['record_checks_v1']) + sum(len(v) for v in out['models'].values())),
                          failed_checks=[c for c in allc if not c['passed']])
    (P44 / 'results/registry_check44.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    lines = [f'{m}: {sum(c["passed"] for c in v)}/{len(v)}' for m, v in out['models'].items()]
    lines.append(f'KAYIT (R1–R13, v1 şema): {sum(c["passed"] for c in out["record_checks_v1"])}/{len(out["record_checks_v1"])}')
    lines.append(f'ŞEMA v2 (S1–S6): {sum(c["passed"] for c in out["schema_v2_checks"])}/{len(out["schema_v2_checks"])}')
    lines.append(f'XLIII eşdeğeri: {out["summary"]["xliii_equivalent"]["passed"]}/{out["summary"]["xliii_equivalent"]["total"]}')
    lines.append(f'TOPLAM: {n_pass} geçti / {len(allc) - n_pass} kaldı (toplam {len(allc)})')
    lines += ['KALDI: ' + c['check'] + ' | ' + c['detail'][:200] for c in out['summary']['failed_checks']]
    txt = '\n'.join(lines)
    print(txt)
    (P44 / 'logs/registry_check44.log').write_text(txt + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
