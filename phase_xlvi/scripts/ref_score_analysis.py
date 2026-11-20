"""Phase XLVI — Görev 3: fibrozis ve osteoporoz için referans skor karşılaştırması (POST-HOC, TANIMLAYICI).

Kullanıcı kararı (2026-11-20): XXX/XXXI fazlarında kişi düzeyi test tahminleri ve referans skor değerleri dosyaya
kaydedilmemişti. Bu nedenle donmuş model, kilitli eşik ve ZATEN AÇILMIŞ test dosyasıyla deterministik TEKNİK YENİDEN
SKORLAMA yapılır (Phase XXVII 'rescore' ve Phase XXXI 01 ile aynı yöntem). Kapı: kayıtlı TP/FP/TN/FN, AUC ve ΔAUC değerleri
birebir yeniden üretilmezse analiz durur. Model yeniden fit edilmez; eşik, feature, test kümesi değişmez; sonuçlar model
veya eşik seçimi için kullanılmaz.

Referans skor formülleri ve eşikleri özgün faz betiklerinden salt okunur içe aktarılır:
  fib4, nfs  : phase_xxxi/scripts/t3_fib_dev.py
  ost        : phase_xxx/scripts/t2_dev.py
  metrikler  : phase_xxx/scripts/p30_engine.py (decision_metrics, boot_auc_ap, paired_delta, wilson)
Çalıştırma (catboost gerekir): Focused_Current_Disease_Improvement_2026/.venv/Scripts/python.exe -B phase_xlvi/scripts/ref_score_analysis.py
Çıktılar: phase_xlvi/results/reference_score_analysis.csv, reference_score_gate.json, reference_score_meta.json
"""
import hashlib
import json
import sys
import warnings
from pathlib import Path

sys.dont_write_bytecode = True
warnings.filterwarnings('ignore')
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'phase_xxx/scripts'))
sys.path.insert(0, str(V2 / 'phase_xxxi/scripts'))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import binomtest  # noqa: E402

import p30_engine as E  # noqa: E402
from t2_dev import ost  # noqa: E402
from t3_fib_dev import fib4, nfs  # noqa: E402

SEED = 20261120
NBOOT = 2000
OUT = V2 / 'phase_xlvi/results'
LABEL = 'POST-HOC TANIMLAYICI (teknik yeniden skorlama; kilitli sonuç değil)'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mcnemar(y, d1, d2, subset):
    """Eşleştirilmiş ikili kararlar için kesin McNemar (iki yönlü binom). subset: 'pos' (Recall) / 'neg' (FPR)."""
    k = (y == 1) if subset == 'pos' else (y == 0)
    a, b = d1[k], d2[k]
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return n10, n01, float(p)


def thr_recall_ge(y, s, r):
    """Recall ≥ r sağlayan EN YÜKSEK eşik (p30_engine.threshold_recall ile aynı kural)."""
    return E.threshold_recall(y, s, target=r)[0]


def topk(s, k):
    """En yüksek skorlu k kişi; eşitlikte kararlı (orijinal sıra) — sınırdaki eşitlik sayısı raporlanır."""
    order = np.argsort(-s, kind='stable')
    d = np.zeros(len(s), bool)
    d[order[:k]] = True
    ties = int((s == s[order[k - 1]]).sum()) if k else 0
    return d, ties


def metr(y, d):
    m = E.decision_metrics(y, d)
    tn, fn = m['TN'], m['FN']
    npv = E.wilson(tn, tn + fn)
    return {**{k: m[k] for k in ('TP', 'FP', 'TN', 'FN', 'P', 'P_lo', 'P_hi', 'R', 'R_lo', 'R_hi', 'FPR', 'FPR_lo',
                                 'FPR_hi', 'yonlendirme_orani')}, 'NPV': npv[0], 'NPV_lo': npv[1], 'NPV_hi': npv[2],
            'yonlendirilen': int(d.sum())}


