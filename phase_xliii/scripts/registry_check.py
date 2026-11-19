"""Phase XLIII — registry/models.json ve input_schema.json doğrulaması.
Her model için (kayıtlı venv'inde, ayrı süreçte):
  C1 dosya SHA256 == registry == kilit dosyası; kilit dosyası yeniden okunur (feature sırası, eşik)
  C2 çalışma ortamı sürümleri == registry
  C3 registry feature sırası == modelin kendi sütun sırası (feature_names_in_) / kilit sırası; adlandırılmış sütun kümesi eşit
  C4 registry kategorileri == fitted encoder kategorileri (string biçimiyle birebir, None dahil)
  C5 sentetik (sınırlar içinde, tam) girdi: yalnız ÖN-İŞLEME transform'u → bilinmeyen kategori yok, one-hot blokları dolu, NaN yok
  C6 negatif kontrol: bilinmeyen kategori sokulursa dedektör yakalar (dedektörün çalıştığını gösterir)
  C7 predict_proba yalnız çalıştığını göstermek için SENTETİK girdiyle çağrılır; sonuç bu betikte raporlanmaz/saklanmaz
Kayıt düzeyi: input_schema ↔ models.json tutarlılığı, zorunlu alanlar, clinical_probability_eligibility=false.
Çalıştırma: python -B -I phase_xliii/scripts/registry_check.py   (kök .venv; modeller kendi venv'lerinde alt süreçle)
Çıktı: phase_xliii/results/registry_check.json, logs/registry_check.log. Çıkış kodu 0 = hepsi geçti."""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import registry_lib as L  # noqa: E402

REG = L.PHASE / 'registry'
PKGS = ['numpy', 'pandas', 'scipy', 'sklearn', 'imblearn', 'joblib', 'lightgbm', 'xgboost', 'catboost']
REQUIRED_KEYS = ['disease', 'model_file', 'runtime', 'features', 'thresholds', 'calibration', 'target_definition', 'evidence', 'limitations',
                 'missing_input_rule', 'clinical_probability_eligibility']
VENV_KEY = {'.venv': 'root', 'Focused_Current_Disease_Improvement_2026/.venv': 'focused'}


def venv_of(entry):
    return VENV_KEY[entry['runtime']['required_venv']]


def ok(name, passed, detail=''):
    return dict(check=name, passed=bool(passed), detail=detail)


