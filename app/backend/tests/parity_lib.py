"""Parity: ham NHANES/UCI alanları -> input_schema alanları -> SUNUCU dönüşümleri -> feature vektörü; o fazın
GELİŞTİRME feature tablosuyla karşılaştırma (|Δ| ≤ 1e-6 veya birebir).

Yalnız geliştirme (development) tabloları okunur; *_test_sealed / *_external_sealed dosyaları OKUNMAZ.
Ham XPT/UCI dosyaları bazı fazlarda test kişilerini de içerir; okunduktan hemen sonra yalnız örneklenen geliştirme
kişilerine indirgenir (başka satırlarda hiçbir hesap yapılmaz).
Adaptör = ham kod -> şema alanı eşlemesi (kullanıcının forma gireceği değer). Fazın kendi uyumlaştırma adımları
(CDC geri denklemleri, kreatinin standardizasyonu) adaptörde uygulanır; model feature'ı adaptörde HESAPLANMAZ."""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
BACKEND = Path(__file__).resolve().parents[1]
V2 = BACKEND.parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

SEED = 20261119
N_SAMPLE = 200
TOL = 1e-6
RACE1 = {1: 'mexican_american', 2: 'other_hispanic', 3: 'nh_white', 4: 'nh_black', 5: 'other_incl_multi'}
SEALED_MARKERS = ('test_sealed', 'external_sealed', '_sealed')


def _guard(path):
    p = str(path)
    assert not any(m in p for m in SEALED_MARKERS), f'mühürlü dosya okunamaz: {p}'
    return path


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, _guard(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _v(x):
    """NaN/None -> None, numpy skaler -> python."""
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return x.item() if hasattr(x, 'item') else x


def _num(x, positive=False):
    x = _v(x)
    if x is None:
        return None
    x = float(x)
    return None if (positive and x <= 0) else x


def _yn(x):
    x = _v(x)
    return True if x == 1 else False if x == 2 else None


def _sex(x):
    x = _v(x)
    return 'male' if x == 1 else 'female' if x == 2 else None


def _race(x):
    return RACE1.get(_v(x))


def _smoking(smq020, smq040, require_ever_for_former=False):
    s20, s40 = _v(smq020), _v(smq040)
    if s40 in (1, 2):
        return 'current'
    if s40 == 3 and (s20 == 1 or not require_ever_for_former):
        return 'former'
    if s20 == 2:
        return 'never'
    return None


def _clean(fields):
    return {k: v for k, v in fields.items() if v is not None}


def sample(dev, complete_cols, n=N_SAMPLE, seed=SEED):
    pool = dev[dev[complete_cols].notna().all(axis=1)]
    k = min(n, len(pool))
    return pool.sample(n=k, random_state=seed), len(pool)


# ============================================================== DM (phase_xlii)
def dm_case(model_id):
    t1 = _import('p42_t1_data', V2 / 'phase_xlii/scripts/t1_data.py')
    dev = pd.read_pickle(_guard(V2 / 'phase_xlii/data/processed/dm_dev.pkl'))
    feats = t1.FEAT_B if model_id == 'dm_B' else t1.FEAT_A
    s, pool = sample(dev, feats)
    rows = {}
    for c, g in s.groupby('cycle'):
        d = t1.raw(c).loc[g.index]
        if c == 'J':                                     # fazın CDC BIOPRO_J geri denklemi (uyumlaştırma)
            for k, (a, b) in t1.BIOPRO_J_BACKWARD.items():
                d[k] = a * d[k] + b
        for seqn, r in d.iterrows():
            fem = _v(r.RIAGENDR) == 2
            gdm = None
            if fem:
                gdm = _yn(r.RHQ162)
                if gdm is None and _v(r.RHQ131) == 2:
                    gdm = False                          # hiç gebe kalmamış -> GDM yok
            vig, mod = _yn(r.PAQ650), _yn(r.PAQ665)
            pa = True if (vig is True or mod is True) else False if (vig is False and mod is False) else None
            f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), race_ethnicity=_race(r.RIDRETH1),
                     height_cm=_num(r.BMXHT), weight_kg=_num(r.BMXWT), waist_cm=_num(r.BMXWAIST),
                     told_hypertension=_yn(r.BPQ020), on_bp_medication=_yn(r.BPQ050A),
                     family_hx_diabetes=_yn(r.MCQ300C), gestational_diabetes_hx=gdm, recreational_activity=pa,
                     smoking_status=_smoking(r.SMQ020, r.SMQ040),
                     told_diabetes={1: True, 2: False, 3: False}.get(_v(r.DIQ010)),
                     pregnant=False if fem else None)
            for i in (1, 2, 3):
                f[f'sbp_{i}_mmhg'] = _num(r[f'BPXSY{i}'], positive=True)
                f[f'dbp_{i}_mmhg'] = _num(r[f'BPXDI{i}'], positive=True)
            if model_id == 'dm_B':
                f.update(total_chol_mgdl=_num(r.LBXTC), hdl_mgdl=_num(r.LBDHDD), tg_mgdl=_num(r.LBXSTR),
                         alt_ul=_num(r.LBXSATSI), uric_acid_mgdl=_num(r.LBXSUA))
            rows[seqn] = _clean(f)
    return s, pool, rows, dict(dev_file='phase_xlii/data/processed/dm_dev.pkl', raw='phase_xlii/data/nhanes/<E,F,I,J>/*.xpt',
                               adapter_notes=['J döngüsü BIOPRO (TG/ALT/ürik asit) CDC geri denklemi fazın kendi sabitleriyle uygulandı',
                                              'pregnant=False (popülasyon gebe değil); told_diabetes DIQ010 (3=sınırda -> hayır)'])