def compare(rows, disease, group, scheme, y, dm, name_m, dr, name_r, extra=''):
    mm, mr = metr(y, dm), metr(y, dr)
    pos = mcnemar(y, dm, dr, 'pos')
    neg = mcnemar(y, dm, dr, 'neg')
    for who, name, m in (('model', name_m, mm), ('referans', name_r, mr)):
        rows.append(dict(etiket=LABEL, hastalik=disease, grup=group, karsilastirma=scheme, taraf=who, kural=name,
                         n=len(y), pos=int(y.sum()), **m, not_=extra))
    rows.append(dict(etiket=LABEL, hastalik=disease, grup=group, karsilastirma=scheme, taraf='fark (model − referans)',
                     kural=f'{name_m} vs {name_r}', n=len(y), pos=int(y.sum()),
                     dR=mm['R'] - mr['R'], dFPR=mm['FPR'] - mr['FPR'], dP=mm['P'] - mr['P'],
                     dYonlendirme=mm['yonlendirme_orani'] - mr['yonlendirme_orani'],
                     mcnemar_pozitif_model_yalniz=pos[0], mcnemar_pozitif_ref_yalniz=pos[1], mcnemar_pozitif_p=pos[2],
                     mcnemar_negatif_model_yalniz=neg[0], mcnemar_negatif_ref_yalniz=neg[1], mcnemar_negatif_p=neg[2],
                     not_=extra))


def schemes(rows, disease, group, y, p, thr, ref_score, ref_name, ref_std_dec, ref_std_name):
    """ref_score: yüksek = riskli yönde (OST için −OST)."""
    dm = p >= thr
    R_m, k_m = E.decision_metrics(y, dm)['R'], int(dm.sum())
    # 1) eşit duyarlılık: referans eşiği testte modelin Recall'una (≥) eşlenir
    t_r = thr_recall_ge(y, ref_score, R_m)
    compare(rows, disease, group, 'eşit duyarlılık (referans eşiği testte model Recall\'una eşlendi)', y, dm,
            'model (kilitli eşik)', ref_score >= t_r, f'{ref_name} ≥ {t_r:.4g} (testte eşlenmiş)',
            f'hedef Recall {R_m:.3f}')
    # 2a) eşit yönlendirme: referans top-k, k = modelin kilitli eşikte yönlendirdiği kişi sayısı
    dr, ties = topk(ref_score, k_m)
    compare(rows, disease, group, 'eşit yönlendirme (referans en yüksek k; k = model yönlendirmesi)', y, dm,
            'model (kilitli eşik)', dr, f'{ref_name} en yüksek {k_m}', f'sınırdaki eşit referans skoru: {ties} kişi')
    # 2b) referansın standart eşiği ile aynı sayıda kişiyi yönlendiren model (top-k)
    k_r = int(ref_std_dec.sum())
    dmk, ties = topk(p, k_r)
    compare(rows, disease, group, f'eşit yönlendirme (model en yüksek k; k = {ref_std_name} yönlendirmesi)', y, dmk,
            f'model en yüksek {k_r}', ref_std_dec, ref_std_name, f'sınırdaki eşit model skoru: {ties} kişi')


def gate_rows(df, analiz, m):
    r = df[df.analiz == analiz].iloc[0]
    ok = all(int(r[c]) == int(m[c]) for c in ('TP', 'FP', 'TN', 'FN'))
    return dict(analiz=analiz, kayitli={c: int(r[c]) for c in ('TP', 'FP', 'TN', 'FN')},
                yeniden={c: int(m[c]) for c in ('TP', 'FP', 'TN', 'FN')}, ok=ok)


def auc_gate(df, analiz, y, s, key='AUC'):
    r = df[df.analiz == analiz].iloc[0]
    v = E.roc_auc_score(y, s)
    return dict(analiz=analiz, metrik=key, kayitli=float(r[key]), yeniden=float(v), ok=abs(float(r[key]) - v) < 1e-12)


def dauc_gate(df, analiz, y, a, b):
    r = df[df.analiz == analiz].iloc[0]
    d = E.paired_delta(y, a, b)        # özgün fazdaki tohum (p30_engine.SEED) ile
    ok = all(abs(float(r[k]) - d[k]) < 1e-12 for k in ('dAUC', 'dAUC_lo', 'dAUC_hi'))
    return dict(analiz=analiz, metrik='dAUC (özgün tohum)', kayitli=[float(r[k]) for k in ('dAUC', 'dAUC_lo', 'dAUC_hi')],
                yeniden=[d[k] for k in ('dAUC', 'dAUC_lo', 'dAUC_hi')], ok=ok)