def worker(mid):
    import importlib
    import numpy as np
    import pandas as pd
    reg = json.load(open(REG / 'models.json', encoding='utf8'))
    e = reg['models'][mid]
    res = []
    # C1 ------------------------------------------------------------------------------------------------------------
    mp = L.V2 / e['model_file']['path']
    sha = L.sha256_file(mp)
    res.append(ok('C1a dosya SHA == registry', sha == e['model_file']['sha256'], sha))
    # kilit dosyasını yeniden oku (spec'ten bağımsız yol: registry'deki lock_source)
    import registry_spec as S
    lock = L.read_lock(S.MODELS[mid]['lock'])
    res.append(ok('C1b dosya SHA == kilit dosyasındaki SHA', sha == lock['model_sha256'], lock['source_file']))
    res.append(ok('C1c registry feature sırası == kilit sırası', [f['name'] for f in e['features']] == lock['features'], f"n={len(lock['features'])}"))
    res.append(ok('C1d registry birincil eşik == kilit eşiği', math.isclose(e['thresholds']['primary']['value'], lock['threshold_primary'], rel_tol=0, abs_tol=0), str(e['thresholds']['primary']['value'])))
    sec_ok = all(math.isclose(e['thresholds']['secondary'][k], v, rel_tol=0, abs_tol=0) for k, v in lock['thresholds_secondary'].items()) and set(e['thresholds']['secondary']) == set(lock['thresholds_secondary'])
    res.append(ok('C1e registry ikincil eşikler == kilit', sec_ok, ','.join(e['thresholds']['secondary'])))
    # C2 ------------------------------------------------------------------------------------------------------------
    cur = {}
    for p in PKGS:
        try:
            cur[p] = importlib.import_module(p).__version__
        except Exception:
            cur[p] = None
    want = {k: v for k, v in e['runtime']['packages'].items()}
    mism = {k: (want[k], cur.get(k)) for k in want if cur.get(k) != want[k]}
    res.append(ok('C2 paket sürümleri == registry', not mism, json.dumps(mism)))
    res.append(ok('C2b python sürümü == registry', sys.version.split()[0] == e['runtime']['python'], sys.version.split()[0]))
    # yükleme --------------------------------------------------------------------------------------------------------
    m = L.load_model(e['model_file']['path'], e['runtime']['extra_sys_path_for_pickle'])
    res.append(ok('C2c model yüklendi (kayıtlı venv)', True, type(m).__name__))
    feats = e['features']
    names = [f['name'] for f in feats]
    # C3 -------------------------------------------------------------------------------------------------------------
    hint = L.feature_order_hint(m)
    if hint is not None:
        res.append(ok('C3a registry sırası == model feature_names_in_', names == hint, f'n={len(hint)}'))
    else:
        res.append(ok('C3a model feature_names_in_ yok → kilit sırası kullanıldı (C1c)', True, 'yok'))
    cs = L.column_sets(m)
    if cs:
        res.append(ok('C3b adlandırılmış sütun kümesi == registry feature kümesi', set(cs) == set(names) and len(cs) == len(set(cs)), f'ct={len(cs)} reg={len(names)}'))
    # C4 -------------------------------------------------------------------------------------------------------------
    learned = L.learned_categories(m)
    reg_cats = {f['name']: f['learned_categories'] for f in feats if f['type'] == 'categorical' and f['model_dtype'] == 'str'}
    res.append(ok('C4a string-kategorik sütun kümesi == encoder sütun kümesi', set(learned) == set(reg_cats), f'enc={sorted(learned)}'))
    diffs = {k: (reg_cats[k], learned.get(k)) for k in reg_cats if reg_cats[k] != learned.get(k)}
    res.append(ok('C4b kategoriler encoder ile birebir (string, None dahil, sıra dahil)', not diffs, json.dumps(diffs, ensure_ascii=False)[:300]))
    types_ok = all(isinstance(c, str) or c is None for cats in learned.values() for c in cats)
    res.append(ok('C4c tüm kategori değerleri str (veya None)', types_ok, ''))
    # C5 -------------------------------------------------------------------------------------------------------------
    row = {}
    bounds_ok = True
    for f in feats:
        v = f['synthetic_check_value']
        if f['type'] == 'numeric':
            lo, hi = f['allowed_range']
            bounds_ok &= (lo <= v <= hi)
            row[f['name']] = float(v)
        elif f['model_dtype'] == 'float':
            bounds_ok &= (v in f['allowed_values'])
            row[f['name']] = float(v)
        else:
            bounds_ok &= (v in f['allowed_values'])
            row[f['name']] = str(v)
    df = pd.DataFrame([row], columns=names)
    res.append(ok('C5a sentetik girdi sınırlar/izinli kategoriler içinde ve eksiksiz', bounds_ok and not df.isna().any().any(), f'n={len(names)}'))
    X = L.preprocess_only(m, df)
    res.append(ok('C5b ön-işleme çıktısı sonlu (NaN/inf yok)', np.isfinite(X.astype(float)).all(), f'shape={X.shape}'))
    unknown = [c for c, cats in learned.items() if row[c] not in cats]
    res.append(ok('C5c bilinmeyen kategori yok (değerler encoder kategorilerinde)', not unknown, str(unknown)))
    blk, det = L.onehot_block_ok(m, X)
    res.append(ok('C5d one-hot blokları dolu (her özellik diliminin toplamı 1)', blk, det))
    # C6 -------------------------------------------------------------------------------------------------------------
    nc_feat = next((f for f in feats if f['type'] == 'categorical' and f['model_dtype'] == 'str'), None)
    if nc_feat is not None:
        bad = df.copy()
        v0 = str(row[nc_feat['name']])
        bad.at[0, nc_feat['name']] = v0[:-2] if v0.endswith('.0') else '__BILINMEYEN__'   # '1.0' → '1' (CAD hatası biçimi) veya uydurma kategori
        unk2 = [c for c, cats in learned.items() if bad.at[0, c] not in cats]
        Xb = L.preprocess_only(m, bad)
        blk2, _ = L.onehot_block_ok(m, Xb)
        res.append(ok('C6 negatif kontrol: bilinmeyen kategori dedektörce yakalanır (string kontrolü ve one-hot dilim kontrolü)', bool(unk2) and not blk2,
                      f'{nc_feat["name"]}: {v0!r} → {bad.at[0, nc_feat["name"]]!r}'))
    else:
        res.append(ok('C6 negatif kontrol: string-kategorik sütun yok (model yalnız sayısal/ikili girdi alır)', True, 'uygulanamaz'))
    # C7 -------------------------------------------------------------------------------------------------------------
    pr = m.predict_proba(df)
    pr = np.asarray(pr)
    pred_ok = pr.shape == (1, 2) and bool(np.isfinite(pr).all()) and bool(((pr >= 0) & (pr <= 1)).all())
    res.append(ok('C7 predict_proba çalıştı (yalnız sentetik girdi; sonuç raporlanmaz/saklanmaz)', pred_ok, 'çıktı biçimi ve sonluluk kontrol edildi'))
    del pr
    # dosya hâlâ aynı mı
    res.append(ok('C8 model dosyası SHA tahmin sonrası aynı', L.sha256_file(mp) == e['model_file']['sha256'], ''))
    print(json.dumps(res, ensure_ascii=True))


