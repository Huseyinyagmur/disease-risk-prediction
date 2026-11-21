"""Phase XLVI kapanış — AF çalışma ortamı (Octave + ECGDeli + kilitli pipeline) kurulum doğrulaması.

Kurulumdan sonra her dosyanın SHA256'sını phase_xxviii/config/af_pipeline_lock.json ile karşılaştırır (sunucunun
başlangıç denetimiyle aynı tanımlar; ağaç özeti = healthrisk_api.ecg_af._tree_hash). Dosya yazmaz/değiştirmez
(--out verilirse yalnız o JSON yazılır). Sonda sunucunun kendi denetimi (AFPipeline) çalıştırılır.

Kullanım (depo kökünden, backend venv'iyle):
    app\\backend\\.venv\\Scripts\\python.exe -B phase_xlvi\\scripts\\verify_af_env.py
    app\\backend\\.venv\\Scripts\\python.exe -B phase_xlvi\\scripts\\verify_af_env.py --ecgdeli-zip <ECGdeli_v1.1.zip> --octave-7z <octave-10.3.0-w64.7z>
Çıkış kodu: 0 = hepsi kilitle aynı ve AF etkin; 1 = en az bir uyuşmazlık/eksik.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))

from healthrisk_api import ecg_af as A  # noqa: E402
from healthrisk_api import ecg_window as W  # noqa: E402

# Proje kayıtlarındaki indirme arşivleri (kilitte arşiv SHA'sı yalnız ECGDeli için var; Octave arşivi Phase25 kaydından)
ECGDELI_ZIP_SHA = '5da77e68f3170f20ff4f94ef63b069e3aa11b86faddeaf1b093d9c487ee2d9ad'      # = lock.ecgdeli.archive_sha256
OCTAVE_7Z_SHA = '4595b055c73de090839f5b86f289b0ac22b69549676b3452252306fffdc37ac6'        # Phase25 octave_complete_download.json
ECGDELI_COMMIT = '3c13b1b2ff55152360f3cee992c1d1d66099aa14'                                # zip arşiv yorumu (GitHub zipball)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ecgdeli-zip')
    ap.add_argument('--octave-7z')
    ap.add_argument('--out')
    a = ap.parse_args()
    rows = []

    def add(item, path, expected, actual, note=''):
        rows.append(dict(item=item, path=path, expected=expected, actual=actual,
                         ok=actual is not None and actual == expected, note=note))

    lock_p, side_p = A.AF_LOCK, A.AF_LOCK_SHA
    if not lock_p.exists():
        add('kilit dosyası', lock_p.relative_to(V2).as_posix(), 'var', None, 'kilit yoksa diğer kontroller yapılamaz')
        return finish(rows, a)
    add('kilit dosyası (sidecar)', lock_p.relative_to(V2).as_posix(),
        side_p.read_text(encoding='utf8').strip() if side_p.exists() else 'sidecar yok', sha(lock_p))
    lock = json.loads(lock_p.read_text(encoding='utf8'))
    add('pipeline kodu', A.AF_PIPELINE.relative_to(V2).as_posix(), lock['pipeline_sha256'],
        sha(A.AF_PIPELINE) if A.AF_PIPELINE.exists() else None)
    exe = V2 / lock['octave']['exe']
    add(f"Octave {lock['octave']['version']} octave-cli.exe", lock['octave']['exe'], lock['octave']['exe_sha256'],
        sha(exe) if exe.exists() else None)
    pk = exe.parents[1] / 'share/octave/packages' if exe.exists() else None
    for spec in lock['octave']['packages']:
        name, ver = spec.split()
        d = pk / f'{name}-{ver}' if pk else None
        add(f'Octave paketi {spec}', (d.relative_to(V2).as_posix() if d else '—'), 'klasör var',
            'klasör var' if d is not None and d.is_dir() else None, 'Windows 7z paketiyle gelir; ayrı pkg install yok')
    src = V2 / 'Clinical_Optimization_Phase25/src/ecg_extraction/native_source'
    tree, n = A._tree_hash(src) if src.exists() else (None, 0)
    add(f"ECGDeli {lock['ecgdeli']['version']} kaynak ağacı ({lock['ecgdeli']['n_m_files']} .m)",
        src.relative_to(V2).as_posix(), lock['ecgdeli']['source_tree_sha256'], tree, f'bulunan .m: {n}')
    for rel, h in lock['compat'].items():
        p = V2 / rel
        add('uyumluluk dosyası', rel, h, sha(p) if p.exists() else None)
    vend = V2 / 'Clinical_Optimization_Phase25/src/ecg_extraction/vendor'
    vf = next(iter(vend.rglob('wfdb/version.py')), None) if vend.exists() else None
    vtxt = vf.read_text(encoding='utf8') if vf else ''
    add('vendored WFDB', vend.relative_to(V2).as_posix(), lock['wfdb_vendor_version'],
        lock['wfdb_vendor_version'] if lock['wfdb_vendor_version'] in vtxt else (None if not vf else 'farklı sürüm'))
    wp = W.verify_source() if (V2 / W.SOURCE_FILE).exists() else ['kaynak dosya yok']
    add('ilk 10 sn ön adımı kaynağı', W.SOURCE_FILE, 'uyuşuyor', 'uyuşuyor' if not wp else '; '.join(wp))
    if a.ecgdeli_zip:
        add('ECGDeli v1.1 arşivi (isteğe bağlı)', a.ecgdeli_zip, ECGDELI_ZIP_SHA, sha(a.ecgdeli_zip),
            'GitHub zipball baytları zamanla değişebilir; belirleyici kontrol kaynak ağacı SHA256')
    if a.octave_7z:
        add('Octave 10.3.0 arşivi (isteğe bağlı)', a.octave_7z, OCTAVE_7Z_SHA, sha(a.octave_7z))
    return finish(rows, a)


def finish(rows, a):
    af = A.AFPipeline()                                 # sunucunun başlangıç denetimi (aynı kod)
    res = dict(lock_file='phase_xxviii/config/af_pipeline_lock.json', ecgdeli_commit=ECGDELI_COMMIT, rows=rows,
               server_check=dict(enabled=af.enabled, problems=af.problems),
               ok=all(r['ok'] for r in rows) and af.enabled)
    for r in rows:
        print(('OK   ' if r['ok'] else 'HATA ') + f"{r['item']}: {r['path']}" + ('' if r['ok'] else
              f"\n       beklenen {r['expected']}\n       bulunan  {r['actual']}") + (f"  [{r['note']}]" if r['note'] else ''))
    print(f"sunucu denetimi (AFPipeline): enabled={af.enabled}" + ('' if af.enabled else f" problems={af.problems}"))
    print('SONUÇ:', 'AF ortamı kilitle aynı' if res['ok'] else 'AF ortamı kilitle UYUŞMUYOR / eksik')
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
    return 0 if res['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