# ============================================================== CKD (phase_xxxv)
def ckd_case(model_id):
    t1 = _import('p35_t1_data', V2 / 'phase_xxxv/scripts/t1_data.py')
    dev = pd.read_pickle(_guard(V2 / 'phase_xxxv/data/processed/ckd_dev.pkl'))
    feats = t1.FEAT_B if model_id == 'ckd_B' else t1.FEAT_A
    s, pool = sample(dev, feats)
    rows = {}
    for c, g in s.groupby('cycle'):
        ix = g.index
        L = lambda m: t1.load(m, c).reindex(ix)
        demo, bmx, bpx, bpq, diq, mcq, smq = (L(m) for m in ('DEMO', 'BMX', 'BPX', 'BPQ', 'DIQ', 'MCQ', 'SMQ'))
        lab = pd.concat([L('BIOPRO')[['LBXSGL']], L('GHB')[['LBXGH']], L('TCHOL')[['LBXTC']], L('HDL')[['LBDHDD']],
                         L('CBC')[['LBXHGB']]], axis=1) if model_id == 'ckd_B' else None
        pills_col = 'DID070' if c == 'E' else 'DIQ070'
        for seqn in ix:
            r = demo.loc[seqn]
            told_htn = _yn(bpq.at[seqn, 'BPQ020'])
            med = _yn(bpq.at[seqn, 'BPQ050A'])
            if med is None and 'BPQ040A' in bpq and _v(bpq.at[seqn, 'BPQ040A']) == 2:
                med = False                              # ilaç önerilmemiş -> kullanmıyor
            cvd = [_yn(mcq.at[seqn, v]) for v in ('MCQ160C', 'MCQ160D', 'MCQ160E')]
            chd = True if any(x is True for x in cvd) else False if any(x is False for x in cvd) else None
            f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), race_ethnicity=_race(r.RIDRETH1),
                     height_cm=_num(bmx.at[seqn, 'BMXHT']), weight_kg=_num(bmx.at[seqn, 'BMXWT']),
                     waist_cm=_num(bmx.at[seqn, 'BMXWAIST']), told_hypertension=told_htn, on_bp_medication=med,
                     told_diabetes={1: True, 2: False, 3: False}.get(_v(diq.at[seqn, 'DIQ010'])),
                     on_insulin=_yn(diq.at[seqn, 'DIQ050']), on_diabetes_pills=_yn(diq.at[seqn, pills_col]),
                     hx_coronary_disease=chd, hx_heart_failure=_yn(mcq.at[seqn, 'MCQ160B']),
                     hx_stroke=_yn(mcq.at[seqn, 'MCQ160F']), smoking_status=_smoking(smq.at[seqn, 'SMQ020'], smq.at[seqn, 'SMQ040']),
                     pregnant=False if _v(r.RIAGENDR) == 2 else None, told_weak_failing_kidneys=False)
            for i in (1, 2, 3):
                f[f'sbp_{i}_mmhg'] = _num(bpx.at[seqn, f'BPXSY{i}'], positive=True)
                f[f'dbp_{i}_mmhg'] = _num(bpx.at[seqn, f'BPXDI{i}'], positive=True)
            if lab is not None:
                f.update(glucose_serum_mgdl=_num(lab.at[seqn, 'LBXSGL']), hba1c_pct=_num(lab.at[seqn, 'LBXGH']),
                         total_chol_mgdl=_num(lab.at[seqn, 'LBXTC']), hdl_mgdl=_num(lab.at[seqn, 'LBDHDD']),
                         hemoglobin_gdl=_num(lab.at[seqn, 'LBXHGB']))
            rows[seqn] = _clean(f)
    return s, pool, rows, dict(dev_file='phase_xxxv/data/processed/ckd_dev.pkl', raw='phase_xxxiv ckd_inventory_meta yolları (E–H)',
                               adapter_notes=['on_bp_medication: BPQ050A; yanıtsız ve BPQ040A=2 (ilaç önerilmemiş) ise hayır',
                                              'hx_coronary_disease: MCQ160C/D/E herhangi biri evet -> evet; en az biri hayır ve hiçbiri evet değil -> hayır',
                                              'pregnant=False, told_weak_failing_kidneys=False (popülasyon tanımı)'])