def delta_rows(rows, disease, group, y, p, s, ref_name):
    d = E.paired_delta(y, p, s, n=NBOOT, seed=SEED)
    a = E.boot_auc_ap(y, p, n=NBOOT, seed=SEED)
    b = E.boot_auc_ap(y, s, n=NBOOT, seed=SEED)
    rows.append(dict(etiket=LABEL, hastalik=disease, grup=group, karsilastirma='ΔAUC (paired stratified bootstrap 2000, seed 20261120)',
                     taraf='fark (model − referans)', kural=f'model vs {ref_name}', n=len(y), pos=int(y.sum()),
                     AUC_model=a['AUC'], AUC_model_lo=a['AUC_lo'], AUC_model_hi=a['AUC_hi'],
                     AUC_ref=b['AUC'], AUC_ref_lo=b['AUC_lo'], AUC_ref_hi=b['AUC_hi'],
                     dAUC=d['dAUC'], dAUC_lo=d['dAUC_lo'], dAUC_hi=d['dAUC_hi']))


def fibrosis(rows, gates, meta):
    P31 = V2 / 'phase_xxxi'
    lock = json.loads((P31 / 'config/fibrosis_model_lock.json').read_text(encoding='utf8'))
    assert (P31 / 'results/fibrosis_test_opened.json').exists(), 'fibrozis testi açılmamış: bu analiz yapılamaz'
    mf = P31 / lock['model_file']
    assert sha(mf) == lock['model_sha256']
    t = pd.read_pickle(P31 / 'data/processed/fib_test_sealed.pkl')
    meta['fibrosis'] = dict(model_sha256=lock['model_sha256'], test_file_sha256=sha(P31 / 'data/processed/fib_test_sealed.pkl'),
                            threshold=lock['threshold'], n=len(t))
    y = t.target.to_numpy().astype(int)
    p = joblib.load(mf).predict_proba(t[lock['features']])[:, 1]
    f4, nf = fib4(t).to_numpy(), nfs(t).to_numpy()
    rec = pd.read_csv(P31 / 'results/fibrosis_test_results.csv')
    thr = lock['threshold']
    gates += [gate_rows(rec, 'BİRİNCİL: LSM≥8, kilitli eşik', E.decision_metrics(y, p >= thr)),
              auc_gate(rec, 'BİRİNCİL: LSM≥8, kilitli eşik', y, p),
              gate_rows(rec, 'FIB-4≥1.3', E.decision_metrics(y, f4 >= 1.3)),
              gate_rows(rec, 'FIB-4≥2.67', E.decision_metrics(y, f4 >= 2.67)),
              gate_rows(rec, 'NFS≥−1.455', E.decision_metrics(y, nf >= -1.455)),
              gate_rows(rec, 'NFS>0.676', E.decision_metrics(y, nf > 0.676)),
              auc_gate(rec, 'FIB-4≥1.3', y, f4), auc_gate(rec, 'NFS≥−1.455', y, nf),
              dauc_gate(rec, 'FIB-4≥1.3', y, p, f4), dauc_gate(rec, 'NFS≥−1.455', y, p, nf)]
    for sx in ('female', 'male'):
        k = (t.sex == sx).to_numpy()
        gates.append(gate_rows(rec, f'{sx}: birincil tek eşik', E.decision_metrics(y[k], p[k] >= thr)))
    if not all(g['ok'] for g in gates):
        return False
    groups = [('tümü', np.ones(len(t), bool)), ('kadın', (t.sex == 'female').to_numpy()), ('erkek', (t.sex == 'male').to_numpy())]
    for g, k in groups:
        for name, s, dec, dname in (('FIB-4', f4, f4 >= 1.3, 'FIB-4 ≥ 1,30'), ('NFS', nf, nf >= -1.455, 'NFS ≥ −1,455')):
            schemes(rows, 'fibrozis', g, y[k], p[k], thr, s[k], name, dec[k], dname)
            delta_rows(rows, 'fibrozis', g, y[k], p[k], s[k], name)
        # yüksek eşikler (yalnız tanımlayıcı; karar satırları)
        for name, dec in (('FIB-4 ≥ 2,67', f4 >= 2.67), ('NFS > 0,676', nf > 0.676)):
            rows.append(dict(etiket=LABEL, hastalik='fibrozis', grup=g, karsilastirma='referans yüksek eşik (tek başına)',
                             taraf='referans', kural=name, n=int(k.sum()), pos=int(y[k].sum()), **metr(y[k], dec[k])))
    return True


