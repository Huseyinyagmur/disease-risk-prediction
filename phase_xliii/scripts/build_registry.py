"""Phase XLIII — registry/models.json ve registry/input_schema.json üretir.
Eşik, feature sırası, model SHA'sı kilit dosyalarından; kategoriler fitted encoder'lardan okunur; birim/aralık/kanıt registry_spec.py'dan.
Model eğitilmez, predict çağrılmaz. Çalıştırma: python -B -I phase_xliii/scripts/build_registry.py   (kök .venv)
İç kullanım: --extract <model_id>  (ilgili venv'de çalışan işçi; JSON basar)"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import registry_lib as L  # noqa: E402
import registry_spec as S  # noqa: E402

OUT = L.PHASE / 'registry'
PKGS = ['numpy', 'pandas', 'scipy', 'sklearn', 'imblearn', 'joblib', 'lightgbm', 'xgboost', 'catboost']


def worker(mid):
    spec = S.MODELS[mid]
    m = L.load_model(spec['model_path'], spec.get('extra_sys_path'))
    import importlib
    ver = {}
    for p in PKGS:
        try:
            ver[p] = importlib.import_module(p).__version__
        except Exception:
            ver[p] = None
    med = {}
    p = L.inner_pipeline(m)
    stack = [p]
    while stack:
        o = stack.pop(0)
        if hasattr(o, 'transformers_'):
            for _, t, cols in o.transformers_:
                if isinstance(cols, str) or t == 'drop' or not cols or not all(isinstance(c, str) for c in cols):
                    continue
                first = t.steps[0][1] if hasattr(t, 'steps') else t
                if type(first).__name__ == 'SimpleImputer' and getattr(first, 'strategy', '') == 'median':
                    for c, v in zip(cols, first.statistics_):
                        med[c] = float(v)
        for _, ch in L._children(o):
            stack.append(ch)
    print(json.dumps(dict(categories=L.learned_categories(m), feature_order_hint=L.feature_order_hint(m), column_sets=L.column_sets(m),
                          fit_sklearn_version=L.fit_sklearn_version(m), final_estimator=type(L.final_estimator(m)).__name__,
                          wrapper=type(m).__name__, imputer_medians=med, runtime_packages=ver, python=sys.version.split()[0]), ensure_ascii=True))


def run_worker(venv, mid):
    r = subprocess.run([str(L.VENVS[venv]), '-B', '-I', str(Path(__file__).resolve()), '--extract', mid], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        raise RuntimeError(f'{mid}: işçi başarısız\n{r.stderr[-1500:]}')
    return json.loads(r.stdout.strip().splitlines()[-1])


def mi_features(lock_features, med, cats):
    out = []
    for f in lock_features:
        if f == 'age':
            out.append(dict(name=f, kind='num', unit='yıl', input_field='ecg_ptbxl_ecgdeli_168', transform='ptbxl_group', allowed_range=[18, 90], synthetic=60.0,
                            note='PTB-XL: >89 yaş 90 olarak kodlandı'))
        elif f == 'sex':
            out.append(dict(name=f, kind='bin', unit='PTB-XL kodu 0=erkek 1=kadın', input_field='ecg_ptbxl_ecgdeli_168', transform='ptbxl_group', allowed_values=[0.0, 1.0], synthetic=1.0))
        elif f == 'ST_Elev_missing':
            out.append(dict(name=f, kind='bin', unit='0/1', input_field='ecg_ptbxl_ecgdeli_168', transform='ptbxl_group', allowed_values=[0.0, 1.0], synthetic=0.0,
                            note='12 ST_Elev sütununun hepsi NaN ise 1 (eğitimde göstergeli medyan doldurma)'))
        elif f == 'HA__Global':
            out.append(dict(name=f, kind='cat', unit='ECGDeli elektriksel aks kategorisi (1–6, string float)', input_field='ecg_ptbxl_ecgdeli_168', transform='ptbxl_group', synthetic='2.0'))
        else:
            amp = f.split('_')[0] in ('Q', 'R', 'S', 'T', 'P') and '_Amp_' in f or f.startswith('ST_Elev')
            unit, rng = ('mV', [-10.0, 10.0]) if amp else ('ms', [0.0, 3000.0])
            out.append(dict(name=f, kind='num', unit=unit, input_field='ecg_ptbxl_ecgdeli_168', transform='ptbxl_group', allowed_range=rng, synthetic=med[f]))
    return out


def main():
    OUT.mkdir(exist_ok=True)
    venv_pk = {}
    models = {}
    usage = {}
    for mid, spec in S.MODELS.items():
        lock = L.read_lock(spec['lock'])
        sha_actual = L.sha256_file(L.V2 / spec['model_path'])
        assert sha_actual == lock['model_sha256'], f'{mid}: model SHA kilitle uyuşmuyor'
        ex = run_worker(spec['venv'], mid)
        venv_pk.setdefault(spec['venv'], dict(python=ex['python'], packages=ex['runtime_packages']))
        feats = spec['features'] if spec['features'] is not None else mi_features(lock['features'], ex['imputer_medians'], ex['categories'])
        assert [f['name'] for f in feats] == lock['features'], f'{mid}: spec feature sırası kilit sırasından farklı'
        if ex['feature_order_hint'] is not None:
            assert ex['feature_order_hint'] == lock['features'], f'{mid}: model feature_names_in_ kilit sırasından farklı'
        out_feats = []
        for f in feats:
            d = dict(name=f['name'])
            if f['kind'] == 'cat':
                cats = ex['categories'][f['name']]
                allowed = [c for c in cats if c is not None]
                d.update(type='categorical', model_dtype='str', unit=f['unit'], learned_categories=cats, allowed_values=allowed)
                assert f['synthetic'] in allowed, f'{mid}.{f["name"]}: sentetik değer öğrenilen kategorilerde yok'
            elif f['kind'] == 'bin':
                d.update(type='categorical', model_dtype='float', encoding='binary_0_1_numeric', unit=f['unit'], allowed_values=f['allowed_values'])
                assert f['synthetic'] in f['allowed_values']
            else:
                d.update(type='numeric', model_dtype='float', unit=f['unit'], allowed_range=f['allowed_range'])
                lo, hi = f['allowed_range']
                assert lo <= f['synthetic'] <= hi, f'{mid}.{f["name"]}: sentetik değer aralık dışı'
            d.update(input_field=f['input_field'], transform=f['transform'], synthetic_check_value=f['synthetic'])
            if f.get('note'):
                d['note'] = f['note']
            out_feats.append(d)
        sec = {k: v for k, v in lock['thresholds_secondary'].items()}
        e = spec['evidence']
        models[mid] = dict(
            disease=spec['disease'], disease_key=spec['disease_key'], role=spec['role'], phase_of_origin=spec['phase_of_origin'],
            model_file=dict(path=spec['model_path'], sha256=sha_actual, size_bytes=(L.V2 / spec['model_path']).stat().st_size, sha256_in_lock=lock['model_sha256'], lock_source=lock['source_file']),
            runtime=dict(required_venv=('.venv' if spec['venv'] == 'root' else 'Focused_Current_Disease_Improvement_2026/.venv'),
                         python=ex['python'], packages={k: v for k, v in ex['runtime_packages'].items() if v is not None},
                         fit_sklearn_version=ex['fit_sklearn_version'], fit_environment_evidence=spec['fit_environment_evidence'],
                         extra_sys_path_for_pickle=spec.get('extra_sys_path'), pickle_wrapper=ex['wrapper'], final_estimator=ex['final_estimator'],
                         note='Pickle yalnız bu venv sürümleriyle doğrulanmıştır (registry_check). Farklı sürümde yükleme sessiz uyarı verebilir; yeniden fit YASAK.'),
            family=spec['family'], target_definition=spec['target_definition'], population=spec['population'], input_source_note=spec['input_source_note'],
            features=out_feats, n_features=len(out_feats), feature_order_source=lock['source_file'],
            thresholds=dict(primary=dict(value=lock['threshold_primary'], rule=lock['threshold_primary_rule'] or 'BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)'),
                            secondary=sec, source=lock['source_file'],
                            note='Eşikler dondurulmuştur; uygulamada değiştirilmez. Karar yalnız bu eşikte "araştırma sınıflaması"dır, klinik karar değildir.'),
            calibration=dict(status=spec['calibration_status'], manifest_value=lock['extra'].get('calibration')),
            evidence=e, limitations=spec['limitations'], app_feasibility=spec['app_feasibility'], missing_input_rule=spec['missing_rule'],
            app_visible=S.APP[mid]['app_visible'], app_mode=S.APP[mid]['app_mode'], app_mode_reason=S.APP[mid]['reason'],
            clinical_probability_eligibility=False)
        usage[mid] = [dict(model_feature=f['name'], input_field=f['input_field'], transform=f['transform']) for f in out_feats]
    registry = dict(
        registry_version='1.0', phase='XLIII', created_utc='2026-11-19',
        note=('Uygulama için donmuş model kaydı. Model yeniden fit edilmez; eşik, kalibrasyon, feature sırası ve birimler değiştirilmez. '
              'Tüm model çıktıları araştırma skorudur: clinical_probability_eligibility=false (klinik olasılık olarak sunulamaz). '
              'Kanıt düzeyleri ayrı tutulur: iç test / zamansal / dış doğrulama. Bulunamayan bilgi BULUNAMADI.'),
        clinical_probability_eligibility=False,
        research_targets=dict(precision_min=0.70, recall_min=0.75, fpr_max=0.15, note='Araştırma hedefleri; klinik onay kriteri değildir.'),
        venvs={('.venv' if k == 'root' else 'Focused_Current_Disease_Improvement_2026/.venv'): v for k, v in venv_pk.items()},
        models=models, candidates_not_registered=S.CANDIDATES)
    (OUT / 'models.json').write_text(json.dumps(registry, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    schema = dict(
        schema_version='1.0', phase='XLIII', created_utc='2026-11-19',
        policy=dict(
            units='Her alan tek birimde tanımlıdır (fields.*.unit). Kullanıcı farklı birim girerse arayüz unit_conversions ile çevirir; birim belirsiz ve değer aralık dışıysa tahmin üretilmez.',
            missing='Hiçbir model için eksik girdi tahminle doldurulmaz. Eksik zorunlu alan → o model ABSTAIN (tahmin üretmez). Dondurulmuş imputer uygulama tarafında kullanılmaz. Yapısal atlama kuralları (ör. erkekte gdm=0, hipertansiyon yoksa htn_med=0) eğitimdeki tanımın aynısıdır ve eksik sayılmaz.',
            categorical_strings='Kategorik modeller string biçimini birebir ister (ör. CAD \'1.0\'; MI HA__Global \'2.0\'). Dönüşüm tablosu (transforms) tek kaynaktır; sessiz tür dönüşümü (\'1\' → \'1.0\') YAPILMAZ, dönüşüm tablosuyla üretilir.',
            range_basis='plausible_range fiziksel olarak makul giriş sınırıdır (uygulama doğrulaması); modelin eğitim kapsamı değildir. Model popülasyon sınırları models.json içinde (population, allowed_range).',
            applicability='Her model yalnız kendi hedef popülasyonunda geçerlidir (models.json: population). Hedefi tanımlayan değer (ör. HbA1c/glukoz diyabet için, ölçülen tansiyon HTN için) biliniyorsa doğrudan klinik eşik kullanılmalıdır.',
            structural_blanks='Yapısal boşluklarda (ör. osteo age_last_period: erkek veya adeti süren kadın) modelin kendi pipeline imputer\'ı eğitimdeki gibi çalışır; kullanıcının yanıtlamadığı alanlar için ÇALIŞMAZ (o durumda model ABSTAIN eder).',
            optional_race='race_ethnicity isteğe bağlı sorulur; yanıt yoksa race_ethnicity kullanan modeller (dm_A, dm_B, ckd_A, ckd_B, htn_M1) ABSTAIN eder; varsayılan sınıf atanmaz.',
            clinical_probability_eligibility=False),
        fields=S.F, transforms=S.TRANSFORMS, unit_conversions=S.UNIT_CONVERSIONS, unit_conversion_note=S.CONVERSION_NOTE,
        derived_fields=dict(
            bmi_kgm2='weight_kg / (height_cm/100)^2', bp_means='sbp/dbp için 3 okumanın ortalaması (DM) veya 2. ve 3. okumanın ortalaması (KBH)',
            egfr='CKD-EPI 2021 ırksız (creatinine_mgdl, age_years, sex)', uacr_mg_g='100 × urine_albumin_mgl / urine_creatinine_mgdl'),
        model_usage=usage,
        model_missing_rule={mid: dict(required_features=[f['name'] for f in models[mid]['features']], rule=models[mid]['missing_input_rule'], app_feasibility=models[mid]['app_feasibility']) for mid in models})
    (OUT / 'input_schema.json').write_text(json.dumps(schema, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('models', len(models), 'fields', len(S.F), 'transforms', len(S.TRANSFORMS))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--extract':
        worker(sys.argv[2])
    else:
        main()
