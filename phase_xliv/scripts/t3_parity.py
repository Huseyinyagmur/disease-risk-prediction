"""Phase XLIV Görev 3 — parity sürücüsü. app/backend/tests/parity_lib.py'yi çalıştırır, sonuçları faz klasörüne yazar.
Yalnız geliştirme verisi; sabit seed (parity_lib.SEED). Olasılık yazılmaz (yalnız karar değişimi sayısı).
Kullanım (app venv):  python -B -I t3_parity.py"""
import json
import sys
from pathlib import Path

P44 = Path(__file__).resolve().parents[1]
V2 = P44.parent
BACKEND = V2 / 'app' / 'backend'
sys.dont_write_bytecode = True
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / 'tests'))

import pandas as pd  # noqa: E402
import parity_lib as PL  # noqa: E402
from healthrisk_api.service import Service  # noqa: E402

MODELS = ['cad_DEVICE', 'dm_A', 'dm_B', 'anemia_LR16', 'copd_S4_DEVICE', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_A', 'ckd_B']


def main():
    svc = Service()
    out, feats, ex_all = [], [], []
    for m in MODELS:
        r, ex = PL.run_case(svc, m)
        out.append(r)
        ex_all += ex
        for f in r['features']:
            feats.append(dict(model=m, **f))
        print(m, r['n_sampled'], r['outcome'], 'flip', r['decision_flips'], flush=True)
    res = dict(seed=PL.SEED, n_target=PL.N_SAMPLE, tolerance=PL.TOL,
               note='Ham alanlar -> şema alanları (adaptör) -> sunucu dönüşümleri -> registry sırası; geliştirme tablosuyla '
                    'karşılaştırma. MATCH: tüm feature’lar |Δ| ≤ 1e-6 / birebir. Test/mühürlü dosya okunmadı.',
               models=out)
    (P44 / 'results' / 'parity_summary.json').write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding='utf8')
    pd.DataFrame(feats).to_csv(P44 / 'results' / 'parity_features.csv', index=False)
    pd.DataFrame(ex_all).to_csv(P44 / 'results' / 'parity_mismatch_examples.csv', index=False)


if __name__ == '__main__':
    main()