# ============================================================== Osteo (phase_xxx)
def osteo_case(model_id='osteo_final'):
    t2 = _import('p30_t2_osteo', V2 / 'phase_xxx/scripts/t2_osteo_data.py')
    dev = pd.read_pickle(_guard(V2 / 'phase_xxx/data/processed/osteo_dev.pkl'))
    feats = [f for f in t2.FEATURES if f != 'age_last_period']
    s, pool = sample(dev, feats)
    rows = {}
    for c, g in s.groupby('cycle'):
        seqns = [float(i.split('_', 1)[1]) for i in g.index]
        d = t2.x(c, 'DEMO', ['RIDAGEYR', 'RIAGENDR']).join(t2.x(c, 'BMX', ['BMXWT', 'BMXHT']))
        d = d.join(t2.x(c, 'SMQ', ['SMQ020', 'SMQ040']))
        acols = ['ALQ111', 'ALQ121', 'ALQ130'] if c == 'J' else ['ALQ101', 'ALQ110', 'ALQ120Q', 'ALQ120U', 'ALQ130']
        try:
            a = t2.x(c, 'ALQ', acols)
        except Exception:
            a = t2.x(c, 'ALQ', [k for k in acols if k != 'ALQ110'])
        d = d.join(a).join(t2.x(c, 'OSQ', ['OSQ010A', 'OSQ010B', 'OSQ010C', 'OSQ080', 'OSQ130', 'OSQ170', 'OSQ200']))
        d = d.join(t2.x(c, 'RHQ', ['RHQ031', 'RHQ060', 'RHQ540']))
        d = d.loc[seqns]
        dpd = t2.alcohol_dpd(d, c)                      # şema alanı alkol/gün: fazın kendi ham->alan tanımı
        for pid, (seqn, r) in zip(g.index, d.iterrows()):
            fem = _v(r.RIAGENDR) == 2
            o170, o200 = _v(r.OSQ170), _v(r.OSQ200)
            parent = True if (o170 == 1 or o200 == 1) else False if (o170 == 2 and o200 == 2) else None
            alp = _num(r.RHQ060)
            f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), weight_kg=_num(r.BMXWT), height_cm=_num(r.BMXHT),
                     smoking_status=_smoking(r.SMQ020, r.SMQ040), alcohol_drinks_per_day=_num(dpd.loc[seqn]),
                     glucocorticoid_ge1month=_yn(r.OSQ130), fracture_hip=_yn(r.OSQ010A), fracture_wrist=_yn(r.OSQ010B),
                     fracture_spine=_yn(r.OSQ010C), fracture_after_age20=_yn(r.OSQ080), parent_hip_fracture=parent)
            if fem:
                f.update(menses_absent_12m={1: False, 2: True}.get(_v(r.RHQ031)), hrt_ever=_yn(r.RHQ540),
                         age_last_period_years=alp if (alp is not None and 10 <= alp <= 70) else None)
            rows[pid] = _clean(f)
    return s, pool, rows, dict(dev_file='phase_xxx/data/processed/osteo_dev.pkl', raw='phase_xxx/data/raw/<D,E,F,H>/*.xpt',
                               adapter_notes=['alcohol_drinks_per_day: fazın alcohol_dpd() tanımı (döngüye göre ALQ120Q/U veya ALQ121)',
                                              'age_last_period_years: RHQ060 (10–70 dışı yanıtsız)'])


