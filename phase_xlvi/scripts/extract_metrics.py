"""Phase XLVI — Görev 1: model kartlarının sayısal içeriğini YALNIZ önceki fazların kayıtlı sonuç dosyalarından okur.

- Yeni tahmin üretilmez; model yüklenmez; mühürlü veri okunmaz.
- TP/FP/TN/FN, P/R/FPR ve AUC (+GA) kaynak dosyadaki değerlerdir. NPV ve Wilson GA'sı kayıtlı TN/FN sayılarından
  hesaplanır (kaynak dosyada NPV yoksa); bu türetme `npv_source` alanında belirtilir.
- Her satır kaynak dosya yolunu, dosyanın SHA256'sını ve satır seçicisini taşır.
- Registry (phase_xliii/registry/models.json) evidence değerleriyle 3 ondalıkta çapraz kontrol yapılır.
Çıktı: phase_xlvi/results/card_metrics.json, phase_xlvi/results/card_metrics_check.json
Kullanım: python -B -I phase_xlvi/scripts/extract_metrics.py
"""
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
OUT = V2 / 'phase_xlvi/results'
Z = 1.959963984540054


def sha(p):
    return hashlib.sha256((V2 / p).read_bytes()).hexdigest()


def wilson(k, n):
    if n == 0:
        return [None, None, None]
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [p, max(0.0, c - h), min(1.0, c + h)]


def csv(p):
    return pd.read_csv(V2 / p)


def one(df, **kw):
    m = pd.Series(True, index=df.index)
    for k, v in kw.items():
        m &= df[k].astype(str) == str(v)
    r = df[m]
    assert len(r) == 1, (kw, len(r))
    return r.iloc[0]


def row(tier, label, src, selector, tp, fp, tn, fn, p, r, f, auc, threshold, extra=None, npv=None):
    """p/r/f: [değer, lo, hi]; auc: [değer, lo, hi] veya None."""
    tp, fp, tn, fn = (int(x) for x in (tp, fp, tn, fn))
    if npv is None:
        npv, npv_src = wilson(tn, tn + fn), 'kayıtlı TN/FN sayılarından hesaplandı (Wilson)'
    else:
        npv_src = 'kaynak dosyada kayıtlı'
    return dict(tier=tier, label=label, source=src, source_sha256=sha(src), selector=selector,
                n=tp + fp + tn + fn, n_pos=tp + fn, TP=tp, FP=fp, TN=tn, FN=fn,
                precision=[float(x) for x in p], recall=[float(x) for x in r], fpr=[float(x) for x in f],
                npv=[float(x) for x in npv], npv_source=npv_src,
                auc=[float(x) for x in auc] if auc is not None else None, threshold=threshold, **(extra or {}))


def delta(label, src, selector, d, lo, hi, base_auc=None, note=None):
    return dict(label=label, source=src, source_sha256=sha(src), selector=selector,
                dAUC=[float(d), float(lo), float(hi)], baseline_auc=base_auc, note=note)


REG = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))['models']


def thr(mid):
    return REG[mid]['thresholds']['primary']['value']


# --------------------------------------------------------------------------------------------- kaynak okuyucular
def xxvii(model, kume, tier, label, mid):
    src = 'phase_xxvii/results/ci_metrics.csv'
    r = one(csv(src), model=model, kume=kume)
    return row(tier, label, src, f'model={model}, kume={kume}', r.TP, r.FP, r.TN, r.FN,
               [r.precision, r.precision_lo, r.precision_hi], [r.recall, r.recall_lo, r.recall_hi],
               [r.fpr, r.fpr_lo, r.fpr_hi], [r.auc, r.auc_lo, r.auc_hi], float(r.esik),
               extra=dict(evidence_type=r.kanit_turu, dataset=r.veri_seti))


def xxvii_base(model, kume, baseline):
    src = 'phase_xxvii/results/baselines.csv'
    r = one(csv(src), model=model, kume=kume, baseline=baseline)
    return delta(f'model − {baseline}', src, f'model={model}, kume={kume}, baseline={baseline}', r.delta_auc,
                 r.delta_lo, r.delta_hi, base_auc=float(r.base_auc), note=f'karar: {r.karar}')


