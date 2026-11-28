"""Phase L2 bütünlük ve kural denetimi. Kullanım (V2 kökünden): python -B phase_l2/scripts/verifyL2.py
Girdi: phase_l2/results/sha_before.json, sha_after.json (sha_full_scan.py). Çıktı: phase_l2/results/verificationL2.json
Kurallar (CLAUDE.md + görev): önceki faz/ham veri/model/eşik/registry/şema dosyalarında değişen/silinen = 0; faz dışı yeni
dosya = 0. İstisna: app/ (uygulama kodu; CLAUDE.md). app/ içinde de model/uygunluk/dönüşüm mantığı dosyaları değişmemeli."""
import json
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
R = V2 / 'phase_l2/results'
before = json.loads((R / 'sha_before.json').read_text(encoding='utf8'))
after = json.loads((R / 'sha_after.json').read_text(encoding='utf8'))

changed = sorted(k for k in before if k in after and before[k] != after[k])
deleted = sorted(k for k in before if k not in after)
added = sorted(k for k in after if k not in before)

inside = lambda k: k.startswith('phase_l2/') or k.startswith('app/')  # noqa: E731
LOGIC = ['app/backend/healthrisk_api/eligibility.py', 'app/backend/healthrisk_api/features.py',
         'app/backend/healthrisk_api/validation.py', 'app/backend/healthrisk_api/transforms.py',
         'app/backend/healthrisk_api/service.py', 'app/backend/healthrisk_api/model_loader.py',
         'app/backend/healthrisk_api/ecg_af.py', 'app/backend/healthrisk_api/ecg_window.py']
# Kullanıcının açık talebi (Phase L2 görevi D): 03_eval.md'ye yalnız SONA bölüm eklendi; önceki içerik bayt düzeyinde aynı.
APPEND_OK = ['phase_xlviii/03_eval.md']
REG = [k for k in before if k.startswith(('phase_xliii/registry/', 'phase_xliv/registry/'))]

cfg = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
out = dict(
    n_before=len(before), n_after=len(after),
    changed_outside=[k for k in changed if not inside(k) and k not in APPEND_OK],
    deleted_outside=[k for k in deleted if not inside(k)],
    added_outside=[k for k in added if not inside(k)],
    changed_previous_phase_files=[k for k in changed + deleted if k.startswith('phase_') and not k.startswith('phase_l2/') and k not in APPEND_OK],
    append_only_exceptions={k: (V2 / k).read_bytes().startswith((V2 / 'phase_l2/results/03_eval_before_append.md').read_bytes()) for k in APPEND_OK},
    logic_files_changed=[k for k in LOGIC if before.get(k) != after.get(k)],
    registry_files_changed=[k for k in REG if before.get(k) != after.get(k)],
    app_config_registry_sha_unchanged=cfg['registry_files_sha256'] == {
        'phase_xliii/registry/models.json': '5d2b88a012366f1541fc31dea37bb4781ba1a9e90e9ba882a5c48ef6b5d1c64f',
        'phase_xliii/registry/input_schema.json': '70b9a9e8cda7347676325b150400b9a41ba1b3189d1eb07ca794e9eee058f350',
        'phase_xliv/registry/input_schema_v2.json': '01f0241abf628ffd49a0ce32a49378eeda58179a12974f84fed9acd112900a79'},
    module_labels_unchanged=cfg['module_labels'] == {'af_S4_DEVICE': 'ana modül', 'fibrosis_final': 'ana modül',
                                                     'osteo_final': 'araştırma modülü', '_default': 'deneysel'},
    disclaimer=cfg['disclaimer_tr'],
    app_changed=[k for k in changed if k.startswith('app/')],
    app_added=[k for k in added if k.startswith('app/')],
    app_deleted=[k for k in deleted if k.startswith('app/')],
)
out['ok'] = not (out['changed_outside'] or out['deleted_outside'] or out['added_outside'] or out['logic_files_changed']
                 or out['registry_files_changed'] or out['changed_previous_phase_files']
                 or not out['app_config_registry_sha_unchanged'] or not out['module_labels_unchanged']
                 or not all(out['append_only_exceptions'].values()))
(R / 'verificationL2.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in out.items()}, ensure_ascii=False, indent=1))
for k in ('changed_outside', 'deleted_outside', 'added_outside', 'logic_files_changed'):
    if out[k]:
        print(k, out[k][:20])
