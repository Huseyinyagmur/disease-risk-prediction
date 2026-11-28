"""Phase L (XLVIII kopyası): Vitest schema fixture'ını gerçek backend /schema yanıtından üretir (elle yazılmaz).

Önce mevcut fixture ile yeni yanıt, Phase XLVII'de eklenen anahtarlar (ui, form.field_ui_tr) ve metni güncellenen bölüm
başlık/açıklamaları (form.sections) dışında birebir karşılaştırılır; fark varsa yazmadan durur (yalnız sunum değişti).
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlviii/scripts/gen_schema_fixture.py
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))
from fastapi.testclient import TestClient  # noqa: E402
from healthrisk_api import main  # noqa: E402

client = TestClient(main.app)
new = client.get('/schema').json()
fx = V2 / 'app/frontend/src/test/fixtures/schema.json'
# Karşılaştırma tabanı: son commit'teki fixture (yeniden çalıştırmada da aynı taban; tekrarlanabilir)
old = json.loads(subprocess.run(['git', 'show', 'HEAD:app/frontend/src/test/fixtures/schema.json'], cwd=V2,
                                capture_output=True, check=True).stdout.decode('utf8'))


def strip(d):
    d = copy.deepcopy(d)
    d.pop('ui', None)
    d['form'].pop('field_ui_tr', None)
    d['form'].pop('virtual_field_labels_tr', None)   # Phase L: ecg_record etiketi sadeleşti (yalnız sunum)
    d['form']['sections'] = [s['id'] for s in d['form']['sections']]
    return d


a, b = strip(old), strip(new)
if a != b:
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    sys.exit(f'DUR: fixture ile backend sunum dışı alanlarda farklı: {diff}')
fx.write_text(json.dumps(new, ensure_ascii=False, indent=1) + '\n', encoding='utf8')  # orijinal fixture biçimi
res = dict(fixture=str(fx.relative_to(V2)), identical_except=['ui', 'form.field_ui_tr', 'form.sections (metin)'], phase='L: ui metinleri, form.sections açıklamaları, virtual_field_labels_tr.ecg_record',
           section_text_changes=[dict(id=o['id'], old=o, new=n) for o, n in zip(old['form']['sections'], new['form']['sections']) if o != n])
(V2 / 'phase_l/results/schema_fixture_regen.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
print('yazıldı', res['fixture'], 'bölüm metni değişen:', [x['id'] for x in res['section_text_changes']])