def xxxiii(fname, analiz, kapsam, tier, label):
    src = f'phase_xxxiii/results/{fname}'
    df = csv(src)
    r = one(df, analiz=analiz, skor='MODEL', kapsam=kapsam)
    b = one(df, analiz=analiz, skor='BASELINE', kapsam=kapsam)
    out = row(tier, label, src, f'analiz={analiz}, skor=MODEL, kapsam={kapsam}', r.TP, r.FP, r.TN, r.FN,
              [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi], [r.AUC, r.AUC_lo, r.AUC_hi],
              thr('af_S4_DEVICE'), extra=dict(note=None if pd.isna(r.yorum) else r.yorum,
                                             precision_reportable=False))
    out['delta'] = [delta('model − RR_iqr/RR_mean ≥ 0,138235', src,
                          f'analiz={analiz}, skor=MODEL, kapsam={kapsam} (dAUC)', r.dAUC, r.dAUC_lo, r.dAUC_hi,
                          base_auc=float(b.AUC))]
    return out


def af():
    rows = [xxvii('af', 'test', 'internal_test', 'İç test — PTB-XL fold 10 (hasta düzeyinde ayrık)', 'af_S4_DEVICE')]
    rows[0]['delta'] = [xxvii_base('af', 'test', 'RR_iqr / RR_mean')]
    rows.append(xxxiii('a2_results.csv', 'A2 — birincil', 'Havuz (4 kaynak, ikincil)', 'external',
                       'Dış doğrulama — Challenge 2021, 4 kaynak havuzu, AF vs SR (A2)'))
    for k in ('CPSC 2018', 'CPSC-Extra', 'Chapman-Shaoxing', 'Georgia'):
        rows.append(xxxiii('a2_results.csv', 'A2 — birincil', k, 'external_source', f'Dış doğrulama — {k}, AF vs SR (A2)'))
    rows.append(xxxiii('b_results.csv', 'B — birincil', 'Havuz (4 kaynak, ikincil)', 'external_secondary',
                       'Dış — ikincil analiz: AF vs SR + diğer ritimler (B), havuz'))
    return rows


def mi():
    src, sa, sd = ('phase_xxxviii/results/test_operating_points.csv', 'phase_xxxviii/results/test_auc.csv',
                   'phase_xxxviii/results/test_delta_auc.csv')
    out = []
    for kume, tier, lab in (('birincil_tum_test', 'internal_test', 'İç test — tümü (fold 9 + fold 10 AF-test dışı)'),
                            ('birincil_temiz', 'internal_test_subset', 'İç test — temiz alt küme (PREVIOUSLY_EXPOSED hariç)')):
        df = csv(src)
        r = df[(df.kume == kume) & (df.model == 'MODEL(LightGBM)') & df.esik_turu.str.startswith('KILITLI')]
        assert len(r) == 1
        r = r.iloc[0]
        a = one(csv(sa), kume=kume, model='MODEL')
        o = row(tier, lab, src, f'kume={kume}, model=MODEL(LightGBM), esik_turu=KILITLI…', r.TP, r.FP, r.TN, r.FN,
                [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi], [a.AUC, a.AUC_lo, a.AUC_hi],
                float(r.esik), npv=[r.NPV, r.NPV_lo, r.NPV_hi], extra=dict(auc_source=sa))
        d = one(csv(sd), kume=kume, karsilastirma='MODEL-B1_yas_cinsiyet')
        b1 = one(csv(sa), kume=kume, model='B1_yas_cinsiyet')
        o['delta'] = [delta('model − B1 yaş+cinsiyet LR', sd, f'kume={kume}, karsilastirma=MODEL-B1_yas_cinsiyet',
                            d.dAUC, d.dAUC_lo, d.dAUC_hi, base_auc=float(b1.AUC)),
                      delta('model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz)', sd,
                            f'kume={kume}, karsilastirma=MODEL-B2_Q_kurali',
                            *one(csv(sd), kume=kume, karsilastirma='MODEL-B2_Q_kurali')[['dAUC', 'dAUC_lo', 'dAUC_hi']],
                            note='B2 AUC < 0,5; geçerli kural baseline\'ı kurulamadı (Phase XXXVIII 02 §4)')]
        out.append(o)
    return out