# ============================================================== Fibrosis (phase_xxxi)
def fib_case(model_id='fibrosis_final'):
    t3 = _import('p31_t3_fib', V2 / 'phase_xxxi/scripts/t3_fib_data.py')
    dev = pd.read_pickle(_guard(V2 / 'phase_xxxi/data/processed/fib_dev.pkl'))
    s, pool = sample(dev, t3.FEATURES)
    f_ = lambda b: t3.P30R / 'P' / f'P_{b}.xpt'
    d = t3.x(f_('DEMO'), ['RIDAGEYR', 'RIAGENDR']).join(t3.x(f_('BMX'), ['BMXWT', 'BMXHT', 'BMXWAIST']))
    d = d.join(t3.x(f_('BIOPRO'), ['LBXSATSI', 'LBXSASSI', 'LBXSGTSI', 'LBXSAPSI', 'LBXSAL', 'LBXSGL', 'LBXSTR']))
    d = d.join(t3.x(t3.P31 / 'data/raw/P/P_CBC.xpt', ['LBXPLTSI'])).join(t3.x(f_('GHB'), ['LBXGH']))
    d = d.join(t3.x(f_('HDL'), ['LBDHDD'])).join(t3.x(f_('DIQ'), ['DIQ010', 'DIQ050', 'DIQ070']))
    d = d.join(t3.x(f_('ALQ'), ['ALQ111', 'ALQ121', 'ALQ130']))
    seqns = [float(i.split('_', 1)[1]) for i in s.index]
    d = d.loc[seqns]
    freq = d.ALQ121.map(t3.ALQ121_PER_YEAR)
    dpd = (freq * d.ALQ130.where(d.ALQ130.between(1, 15)) / 365).where(freq.ne(0), 0.0).where(~d.ALQ111.eq(2), 0.0)
    rows = {}
    for pid, (seqn, r) in zip(s.index, d.iterrows()):
        f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), height_cm=_num(r.BMXHT), weight_kg=_num(r.BMXWT),
                 waist_cm=_num(r.BMXWAIST), alt_ul=_num(r.LBXSATSI), ast_ul=_num(r.LBXSASSI), ggt_ul=_num(r.LBXSGTSI),
                 alp_ul=_num(r.LBXSAPSI), albumin_gdl=_num(r.LBXSAL), platelets_k_ul=_num(r.LBXPLTSI),
                 glucose_serum_mgdl=_num(r.LBXSGL), hba1c_pct=_num(r.LBXGH), tg_mgdl=_num(r.LBXSTR), hdl_mgdl=_num(r.LBDHDD),
                 told_diabetes={1: True, 2: False, 3: False}.get(_v(r.DIQ010)), on_insulin=_yn(r.DIQ050),
                 on_diabetes_pills=_yn(r.DIQ070), alcohol_drinks_per_day=_num(dpd.loc[seqn]),
                 pregnant=False if _v(r.RIAGENDR) == 2 else None)
        rows[pid] = _clean(f)
    return s, pool, rows, dict(dev_file='phase_xxxi/data/processed/fib_dev.pkl', raw='phase_xxx/data/raw/P + phase_xxxi/data/raw/P (CBC)',
                               adapter_notes=['alcohol_drinks_per_day: fazın tanımı ALQ121 frekansı × ALQ130 (1–15) / 365; ALQ111=2 -> 0'])


