"""Phase XLIX — Hoca 3d: UCI Heart Disease 4 merkezde cad_DEVICE'ın 11 özniteliğinin varlığı/eksiklik oranı.

Yalnız uyumluluk raporu: model yüklenmez, yeniden eğitilmez, skor üretilmez. Hedef sütunu (num) yalnız merkez
prevalansını raporlamak için sayılır.
Eksik tanımı (iki katman, ayrı sütun):
  - '?' : UCI dosyasındaki açık eksik kodu (heart-disease.names).
  - fizyolojik 0: age/trestbps/chol/thalach = 0 -> eksik (V2 kuralı: src/datasets/prepare.py satır 91).
Kategorik değerlerin Cleveland'da (eğitim merkezi) görülen kategori kümesi dışında olup olmadığı da sayılır.
Kullanım: .venv/Scripts/python.exe -B phase_xlix/scripts/uci_cad_availability.py
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
OUT = V2 / 'phase_xlix/results'
RAW = V2 / 'data/raw/uci_45'
HC = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'num']
FEAT = HC[:11]  # cad_DEVICE öznitelikleri (registry sırası ile aynı: phase_xliii/registry/models.json)
ZERO_MISSING = ['age', 'trestbps', 'chol', 'thalach']
CAT = ['sex', 'cp', 'fbs', 'restecg', 'exang', 'slope']
CENTERS = {'cleveland': 'Cleveland (eğitim)', 'hungarian': 'Hungarian', 'switzerland': 'Switzerland', 'va': 'VA Long Beach'}


def main():
    reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
    reg_feat = [f['name'] for f in reg['models']['cad_DEVICE']['features']]
    assert reg_feat == FEAT, reg_feat
    data, meta = {}, {}
    for c in CENTERS:
        p = RAW / f'processed.{c}.data'
        meta[c] = {'file': f'data/raw/uci_45/processed.{c}.data', 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        data[c] = pd.read_csv(p, header=None, names=HC, na_values='?')
    cle_cats = {k: sorted(data['cleveland'][k].dropna().unique().tolist()) for k in CAT}
    rows, summ = [], {}
    for c, d in data.items():
        n = len(d)
        complete = pd.Series(True, index=d.index)
        for f in FEAT:
            q = int(d[f].isna().sum())
            z = int(d[f].eq(0).sum()) if f in ZERO_MISSING else 0
            miss = d[f].isna() | (d[f].eq(0) if f in ZERO_MISSING else False)
            complete &= ~miss
            oos = int((~d[f].isin(cle_cats[f]) & d[f].notna()).sum()) if f in CAT else 0
            rows.append(dict(merkez=CENTERS[c], oznitelik=f, n=n, eksik_soru_isareti=q, eksik_fizyolojik_sifir=z,
                             eksik_toplam=int(miss.sum()), eksik_oran=round(miss.mean(), 3),
                             cleveland_kategori_disi=oos))
        pos = int(d.num.gt(0).sum())
        summ[CENTERS[c]] = dict(n=n, birebir_yinelenen_satir=int(d.duplicated().sum()), pozitif_num_gt0=pos, prevalans=round(pos / n, 3),
                                eksiksiz_11=int(complete.sum()), eksiksiz_oran=round(complete.mean(), 3),
                                eksiksiz_pozitif=int((complete & d.num.gt(0)).sum()))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'uci_cad_feature_availability.csv', index=False)
    wide = df.pivot(index='oznitelik', columns='merkez', values='eksik_oran').reindex(FEAT)[list(CENTERS.values())]
    out = {'inputs': meta, 'features': FEAT, 'cleveland_categories': cle_cats, 'summary': summ,
           'missing_rate_wide': wide.to_dict(orient='index'),
           'note': 'Uyumluluk raporu; model yeniden eğitilmedi, skor üretilmedi. Phase XLI teknik tekrarı eksiksiz-vaka '
                   'alt kümesinde yapıldı (Hungarian 95, VA 64); Switzerland chol nedeniyle yapılamadı.'}
    (OUT / 'uci_cad_feature_availability.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
    print(wide.to_string())
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    print(df[df.cleveland_kategori_disi > 0].to_string())


if __name__ == '__main__':
    main()