def osteo(rows, gates, meta):
    P30 = V2 / 'phase_xxx'
    lock = json.loads((P30 / 'config/osteo_model_lock.json').read_text(encoding='utf8'))
    assert (P30 / 'results/osteo_test_opened.json').exists(), 'osteo testi açılmamış: bu analiz yapılamaz'
    mf = P30 / lock['model_file']
    assert sha(mf) == lock['model_sha256']
    t = pd.read_pickle(P30 / 'data/processed/osteo_test_sealed.pkl')
    meta['osteo'] = dict(model_sha256=lock['model_sha256'], test_file_sha256=sha(P30 / 'data/processed/osteo_test_sealed.pkl'),
                         threshold=lock['threshold'], n=len(t))
    y = t.target.to_numpy().astype(int)
    p = joblib.load(mf).predict_proba(t[lock['features']])[:, 1]
    o = ost(t).to_numpy()
    thr = lock['threshold']
    prim = np.where(t.sex == 'female', o < 2, o <= 3)
    rec = pd.read_csv(P30 / 'results/osteo_test_results.csv')
    groups = [('tümü', np.ones(len(t), bool)), ('kadın', (t.sex == 'female').to_numpy()), ('erkek', (t.sex == 'male').to_numpy())]
    for g, k in groups:
        gates.append(gate_rows(rec, f'BİRİNCİL MODEL (D+E+F+H) — {g}', E.decision_metrics(y[k], p[k] >= thr)))
        gates.append(auc_gate(rec, f'BİRİNCİL MODEL (D+E+F+H) — {g}', y[k], p[k]))
        gates.append(gate_rows(rec, f'OST birincil (K<2, E<=3) — {g}', E.decision_metrics(y[k], prim[k])))
        gates.append(dauc_gate(rec, f'OST birincil (K<2, E<=3) — {g}', y[k], p[k], -o[k]))
    if not all(g['ok'] for g in gates):
        return False
    for g, k in groups[1:]:                      # kadın ve erkek AYRI (birincil); tümü yalnız bağlam
        std_name = 'OST < 2 (kadın)' if g == 'kadın' else 'OST ≤ 3 (erkek)'
        note = '' if g == 'kadın' else 'OST erkekte özgün geliştirme popülasyonu dışında (bkz. §1)'
        schemes(rows, 'osteoporoz', g, y[k], p[k], thr, -o[k], '−OST', prim[k], std_name)
        delta_rows(rows, 'osteoporoz', g, y[k], p[k], -o[k], '−OST')
        if note:
            for r in rows:
                if r['hastalik'] == 'osteoporoz' and r['grup'] == g and not r.get('not_'):
                    r['not_'] = note
    k = groups[0][1]
    delta_rows(rows, 'osteoporoz', 'tümü (bağlam; cinsiyete özgü OST eşikleri)', y[k], p[k], -o[k], '−OST')
    return True


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, gates, meta = [], [], dict(seed=SEED, n_boot=NBOOT, label=LABEL, p30_engine_seed=E.SEED,
                                     python=sys.version.split()[0], executable=sys.executable)
    ok_f = fibrosis(rows, gates, meta)
    ok_o = osteo(rows, gates, meta)
    (OUT / 'reference_score_gate.json').write_text(json.dumps(dict(all_ok=ok_f and ok_o, gates=gates), ensure_ascii=False,
                                                              indent=1, default=float), encoding='utf8')
    assert ok_f and ok_o, 'KAPI: kayıtlı sonuçlar birebir üretilemedi; analiz durduruldu'
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'reference_score_analysis.csv', index=False, encoding='utf-8')
    (OUT / 'reference_score_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf8')
    print('kapı', sum(g['ok'] for g in gates), '/', len(gates), 'satır', len(df))


if __name__ == '__main__':
    main()