# ============================================================== HTN (phase_xxxvii)
def htn_case(model_id='htn_M1'):
    c37 = _import('p37_c37', V2 / 'phase_xxxvii/scripts/c37.py')
    dev = pd.read_pickle(_guard(V2 / 'phase_xxxvii/data/processed/htn3_dev.pkl'))
    core = ['age', 'sex', 'race', 'bmi', 'waist', 'smoking', 'alcohol_dpd', 'diabetes', 'hba1c', 'tc', 'hdl', 'egfr', 'uacr_log']
    s, pool = sample(dev, core)
    rows = {}
    ALQ = {0: 0, 1: 365, 2: 286, 3: 182, 4: 104, 5: 52, 6: 30, 7: 12, 8: 9, 9: 4.5, 10: 1.5}
    for c, g in s.groupby('cycle'):
        seqns = [int(i.split('_', 1)[1]) for i in g.index]
        L = lambda m, cols: c37.load(m, c, cols).reindex(seqns)
        d = L('DEMO', ['RIDAGEYR', 'RIAGENDR', 'RIDRETH1']).join(L('BMX', ['BMXWT', 'BMXHT', 'BMXWAIST']))
        d = d.join(L('BIOPRO', ['LBXSCR'])).join(L('GHB', ['LBXGH'])).join(L('TCHOL', ['LBXTC'])).join(L('HDL', ['LBDHDD']))
        u = L('ALB_CR', ['URXUMA', 'URXUCR'])
        if c == 'L':                                      # fazın CDC ALB_CR_L geri denklemi (LC-MS/MS -> FIA)
            u['URXUMA'] = np.maximum(-1.643 + 1.189 * u.URXUMA.astype(float), 0.0)
        d = d.join(u).join(L('DIQ', ['DIQ010', 'DIQ050', 'DIQ070'])).join(L('SMQ', ['SMQ020', 'SMQ040']))
        d = d.join(L('ALQ', ['ALQ111', 'ALQ121', 'ALQ130']))
        freq = d.ALQ121.map(ALQ).where(~d.ALQ111.eq(2), 0.0)
        dpd = (freq * d.ALQ130.where(d.ALQ130.between(1, 15)) / 365).where(freq.ne(0), 0.0).where(freq.notna(), np.nan)
        for pid, (seqn, r) in zip(g.index, d.iterrows()):
            f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), race_ethnicity=_race(r.RIDRETH1),
                     height_cm=_num(r.BMXHT), weight_kg=_num(r.BMXWT), waist_cm=_num(r.BMXWAIST),
                     smoking_status=_smoking(r.SMQ020, r.SMQ040, require_ever_for_former=True),
                     alcohol_drinks_per_day=_num(dpd.loc[seqn]),
                     told_diabetes={1: True, 2: False, 3: False}.get(_v(r.DIQ010)), on_insulin=_yn(r.DIQ050),
                     on_diabetes_pills=_yn(r.DIQ070), hba1c_pct=_num(r.LBXGH), total_chol_mgdl=_num(r.LBXTC),
                     hdl_mgdl=_num(r.LBDHDD), creatinine_mgdl=_num(r.LBXSCR), urine_albumin_mgl=_num(r.URXUMA),
                     urine_creatinine_mgdl=_num(r.URXUCR), pregnant=False if _v(r.RIAGENDR) == 2 else None)
            rows[pid] = _clean(f)
    return s, pool, rows, dict(dev_file='phase_xxxvii/data/processed/htn3_dev.pkl', raw='phase_xxxvii download_manifest37 yolları (P, L)',
                               adapter_notes=['L döngüsü idrar albümini CDC geri denklemiyle FIA ölçeğine çevrildi (fazın uyumlaştırması; <0 -> 0)',
                                              'alcohol_drinks_per_day: fazın P/L tanımı (ALQ130 1–15)'])


# ============================================================== Phase21/24/25 ortak ham okuyucu
def _read_dir(folder, names=None):
    import pyreadstat
    paths = sorted(Path(folder).glob('*.xpt'), key=lambda p: (not p.stem.upper().startswith('DEMO'), p.name))
    if names is not None:
        paths = [p for p in paths if p.stem in names]
    d = None
    for p in paths:
        z, _ = pyreadstat.read_xport(_guard(p))
        z = z.set_index('SEQN')
        d = z if d is None else d.join(z, how='left', rsuffix='__' + p.stem)
    return d


# ============================================================== Anemia (Phase24 D + Phase25 A geliştirme)
def anemia_case(model_id='anemia_LR16'):
    dev = pd.read_pickle(_guard(V2 / 'Clinical_Optimization_Phase25/data/processed/anemia_development.pkl')).set_index('person_id')
    feats = ['age', 'sex', 'bmi', 'waist', 'smoker', 'hba1c', 'alt', 'ast', 'tc', 'hdl', 'creatinine', 'wbc', 'rbc', 'mcv', 'rdw', 'albumin']
    s, pool = sample(dev, feats)
    rows = {}
    for cyc, folder in (('D', V2 / 'Clinical_Model_Improvement_Phase24/data/raw/nhanes/D'),
                        ('A', V2 / 'Clinical_Optimization_Phase25/data/raw/nhanes/A')):
        pids = [p for p in s.index if p.startswith(f'NH_{cyc}_')]
        if not pids:
            continue
        d = _read_dir(folder).loc[[float(p.split('_')[2]) for p in pids]]
        for pid, (seqn, r) in zip(pids, d.iterrows()):
            if cyc == 'D':
                cr, hdl = -.016 + .978 * r.LBXSCR, r.LBDHDD          # Phase24: CDC 2005–06 düzeltmesi
            else:
                cr, hdl = 1.013 * r.LBXSCR + .147, r.LBDHDL          # Phase25: LAB18 standardizasyonu
            f = dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), height_cm=_num(r.BMXHT), weight_kg=_num(r.BMXWT),
                     waist_cm=_num(r.BMXWAIST, positive=True), smoking_status=_smoking(r.SMQ020, r.SMQ040),
                     hba1c_pct=_num(r.LBXGH), alt_ul=_num(r.LBXSATSI), ast_ul=_num(r.LBXSASSI), total_chol_mgdl=_num(r.LBXTC),
                     hdl_mgdl=_num(hdl), creatinine_mgdl=_num(cr, positive=True), wbc_k_ul=_num(r.LBXWBCSI),
                     rbc_m_ul=_num(r.LBXRBCSI), mcv_fl=_num(r.LBXMCVSI), rdw_pct=_num(r.LBXRDW), albumin_gdl=_num(r.LBXSAL),
                     pregnant=False if _v(r.RIAGENDR) == 2 else None)
            rows[pid] = _clean(f)
    return s, pool, rows, dict(dev_file='Clinical_Optimization_Phase25/data/processed/anemia_development.pkl',
                               raw='Phase24 raw/nhanes/D + Phase25 raw/nhanes/A',
                               adapter_notes=['kreatinin: D için -0,016+0,978×LBXSCR, A için 1,013×LBXSCR+0,147 (fazların CDC düzeltmeleri)',
                                              'smoking: SMQ040 1/2 -> current, 3 -> former, SMQ020=2 -> never'])


