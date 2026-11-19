"""Kullanıcı alanları -> model feature vektörü. Feature SIRASI models.json'dan; dönüşüm adı models.json ve
input_schema.model_usage'dan (ikisinin aynı olduğu başlangıçta doğrulanır); dönüşüm uygulaması transforms.py."""
import math
from dataclasses import dataclass, field

from . import transforms as T


@dataclass
class FeatureResult:
    names: list
    values: dict = field(default_factory=dict)
    missing: list = field(default_factory=list)
    unknown: list = field(default_factory=list)          # [(alan, değer)]
    not_applicable: list = field(default_factory=list)   # gerekçe metinleri
    structural_blank: list = field(default_factory=list)
    internal: list = field(default_factory=list)

    @property
    def complete(self):
        return not (self.missing or self.unknown or self.not_applicable or self.internal)


def consistency_problems(entry, usage, allowed_changes=()):
    """models.json feature listesi ile input_schema.model_usage birebir mi (ad kümesi ve dönüşüm)?
    allowed_changes: şema v2 changes_from_v1'den bu model için {(feature, eski_dönüşüm, yeni_dönüşüm)} — yalnız bunlar farklı olabilir."""
    probs = []
    names = [f['name'] for f in entry['features']]
    umap = {u['model_feature']: u for u in usage}
    if set(names) != set(umap) or len(names) != len(usage):
        probs.append(f'feature kümesi uyuşmuyor: models.json={len(names)} model_usage={len(usage)}')
    for f in entry['features']:
        u = umap.get(f['name'])
        if u is None:
            continue
        if u['transform'] != f['transform'] and (f['name'], f['transform'], u['transform']) not in set(allowed_changes):
            probs.append(f'{f["name"]}: dönüşüm uyuşmuyor ({f["transform"]} vs {u["transform"]})')
        if u['input_field'] != f['input_field']:
            probs.append(f'{f["name"]}: input_field uyuşmuyor')
        if f['transform'] not in T.TRANSFORMS:
            probs.append(f'{f["name"]}: dönüşüm uygulanmamış: {f["transform"]}')
    if len(entry['features']) != entry['n_features']:
        probs.append('n_features uyuşmuyor')
    return probs


def build(entry, F, usage=None):
    """usage verilirse dönüşüm adı şemadan (v2), verilmezse models.json'dan alınır. Sıra her zaman models.json."""
    names = [f['name'] for f in entry['features']]
    tmap = {u['model_feature']: u['transform'] for u in usage} if usage else {}
    r = FeatureResult(names=names)
    miss = []
    for f in entry['features']:
        n = f['name']
        try:
            v = T.apply(tmap.get(n, f['transform']), F, f['input_field'])
        except T.Missing as e:
            miss += e.fields
            continue
        except T.UnknownCategory as e:
            r.unknown.append((e.field, repr(e.value)))
            continue
        except T.NotApplicable as e:
            r.not_applicable.append(f'{n}: {e}')
            continue
        if f['model_dtype'] == 'float':
            if isinstance(v, str):
                r.internal.append(f'{n}: float beklenirken string üretildi')
                continue
            v = float(v)
            if f['type'] == 'numeric':
                if math.isnan(v):
                    if f['transform'] == 'osteo_age_last_period':
                        r.structural_blank.append(n)
                    else:
                        r.internal.append(f'{n}: NaN üretildi')
                        continue
                else:
                    lo, hi = f['allowed_range']
                    if not (lo <= v <= hi):
                        r.not_applicable.append(f'{n}={v:.6g} {f.get("unit", "")} model girdi aralığı dışında [{lo}, {hi}]')
                        continue
            elif v not in [float(a) for a in f['allowed_values']]:
                r.internal.append(f'{n}: izinli olmayan ikili değer {v!r}')
                continue
        else:
            if not isinstance(v, str) or v not in f['allowed_values']:
                r.internal.append(f'{n}: izinli olmayan kategori {v!r} (izinli: {f["allowed_values"]})')
                continue
        r.values[n] = v
    r.missing = list(dict.fromkeys(miss))
    r.unknown = list(dict.fromkeys(r.unknown))
    return r


def to_frame(entry, values):
    """Tek satırlık DataFrame; sütun sırası registry sırası, tipler registry model_dtype."""
    import numpy as np
    import pandas as pd
    names = [f['name'] for f in entry['features']]
    df = pd.DataFrame([[values[n] for n in names]], columns=names)
    for f in entry['features']:
        if f['model_dtype'] == 'float':
            df[f['name']] = df[f['name']].astype(np.float64)
        else:
            df[f['name']] = df[f['name']].astype(object)
    return df