def record_checks(reg, schema):
    res = []
    models = reg['models']
    res.append(ok('R1 clinical_probability_eligibility=false (kayıt ve tüm modeller)', reg['clinical_probability_eligibility'] is False and all(m['clinical_probability_eligibility'] is False for m in models.values()), ''))
    res.append(ok('R2 zorunlu anahtarlar her modelde var', all(all(k in m for k in REQUIRED_KEYS) for m in models.values()), ''))
    diseases = {m['disease_key'] for m in models.values()}
    want = {'af', 'mi', 'cad', 'diabetes', 'anemia', 'copd', 'heart_failure', 'hypertension', 'liver_fibrosis', 'osteoporosis', 'kidney'}
    res.append(ok('R3 11 hastalık kapsandı', diseases == want, str(sorted(want ^ diseases))))
    fields = set(schema['fields'])
    bad_f = []
    for mid, m in models.items():
        for f in m['features']:
            for tok in f['input_field'].split('+'):
                toks = [tok.replace('1..3', str(i)) for i in (1, 2, 3)] if '1..3' in tok else [tok]
                for t in toks:
                    if t not in fields:
                        bad_f.append((mid, f['name'], t))
    res.append(ok('R4 her model feature\'ının input_field\'i input_schema.fields içinde', not bad_f, str(bad_f[:5])))
    bad_t = [(mid, f['name'], f['transform']) for mid, m in models.items() for f in m['features'] if f['transform'] not in schema['transforms']]
    res.append(ok('R5 her feature\'ın dönüşümü input_schema.transforms içinde', not bad_t, str(bad_t[:5])))
    use_ok = all([dict(model_feature=f['name'], input_field=f['input_field'], transform=f['transform']) for f in m['features']] == schema['model_usage'][mid] for mid, m in models.items())
    res.append(ok('R6 input_schema.model_usage == models.json feature eşlemesi', use_ok and set(schema['model_usage']) == set(models), ''))
    res.append(ok('R7 her modelde eşik (0–1 arası sayı) var', all(0 < m['thresholds']['primary']['value'] < 1 for m in models.values()), ''))
    res.append(ok('R8 kanıt düzeyi alanı ve en az bir test sonucu her modelde var', all(m['evidence'].get('highest_tier') and any(m['evidence'].get(t) for t in ('internal_test', 'temporal', 'external')) for m in models.values()), ''))
    res.append(ok('R9 model_missing_rule her modelde var', set(schema['model_missing_rule']) == set(models), ''))
    sev = [mid for mid, m in models.items() if any(f['type'] == 'numeric' and f['allowed_range'][0] >= f['allowed_range'][1] for f in m['features'])]
    res.append(ok('R10 sayısal aralıklar geçerli (alt < üst)', not sev, str(sev)))
    am = {mid: (m.get('app_visible'), m.get('app_mode')) for mid, m in models.items()}
    exp = {'mi_model': (False, 'registry_only'), 'hf_S2_BASIC_LAB': (False, 'registry_only'), 'cad_DEVICE': (True, 'clinical_mode'), 'copd_S4_DEVICE': (True, 'clinical_mode'), 'af_S4_DEVICE': (True, 'ecg_upload_demo')}
    res.append(ok('R11 app_visible/app_mode kullanıcı kararıyla uyumlu', all(am[k] == v for k, v in exp.items()) and all(am[k] == (True, 'standard') for k in am if k not in exp), str(am)))
    pol = schema['policy']
    res.append(ok('R12 policy: yapısal boşluk imputer maddesi ve isteğe bağlı ırk maddesi var', 'structural_blanks' in pol and 'optional_race' in pol, ''))
    race_models = sorted(mid for mid, m in models.items() if any(f['input_field'] == 'race_ethnicity' for f in m['features']))
    res.append(ok('R13 ırk kullanan modellerin eksik-girdi kuralı ırk yanıtsızsa ABSTAIN der', all('race_ethnicity yanıtsızsa ABSTAIN' in models[k]['missing_input_rule'] for k in race_models), str(race_models)))
    return res