# ============================================================== COPD (Phase21 G geliştirme)
def copd_case(model_id='copd_S4_DEVICE'):
    dev = pd.read_pickle(_guard(V2 / 'All_Disease_Improvement_Phase21/data/processed/copd_development.pkl')).set_index('person_id')
    feats = ['age', 'sex', 'bmi', 'smoker', 'fev1_pre', 'fvc_pre']
    s, pool = sample(dev, feats)
    folder = V2 / 'All_Disease_Improvement_Phase21/data/raw/nhanes/G'
    d = _read_dir(folder, names=['DEMO_G', 'BMX_G', 'SMQ_G', 'SPX_G']).loc[[float(p.split('_')[2]) for p in s.index]]
    rows = {}
    for pid, (seqn, r) in zip(s.index, d.iterrows()):
        rows[pid] = _clean(dict(age_years=_num(r.RIDAGEYR), sex=_sex(r.RIAGENDR), height_cm=_num(r.BMXHT),
                                weight_kg=_num(r.BMXWT), smoking_status=_smoking(r.SMQ020, r.SMQ040),
                                fev1_pre_ml=_num(r.SPXNFEV1), fvc_pre_ml=_num(r.SPXNFVC)))
    return s, pool, rows, dict(dev_file='All_Disease_Improvement_Phase21/data/processed/copd_development.pkl',
                               raw='All_Disease_Improvement_Phase21/data/raw/nhanes/G (DEMO, BMX, SMQ, SPX)',
                               adapter_notes=['geliştirme kümesi 145 kişi (<200): tamamı kullanıldı (eksiksiz olanlar)'])


# ============================================================== CAD (UCI Cleveland geliştirme: train+validation)
def cad_case(model_id='cad_DEVICE'):
    import json
    split = json.loads((V2 / 'experiments/cad_split.json').read_text())
    dev_ids = set(split['train']) | set(split['validation'])            # test kimlikleri kullanılmaz
    allcad = pd.read_pickle(_guard(V2 / 'data/processed/cad.pkl'))       # 303 satır; hemen geliştirme kişilerine indirgenir
    dev = allcad[allcad.person_id.isin(dev_ids)].set_index('person_id')
    del allcad
    feats = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope']
    s, pool = sample(dev, feats)
    hc = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'num']
    raw = pd.read_csv(V2 / 'data/raw/uci_45/processed.cleveland.data', header=None, names=hc, na_values='?')
    raw.index = raw.index.astype(str)
    raw = raw.loc[list(s.index), hc[:11]]                                 # yalnız örneklenen geliştirme satırları
    CP = {1: 'typical_angina', 2: 'atypical_angina', 3: 'non_anginal', 4: 'asymptomatic'}
    RE = {0: 'normal', 1: 'st_t_abnormality', 2: 'lv_hypertrophy'}
    SL = {1: 'upsloping', 2: 'flat', 3: 'downsloping'}
    rows = {}
    for pid, r in raw.iterrows():
        fbs = _v(r.fbs)
        rows[pid] = _clean(dict(age_years=_num(r.age), sex={1: 'male', 0: 'female'}.get(_v(r.sex)),
                                cad_chest_pain_type=CP.get(_v(r.cp)), sbp_1_mmhg=_num(r.trestbps),
                                total_chol_mgdl=_num(r.chol),
                                glucose_fasting_mgdl=None if fbs is None else (126.0 if fbs == 1 else 100.0),
                                cad_resting_ecg=RE.get(_v(r.restecg)), cad_max_hr_bpm=_num(r.thalach),
                                cad_exercise_angina={1: True, 0: False}.get(_v(r.exang)),
                                cad_st_depression_mm=_num(r.oldpeak), cad_st_slope=SL.get(_v(r.slope))))
    return s, pool, rows, dict(dev_file='data/processed/cad.pkl (yalnız experiments/cad_split.json train+validation)',
                               raw='data/raw/uci_45/processed.cleveland.data',
                               adapter_notes=['UCI fbs yalnız ikili (açlık glukozu >120 mg/dL); adaptör temsilî değer verir: fbs=1 -> 126, fbs=0 -> 100 mg/dL '
                                              '(dönüşümün eşik mantığını sınar, değerin kendisini değil)'])


