"""Phase XLIV faz sonu denetimi. Girdi: config/sha256_before.json (faz başı), results/sha256_after.json (faz sonu).
Kontroller:
  V1 phase_xliv/ ve app/ DIŞINDA değişen = 0, silinen = 0, yeni = 0 (app/ CLAUDE.md istisnası; .venv/__pycache__ taranmaz)
  V2 registry'deki 13 model dosyasının SHA256'sı faz başı envanteri ve registry ile aynı
  V3 registry/şema ve AF kilit dosyaları faz başıyla aynı
  V4 app/ altında yeni dosyaların listesi (bilgi)
  V5 önceki faz klasörlerinde faz başından sonra yazılmış .pyc / __pycache__ yok (tarama dışı olduğu için ayrıca)
Çıktı: results/verification44.json"""
import json
import os
from pathlib import Path

P44 = Path(__file__).resolve().parents[1]
V2 = P44.parent


def main():
    b = json.loads((P44 / 'config/sha256_before.json').read_text(encoding='utf8'))
    a = json.loads((P44 / 'results/sha256_after.json').read_text(encoding='utf8'))
    mine = lambda k: k.startswith('phase_xliv/') or k.startswith('app/')
    bo = {k: v for k, v in b.items() if not mine(k)}
    ao = {k: v for k, v in a.items() if not mine(k)}
    changed = sorted(k for k in bo if k in ao and bo[k] != ao[k])
    deleted = sorted(k for k in bo if k not in ao)
    new = sorted(k for k in ao if k not in bo)
    reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
    model_rows = []
    for mid, e in reg['models'].items():
        p = e['model_file']['path'].replace('\\', '/')
        model_rows.append(dict(model=mid, path=p, registry=e['model_file']['sha256'] == a.get(p) == b.get(p)))
    locks = ['phase_xliii/registry/models.json', 'phase_xliii/registry/input_schema.json',
             'phase_xxviii/config/af_pipeline_lock.json', 'phase_xxviii/pipeline/af_pipeline_v1.py']
    t0 = (P44 / 'config/sha256_before.json').stat().st_mtime
    pyc = []
    skip_venvs = {str((V2 / x).resolve()) for x in ('.venv', 'app/backend/.venv', 'Focused_Current_Disease_Improvement_2026/.venv')}
    for root, dirs, files in os.walk(V2):
        dirs[:] = [d for d in dirs if str((Path(root) / d).resolve()) not in skip_venvs]
        for fn in files:
            if fn.endswith('.pyc'):
                p = Path(root) / fn
                if p.stat().st_mtime > t0:
                    pyc.append(str(p.relative_to(V2)).replace('\\', '/'))
    res = dict(
        files_before_total=len(b), files_after_total=len(a),
        outside_phase_and_app=dict(before=len(bo), after=len(ao), changed=len(changed), deleted=len(deleted), new=len(new),
                                   changed_list=changed[:50], deleted_list=deleted[:50], new_list=new[:50]),
        V1_pass=not (changed or deleted or new),
        V2_models=model_rows, V2_pass=all(r['registry'] for r in model_rows),
        V3_locks={k: (a.get(k) == b.get(k) and a.get(k) is not None) for k in locks},
        V4_app_files=sorted(k for k in a if k.startswith('app/')),
        V4_phase_files=len([k for k in a if k.startswith('phase_xliv/')]),
        V5_new_pyc_after_phase_start=pyc, V5_pass=not pyc,
        note='phase_xliv/ ve app/ karşılaştırma dışı (CLAUDE.md: faz klasörü + app/ istisnası). .venv ve __pycache__ taranmaz '
             '(XXXIX–XLIII ile aynı kapsam); V5 bytecode için ayrıca bakar.')
    res['V3_pass'] = all(res['V3_locks'].values())
    res['all_pass'] = res['V1_pass'] and res['V2_pass'] and res['V3_pass'] and res['V5_pass']
    (P44 / 'results/verification44.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf8')
    print(json.dumps({k: res[k] for k in ('V1_pass', 'V2_pass', 'V3_pass', 'V5_pass', 'all_pass')}),
          res['outside_phase_and_app'] | dict(changed_list=None, deleted_list=None, new_list=None), len(res['V4_app_files']))


if __name__ == '__main__':
    main()
