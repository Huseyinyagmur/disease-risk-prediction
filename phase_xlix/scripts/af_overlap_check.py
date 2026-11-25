"""Phase XLIX — Hoca 3a: PTB-XL <-> Challenge 2021 ve Challenge kaynakları arası kayıt/hasta çakışması kontrolü.

Yeni test açılışı YOK, model yüklenmez, tahmin üretilmez. Yalnız kimlik/başlık meta verisi ve ham EKG sinyal
hash'leri (etiket ve sonuç verisi değil) okunur. Tüm girdiler önceki fazlarda indirilmiş, salt okunur dosyalardır.

Kontroller
  A. Kimlik ad alanı: kullanılan Challenge kayıtlarının adları/kaynakları; Challenge'ın PTB-XL kopyası 'HR' önekli.
  B. Başlık meta verisi parmak izi: (yaş, cinsiyet, uzunluk=5000 @500 Hz, ritim etiketi) PTB-XL AF kohortu vs Challenge.
  C. Sinyal hash'i: yerelde bulunan PTB-XL 500 Hz dalga formlarının pencere hash'i (ilk 5000 örnek x 12 lead, int16;
     Phase XXIX yöntemi) vs kullanılan tüm Challenge kayıtlarının pencere hash'leri.
  D. Kaynaklar arası yakın kopya: aynı (yaş, cinsiyet, Dx, uzunluk) olan farklı kaynak çiftlerinde lead II ilk 5000
     örnek Pearson korelasyonu (r >= 0,99 -> yakın kopya adayı). Aynı kaynak içi çiftler de ayrıca sayılır.
Kullanım: .venv/Scripts/python.exe -B phase_xlix/scripts/af_overlap_check.py
"""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

V2 = Path(__file__).resolve().parents[2]
OUT = V2 / 'phase_xlix/results'
PTB = V2 / 'All_Disease_Improvement_Phase21/data/raw/ptbxl/ptbxl_database.csv'
SPLITS = V2 / 'All_Disease_Improvement_Phase21/config/af_splits.json'
REC33 = V2 / 'phase_xxxiii/results/records33.csv'
HDR33 = V2 / 'phase_xxxiii/results/all_headers33.csv'
H29 = V2 / 'phase_xxix/results/candidate_hashes.csv'
H33 = V2 / 'phase_xxxiii/results/b_afl_hashes.csv'
RAW = [V2 / 'phase_xxix/data/raw', V2 / 'phase_xxxiii/data/raw']
LOCAL_PTB = [V2 / 'phase_xxviii/data/ptbxl500', V2 / 'Clinical_Model_Improvement_Phase24/data/raw/af_golden',
             V2 / 'app/frontend/public/samples']
R_THR = 0.99


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_ptb_dat(hea):
    """PTB-XL WFDB format 16: 12 lead int16, örnekler iç içe. (12, n) döner."""
    lines = hea.read_text().splitlines()
    nsig, fs, n = (int(float(x)) for x in lines[0].split()[1:4])
    fmt = {ln.split()[1] for ln in lines[1:1 + nsig]}
    assert fmt == {'16'} and nsig == 12, (hea, fmt, nsig)
    v = np.fromfile(hea.with_suffix('.dat'), dtype='<i2').reshape(n, nsig).T
    return v, fs


def win_hash(v):
    w = np.ascontiguousarray(v[:, :5000]).astype('<i2')
    return hashlib.sha256(w.tobytes()).hexdigest()


def find_mat(rel):
    for r in RAW:
        p = r / f'{rel}.mat'
        if p.exists():
            return p
    return None