# Phase XLVI kapanış: model başına gereken araştırma ağacı yolları (V2 köküne göre). Testler bunları
# `requires_research_tree` ile işaretler; yoksa (GitHub klonu) SKIP. Ham döngü dosyalarının ayrıntısı faz betiklerindedir.
_DM = ('phase_xlii/scripts/t1_data.py', 'phase_xlii/data/processed/dm_dev.pkl', 'phase_xlii/data/nhanes')
_CKD = ('phase_xxxv/scripts/t1_data.py', 'phase_xxxv/data/processed/ckd_dev.pkl', 'phase_xxxiv/results/ckd_inventory_meta.json')
REQUIRED_FILES = {
    'dm_A': _DM, 'dm_B': _DM, 'ckd_A': _CKD, 'ckd_B': _CKD,
    'osteo_final': ('phase_xxx/scripts/t2_osteo_data.py', 'phase_xxx/data/processed/osteo_dev.pkl', 'phase_xxx/data/raw'),
    'fibrosis_final': ('phase_xxxi/scripts/t3_fib_data.py', 'phase_xxxi/data/processed/fib_dev.pkl', 'phase_xxx/data/raw/P',
                       'phase_xxxi/data/raw/P'),
    'htn_M1': ('phase_xxxvii/scripts/c37.py', 'phase_xxxvii/data/processed/htn3_dev.pkl',
               'phase_xxxvii/results/download_manifest37.json'),
    'anemia_LR16': ('Clinical_Optimization_Phase25/data/processed/anemia_development.pkl',
                    'Clinical_Model_Improvement_Phase24/data/raw/nhanes/D', 'Clinical_Optimization_Phase25/data/raw/nhanes/A'),
    'copd_S4_DEVICE': ('All_Disease_Improvement_Phase21/data/processed/copd_development.pkl',
                       'All_Disease_Improvement_Phase21/data/raw/nhanes/G'),
    'cad_DEVICE': ('experiments/cad_split.json', 'data/processed/cad.pkl', 'data/raw/uci_45/processed.cleveland.data'),
}

CASES = {'dm_A': dm_case, 'dm_B': dm_case, 'ckd_A': ckd_case, 'ckd_B': ckd_case, 'osteo_final': osteo_case,
         'fibrosis_final': fib_case, 'htn_M1': htn_case, 'anemia_LR16': anemia_case, 'copd_S4_DEVICE': copd_case,
         'cad_DEVICE': cad_case}


def _eq(dev_v, srv_v):
    """Döner: (eşit mi, |Δ| veya None)."""
    dn = dev_v is None or (isinstance(dev_v, float) and math.isnan(dev_v))
    sn = srv_v is None or (isinstance(srv_v, float) and math.isnan(srv_v))
    if dn or sn:
        return dn and sn, None
    if isinstance(dev_v, str) or isinstance(srv_v, str):
        return (isinstance(dev_v, str) and isinstance(srv_v, str) and dev_v == srv_v), None
    d = abs(float(dev_v) - float(srv_v))
    return d <= TOL, d