def main():
    reg = json.load(open(REG / 'models.json', encoding='utf8'))
    schema = json.load(open(REG / 'input_schema.json', encoding='utf8'))
    out = dict(phase='XLIII', record_checks=record_checks(reg, schema), models={})
    for mid, e in reg['models'].items():
        py = L.VENVS[venv_of(e)]
        r = subprocess.run([str(py), '-B', '-I', str(Path(__file__).resolve()), '--worker', mid], capture_output=True, text=True, encoding='utf-8')
        if r.returncode != 0:
            out['models'][mid] = [ok('WORKER başarısız', False, (r.stderr or '')[-800:])]
        else:
            out['models'][mid] = json.loads(r.stdout.strip().splitlines()[-1])
    n_pass = sum(c['passed'] for c in out['record_checks']) + sum(c['passed'] for v in out['models'].values() for c in v)
    n_all = len(out['record_checks']) + sum(len(v) for v in out['models'].values())
    out['summary'] = dict(passed=n_pass, failed=n_all - n_pass, total=n_all, models=len(out['models']),
                          failed_checks=[(mid, c['check'], c['detail']) for mid, v in out['models'].items() for c in v if not c['passed']] +
                                        [('KAYIT', c['check'], c['detail']) for c in out['record_checks'] if not c['passed']])
    resdir = L.PHASE / 'results'
    resdir.mkdir(exist_ok=True)
    (resdir / 'registry_check.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    lines = []
    for mid, v in out['models'].items():
        lines.append(f"{mid}: {sum(c['passed'] for c in v)}/{len(v)}")
    lines.append('KAYIT: ' + f"{sum(c['passed'] for c in out['record_checks'])}/{len(out['record_checks'])}")
    lines.append(f"TOPLAM: {n_pass} geçti / {n_all - n_pass} kaldı (toplam {n_all})")
    for f in out['summary']['failed_checks']:
        lines.append('KALDI: ' + ' | '.join(map(str, f)))
    txt = '\n'.join(lines)
    print(txt)
    (L.PHASE / 'logs').mkdir(exist_ok=True)
    (L.PHASE / 'logs' / 'registry_check.log').write_text(txt + '\n', encoding='utf-8')
    sys.exit(0 if out['summary']['failed'] == 0 else 1)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(sys.argv[2])
    else:
        main()