def cad():
    o = xxvii('cad', 'test', 'internal_test', 'İç test — UCI Cleveland (önceden açılmış)', 'cad_DEVICE')
    o['delta'] = [xxvii_base('cad', 'test', 'LR(age, sex)'), xxvii_base('cad', 'test', 'Tek değişken: thalach (− yön; fit AUC=0.282)')]
    out = [o]
    src = 'phase_xli/results/cad_v2_rescore.json'
    js = json.loads((V2 / src).read_text(encoding='utf8'))
    for k, lab in (('hungarian', 'Teknik tekrar — UCI Hungarian (eksiksiz vaka, seçilmiş)'),
                   ('va', 'Teknik tekrar — UCI VA Long Beach (eksiksiz vaka, seçilmiş)')):
        m = js['sets'][k]['model']
        r = row('technical_replication', lab, src, f'sets.{k}.model', m['TP'], m['FP'], m['TN'], m['FN'],
                [m['precision'], m['precision_lo'], m['precision_hi']], [m['recall'], m['recall_lo'], m['recall_hi']],
                [m['fpr'], m['fpr_lo'], m['fpr_hi']], [m['auc'], m['auc_lo'], m['auc_hi']], js['threshold'],
                npv=[m['npv'], m['npv_lo'], m['npv_hi']], extra=dict(note=js['label']))
        b = js['sets'][k]['baselines']['LR(age, sex)']
        r['delta'] = [delta('model − LR(yaş, cinsiyet)', src, f'sets.{k}.baselines.LR(age, sex).delta_vs_model',
                            b['delta_vs_model']['delta_auc'], b['delta_vs_model']['delta_lo'], b['delta_vs_model']['delta_hi'],
                            base_auc=b['auc'], note=b['delta_vs_model']['decision'])]
        out.append(r)
    return out


def dm(model_label, disc_label, mid, deltas):
    src, sd, sdel = ('phase_xlii/results/test_operating_points.csv', 'phase_xlii/results/test_discrimination.csv',
                     'phase_xlii/results/test_delta_auc.csv')
    r = one(csv(src), model=model_label, nokta='birincil Recall>=0.75 (kilitli)')
    a = one(csv(sd), skor=disc_label)
    o = row('internal_test', 'İç test — NHANES G 2011–12 + H 2013–14 (kilitli tek sefer)', src,
            f'model={model_label}, nokta=birincil Recall>=0.75 (kilitli)', r.TP, r.FP, r.TN, r.FN,
            [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi], [a.AUC, a.AUC_lo, a.AUC_hi],
            float(r.esik), npv=[r.NPV, r.NPV_lo, r.NPV_hi], extra=dict(auc_source=sd))
    disc = csv(sd)
    o['delta'] = []
    for k, base in deltas:
        d = one(csv(sdel), karsilastirma=k)
        ba = float(disc[disc.skor == base].AUC.iloc[0]) if base else None
        o['delta'].append(delta(k, sdel, f'karsilastirma={k}', d.dAUC, d.dAUC_lo, d.dAUC_hi, base_auc=ba,
                                note=f'tür: {d.tur}'))
    return [o]