def run_case(service, model_id, with_decision=True):
    """Bir model için parity. Olasılık saklanmaz; karar etkisi yalnız eşik üstü/altı karşılaştırmasıdır."""
    from healthrisk_api import features as FT
    from healthrisk_api.validation import ValidationError422, validate_fields
    s, pool, rows, meta = CASES[model_id](model_id)
    e = service.models[model_id]['entry']
    names = [f['name'] for f in e['features']]
    tr = {u['model_feature']: u['transform'] for u in service.models[model_id]['usage']}   # etkin (şema v2) dönüşüm
    per_feat = {n: dict(feature=n, transform=tr[n], n_compared=0, n_mismatch=0, n_explained_bmi_2dec_source_cycle=0,
                        max_abs_delta=0.0) for n in names}
    outcome = dict(MATCH=0, MATCH_EXCEPT_BMI_2DEC_SOURCE_CYCLE=0, MISMATCH_OTHER=0, ABSTAIN=0, NOT_APPLICABLE=0, HTTP_422=0)
    examples, abstain_reasons, flip_list, n_dec = [], {}, [], 0
    model = service.models[model_id]['obj']
    thr = float(e['thresholds']['primary']['value'])
    for pid in s.index:
        fields = rows.get(pid)
        devrow = s.loc[pid]
        try:
            F, _ = validate_fields(fields, service.schema, service.extra_fields, service.conversions)
        except ValidationError422 as ex:
            outcome['HTTP_422'] += 1
            for er in ex.errors:
                k = '422: ' + er['msg'].split('=')[0].split(':')[0]
                abstain_reasons[k] = abstain_reasons.get(k, 0) + 1
            continue
        fr = FT.build(e, F, service.models[model_id]['usage'])
        if fr.missing or fr.unknown or fr.internal:
            outcome['ABSTAIN'] += 1
            for m in fr.missing:
                abstain_reasons['eksik: ' + m] = abstain_reasons.get('eksik: ' + m, 0) + 1
            for u in fr.unknown:
                abstain_reasons['kategori: ' + u[0]] = abstain_reasons.get('kategori: ' + u[0], 0) + 1
            continue
        if fr.not_applicable:
            outcome['NOT_APPLICABLE'] += 1
            for x in fr.not_applicable:
                k = 'aralık: ' + x.split('=')[0].split(':')[0]
                abstain_reasons[k] = abstain_reasons.get(k, 0) + 1
            continue
        srv = {n: (fr.values.get(n) if n not in fr.structural_blank else None) for n in names}
        diff_feats, other = [], False
        for n in names:
            dv = _v(devrow[n])
            eq, d = _eq(dv, srv[n])
            pf = per_feat[n]
            pf['n_compared'] += 1
            if d is not None:
                pf['max_abs_delta'] = max(pf['max_abs_delta'], d)
            if not eq:
                pf['n_mismatch'] += 1
                diff_feats.append(n)
                # BMI (şema v2: 0,1 veya 0,01'e yuvarlanmış). Açıklama ölçütü: geliştirme değeri 2 ondalıklı kaynak döngüsünden
                # (≤ 2009–10 BMXBMI; 0,1'e indirgenemez) ve |Δ| ≤ 0,05 — yani fark yalnız döngü hassasiyetinden.
                expl = (n == 'bmi' and d is not None and abs(dv * 10 - round(dv * 10)) > 1e-6 and d <= 0.05 + 1e-9)
                if expl:
                    pf['n_explained_bmi_2dec_source_cycle'] += 1
                else:
                    other = True
                if sum(1 for x in examples if x['feature'] == n) < 5:
                    examples.append(dict(model=model_id, person=str(pid), feature=n, transform=tr[n],
                                         dev_value=repr(dv), server_value=repr(srv[n]), abs_delta=d,
                                         explained_bmi_2dec_source_cycle=bool(expl)))
        outcome['MATCH' if not diff_feats else 'MISMATCH_OTHER' if other else 'MATCH_EXCEPT_BMI_2DEC_SOURCE_CYCLE'] += 1
        if with_decision and diff_feats:
            # karar etkisi: geliştirme vektörü ile sunucu vektörü aynı eşikte aynı sınıfı mı veriyor? (olasılık saklanmaz)
            dvals = {n: (_v(devrow[n]) if _v(devrow[n]) is not None else float('nan')) for n in names}
            Xs, Xd = FT.to_frame(e, fr.values), FT.to_frame(e, dvals)
            a = bool(model.predict_proba(Xs)[0, 1] >= thr)
            b = bool(model.predict_proba(Xd)[0, 1] >= thr)
            n_dec += 1
            if a != b:
                flip_list.append(dict(person=str(pid), differing_features=diff_feats))
    return dict(model=model_id, dev_pool_complete=int(pool), n_sampled=int(len(s)), outcome=outcome,
                n_mismatch_persons_decision_checked=n_dec, decision_flips=len(flip_list), decision_flip_detail=flip_list,
                abstain_or_reject_reasons=dict(sorted(abstain_reasons.items(), key=lambda kv: -kv[1])),
                features=list(per_feat.values()), meta=meta), examples