def main():
    res = {'inputs': {str(p.relative_to(V2)).replace('\\', '/'): sha(p) for p in [PTB, SPLITS, REC33, HDR33, H29, H33]}}
    used = pd.read_csv(REC33, usecols=['rel', 'record', 'source', 'grp', 'y', 'age', 'sex', 'dx', 'origin', 'status'])
    hdr = pd.read_csv(HDR33, usecols=['record', 'fs', 'sig_len', 'source', 'rel'])
    used = used.merge(hdr[['rel', 'fs', 'sig_len']], on='rel', how='left')

    # ---- A. kimlik ad alanı
    pref = used.record.str.extract(r'^([A-Z]+)')[0]
    res['A_identifier'] = {
        'used_records': int(len(used)),
        'used_sources': used.source.value_counts().to_dict(),
        'used_prefixes': pref.value_counts().to_dict(),
        'used_with_HR_prefix_(Challenge_PTB-XL_copy)': int(pref.eq('HR').sum()),
        'headers_scanned_all_4_sources': int(len(hdr)),
        'headers_from_ptb-xl_or_ptb_source': int(hdr.source.isin(['ptb-xl', 'ptb']).sum()),
        'note': 'Challenge 2021 PTB-XL kopyası "HR#####" adlıdır (training/ptb-xl); kullanılan kaynaklar A/Q/JS/E önekli.',
    }

    # ---- PTB-XL AF kohortu (Phase21 kuralı: hasta başına ilk EKG; split dosyasındaki kişiler)
    p = pd.read_csv(PTB, usecols=['ecg_id', 'patient_id', 'age', 'sex', 'scp_codes', 'strat_fold', 'filename_hr'])
    first = p.sort_values('ecg_id').drop_duplicates('patient_id')
    sp = json.loads(SPLITS.read_text(encoding='utf8'))
    role = {int(float(pid.split('_')[1])): r for r, ids in sp.items() for pid in ids}
    coh = first[first.patient_id.astype(int).map(role).notna()].copy()
    coh['role'] = coh.patient_id.astype(int).map(role)
    codes = coh.scp_codes.map(ast.literal_eval)
    coh['lab'] = np.where(codes.map(lambda c: 'AFIB' in c), 'AF', 'SR')
    coh['sex_s'] = coh.sex.map({0: 'male', 1: 'female'})
    coh['age_i'] = coh.age.where(coh.age < 300)  # 300 = HIPAA >89 kodu
    res['ptbxl_cohort'] = {'n': int(len(coh)), 'by_role': {f'{a}|{b}': int(n) for (a, b), n in coh.groupby(['role', 'lab']).size().items()}}

    # ---- B. meta veri parmak izi
    u = used[used.status.eq('ok') & used.grp.isin(['AF', 'SR'])].copy()
    u['age_i'] = u.age
    u['len5000_500'] = u.sig_len.eq(5000) & u.fs.eq(500)
    fp_cols = ['age_i', 'sex', 'lab']
    u['lab'] = u.grp
    c = coh.drop(columns=['sex']).rename(columns={'sex_s': 'sex'})
    m = u[u.len5000_500].merge(c[['ecg_id', 'role', 'age_i', 'sex', 'lab']], on=fp_cols, how='inner')
    res['B_metadata_fingerprint'] = {
        'challenge_AF_SR_used': int(len(u)),
        'challenge_AF_SR_used_len5000_fs500': int(u.len5000_500.sum()),
        'fingerprint': 'yaş + cinsiyet + ritim etiketi (AF/SR) + uzunluk 5000 örnek @500 Hz',
        'matching_pairs': int(len(m)),
        'challenge_records_with_>=1_match': int(m.rel.nunique()),
        'ptbxl_records_with_>=1_match': int(m.ecg_id.nunique()),
        'ptbxl_test_records_with_>=1_match': int(m[m.role.eq('test')].ecg_id.nunique()),
        'mean_candidates_per_matched_challenge_record': round(len(m) / max(m.rel.nunique(), 1), 1),
        'interpretation': 'Başlık meta verisi kayıtları tekil tanımlamaz (Challenge başlığında hasta kimliği, tarih, cihaz '
                          'yok); eşleşmeler aynı yaş/cinsiyet/ritmin çok sayıda kişide bulunmasından gelir. Bu kontrol '
                          'çakışmayı ne kanıtlar ne dışlar; karar için sinyal karşılaştırması gerekir (C).',
    }

    # ---- C. sinyal hash'i: yerel PTB-XL dalga formları
    ch = pd.concat([pd.read_csv(H29, usecols=['rel', 'source', 'win_hash', 'full_hash']),
                    pd.read_csv(H33, usecols=['rel', 'source', 'win_hash', 'full_hash'])]).drop_duplicates('rel')
    ch_win = set(ch.win_hash)
    local = []
    for d in LOCAL_PTB:
        for hea in sorted(d.glob('*_hr.hea')):
            v, fs = read_ptb_dat(hea)
            local.append(dict(file=str(hea.relative_to(V2)).replace('\\', '/'), ecg_id=int(hea.stem.split('_')[0]),
                              fs=fs, n=v.shape[1], win_hash=win_hash(v)))
    loc = pd.DataFrame(local).drop_duplicates('ecg_id')
    loc = loc.merge(p[['ecg_id', 'patient_id']], on='ecg_id', how='left')
    loc['role'] = loc.patient_id.astype(int).map(role).fillna('kohort dışı')
    hits = loc[loc.win_hash.isin(ch_win)]
    res['C_signal_hash'] = {
        'challenge_hashes_compared': int(len(ch)),
        'challenge_hash_sources': ch.source.value_counts().to_dict(),
        'local_ptbxl_waveforms_unique': int(len(loc)),
        'local_ptbxl_by_af_role': loc.role.value_counts().to_dict(),
        'window_hash_matches': int(len(hits)),
        'matched_files': hits.file.tolist(),
        'coverage_note': f'PTB-XL 21.799 kaydının yalnız {len(loc)} tanesi yerelde (records500 indirilmedi); '
                         'tam kayıt düzeyi karşılaştırma için records500 (~1,7 GB) gerekir.',
    }

    # ---- D. Challenge içi yakın kopya taraması (korelasyon)
    uu = used[used.status.eq('ok')].copy()
    uu['key'] = (uu.age.astype(str) + '|' + uu.sex + '|' + uu.dx.astype(str) + '|' + uu.sig_len.astype(str))
    grp = uu.groupby('key')
    multi = grp.filter(lambda g: len(g) > 1)
    need = multi.rel.unique()
    lead2 = {}
    missing = 0
    for rel in need:
        mp = find_mat(rel)
        if mp is None:
            missing += 1
            continue
        x = loadmat(mp)['val'][1, :5000].astype(float)
        x = x - x.mean()
        s = np.linalg.norm(x)
        lead2[rel] = x / s if s > 0 else None
    pairs = []
    n_cross = n_within = 0
    for key, g in multi.groupby('key'):
        g = g[g.rel.map(lambda r: lead2.get(r) is not None)]
        if len(g) < 2:
            continue
        X = np.vstack([lead2[r] for r in g.rel])
        C = X @ X.T
        rels, srcs = g.rel.tolist(), g.source.tolist()
        iu = np.triu_indices(len(g), 1)
        cross = np.array([srcs[i] != srcs[j] for i, j in zip(*iu)])
        n_cross += int(cross.sum())
        n_within += int((~cross).sum())
        for (i, j), r in zip(zip(*iu), C[iu]):
            if r >= R_THR:
                pairs.append(dict(rel_a=rels[i], rel_b=rels[j], source_a=srcs[i], source_b=srcs[j],
                                  cross_source=srcs[i] != srcs[j], r_leadII=round(float(r), 5), key=key))
    pdf = pd.DataFrame(pairs, columns=['rel_a', 'rel_b', 'source_a', 'source_b', 'cross_source', 'r_leadII', 'key'])
    pdf.to_csv(OUT / 'af_near_duplicate_pairs.csv', index=False)

    # Pozitif kontrol: Phase XXIX'un birebir kopya grupları (kullanılan kümeden dışlananlar dahil) bu ölçütle yakalanmalı
    dup = pd.read_csv(V2 / 'phase_xxix/results/duplicates.csv')
    pc = []
    for h, g in dup.groupby('win_hash'):
        vs = []
        for rel in g.rel:
            mp = find_mat(rel)
            if mp is not None:
                x = loadmat(mp)['val'][1, :5000].astype(float)
                x = x - x.mean()
                vs.append(x / np.linalg.norm(x) if np.linalg.norm(x) > 0 else None)
        vs = [v for v in vs if v is not None]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                pc.append(float(vs[i] @ vs[j]))
    pc = np.array(pc)
    res['D_positive_control'] = {'source': 'phase_xxix/results/duplicates.csv (bilinen birebir kopya grupları)',
                                 'pairs': int(len(pc)), 'detected_r>=thr': int((pc >= R_THR).sum()),
                                 'min_r': round(float(pc.min()), 6) if len(pc) else None}
    res['D_near_duplicate'] = {
        'records_ok': int(len(uu)),
        'grouping_key': 'yaş|cinsiyet|Dx kod kümesi|örnek sayısı',
        'records_in_groups_ge2': int(len(need)),
        'mat_not_found': missing,
        'pairs_tested_cross_source': n_cross,
        'pairs_tested_within_source': n_within,
        'threshold_r_leadII': R_THR,
        'flagged_cross_source': int(pdf.cross_source.sum()) if len(pdf) else 0,
        'flagged_within_source': int((~pdf.cross_source).sum()) if len(pdf) else 0,
        'note': 'Birebir kopyalar Phase XXIX/XXXIII pencere hash tekilleştirmesiyle zaten dışlanmıştı (XXIX: 226 kopya; XXXIII: 20 kopya/çelişkili grup). '
                'Bu tarama farklı kodlanmış/filtrelenmiş kopyaları arar; farklı günlerde alınmış aynı-hasta kayıtlarını '
                'tespit edemez (Challenge başlıklarında hasta kimliği yok).',
    }
    (OUT / 'af_overlap_check.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
    print(json.dumps({k: v for k, v in res.items() if k != 'inputs'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