def anemia():
    o = xxvii('anemia', 'test', 'internal_test', 'İç test — NHANES A 1999–2000 (Phase25 holdout; önceden açılmış)', 'anemia_LR16')
    o['delta'] = [xxvii_base('anemia', 'test', 'Hct_proxy=RBC×MCV/10 sabit (E<39, K<36)')]
    out = [o]
    src = 'phase_xl/results/anemia_external.json'
    js = json.loads((V2 / src).read_text(encoding='utf8'))
    names = dict(pooled='NHANES C, E, F, I birleşik', C='NHANES C 2003–04', E='NHANES E 2007–08', F='NHANES F 2009–10',
                 I='NHANES I 2015–16')
    for k in ('pooled', 'C', 'E', 'F', 'I'):
        m = js['sets'][k]['model']
        r = row('external' if k == 'pooled' else 'external_source',
                f'Farklı döngüler (aynı program; bağımsız kurum değil) — {names[k]}', src, f'sets.{k}.model',
                m['TP'], m['FP'], m['TN'], m['FN'], [m['precision'], m['precision_lo'], m['precision_hi']],
                [m['recall'], m['recall_lo'], m['recall_hi']], [m['fpr'], m['fpr_lo'], m['fpr_hi']],
                [m['auc'], m['auc_lo'], m['auc_hi']], js['threshold'], npv=[m['npv'], m['npv_lo'], m['npv_hi']],
                extra=dict(note=js['label']))
        d = js['sets'][k]['delta_auc']
        r['delta'] = [delta('model − Hct_proxy kuralı', src, f'sets.{k}.delta_auc', d['delta_auc'], d['delta_lo'],
                            d['delta_hi'], base_auc=js['sets'][k]['baseline_hct']['auc'], note=d['decision'])]
        out.append(r)
    return out


def copd():
    o = xxvii('copd', 'test', 'internal_test', 'İç test — NHANES G 2011–12', 'copd_S4_DEVICE')
    o['delta'] = [xxvii_base('copd', 'test', 'pre-BD FEV1/FVC < 0.70')]
    out = [o]
    for kume, lab in (('F_2009_2010', 'Zamansal tekrar — NHANES F 2009–10'), ('E_2007_2008', 'Zamansal tekrar — NHANES E 2007–08')):
        r = xxvii('copd', kume, 'temporal' if kume.startswith('F') else 'temporal_secondary', lab, 'copd_S4_DEVICE')
        r['delta'] = [xxvii_base('copd', kume, 'pre-BD FEV1/FVC < 0.70')]
        out.append(r)
    return out


def hf():
    o = xxvii('heart_failure', 'test', 'internal_test', 'İç test — Mendeley 7v4w66wxj8.1 (n=37)', 'hf_S2_BASIC_LAB')
    o['delta'] = [xxvii_base('heart_failure', 'test', 'LR(age, sex, bmi)'),
                  xxvii_base('heart_failure', 'test', 'Tek değişken: rip3 (+ yön; fit AUC=0.927)')]
    return [o]


def htn():
    src, sa, sd = ('phase_xxxvii/results/test_operating_points.csv', 'phase_xxxvii/results/test_auc.csv',
                   'phase_xxxvii/results/test_delta_auc.csv')
    r = one(csv(src), model='M1', esik_turu='birincil_Recall>=0.75')
    a = one(csv(sa), model='M1')
    o = row('temporal', 'Zamansal test — NHANES C 2003–04 (ölçüm yöntemi kaymalı)', src, 'model=M1, esik_turu=birincil_Recall>=0.75',
            r.TP, r.FP, r.TN, r.FN, [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi],
            [a.AUC, a.AUC_lo, a.AUC_hi], float(r.esik), npv=[r.NPV, r.NPV_lo, r.NPV_hi], extra=dict(auc_source=sa))
    d = one(csv(sd), karsilastirma='M1-BASELINE')
    o['delta'] = [delta('M1 − LR(yaş, cinsiyet, BMI)', sd, 'karsilastirma=M1-BASELINE', d.dAUC, d.dAUC_lo, d.dAUC_hi,
                        base_auc=float(one(csv(sa), model='BASELINE').AUC))]
    return [o]


