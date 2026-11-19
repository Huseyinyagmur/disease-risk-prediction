"""Phase XLIII — model nesnelerini yalnız okuma amaçlı açan ortak yardımcılar (build_registry.py ve registry_check.py kullanır).
Hiçbir model yeniden fit edilmez; yalnız yükleme, yapı okuma, ön-işleme transform'u ve (check betiğinde) sentetik predict.
Çalıştırma: python -B -I (bytecode yazılmaz; önceki faz klasörlerine dosya yazılmaz)."""
import hashlib
import sys
import warnings
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[2]
PHASE = V2 / 'phase_xliii'
VENVS = {
    'root': V2 / '.venv' / 'Scripts' / 'python.exe',
    'focused': V2 / 'Focused_Current_Disease_Improvement_2026' / '.venv' / 'Scripts' / 'python.exe',
}


def sha256_file(p, bs=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_model(model_path, extra_sys_path=None):
    """Joblib modelini yükler. Phase21/25 pickle'ları kendi 'common' modülünü ister (extra_sys_path)."""
    if extra_sys_path:
        sys.path.insert(0, str(V2 / extra_sys_path))
    import joblib
    warnings.filterwarnings('ignore')
    return joblib.load(V2 / model_path)


def inner_pipeline(m):
    """Sarmalayıcıdan (CalibratedResearchModel / CalibratedClassifierCV) ön-işleme+model pipeline'ını çıkarır."""
    if hasattr(m, 'pipeline'):
        return m.pipeline
    if hasattr(m, 'calibrated_classifiers_'):
        return m.calibrated_classifiers_[0].estimator
    return m


def _children(o):
    if hasattr(o, 'steps'):
        return [(n, s) for n, s in o.steps]
    if hasattr(o, 'transformers_'):
        return [(n, t) for n, t, _ in o.transformers_]
    return []


def walk_encoders(o, found=None):
    """Pipeline/ColumnTransformer ağacında isimli sütunlara bağlı kodlayıcıları toplar.
    Döner: [(kind, columns, encoder)] — kind 'ordinal' | 'onehot'; yalnız sütunları STRING olanlar (sütun indeksli olanlar atlanır)."""
    if found is None:
        found = []
    if hasattr(o, 'transformers_'):
        for n, t, cols in o.transformers_:
            if isinstance(cols, str) or t == 'drop':
                continue
            cols = list(cols)
            if cols and all(isinstance(c, str) for c in cols):
                leaf = t.steps[-1][1] if hasattr(t, 'steps') else t
                if hasattr(leaf, 'categories_'):
                    kind = 'ordinal' if type(leaf).__name__ == 'OrdinalEncoder' else 'onehot'
                    found.append((kind, cols, leaf))
            walk_encoders(t, found)
    elif hasattr(o, 'steps'):
        for _, s in o.steps:
            walk_encoders(s, found)
    return found


def learned_categories(m):
    """{sütun: [kategoriler]} — modelin fitted encoder'larından, string sütun adlarıyla (None dahil, birebir)."""
    out = {}
    for _, cols, enc in walk_encoders(inner_pipeline(m)):
        for c, cats in zip(cols, enc.categories_):
            out[c] = [None if (x is None or (isinstance(x, float) and np.isnan(x))) else x for x in cats]
    return out


def ohe_chain(o, found=None):
    """Zincirdeki TÜM OneHotEncoder'lar (sütun adı ya da indeksli), ağaç sırasıyla."""
    if found is None:
        found = []
    if hasattr(o, 'categories_') and type(o).__name__ == 'OneHotEncoder':
        found.append(o)
    for _, ch in _children(o):
        ohe_chain(ch, found)
    return found


def feature_order_hint(m):
    """Modelin kendi beyan ettiği giriş sütun sırası (varsa)."""
    p = inner_pipeline(m)
    if hasattr(p, 'feature_names_in_'):
        return list(p.feature_names_in_)
    if hasattr(m, 'feature_names_in_'):
        return list(m.feature_names_in_)
    return None


def column_sets(m):
    """İlk ColumnTransformer'ın adlandırılmış sütunlarının birleşimi (sıra bilgisi taşımaz)."""
    p = inner_pipeline(m)
    cols = []
    stack = [p]
    while stack:
        o = stack.pop(0)
        if hasattr(o, 'transformers_'):
            for _, _, c in o.transformers_:
                if not isinstance(c, str) and c and all(isinstance(x, str) for x in c):
                    cols.extend(list(c))
            return cols
        for _, ch in _children(o):
            stack.append(ch)
    return cols


def fit_sklearn_version(m):
    p = inner_pipeline(m)
    for _, s in reversed(getattr(p, 'steps', [])):
        st = s.__getstate__() if hasattr(s, '__getstate__') else {}
        if isinstance(st, dict) and '_sklearn_version' in st:
            return st['_sklearn_version']
    for _, s in getattr(p, 'steps', []):
        for _, ch in _children(s):
            st = ch.__getstate__() if hasattr(ch, '__getstate__') else {}
            if isinstance(st, dict) and '_sklearn_version' in st:
                return st['_sklearn_version']
    return None


def final_estimator(m):
    p = inner_pipeline(m)
    return p.steps[-1][1] if hasattr(p, 'steps') else p


def preprocess_only(m, df):
    """YALNIZ ön-işleme transform'u (son tahmin edici ve resampler hariç). predict çağrılmaz."""
    p = inner_pipeline(m)
    X = df
    for _, s in p.steps[:-1]:
        if hasattr(s, 'fit_resample') or not hasattr(s, 'transform'):
            continue
        X = s.transform(X)
    if hasattr(X, 'toarray'):
        X = X.toarray()
    return np.asarray(X)


def onehot_block_ok(m, X):
    """Zincirdeki SON OneHotEncoder bloğunun (çıktının son K sütunu) her özellik dilimi satır başına tam 1 mi?
    Döner: (ok, ayrıntı). Bilinmeyen kategori handle_unknown='ignore' ile dilimi sıfırlar → ok=False."""
    ohes = ohe_chain(inner_pipeline(m))
    if not ohes:
        return True, 'onehot_yok'
    enc = ohes[-1]
    sizes = [len(c) for c in enc.categories_]
    K = sum(sizes)
    block = X[:, -K:]
    bad = []
    s = 0
    for i, n in enumerate(sizes):
        sl = block[:, s:s + n].sum(axis=1)
        if not np.allclose(sl, 1.0):
            bad.append(i)
        s += n
    return (len(bad) == 0), f'dilim_sayisi={len(sizes)} K={K} bozuk_dilim_idx={bad}'


# ---------------------------------------------------------------------------------------------------------------
# Kilit dosyalarını okuma (build_registry.py ve registry_check.py ortak kullanır)
# ---------------------------------------------------------------------------------------------------------------
import json  # noqa: E402


def fix_mojibake(s):
    """Bazı eski kilit dosyalarında UTF-8 baytları latin-1 gibi çözülmüş metin var; mümkünse geri çevirir."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def read_lock(lock):
    """Spec'teki lock tanımından {model_sha256, features, threshold_primary, thresholds_secondary, rule, source_file, extra} döndürür."""
    if lock['kind'] == 'phase26_manifest':
        p = 'Strong_Model_External_Validation_Phase26/frozen_model_manifest.json'
        ent = [e for e in json.load(open(V2 / p, encoding='utf8')) if e['task'] == lock['task']][0]
        return dict(source_file=p, model_sha256=ent['sha256'], features=ent['features'], threshold_primary=ent['threshold'], threshold_primary_rule=None,
                    thresholds_secondary={}, extra=dict(calibration=ent['calibration'], target=ent['target'], missing_strategy=ent['missing_strategy'],
                                                         input_units=ent['input_units'], clinical_probability_eligibility=ent['clinical_probability_eligibility']))
    d = json.load(open(V2 / lock['path'], encoding='utf8'))
    if lock.get('model_key'):
        e = d[lock.get('section', 'models')][lock['model_key']]
    else:
        e = d
    sec = {}
    for name, key in lock.get('thr_secondary', {}).items():
        sec[name] = e[key[0]][key[1]] if isinstance(key, tuple) else e[key]
    prim_rule = e.get(lock['thr_primary'] + '_rule') or e.get('threshold_rule') or e.get('threshold_locked_rule')
    return dict(source_file=lock['path'], model_sha256=e.get('model_sha256'), features=e['features'], threshold_primary=e[lock['thr_primary']],
                threshold_primary_rule=fix_mojibake(prim_rule), thresholds_secondary=sec, extra={})
