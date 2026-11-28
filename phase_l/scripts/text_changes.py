"""Phase L: app_config.json arayüz metinlerinin önce/sonra tablosu (HEAD'deki dosya ile çalışma kopyası).
Kullanım (V2 kökünden): python -B phase_l/scripts/text_changes.py  -> phase_l/03_text_changes.md"""
import json
import subprocess
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
old = json.loads(subprocess.run(['git', 'show', 'HEAD:app/backend/config/app_config.json'], cwd=V2, capture_output=True,
                                check=True).stdout.decode('utf8'))
new = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))


def flat(d, pre=''):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f'{pre}.{k}' if pre else k))
    elif isinstance(d, list):
        if all(isinstance(x, dict) and ('id' in x or 'term' in x or 'module_label' in x) for x in d) and d:
            for x in d:
                key = x.get('id') or x.get('term') or x.get('module_label')
                out.update(flat(x, f'{pre}[{key}]'))
        else:
            out[pre] = json.dumps(d, ensure_ascii=False)
    else:
        out[pre] = d if isinstance(d, str) else json.dumps(d, ensure_ascii=False)
    return out


a, b = flat(old), flat(new)
esc = lambda s: str(s).replace('|', '\\|').replace('\n', ' ')  # noqa: E731
rows_changed = [(k, a[k], b[k]) for k in sorted(a) if k in b and a[k] != b[k]]
rows_added = [(k, b[k]) for k in sorted(b) if k not in a]
rows_removed = [(k, a[k]) for k in sorted(a) if k not in b]
L = ['# Phase L — değişen arayüz metinleri (app_config.json)', '',
     'Kaynak: `scripts/text_changes.py` (HEAD ile çalışma kopyası karşılaştırması; elle yazılmadı). Model, eşik, registry, '
     'şema ve uygunluk mantığı bu dosyada değil; yalnız sunum metinleri.', '',
     f'Değişen: {len(rows_changed)} · eklenen: {len(rows_added)} · kaldırılan: {len(rows_removed)}', '',
     '## Değişen metinler', '', '| anahtar | önce | sonra |', '|---|---|---|']
L += [f'| `{k}` | {esc(x)} | {esc(y)} |' for k, x, y in rows_changed]
L += ['', '## Kaldırılan anahtarlar', '', '| anahtar | önceki değer |', '|---|---|']
L += [f'| `{k}` | {esc(x)} |' for k, x in rows_removed]
L += ['', '## Eklenen metinler ve kurallar', '', '| anahtar | değer |', '|---|---|']
L += [f'| `{k}` | {esc(x)} |' for k, x in rows_added]
(V2 / 'phase_l/03_text_changes.md').write_text('\n'.join(L) + '\n', encoding='utf8')
print('değişen', len(rows_changed), 'eklenen', len(rows_added), 'kaldırılan', len(rows_removed))