def fibrosis():
    src = 'phase_xxxi/results/fibrosis_test_results.csv'
    df = csv(src)
    r = one(df, analiz='BİRİNCİL: LSM≥8, kilitli eşik')
    o = row('internal_test', 'İç test — NHANES L 2021–23 (PREVIOUSLY_EXPOSED)', src, 'analiz=BİRİNCİL: LSM≥8, kilitli eşik',
            r.TP, r.FP, r.TN, r.FN, [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi],
            [r.AUC, r.AUC_lo, r.AUC_hi], thr('fibrosis_final'), npv=[r.NPV, r.NPV_lo, r.NPV_hi])
    o['delta'] = []
    for b in ('FIB-4≥1.3', 'NFS≥−1.455'):
        x = one(df, analiz=b)
        o['delta'].append(delta(f'model − {b.split("≥")[0]}', src, f'analiz={b} (dAUC)', x.dAUC, x.dAUC_lo, x.dAUC_hi,
                                base_auc=float(x.AUC)))
    return [o]


def osteo():
    src = 'phase_xxx/results/osteo_test_results.csv'
    df = csv(src)
    out = []
    for g, tier, lab in (('tümü', 'temporal', 'Zamansal test — NHANES J 2017–18'),
                         ('kadın', 'temporal_subgroup', 'Zamansal test — kadın'),
                         ('erkek', 'temporal_subgroup', 'Zamansal test — erkek')):
        a = f'BİRİNCİL MODEL (D+E+F+H) — {g}'
        r = one(df, analiz=a)
        o = row(tier, lab, src, f'analiz={a}', r.TP, r.FP, r.TN, r.FN, [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi],
                [r.FPR, r.FPR_lo, r.FPR_hi], [r.AUC, r.AUC_lo, r.AUC_hi], thr('osteo_final'))
        b = one(df, analiz=f'OST birincil (K<2, E<=3) — {g}')
        o['delta'] = [delta('model − (−OST)', src, f'analiz=OST birincil (K<2, E<=3) — {g} (dAUC)', b.dAUC, b.dAUC_lo,
                            b.dAUC_hi, base_auc=float(b.AUC))]
        out.append(o)
    return out


def ckd(m, mid):
    src, sd, sdel = ('phase_xxxv/results/test_operating_points.csv', 'phase_xxxv/results/test_discrimination.csv',
                     'phase_xxxv/results/test_delta_auc.csv')
    r = one(csv(src), model=m, nokta='birincil Recall≥0.75 (kilitli)')
    a = one(csv(sd), skor=f'Model {m}')
    o = row('internal_test', 'İç test — NHANES I 2015–16 (kilitli tek sefer)', src, f'model={m}, nokta=birincil Recall≥0.75 (kilitli)',
            r.TP, r.FP, r.TN, r.FN, [r.P, r.P_lo, r.P_hi], [r.R, r.R_lo, r.R_hi], [r.FPR, r.FPR_lo, r.FPR_hi],
            [a.AUC, a.AUC_lo, a.AUC_hi], float(r.esik), npv=[r.NPV, r.NPV_lo, r.NPV_hi], extra=dict(auc_source=sd))
    sc = float(one(csv(sd), skor='SCORED (modifiye)').AUC)
    o['delta'] = []
    for k in ((f'{m} − SCORED',) + (('B − A',) if m == 'B' else ())):
        d = one(csv(sdel), karsilastirma=k)
        o['delta'].append(delta(k, sdel, f'karsilastirma={k}', d.dAUC, d.dAUC_lo, d.dAUC_hi,
                                base_auc=sc if 'SCORED' in k else float(one(csv(sd), skor='Model A').AUC)))
    return [o]


BUILD = {
    'af_S4_DEVICE': af, 'mi_model': mi, 'cad_DEVICE': cad,
    'dm_A': lambda: dm('Model A (LR)', 'Model A (LR)', 'dm_A', [('A − ADA', 'ADA/Bang 2009'), ('A − yaş+BMI', 'yaş+BMI LR')]),
    'dm_B': lambda: dm('Model B (LR)', 'Model B (LR)', 'dm_B', [('B − ADA', 'ADA/Bang 2009'), ('B − A', 'Model A (LR)'),
                                                                ('B − yaş+BMI', 'yaş+BMI LR')]),
    'anemia_LR16': anemia, 'copd_S4_DEVICE': copd, 'hf_S2_BASIC_LAB': hf, 'htn_M1': htn,
    'fibrosis_final': fibrosis, 'osteo_final': osteo, 'ckd_A': lambda: ckd('A', 'ckd_A'), 'ckd_B': lambda: ckd('B', 'ckd_B'),
}

# registry evidence bloğu ↔ çıkarılan satır eşlemesi (çapraz kontrol)
REG_MAP = {
    'af_S4_DEVICE': [('internal_test', 'internal_test'), ('external', 'external')],
    'mi_model': [('internal_test', 'internal_test')], 'cad_DEVICE': [('internal_test', 'internal_test')],
    'dm_A': [('internal_test', 'internal_test')], 'dm_B': [('internal_test', 'internal_test')],
    'anemia_LR16': [('internal_test', 'internal_test'), ('external', 'external')],
    'copd_S4_DEVICE': [('internal_test', 'internal_test'), ('temporal', 'temporal')],
    'hf_S2_BASIC_LAB': [('internal_test', 'internal_test')], 'htn_M1': [('temporal', 'temporal')],
    'fibrosis_final': [('internal_test', 'internal_test')], 'osteo_final': [('temporal', 'temporal')],
    'ckd_A': [('internal_test', 'internal_test')], 'ckd_B': [('internal_test', 'internal_test')],
}


def r3(x):
    return None if x is None else round(float(x) + 1e-12, 3)


def main():
    res, checks = {}, []
    for mid, fn in BUILD.items():
        assert mid in REG, mid
        rows = fn()
        res[mid] = rows
        for reg_key, tier in REG_MAP[mid]:
            ev = REG[mid]['evidence'][reg_key]
            x = [r for r in rows if r['tier'] == tier][0]
            for k in ('precision', 'recall', 'fpr', 'auc'):
                if ev.get(k) is None:
                    continue
                for i, part in enumerate(('value', 'lo', 'hi')):
                    regv = ev[k]['value'] if part == 'value' else ev[k]['ci95'][i - 1]
                    ok = r3(x[k][i]) == r3(regv)
                    rounding = (not ok) and abs(float(x[k][i]) - float(regv)) < 0.001
                    checks.append(dict(model=mid, tier=tier, metric=f'{k}.{part}', registry=regv, extracted=r3(x[k][i]),
                                       raw=float(x[k][i]), ok=ok or rounding,
                                       status='birebir' if ok else ('yuvarlama farkı (<0,001; ham değer registry\'nin '
                                                                     'kaynak raporundaki çift yuvarlamadan)' if rounding else 'UYUŞMAZ')))
            for k, regk in (('n', 'n'), ('n_pos', 'n_pos')):
                if ev.get(regk) is not None:
                    checks.append(dict(model=mid, tier=tier, metric=k, registry=ev[regk], extracted=x[k], ok=ev[regk] == x[k]))
            if ev.get('threshold') is not None and x['threshold'] is not None:
                checks.append(dict(model=mid, tier=tier, metric='threshold', registry=ev['threshold'], extracted=x['threshold'],
                                   ok=abs(ev['threshold'] - x['threshold']) < 1e-12))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'card_metrics.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
    bad = [c for c in checks if not c['ok']]
    rnd = [c for c in checks if c.get('status', '').startswith('yuvarlama')]
    (OUT / 'card_metrics_check.json').write_text(json.dumps(dict(n_checks=len(checks), n_fail=len(bad), n_rounding=len(rnd),
                                                                 failures=bad, rounding=rnd, checks=checks),
                                                            ensure_ascii=False, indent=1), encoding='utf8')
    print('modeller', len(res), 'satir', sum(len(v) for v in res.values()), 'kontrol', len(checks), 'uyusmayan', len(bad),
          'yuvarlama', len(rnd))
    for b in bad + rnd:
        print('  ', b['model'], b['metric'], b['registry'], b['raw' if 'raw' in b else 'extracted'], b.get('status'))
    assert not bad


if __name__ == '__main__':
    main()
