"""Phase XLIII — elle yazılan kayıt içeriği (birimler, aralıklar, dönüşümler, kanıt, sınırlılıklar).
Model dosyası SHA'sı, eşikler, feature sırası ve kategoriler BURADA YAZILMAZ: build_registry.py bunları kilit dosyalarından
ve model nesnelerinden okur (elle yazım hatasını önlemek için). Kanıt sayıları önceki faz raporlarından aynen alınmıştır.
Bulunamayan bilgi 'BULUNAMADI' yazılır."""
import math

NF = 'BULUNAMADI'

# --------------------------------------------------------------------------------------------------------------------
# Ortak girdi alanları (input_schema.json). tip: numeric | categorical | boolean | device
# range = fiziksel olarak makul giriş aralığı (modelin eğitim kapsamı DEĞİL; uygulama girişi doğrulama sınırı).
# --------------------------------------------------------------------------------------------------------------------
F = {}


def fld(fid, label, typ, unit=None, rng=None, cats=None, note=None, ask_when=None, source='kullanici'):
    d = dict(label_tr=label, type=typ, input_source=source)
    if unit is not None:
        d['unit'] = unit
    if rng is not None:
        d['plausible_range'] = list(rng)
    if cats is not None:
        d['categories'] = cats
    if ask_when:
        d['ask_when'] = ask_when
    if note:
        d['note'] = note
    F[fid] = d


# demografi / antropometri
fld('age_years', 'Yaş', 'numeric', 'yıl', (18, 120), note='Model popülasyon aralıkları modele göre daralır (models.json). NHANES tabanlı modellerde 80 üstü 80 olarak kırpılır (age_cap80).')
fld('sex', 'Biyolojik cinsiyet', 'categorical', cats=['female', 'male'], note='Modeller cinsiyeti kendi kodlamasıyla alır (dönüşüm tablosu).')
fld('race_ethnicity', 'Irk/etnik köken (NHANES RIDRETH1 sınıfları)', 'categorical',
    cats=['mexican_american', 'other_hispanic', 'nh_white', 'nh_black', 'other_incl_multi'],
    note='Yalnız NHANES tabanlı DM ve KBH modelleri (ve HTN) kullanır. Referans: nh_white. İSTEĞE BAĞLI sorulur (kullanıcı kararı, Phase XLIII sonrası): yanıt yoksa dm_A/dm_B/ckd_A/ckd_B ve htn_M1 ABSTAIN eder; varsayılan/referans sınıf ATANMAZ.')
fld('height_cm', 'Boy', 'numeric', 'cm', (100, 230))
fld('weight_kg', 'Kilo', 'numeric', 'kg', (25, 300))
fld('waist_cm', 'Bel çevresi', 'numeric', 'cm', (40, 200), note='NHANES protokolü: iliak krest üstü, ölçülü (kendi beyanı değil).')
# tansiyon
for i in (1, 2, 3):
    fld(f'sbp_{i}_mmhg', f'Sistolik kan basıncı, okuma {i}', 'numeric', 'mmHg', (70, 260), note='Oturarak, ≥5 dk dinlenme sonrası ardışık okuma; sbp_>dbp_ tutarlılığı doğrulanır.')
    fld(f'dbp_{i}_mmhg', f'Diyastolik kan basıncı, okuma {i}', 'numeric', 'mmHg', (30, 150))
# yaşam tarzı / öykü
fld('smoking_status', 'Sigara durumu', 'categorical', cats=['never', 'former', 'current'], note='never: yaşamında ≥100 sigara içmemiş; current: şu an içiyor; former: bıraktı.')
fld('alcohol_drinks_per_day', 'Ortalama alkol (içki/gün, son 12 ay)', 'numeric', 'içki/gün', (0, 30), note='NHANES ALQ121×ALQ130/365 tanımı: içme sıklığı (gün/yıl) × içilen gün başına içki sayısı / 365; hiç içmeyen 0.')
for fid, lab in [('told_hypertension', 'Doktor "yüksek tansiyon" dedi mi'), ('on_bp_medication', 'Tansiyon ilacı kullanıyor mu'),
                 ('told_diabetes', 'Doktor "diyabet" dedi mi (sınırda = hayır)'), ('on_insulin', 'İnsülin kullanıyor mu'),
                 ('on_diabetes_pills', 'Diyabet hapı kullanıyor mu'), ('hx_coronary_disease', 'Koroner kalp hastalığı / anjina / MI öyküsü (herhangi biri)'),
                 ('hx_heart_failure', 'Kalp yetmezliği öyküsü'), ('hx_stroke', 'İnme öyküsü'),
                 ('family_hx_diabetes', 'Yakın akrabada diyabet (NHANES MCQ300C)'), ('gestational_diabetes_hx', 'Gebelikte diyabet söylendi mi (yalnız kadın)'),
                 ('recreational_activity', 'Haftalık orta/şiddetli rekreasyonel fiziksel aktivite var mı (NHANES PAQ650/PAQ665)'),
                 ('glucocorticoid_ge1month', '≥1 ay neredeyse her gün prednizon/kortizon kullandı mı (OSQ130)'),
                 ('fracture_hip', 'Kalça kırığı öyküsü'), ('fracture_wrist', 'El bileği kırığı öyküsü'), ('fracture_spine', 'Omurga kırığı öyküsü'),
                 ('fracture_after_age20', '20 yaş sonrası herhangi kırık (OSQ080)'), ('parent_hip_fracture', 'Ebeveyn kalça kırığı'),
                 ('menses_absent_12m', 'Son 12 ayda adet yok (yalnız kadın)'), ('hrt_ever', 'Hiç hormon tedavisi (yalnız kadın)')]:
    ask = {'on_bp_medication': 'told_hypertension = true', 'on_insulin': 'told_diabetes = true', 'on_diabetes_pills': 'told_diabetes = true',
           'gestational_diabetes_hx': 'sex = female', 'menses_absent_12m': 'sex = female', 'hrt_ever': 'sex = female'}.get(fid)
    fld(fid, lab, 'boolean', cats=[True, False], ask_when=ask)
fld('age_last_period_years', 'Son adet yaşı', 'numeric', 'yıl', (10, 70), ask_when='sex = female ve menses_absent_12m = true',
    note='Eğitimde yalnız kadınlarda ve adeti kesilmişlerde doluydu; diğerlerinde yapısal olarak boş.')
# laboratuvar (kullanıcı birimi → model birimi dönüşümleri unit_conversions içinde)
LAB = [
    ('hba1c_pct', 'HbA1c', '%', (3.0, 18.0)), ('glucose_serum_mgdl', 'Serum glukoz (açlık şartı yok)', 'mg/dL', (30, 800)),
    ('glucose_fasting_mgdl', 'Açlık plazma glukozu (≥8 saat)', 'mg/dL', (30, 800)), ('total_chol_mgdl', 'Total kolesterol', 'mg/dL', (50, 600)),
    ('hdl_mgdl', 'HDL kolesterol', 'mg/dL', (5, 200)), ('tg_mgdl', 'Trigliserit', 'mg/dL', (10, 5000)), ('alt_ul', 'ALT', 'U/L', (3, 1000)),
    ('ast_ul', 'AST', 'U/L', (3, 1000)), ('ggt_ul', 'GGT', 'U/L', (1, 2000)), ('alp_ul', 'ALP', 'U/L', (10, 1500)),
    ('albumin_gdl', 'Serum albümin', 'g/dL', (1.0, 6.5)), ('platelets_k_ul', 'Trombosit', '10^3/µL', (10, 1500)),
    ('uric_acid_mgdl', 'Ürik asit', 'mg/dL', (0.5, 20)), ('creatinine_mgdl', 'Serum kreatinin (standardize/enzimatik ölçek)', 'mg/dL', (0.2, 15)),
    ('urine_albumin_mgl', 'İdrar albümini', 'mg/L', (0.1, 10000)), ('urine_creatinine_mgdl', 'İdrar kreatinini', 'mg/dL', (5, 600)),
    ('wbc_k_ul', 'Lökosit (WBC)', '10^3/µL', (0.5, 100)), ('rbc_m_ul', 'Eritrosit (RBC)', '10^6/µL', (1.0, 9.0)), ('mcv_fl', 'MCV', 'fL', (50, 140)),
    ('rdw_pct', 'RDW', '%', (8, 35)), ('hemoglobin_gdl', 'Hemoglobin', 'g/dL', (3, 22)),
]
for fid, lab, unit, rng in LAB:
    fld(fid, lab, 'numeric', unit, rng, source='laboratuvar')
fld('rip3_pgml', 'RIP3 (özel ELISA)', 'numeric', 'pg/mL', (0, 5000), source='arastirma_assay',
    note='Rutin klinik test DEĞİL; özel ELISA. Aralık geçici (eğitim ort. 394, SD 235 pg/mL — scaler istatistiği); assay uyumu BULUNAMADI.')
fld('fev1_pre_ml', 'Bronkodilatör ÖNCESİ FEV1', 'numeric', 'mL', (200, 7000), source='spirometri', note='ATS A/B kalite; birim mL (L değil).')
fld('fvc_pre_ml', 'Bronkodilatör ÖNCESİ FVC', 'numeric', 'mL', (300, 9000), source='spirometri', note='fev1_pre_ml ≤ fvc_pre_ml doğrulanır.')
# cihaz/özel akış
AF_FEATS = [('RR_Mean_Global', 'RR aralığı ortalaması', (300, 2000)), ('RR_Mean_Global_iqr', 'RR IQR', (0, 1500)), ('QRS_Dur_Global', 'QRS süresi (lead’ler arası maksimum)', (40, 400)),
            ('QRS_Dur_Global_iqr', 'QRS IQR', (0, 300)), ('PR_Int_Global', 'PR aralığı', (50, 600)), ('PR_Int_Global_iqr', 'PR IQR', (0, 400)),
            ('P_Dur_Global', 'P süresi', (20, 400)), ('P_Dur_Global_iqr', 'P IQR', (0, 300)), ('QT_Int_Global', 'QT aralığı', (200, 900)), ('QT_Int_Global_iqr', 'QT IQR', (0, 400))]
for fid, lab, rng in AF_FEATS:
    fld('ecg_af_' + fid, 'EKG-ECGDeli: ' + lab, 'numeric', 'ms', rng, source='ecg_pipeline_AF-ECGDELI-OCTAVE-v1',
        note='YALNIZ kilitli AF-ECGDELI-OCTAVE-v1 pipeline çıktısı (phase_xxviii/config/af_pipeline_lock.json); elle girilemez, başka delineasyon aracından alınamaz.')
fld('ecg_ptbxl_ecgdeli_168', 'PTB-XL+ ECGDeli 168 feature grubu (MI modeli)', 'device', source='ecg_pipeline_YOK',
    note='Lead bazlı Q/R/S/T/P/ST genlikleri (mV) ve süreler (ms). Uygulama için üretecek pipeline YOK (MI-ECGDELI-OCTAVE-v1 yazılmadı; phase_xxxviii/PHASE_XXXVIII_REPORT.md §5).')
fld('cad_chest_pain_type', 'Göğüs ağrısı tipi (UCI cp)', 'categorical', cats=['typical_angina', 'atypical_angina', 'non_anginal', 'asymptomatic'], source='klinik_degerlendirme')
fld('cad_resting_ecg', 'İstirahat EKG (UCI restecg)', 'categorical', cats=['normal', 'st_t_abnormality', 'lv_hypertrophy'], source='klinik_degerlendirme')
fld('cad_max_hr_bpm', 'Efor testinde ulaşılan maksimum kalp hızı', 'numeric', 'atım/dk', (20, 260), source='efor_testi')
fld('cad_exercise_angina', 'Efor anjinası var mı', 'boolean', cats=[True, False], source='efor_testi')
fld('cad_st_depression_mm', 'Efor ST depresyonu (oldpeak)', 'numeric', 'mm', (-10, 20), source='efor_testi')
fld('cad_st_slope', 'Efor ST eğimi', 'categorical', cats=['upsloping', 'flat', 'downsloping'], source='efor_testi')

# --------------------------------------------------------------------------------------------------------------------
# Birim dönüşümleri (kullanıcı birimi → alanın kayıtlı birimi). Standart faktörler; bu fazda yeniden türetilmedi.
# --------------------------------------------------------------------------------------------------------------------
UNIT_CONVERSIONS = [
    dict(field='glucose_serum_mgdl / glucose_fasting_mgdl', from_unit='mmol/L', to_unit='mg/dL', op='x * 18.016', note='ondalık ayraç ve birim karışıklığı için arayüz birim seçtirmeli'),
    dict(field='total_chol_mgdl / hdl_mgdl', from_unit='mmol/L', to_unit='mg/dL', op='x * 38.67'),
    dict(field='tg_mgdl', from_unit='mmol/L', to_unit='mg/dL', op='x * 88.57'),
    dict(field='creatinine_mgdl', from_unit='µmol/L', to_unit='mg/dL', op='x / 88.4'),
    dict(field='uric_acid_mgdl', from_unit='µmol/L', to_unit='mg/dL', op='x / 59.48'),
    dict(field='hba1c_pct', from_unit='mmol/mol (IFCC)', to_unit='% (NGSP)', op='x * 0.09148 + 2.152'),
    dict(field='hemoglobin_gdl / albumin_gdl', from_unit='g/L', to_unit='g/dL', op='x / 10'),
    dict(field='height_cm', from_unit='inç', to_unit='cm', op='x * 2.54'), dict(field='weight_kg', from_unit='lb', to_unit='kg', op='x * 0.45359237'),
    dict(field='waist_cm', from_unit='inç', to_unit='cm', op='x * 2.54'),
    dict(field='fev1_pre_ml / fvc_pre_ml', from_unit='L', to_unit='mL', op='x * 1000'),
    dict(field='urine_albumin_mgl', from_unit='mg/dL', to_unit='mg/L', op='x * 10'),
    dict(field='wbc_k_ul / platelets_k_ul', from_unit='10^9/L', to_unit='10^3/µL', op='x * 1 (sayısal aynı)'),
    dict(field='rbc_m_ul', from_unit='10^12/L', to_unit='10^6/µL', op='x * 1 (sayısal aynı)'),
]
CONVERSION_NOTE = ('Dönüşümler yalnız arayüz katmanında yapılır; model her zaman kayıtlı model birimini görür. Birim belirsizse (ör. mg/dL mi mmol/L mi) '
                   'değer aralık kontrolünden geçmiyorsa tahmin üretilmez (örn. glukoz 5.4 → mmol/L olasılığı: mg/dL aralığı 30–800 içinde kalmadığı için reddedilir).')

# --------------------------------------------------------------------------------------------------------------------
# Dönüşüm tanımları (transform_id → açıklama)
# --------------------------------------------------------------------------------------------------------------------
TRANSFORMS = {
    'identity': 'Değer olduğu gibi (birim: kayıtlı birim).',
    'age_cap80': 'min(age_years, 80). NHANES yaşı 80+ için 80 kodlar (eğitim dağılımı); 80 üstü modele 80 olarak girer.',
    'age_cap89_ptbxl': 'Yaş ≥ 90 ise tahmin üretilmez (PTB-XL >89 yaşları gizlilik nedeniyle 300 kodlu, eğitimde eksik sayıldı).',
    'bmi_kgm2': 'weight_kg / (height_cm/100)^2.',
    'sex_str': "sex → 'female' | 'male' (string, birebir).",
    'sex_male01': 'sex = male → 1.0, female → 0.0.',
    'sex_female01': 'sex = female → 1.0, male → 0.0.',
    'sex_ptbxl01': 'sex = male → 0, female → 1 (PTB-XL kodu).',
    'race_mexam': 'race_ethnicity = mexican_american → 1.0 değilse 0.0.',
    'race_othhisp': 'race_ethnicity = other_hispanic → 1.0 değilse 0.0.',
    'race_black': 'race_ethnicity = nh_black → 1.0 değilse 0.0.',
    'race_other': 'race_ethnicity = other_incl_multi → 1.0 değilse 0.0 (referans nh_white: dördü de 0).',
    'race_str': 'race_ethnicity → string kategori (birebir).',
    'sbp_mean_all': 'sbp_1..3 aritmetik ortalaması (DM eğitimi: BPX okumalarının ortalaması, 1–4 okuma; uygulama 3 okuma ister).',
    'dbp_mean_all': 'dbp_1..3 aritmetik ortalaması.',
    'sbp_mean_23': 'sbp_2 ve sbp_3 ortalaması (KBH eğitimi: ilk okuma atılır).',
    'dbp_mean_23': 'dbp_2 ve dbp_3 ortalaması.',
    'smoke_current01': "smoking_status = current → 1.0, aksi 0.0.",
    'smoke_former01': "smoking_status = former → 1.0, aksi 0.0 (never → 0.0).",
    'smoking_str': "smoking_status → 'current' | 'former' | 'never' (string).",
    'smoker_yesno': "smoking_status = current → 'yes'; never veya former → 'no' (eğitim tanımı: şu an içen).",
    'bool01': 'true → 1.0, false → 0.0.',
    'bool_yesno': "true → 'yes', false → 'no' (string).",
    'htn_dx_med': 'told_hypertension veya on_bp_medication true ise 1.0, değilse 0.0.',
    'gdm_rule': 'sex = male → 0.0 (eğitimde yapısal 0); female → gestational_diabetes_hx (bool01). Kadında yanıt yoksa tahmin üretilmez.',
    'htn_med_rule': 'told_hypertension = false → 0.0 (yapısal atlama); true → bool01(on_bp_medication).',
    'dm_insulin_rule': 'told_diabetes = false → 0.0 (yapısal atlama); true → bool01(on_insulin).',
    'dm_pills_rule': 'told_diabetes = false → 0.0 (yapısal atlama); true → bool01(on_diabetes_pills).',
    'diabetes_yesno': "told_diabetes veya on_insulin veya on_diabetes_pills true ise 'yes', değilse 'no'.",
    'alcohol_ge3_yesno': "alcohol_drinks_per_day ≥ 3 → 'yes', değilse 'no'.",
    'ln_clip1': 'ln(max(x, 1)) (x: model biriminde ham değer; DM eğitimindeki np.log(x.clip(lower=1)) ile aynı).',
    'egfr_ckdepi2021': ('CKD-EPI 2021 (ırksız): 142 × min(Scr/κ,1)^α × max(Scr/κ,1)^−1,200 × 0,9938^yaş × 1,012[kadın]; κ = 0,7 (K) / 0,9 (E); α = −0,241 (K) / −0,302 (E); '
                        'Scr mg/dL, yaş yıl (age_cap80 DEĞİL, ham yaş — XXXVII t1_data egfr_ckdepi2021(scr, age, female); eğitimde age ham NHANES yaşı yani ≤80).'),
    'uacr_log1p': 'ln(1 + 100 × urine_albumin_mgl / urine_creatinine_mgdl) — UACR mg/g.',
    'osteo_period_yesno': "female → bool_yesno(menses_absent_12m); male → 'na_male'.",
    'osteo_hrt': "female → bool_yesno(hrt_ever); male → 'na_male'.",
    'osteo_age_last_period': 'female ve menses_absent_12m = true → age_last_period_years; aksi (erkek / adeti süren kadın) yapısal boş (null) — eğitimde de boştu, dondurulmuş imputer eğitimdeki gibi uygular.',
    'alcohol_dpd': 'identity (içki/gün).',
    'fasting_gt120_strfloat': "glucose_fasting_mgdl > 120 → '1.0', değilse '0.0' (UCI fbs; açlık şartı zorunlu).",
    'cad_sex_strfloat': "female → '0.0', male → '1.0' (UCI sex; string biçim ZORUNLU, bkz. phase_xlii/ERRATA_CAD_V2.md).",
    'cad_cp_strfloat': "typical_angina '1.0' | atypical_angina '2.0' | non_anginal '3.0' | asymptomatic '4.0'.",
    'cad_restecg_strfloat': "normal '0.0' | st_t_abnormality '1.0' | lv_hypertrophy '2.0'.",
    'cad_exang_strfloat': "true '1.0' | false '0.0'.",
    'cad_slope_strfloat': "upsloping '1.0' | flat '2.0' | downsloping '3.0'.",
    'cad_trestbps': 'sbp_1 (tek istirahat sistolik okuma, mmHg).',
    'ecg_pipeline_output': 'Kilitli AF pipeline çıktısı olduğu gibi (ms).',
    'ptbxl_group': 'ECGDeli 168 feature grubu (PTB-XL+ şemasıyla birebir; HA__Global string float kodu).',
}

# --------------------------------------------------------------------------------------------------------------------
# Model tanımları
# k(name, kind, unit, input_field, transform, lo, hi, syn)  kind: num | bin | cat
# --------------------------------------------------------------------------------------------------------------------


def num(name, unit, field, tf, lo, hi, syn, note=None):
    return dict(name=name, kind='num', unit=unit, input_field=field, transform=tf, allowed_range=[lo, hi], synthetic=syn, note=note)


def binf(name, field, tf, syn=0.0, note=None):
    return dict(name=name, kind='bin', unit='0/1', input_field=field, transform=tf, allowed_values=[0.0, 1.0], synthetic=syn, note=note)


def cat(name, field, tf, syn, note=None, allowed=None):
    d = dict(name=name, kind='cat', unit='kategori', input_field=field, transform=tf, synthetic=syn, note=note)
    if allowed:
        d['allowed_values_override'] = allowed
    return d


def ln_rng(lo, hi):
    return round(math.log(max(lo, 1)), 4), round(math.log(hi), 4)


AGE = lambda lo, hi, syn=55, tf='age_cap80': num('age', 'yıl', 'age_years', tf, lo, hi, syn)  # noqa: E731
BMI = lambda: num('bmi', 'kg/m2', 'height_cm+weight_kg', 'bmi_kgm2', 12, 80, 27.0)  # noqa: E731
WAIST = lambda: num('waist', 'cm', 'waist_cm', 'identity', 40, 200, 95.0)  # noqa: E731


def race4(prefix=''):
    return [binf('race_mexam', 'race_ethnicity', 'race_mexam'), binf('race_othhisp', 'race_ethnicity', 'race_othhisp'),
            binf('race_black', 'race_ethnicity', 'race_black'), binf('race_other', 'race_ethnicity', 'race_other')]


DM_A_FEATS = ([AGE(20, 80), binf('sex_male', 'sex', 'sex_male01', 0.0)] + race4() +
              [BMI(), WAIST(), num('sbp', 'mmHg', 'sbp_1..3_mmhg', 'sbp_mean_all', 70, 260, 120.0), num('dbp', 'mmHg', 'dbp_1..3_mmhg', 'dbp_mean_all', 30, 150, 75.0),
               binf('htn_dx_med', 'told_hypertension+on_bp_medication', 'htn_dx_med'), binf('fam_dm', 'family_hx_diabetes', 'bool01'),
               binf('gdm', 'sex+gestational_diabetes_hx', 'gdm_rule'), binf('pa_rec', 'recreational_activity', 'bool01', 1.0),
               binf('smoke_current', 'smoking_status', 'smoke_current01'), binf('smoke_former', 'smoking_status', 'smoke_former01')])
DM_B_EXTRA = [num('tc', 'mg/dL', 'total_chol_mgdl', 'identity', 50, 600, 190.0), num('hdl', 'mg/dL', 'hdl_mgdl', 'identity', 5, 200, 50.0),
              num('tg_log', 'ln(mg/dL)', 'tg_mgdl', 'ln_clip1', *ln_rng(10, 5000), 4.6052, note='ln(TG mg/dL)'),
              num('alt_log', 'ln(U/L)', 'alt_ul', 'ln_clip1', *ln_rng(3, 1000), 3.1781, note='ln(ALT U/L)'),
              num('uric_acid', 'mg/dL', 'uric_acid_mgdl', 'identity', 0.5, 20, 5.4)]

CKD_A_FEATS = ([AGE(20, 80), binf('sex_female', 'sex', 'sex_female01', 1.0)] + race4() +
               [BMI(), WAIST(), num('sbp', 'mmHg', 'sbp_1..3_mmhg', 'sbp_mean_23', 70, 260, 120.0), num('dbp', 'mmHg', 'dbp_1..3_mmhg', 'dbp_mean_23', 30, 150, 75.0),
                binf('htn_told', 'told_hypertension', 'bool01'), binf('dm_told', 'told_diabetes', 'bool01'), binf('chd_hist', 'hx_coronary_disease', 'bool01'),
                binf('chf', 'hx_heart_failure', 'bool01'), binf('stroke', 'hx_stroke', 'bool01'), binf('htn_med', 'told_hypertension+on_bp_medication', 'htn_med_rule'),
                binf('dm_insulin', 'told_diabetes+on_insulin', 'dm_insulin_rule'), binf('dm_pills', 'told_diabetes+on_diabetes_pills', 'dm_pills_rule'),
                binf('smoke_current', 'smoking_status', 'smoke_current01'), binf('smoke_former', 'smoking_status', 'smoke_former01')])
CKD_B_EXTRA = [num('glucose', 'mg/dL', 'glucose_serum_mgdl', 'identity', 30, 800, 95.0), num('hba1c', '%', 'hba1c_pct', 'identity', 3.0, 18.0, 5.4),
               num('tc', 'mg/dL', 'total_chol_mgdl', 'identity', 50, 600, 190.0), num('hdl', 'mg/dL', 'hdl_mgdl', 'identity', 5, 200, 50.0),
               num('hemoglobin', 'g/dL', 'hemoglobin_gdl', 'identity', 3, 22, 14.0)]

HTN_FEATS = [AGE(18, 80), cat('sex', 'sex', 'sex_str', 'female'), cat('race', 'race_ethnicity', 'race_str', 'nh_white'), BMI(), WAIST(),
             cat('smoking', 'smoking_status', 'smoking_str', 'never'), num('alcohol_dpd', 'içki/gün', 'alcohol_drinks_per_day', 'alcohol_dpd', 0, 30, 0.2),
             cat('diabetes', 'told_diabetes+on_insulin+on_diabetes_pills', 'diabetes_yesno', 'no'), num('hba1c', '%', 'hba1c_pct', 'identity', 3.0, 18.0, 5.4),
             num('tc', 'mg/dL', 'total_chol_mgdl', 'identity', 50, 600, 190.0), num('hdl', 'mg/dL', 'hdl_mgdl', 'identity', 5, 200, 50.0),
             num('egfr', 'mL/dk/1.73m2', 'creatinine_mgdl+age_years+sex', 'egfr_ckdepi2021', 5, 160, 95.0),
             num('uacr_log', 'ln(1+mg/g)', 'urine_albumin_mgl+urine_creatinine_mgdl', 'uacr_log1p', 0.0, 10.4, 2.5)]

FIB_FEATS = [AGE(20, 80), cat('sex', 'sex', 'sex_str', 'female'), BMI(), WAIST(), num('weight', 'kg', 'weight_kg', 'identity', 25, 300, 80.0),
             num('alt', 'U/L', 'alt_ul', 'identity', 3, 1000, 20.0), num('ast', 'U/L', 'ast_ul', 'identity', 3, 1000, 20.0), num('ggt', 'U/L', 'ggt_ul', 'identity', 1, 2000, 22.0),
             num('alp', 'U/L', 'alp_ul', 'identity', 10, 1500, 74.0), num('albumin', 'g/dL', 'albumin_gdl', 'identity', 1.0, 6.5, 4.2),
             num('platelets', '10^3/µL', 'platelets_k_ul', 'identity', 10, 1500, 240.0), num('glucose', 'mg/dL', 'glucose_serum_mgdl', 'identity', 30, 800, 95.0),
             num('hba1c', '%', 'hba1c_pct', 'identity', 3.0, 18.0, 5.4), cat('diabetes', 'told_diabetes+on_insulin+on_diabetes_pills', 'diabetes_yesno', 'no'),
             num('tg', 'mg/dL', 'tg_mgdl', 'identity', 10, 5000, 110.0), num('hdl', 'mg/dL', 'hdl_mgdl', 'identity', 5, 200, 50.0),
             num('alcohol_dpd', 'içki/gün', 'alcohol_drinks_per_day', 'alcohol_dpd', 0, 30, 0.2)]

OSTEO_FEATS = [AGE(50, 80, 64), cat('sex', 'sex', 'sex_str', 'female'), num('weight', 'kg', 'weight_kg', 'identity', 25, 300, 77.0), num('height', 'cm', 'height_cm', 'identity', 100, 230, 166.0),
               BMI(), cat('smoker_current', 'smoking_status', 'smoker_yesno', 'no'), cat('alcohol_3plus', 'alcohol_drinks_per_day', 'alcohol_ge3_yesno', 'no'),
               cat('glucocorticoid', 'glucocorticoid_ge1month', 'bool_yesno', 'no'), cat('fx_hip', 'fracture_hip', 'bool_yesno', 'no'),
               cat('fx_wrist', 'fracture_wrist', 'bool_yesno', 'no'), cat('fx_spine', 'fracture_spine', 'bool_yesno', 'no'),
               cat('fx_after20', 'fracture_after_age20', 'bool_yesno', 'no'), cat('parent_hip_fx', 'parent_hip_fracture', 'bool_yesno', 'no'),
               cat('no_period_12m', 'sex+menses_absent_12m', 'osteo_period_yesno', 'yes'),
               num('age_last_period', 'yıl', 'age_last_period_years', 'osteo_age_last_period', 10, 70, 48.0, note='erkekte/adeti süren kadında yapısal boş (null) kabul; sentetik kontrol dolu değerle yapılır'),
               cat('hrt_ever', 'sex+hrt_ever', 'osteo_hrt', 'no')]

ANEMIA_FEATS = [AGE(20, 65, 35), cat('sex', 'sex', 'sex_str', 'female'), BMI(), WAIST(), cat('smoker', 'smoking_status', 'smoker_yesno', 'no'),
                num('hba1c', '%', 'hba1c_pct', 'identity', 3.0, 18.0, 5.3), num('alt', 'U/L', 'alt_ul', 'identity', 3, 1000, 23.0), num('ast', 'U/L', 'ast_ul', 'identity', 3, 1000, 23.0),
                num('tc', 'mg/dL', 'total_chol_mgdl', 'identity', 50, 600, 190.0), num('hdl', 'mg/dL', 'hdl_mgdl', 'identity', 5, 200, 50.0),
                num('creatinine', 'mg/dL', 'creatinine_mgdl', 'identity', 0.2, 15, 0.85), num('wbc', '10^3/µL', 'wbc_k_ul', 'identity', 0.5, 100, 7.0),
                num('rbc', '10^6/µL', 'rbc_m_ul', 'identity', 1.0, 9.0, 4.8), num('mcv', 'fL', 'mcv_fl', 'identity', 50, 140, 90.0), num('rdw', '%', 'rdw_pct', 'identity', 8, 35, 12.5),
                num('albumin', 'g/dL', 'albumin_gdl', 'identity', 1.0, 6.5, 4.4)]

COPD_FEATS = [AGE(40, 79, 62), cat('sex', 'sex', 'sex_str', 'male'), BMI(), cat('smoker', 'smoking_status', 'smoker_yesno', 'no'),
              num('fev1_pre', 'mL', 'fev1_pre_ml', 'identity', 200, 7000, 2350.0), num('fvc_pre', 'mL', 'fvc_pre_ml', 'identity', 300, 9000, 3600.0)]

HF_FEATS = [AGE(18, 100, 56), cat('sex', 'sex', 'sex_str', 'male'), BMI(), cat('smoker', 'smoking_status', 'smoker_yesno', 'no'),
            num('rip3', 'pg/mL', 'rip3_pgml', 'identity', 0, 5000, 338.0)]

AF_FEATS_SPEC = ([AGE(18, 89, 63, 'age_cap89_ptbxl'), cat('sex', 'sex', 'sex_str', 'female')] +
                 [num(f, 'ms', 'ecg_af_' + f, 'ecg_pipeline_output', lo, hi, syn) for (f, _, (lo, hi)), syn in zip(
                     AF_FEATS, [842.0, 24.0, 158.0, 11.5, 270.0, 22.5, 196.0, 27.0, 499.0, 48.0])])

CAD_FEATS = [AGE(20, 100, 56, 'identity'), cat('sex', 'sex', 'cad_sex_strfloat', '0.0'), cat('cp', 'cad_chest_pain_type', 'cad_cp_strfloat', '1.0'),
             num('trestbps', 'mmHg', 'sbp_1_mmhg', 'cad_trestbps', 50, 300, 130.0), num('chol', 'mg/dL', 'total_chol_mgdl', 'identity', 30, 1000, 243.0),
             cat('fbs', 'glucose_fasting_mgdl', 'fasting_gt120_strfloat', '0.0'), cat('restecg', 'cad_resting_ecg', 'cad_restecg_strfloat', '0.0'),
             num('thalach', 'atım/dk', 'cad_max_hr_bpm', 'identity', 20, 260, 152.0), cat('exang', 'cad_exercise_angina', 'cad_exang_strfloat', '0.0'),
             num('oldpeak', 'mm', 'cad_st_depression_mm', 'identity', -10, 20, 0.8), cat('slope', 'cad_st_slope', 'cad_slope_strfloat', '1.0')]

# MI: 168 feature; ayrıntı build_registry.py'de model nesnesinden üretilir (sufiksten aralık).

# --------------------------------------------------------------------------------------------------------------------
# Kanıt yardımcıları
# --------------------------------------------------------------------------------------------------------------------


def M(n, pos, P=None, R=None, FPR=None, AUC=None, thr=None, **extra):
    d = dict(n=n, n_pos=pos, precision=P, recall=R, fpr=FPR, auc=AUC, threshold=thr)
    d.update(extra)
    return d


def ci(v, lo, hi):
    return dict(value=v, ci95=[lo, hi])


# --------------------------------------------------------------------------------------------------------------------
# Model kayıtları (elle yazılan kısım). 'lock' = eşik/feature/SHA için okunacak kaynak.
# --------------------------------------------------------------------------------------------------------------------
MODELS = {}

MODELS['af_S4_DEVICE'] = dict(
    disease='Atriyal fibrilasyon (AF)', disease_key='af', role='primary', phase_of_origin='Phase21 (All_Disease_Improvement_Phase21); pipeline: phase_xxviii',
    model_path='All_Disease_Improvement_Phase21/models/af_S4_DEVICE.joblib', extra_sys_path='All_Disease_Improvement_Phase21/src', venv='focused',
    fit_environment_evidence='All_Disease_Improvement_Phase21/config/environment.json: sklearn 1.8.0, lightgbm 4.7.0, python 3.13.3',
    lock=dict(kind='phase26_manifest', task='af'), family='LightGBM (CalibratedResearchModel sarmalayıcı, ham skor)',
    calibration_status='raw (kalibrasyon uygulanmadı)', features=AF_FEATS_SPEC,
    target_definition='PTB-XL kayıtlarında insan-doğrulamalı 12 derivasyonlu EKG ritminin atriyal fibrilasyon mu sinüs ritmi mi olduğu (AF vs SR; mevcut ritim).',
    population='≥18 yaş, hasta başına ilk EKG, yalnız insan-doğrulamalı AFIB xor SR; 10 s, 500 Hz EKG. Diğer ritimler (AFL, taşikardi, bradikardi, PAC, PVC vb.) eğitimde negatif DEĞİLDİ.',
    input_source_note='10 EKG feature yalnız kilitli AF-ECGDELI-OCTAVE-v1 (Octave + ECGDeli v1.1) pipeline çıktısıdır: phase_xxviii/config/af_pipeline_lock.json (SHA256 sidecar: af_pipeline_lock.sha256).',
    evidence=dict(
        highest_tier='dış doğrulama (bağımsız, farklı kaynaklar; donmuş model + kilitli pipeline bileşimi)',
        internal_test=dict(source='Phase XXVII (PTB-XL, hasta düzeyinde ayrık)', **M(1572, 114, ci(0.873, 0.801, 0.921), ci(0.904, 0.835, 0.945), ci(0.010, 0.006, 0.017), ci(0.980, 0.959, 0.995), 0.2360882763700418)),
        temporal=None,
        external=dict(
            source='Phase XXXIII A2 (Challenge 2021: CPSC2018, CPSC-Extra, Chapman-Shaoxing, Georgia; AF vs SR, tam örneklem, havuz)',
            **M(7817, 3497, None, ci(0.929, 0.919, 0.937), ci(0.003, 0.001, 0.005), ci(0.990, 0.987, 0.992), 0.2360882763700418),
            precision_note='P havuzda 0,997 ama örneklem prevalansı gerçek popülasyonu temsil etmez; hedef karşılaştırması için KULLANILMAZ.',
            other_rhythms=dict(source='Phase XXXIII B (AF vs diğer ritimler, havuz)', **M(5477, 3497, None, ci(0.929, 0.919, 0.937), ci(0.072, 0.062, 0.084), ci(0.965, 0.960, 0.970), 0.2360882763700418)),
            georgia=dict(recall=0.764, fpr=0.002, note='Georgia en zayıf kaynak (Recall 0,764)')),
        research_target_note='Üç hedef AF vs SR iç testte GA ile birlikte sağlandı; dış doğrulamada P prevalansa bağlı olduğu için değerlendirilemez. Diğer ritimlerde FPR 0,072 (sinüs taşikardisinde 0,181; PVC 0,306).'),
    limitations=['Model yalnız AF vs sinüs ritmi ayırır; diğer ritimlere karşı FPR 0,072, sinüs taşikardisinde 0,181, PVC 0,306.',
                 'Feature\'lar yalnız AF-ECGDELI-OCTAVE-v1 ile üretilebilir (Octave 10.3.0 + ECGDeli v1.1 + vendor WFDB). Pipeline-golden uyumu: karar uyumu 0,99 (Wilson alt sınır 0,946); QT ve P/PR sapması sürüyor.',
                 'Georgia kaynağında Recall 0,764; RR düzensizliği göstermeyen ilk 10 s\'lik AF kayıtları kaçıyor.',
                 'Pipeline başarısızlığı (zero_beats, ecgdeli_error, feature_error) → tahmin üretilmez.',
                 'Olasılıklar kalibre değil; yalnız sabit eşikte karar. Pipeline sapması AF kayıtlarında olasılığı kaydırabilir (p95 |Δp| 0,24).',
                 'Tek ritim kaydı; semptom/klinik bağlam yok. Klinik tanı DEĞİL.'],
    app_feasibility='ECG sinyali + kilitli Octave pipeline gerekir (≈3,6 s/kayıt). Tek başına mobil/web formu ile ÜRETİLEMEZ.',
    missing_rule='ZORUNLU: 12 feature\'ın tamamı. Pipeline herhangi birini üretemezse (NaN) tahmin üretilmez. Yaş ≥ 90 → tahmin yok. Dondurulmuş imputer uygulama tarafında KULLANILMAZ.')

MODELS['mi_model'] = dict(
    disease='Miyokard enfarktüsü (EKG bulgusu)', disease_key='mi', role='primary', phase_of_origin='phase_xxxviii',
    model_path='phase_xxxviii/models/mi_model.joblib', extra_sys_path=None, venv='focused',
    fit_environment_evidence='phase_xxxviii/PHASE_XXXVIII_REPORT.md §7: ilk çalıştırma kök .venv\'de catboost yokluğundan durdu, Focused 2026 .venv ile tekrarlandı (lightgbm 4.7.0).',
    lock=dict(kind='lock_json', path='phase_xxxviii/config/model_lock.json', model_key='MODEL', thr_primary='threshold_locked', thr_secondary={'threshold_recall075_reporting_only': 'threshold_recall075'}),
    family='LightGBM (sınıf ağırlıklı; imblearn Pipeline)', calibration_status='yok (ham skor, class_weight)', features=None,
    target_definition='PTB-XL\'de kardiyoloğun aynı EKG\'yi MI (eski veya akut) olarak kodlamasının NORM kayıtlardan ayrımı (kod: MI; hedef = EKG okuması, troponin/görüntüleme değil).',
    population='≥18 yaş, hasta başına ilk doğrulanmış EKG; MI vs NORM (başka anormallikler negatifte yok).',
    input_source_note='168 feature = PTB-XL+ ECGDeli dışa aktarımının kayıt başına medyanı. Kilitli AF pipeline\'ı bu feature\'ları ÜRETMEZ.',
    evidence=dict(
        highest_tier='iç test',
        internal_test=dict(source='Phase XXXVIII (PTB-XL/PTB-XL+ ; tüm test; %75\'i AF eşik seçiminde görülmüş kişi: PREVIOUSLY_EXPOSED)', **M(1474, 521, ci(0.781, 0.747, 0.811), ci(0.942, 0.919, 0.959), ci(0.145, 0.124, 0.169), ci(0.973, 0.965, 0.980), 0.04425664273332783),
                           clean_subset=M(368, 160, ci(0.812, 0.751, 0.861), ci(0.975, 0.937, 0.990), ci(0.173, 0.128, 0.230), ci(0.972, 0.958, 0.984), 0.04425664273332783),
                           sensitivity_all_non_mi_negatives=M(2207, 521, 0.424, 0.942, 0.396, ci(0.857, 0.841, 0.873), 0.04425664273332783)),
        temporal=None, external=None,
        research_target_note='Tüm testte 3 hedef nokta tahminiyle sağlandı (FPR GA üst sınırı 0,169 > 0,15); temiz alt kümede FPR 0,173 (hedef yok). MI dışı anormallikler negatife katılınca FPR 0,396.'),
    limitations=['Zamansal doğrulama ve bağımsız dış doğrulama YAPILMADI.',
                 'Etiket ve feature aynı EKG\'den gelir; yüksek AUC klinik MI tanı doğruluğu anlamına gelmez (troponin/görüntüleme referansı yok; MI çoğunlukla eski/evresi belirsiz).',
                 'MI\'ya özgüllük sınırlı: STTC/CD/HYP kayıtları negatife eklenince FPR 0,40–0,50; model büyük ölçüde "anormal EKG" ayırıyor. Yaş ≥ 65\'te FPR 0,28.',
                 'Kural baseline\'ı (B2) geçersiz çıktı (AUC 0,31); geçerli basit kurala göre ML katkısı ÖLÇÜLEMEDİ. Ölçülebilen katkı yaş+cinsiyete göre +0,155 AUC.',
                 'Eşik FPR sınırında (OOF FPR 0,149). İkincil eşik (0,8634) yalnız raporlama içindir, kilitli karar eşiği değildir.',
                 'Feature üretim pipeline\'ı YOK (lead bazlı genlikler); dış veride/uygulamada feature üretilemez.'],
    app_feasibility='UYGULAMAYA ALINAMAZ (şimdilik): 168 lead bazlı ECGDeli feature\'ını üretecek kilitli pipeline mevcut değil.',
    missing_rule='ZORUNLU: 168 feature. Yalnız PTB-XL+ eğitiminde olduğu gibi ST_Elev ailesi (12 sütun) birlikte NaN ise ve ST_Elev_missing=1 ise kabul; diğer her eksik → tahmin yok.')

MODELS['cad_DEVICE'] = dict(
    disease='Koroner arter hastalığı (CAD)', disease_key='cad', role='primary', phase_of_origin='V2 başlangıcı (kök models/cad); düzeltilmiş teknik tekrar: phase_xli',
    model_path='models/cad/DEVICE.joblib', extra_sys_path=None, venv='root', fit_environment_evidence=NF,
    lock=dict(kind='phase26_manifest', task='cad'), family='Lojistik regresyon + sigmoid kalibrasyon (CalibratedClassifierCV, OOF)',
    calibration_status='sigmoid_oof (Platt; yine de klinik olasılık DEĞİL)', features=CAD_FEATS,
    target_definition='UCI kohortlarında anjiyografik >%50 koroner daralma (num>0) bulunup bulunmaması (mevcut durum).',
    population='UCI Cleveland eğitim (n=303 türevi; eğitim 181); hastane kohortu, semptomatik/anjiyografiye yönlendirilmiş kişiler (genel popülasyon DEĞİL).',
    input_source_note='Efor testi (thalach, oldpeak, slope, exang) ve istirahat EKG gerektirir.',
    evidence=dict(
        highest_tier='iç test + düzeltilmiş teknik tekrar (bağımsız dış doğrulama DEĞİL)',
        internal_test=dict(source='Cleveland UCI test (phase_xxvii; önceden görülmüş)', **M(61, 28, ci(0.885, 0.710, 0.960), ci(0.821, 0.644, 0.921), ci(0.091, 0.031, 0.236), ci(0.948, 0.888, 0.990), 0.5401802969539393)),
        temporal=None,
        external=dict(source='Phase XLI düzeltilmiş teknik tekrar (UCI Hungarian n=95, VA n=64; eksiksiz-vaka, seçilmiş, PREVIOUSLY_EXPOSED; bağımsız dış doğrulama DEĞİL)',
                      hungarian=M(95, 68, ci(0.857, 0.757, 0.921), ci(0.882, 0.785, 0.939), ci(0.370, 0.215, 0.558), ci(0.852, 0.766, 0.928), 0.5401802969539393),
                      va=M(64, 54, ci(0.885, 0.782, 0.943), ci(1.000, 0.934, 1.000), ci(0.700, 0.397, 0.892), ci(0.667, 0.437, 0.859), 0.5401802969539393),
                      note='Switzerland YAPILAMAZ (chol %100 eksik). Eski V2 dış sonuçları (R≈0,51) kodlama hatası nedeniyle GEÇERSİZ: phase_xlii/ERRATA_CAD_V2.md.'),
        research_target_note='İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil; n=61). Düzeltilmiş dış tekrarlarda FPR 0,37–0,70 (hedef yok).'),
    limitations=['Kategorik girdiler string-float biçiminde olmalı (\'1.0\'); \'1\' biçimi sessizce bilinmeyen sayılır ve one-hot sıfırlanır (V2 kodlama hatası, ERRATA_CAD_V2.md). Uygulama dönüşüm tablosunu birebir uygulamalı.',
                 'İç test n=61 (28 pozitif): geniş GA. Düzeltilmiş dış tekrar seçilmiş eksiksiz-vaka alt kümesi (Hungarian 95, VA 64; negatif 27 ve 10).',
                 'Girdiler efor testi ve EKG gerektirir; genel popülasyon taraması için uygun değil. Hedef anjiyografik darlık (klinik semptom/risk değil).',
                 'BASIC/LAB panelleri yeniden skorlanmadı ve bu kayda alınmadı. Doğrulanmış tek düzeltilmiş kanıt: phase_xli DEVICE teknik tekrarı.',
                 'Eğitim verisinde kişi kimliği yok (satır = kişi varsayımı).'],
    app_feasibility='Efor testi sonuçları ve istirahat EKG\'si olan klinik girdi gerekir; kendi beyanıyla doldurulamaz.',
    missing_rule='ZORUNLU: 11 feature. Herhangi biri eksikse tahmin üretilmez (model manifesti: "inference abstains on any missing required input"). Kategori string-float biçimine dönüştürülemiyorsa tahmin yok.')

MODELS['dm_A'] = dict(
    disease='Diyabet (teşhis edilmemiş)', disease_key='diabetes', role='primary', phase_of_origin='phase_xlii',
    model_path='phase_xlii/models/dm_A_final.joblib', extra_sys_path=None, venv='root', fit_environment_evidence='Yalnız LR (sklearn 1.8.0); phase_xlii\'de venv kaydı BULUNAMADI',
    lock=dict(kind='lock_json', path='phase_xlii/config/model_lock.json', model_key='A', section='models', thr_primary='threshold_primary', thr_secondary={'referral_matched': 'threshold_referral_matched'}),
    family='Lojistik regresyon (class_weight; imputer+scaler+LR)', calibration_status='yok (class_weight nedeniyle olasılık şişik; ham skor)', features=DM_A_FEATS,
    target_definition='Farkında olmayan erişkinde tek ziyaret ölçümüyle HbA1c ≥ 6,5% veya (açlık alt örnekleminde) FPG ≥ 126 mg/dL olması (teşhis edilmemiş diyabet; mevcut durum).',
    population='NHANES ≥20 yaş, gebe değil, diyabet tanısı/ilacı yok (DIQ010≠1, insülin/hap yok), HbA1c ölçülmüş. Prevalans ≈ %4,4.',
    input_source_note='Laboratuvarsız: yaş, cinsiyet, ırk, BMI, bel, tansiyon, hipertansiyon öyküsü/ilacı, aile öyküsü, GDM, aktivite, sigara.',
    evidence=dict(
        highest_tier='iç test (NHANES içi; zamansal değil; PREVIOUSLY_EXPOSED_PERSONS başka hedef; diyabet hedefinde yeni kişiler)',
        internal_test=dict(source='Phase XLII (NHANES G 2011–12 + H 2013–14, kilitli tek sefer)', **M(8895, 389, ci(0.103, 0.092, 0.115), ci(0.733, 0.687, 0.774), ci(0.292, 0.282, 0.302), ci(0.800, 0.781, 0.819), 0.4958988256379918),
                           npv=0.983, adamatched_threshold=dict(threshold=0.47041760192278687, precision=0.099, recall=ci(0.761, 0.716, 0.801), fpr=0.317),
                           delta_auc_vs_ADA=ci(0.042, 0.028, 0.055)),
        temporal=None, external=None,
        research_target_note='Hiçbir eşikte sağlanmadı (P 0,09–0,12; %4,4 prevalansta yapısal olarak zor). Birincil eşikte Recall ≥ 0,75 testte korunmadı (0,733).'),
    limitations=['Tarama sıralayıcısı; P ≈ 0,10: pozitif yönlendirilenlerin ~%10\'u gerçekten pozitif. Kişilerin ≈ %1/3\'ü yönlendiriliyor. NPV 0,983.',
                 'Etiket tek ziyaret ölçümüdür; ADA doğrulama testi yok. FPG yalnız açlık alt örnekleminde (%45) ölçülmüş.',
                 'Bağımsız (NHANES dışı) dış doğrulama ve zamansal olmayan iç test. ADA skoruna göre ΔAUC +0,042 (küçük).',
                 'Survey ağırlığı/PSU/strata kullanılmadı. ADA fiziksel aktivite maddesi operasyonel; ADA GDM\'li güncel formu BULUNAMADI.',
                 '"Diğer/çok ırklı" grupta tüm kurallarda Recall düşük; <45 yaşta Recall 0,47–0,58.',
                 'Model yalnız diyabet TANISI almamış kişi için geçerli; tanılı/ilaç kullananlara uygulanmaz.'],
    app_feasibility='Kullanıcı formuyla doldurulabilir (ölçüm gerektiren: boy/kilo/bel/tansiyon).',
    missing_rule='ZORUNLU: 16 feature (gdm: erkek için otomatik 0). Kadında GDM yanıtı yoksa tahmin yok. Diyabet tanısı/ilacı varsa model uygulanmaz. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN (varsayım yok).')

MODELS['dm_B'] = dict(
    disease='Diyabet (teşhis edilmemiş) — laboratuvarlı', disease_key='diabetes', role='secondary (laboratuvar varsa)', phase_of_origin='phase_xlii',
    model_path='phase_xlii/models/dm_B_final.joblib', extra_sys_path=None, venv='root', fit_environment_evidence='Yalnız LR (sklearn 1.8.0); venv kaydı BULUNAMADI',
    lock=dict(kind='lock_json', path='phase_xlii/config/model_lock.json', model_key='B', section='models', thr_primary='threshold_primary', thr_secondary={'referral_matched': 'threshold_referral_matched'}),
    family='Lojistik regresyon (class_weight)', calibration_status='yok (ham skor)', features=DM_A_FEATS + DM_B_EXTRA,
    target_definition='Model A ile aynı (teşhis edilmemiş diyabet: HbA1c ≥ 6,5% veya açlıkta FPG ≥ 126 mg/dL; HbA1c/glukoz girdi DEĞİL).',
    population='Model A ile aynı.',
    input_source_note='Model A + rutin biyokimya: total kolesterol, HDL, trigliserit (ln), ALT (ln), ürik asit. HbA1c ve glukoz girdi olamaz.',
    evidence=dict(
        highest_tier='iç test (NHANES içi; zamansal değil)',
        internal_test=dict(source='Phase XLII (G+H, kilitli tek sefer)', **M(8895, 389, ci(0.122, 0.109, 0.136), ci(0.715, 0.668, 0.757), ci(0.236, 0.227, 0.245), ci(0.826, 0.808, 0.843), 0.5314872247498732),
                           npv=0.983, delta_auc_vs_A=ci(0.025, 0.014, 0.036), delta_auc_vs_ADA=ci(0.067, 0.050, 0.083)),
        temporal=None, external=None,
        research_target_note='Hiçbir eşikte sağlanmadı (P 0,10–0,12).'),
    limitations=['Model A\'nın tüm sınırlılıkları geçerli. Rutin lab katkısı küçük ama anlamlı (ΔAUC B−A +0,025).',
                 'TG biyokimya değeri (LBXSTR; CDC LBXTR önerir); E-2007 LX20 analitleri düzeltmesiz; J laboratuvarlarına CDC geri denklemi uygulanmıştı (eğitim).',
                 'Kullanıcı HbA1c/glukoz bilse bile modele girilmez (hedefi tanımlar); bu değerler varsa doğrudan tanı eşikleri kullanılmalıdır.'],
    app_feasibility='Rutin biyokimya sonuçları gerekir.',
    missing_rule='ZORUNLU: 21 feature. Lab alanlarından biri eksikse B üretilmez; A\'ya geri dönülebilir (A kendi kuralını sağlıyorsa). Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.')

MODELS['anemia_LR16'] = dict(
    disease='Anemi', disease_key='anemia', role='primary', phase_of_origin='Clinical_Optimization_Phase25 (CBC_MATCHED16); dış doğrulama phase_xl',
    model_path='Clinical_Optimization_Phase25/models/anemia_CBC_MATCHED16.joblib', extra_sys_path='Clinical_Optimization_Phase25/src', venv='root', fit_environment_evidence=NF,
    lock=dict(kind='phase26_manifest', task='anemia'), family='Lojistik regresyon + sigmoid kalibrasyon (CalibratedResearchModel)',
    calibration_status='sigmoid (OOF Platt; klinik olasılık DEĞİL)', features=ANEMIA_FEATS,
    target_definition='Uygun yetişkinlerde düşük hemoglobin: erkek 20–65 yaş Hb < 13 g/dL; kadın 20–44 yaş, gebe olmadığı doğrulanmış, Hb < 12 g/dL (demir eksikliği anemisi DEĞİL).',
    population='NHANES erkek 20–65, kadın 20–44 (gebe değil, RIDEXPRG=2). Hb, MCH, MCHC, hematokrit girdi değil.',
    input_source_note='Tam kan sayımı (RBC, MCV, RDW, WBC) + biyokimya (HbA1c, ALT, AST, TC, HDL, kreatinin, albümin) + antropometri.',
    evidence=dict(
        highest_tier='dış doğrulama (NHANES farklı döngüler; aynı anket programı, PREVIOUSLY_EXPOSED başka hedef) — bağımsız kurum doğrulaması DEĞİL',
        internal_test=dict(source='Phase XXVII (NHANES 1999–2000 A, önceden görülmüş)', **M(410, 21, ci(0.810, 0.600, 0.923), ci(0.810, 0.600, 0.923), ci(0.010, 0.004, 0.026), ci(0.991, 0.980, 0.999), 0.27030089895763654)),
        temporal=None,
        external=dict(source='Phase XL (NHANES C, E, F, I birleşik)', **M(11171, 669, ci(0.709, 0.678, 0.739), ci(0.883, 0.857, 0.906), ci(0.023, 0.020, 0.026), ci(0.991, 0.989, 0.993), 0.27030089895763654),
                      per_cycle=dict(C=dict(precision=0.766, recall=0.921, fpr=0.011), E=dict(precision=0.637, recall=0.955, fpr=0.031), F=dict(precision=0.618, recall=0.902, fpr=0.034), I=dict(precision=0.867, recall=0.809, fpr=0.012)),
                      delta_auc_vs_hct_rule=ci(0.0037, 0.0021, 0.0054)),
        research_target_note='İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil). Dış: P hedefte C/I\'da (0,77/0,87), E/F\'de altında (0,64/0,62); Recall ≥ 0,75 ve FPR ≤ 0,15 tüm döngülerde sağlandı.'),
    limitations=['ML katkısı pratikte YOK: Hct_proxy = RBC×MCV/10 kuralına göre ΔAUC +0,002…+0,004 (eşdeğer). Model Hb\'yi aynı hemogramdan yeniden hesaplıyor (Hb varyansının R²=0,943\'ü RBC ve MCV ile açıklanıyor).',
                 'İç test küçük (21 pozitif). Dış test aynı anket programı; E/F döngülerinde Precision hedefin altında.',
                 'Etiyoloji yok (demir eksikliği vb.); yükseklik/sigara Hb düzeltmesi yok. Gebelik durumu bilinmeyen kadın uygun değil.',
                 'Kreatinin standardize ölçek (E-2007 CDC düzeltmesi yayımlanmış dosyada uygulanmış); I döngüsü CBC yöntemi (DxH 800) Phase XL\'de belgelenmiş, diğer yöntem farkları sınırlılık.',
                 'Anemi için doğrudan Hb ölçümü varken bu modelin klinik katkısı yoktur; uygulama değeri "Hb yokken CBC ile tarama" ile sınırlı.'],
    app_feasibility='Tam kan sayımı + biyokimya sonuçları gerekir; 16 alan.',
    missing_rule='ZORUNLU: 16 feature. Hb ölçülmüşse model yerine Hb eşiği kullanılmalı. Kadın için gebelik dışlanamıyorsa (ve yaş 20–44 dışındaysa) uygulanmaz. Dondurulmuş imputer kullanılmaz.')

MODELS['copd_S4_DEVICE'] = dict(
    disease='KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi)', disease_key='copd', role='primary', phase_of_origin='Phase21; zamansal tekrar phase_xxvii',
    model_path='All_Disease_Improvement_Phase21/models/copd_S4_DEVICE.joblib', extra_sys_path='All_Disease_Improvement_Phase21/src', venv='focused',
    fit_environment_evidence='All_Disease_Improvement_Phase21/config/environment.json: sklearn 1.8.0',
    lock=dict(kind='phase26_manifest', task='copd'), family='Lojistik regresyon (CalibratedResearchModel, ham skor)', calibration_status='raw', features=COPD_FEATS,
    target_definition='Post-bronkodilatör FEV1/FVC < 0,70 (sabit oran) olması; popülasyon: bronkodilatör testine seçilmiş kişiler.',
    population='NHANES 40–79 yaş, pre-BD FEV1/FVC < LLN ve/veya < 0,70 nedeniyle bronkodilatör testi yapılmış ve ATS A/B kalitesinde tamamlamış kişiler. Negatif = bronkodilatörle düzelen kişiler (sağlıklı popülasyon DEĞİL).',
    input_source_note='Pre-BD spirometri (FEV1, FVC mL) + yaş, cinsiyet, BMI, sigara.',
    evidence=dict(
        highest_tier='zamansal tekrar (aynı anket, farklı döngü; PREVIOUSLY_EXPOSED) — bağımsız klinik kohort DEĞİL',
        internal_test=dict(source='Phase XXVII (NHANES G 2011–12)', **M(37, 20, ci(1.000, 0.772, 1.000), ci(0.650, 0.433, 0.819), ci(0.000, 0.000, 0.184), ci(0.921, 0.824, 0.988), 0.5707211331015863)),
        temporal=dict(source='Phase XXVII (NHANES F 2009–10)', **M(250, 156, ci(0.929, 0.871, 0.962), ci(0.756, 0.683, 0.817), ci(0.096, 0.051, 0.172), ci(0.898, 0.857, 0.934), 0.5707211331015863),
                      E_2007_2008=M(274, 163, ci(0.929, 0.870, 0.962), ci(0.718, 0.644, 0.781), ci(0.081, 0.043, 0.147), ci(0.901, 0.865, 0.933), 0.5707211331015863)),
        external=None,
        research_target_note='F 2009–10\'da 3 hedef nokta tahminiyle sağlandı (GA ile değil; E 2007–08\'de Recall 0,718 < 0,75). Seçilmiş popülasyonda P/FPR genel popülasyona taşınamaz.'),
    limitations=['Hedef popülasyon dar: yalnız pre-BD spirometride obstrüksiyon saptanıp BD testine alınmış kişiler. Genel popülasyon KOAH taramasında KULLANILAMAZ; FPR/Precision genel popülasyona taşınamaz.',
                 'Model pre-BD FEV1/FVC < 0,70 kuralına eşdeğer: ΔAUC +0,009 (−0,059…+0,076).',
                 'İç test n=37 (20 pozitif). Zamansal tekrar aynı anket programı; kişi takibi yok.',
                 'Astımı ayırt etmez; klinik KOAH tanısı DEĞİL (post-BD sabit oran).',
                 'Sigara = şu an içen (never/former → no); paket-yıl yok.'],
    app_feasibility='Kalite-kontrollü spirometri (pre-BD FEV1 ve FVC, mL) gerekir ve kişi yalnız pre-BD obstrüksiyon saptanmış 40–79 yaş olmalıdır.',
    missing_rule='ZORUNLU: 6 feature. Yaş 40–79 dışı veya pre-BD FEV1/FVC ≥ 0,70 ise model uygulanmaz (eğitim popülasyonu dışı). fev1_pre ≤ fvc_pre. Dondurulmuş imputer kullanılmaz.')

MODELS['hf_S2_BASIC_LAB'] = dict(
    disease='Kalp yetmezliği', disease_key='heart_failure', role='primary (araştırma amaçlı)', phase_of_origin='Phase21; baseline karşılaştırması phase_xxvii; dondurulmuş manifest Strong_Model_External_Validation_Phase26',
    model_path='All_Disease_Improvement_Phase21/models/heart_failure_S2_BASIC_LAB.joblib', extra_sys_path='All_Disease_Improvement_Phase21/src', venv='focused',
    fit_environment_evidence='All_Disease_Improvement_Phase21/config/environment.json: xgboost 3.4.1, sklearn 1.8.0',
    lock=dict(kind='phase26_manifest', task='heart_failure'), family='XGBoost + sigmoid kalibrasyon (CalibratedResearchModel)', calibration_status='sigmoid (Platt; klinik olasılık DEĞİL)', features=HF_FEATS,
    target_definition='Kaynak veri setinde klinik olarak tanılı kalp yetmezliği (HF) ile sağlıklı kontrol ayrımı (vaka-kontrol; mevcut durum).',
    population='Mendeley 7v4w66wxj8.1 (özel RIP3 ELISA çalışması): HF hastaları (akut/kronik karışık) vs sağlıklı kontrol; fit n=110. Semptomlu kontrol veya genel popülasyon DEĞİL.',
    input_source_note='RIP3 özel ELISA assay değeri (pg/mL) gerekir.',
    evidence=dict(
        highest_tier='iç test (n=37)',
        internal_test=dict(source='Phase XXVII (Mendeley 7v4w66wxj8.1)', **M(37, 18, ci(0.824, 0.590, 0.938), ci(0.778, 0.548, 0.910), ci(0.158, 0.055, 0.376), ci(0.950, 0.877, 0.997), 0.4476970841762816)),
        temporal=None, external=None,
        research_target_note='İç testte P ve Recall hedefte, FPR 0,158 > 0,15 (GA geniş). Dış doğrulama YAPILAMADI (Phase XXXIX: uyumlu RIP3 assay\'li başka veri BULUNAMADI).'),
    limitations=['Eğitim n=110, test n=37 (18 pozitif): GA çok geniş; sonuç kararsız.',
                 'Tek değişkene (RIP3) eşdeğer: ΔAUC vs RIP3 −0,006 (−0,044…+0,023); çok değişkenli katkı kanıtı yok.',
                 'Vaka-kontrol tasarımı (sağlıklı kontrol); genel popülasyon veya semptomlu kişilerde performans bilinmiyor. HF alt tipi/LVEF/BNP yok.',
                 'RIP3 rutin klinik test değildir; assay/birim uyumu başka laboratuvarlarda doğrulanmadı (BULUNAMADI).',
                 'Dış doğrulama YOK.'],
    app_feasibility='UYGULAMAYA ALINAMAZ (şimdilik): RIP3 özel assay değeri ve sağlıklı-kontrol tasarımı; kullanıcı girdisiyle üretilemez.',
    missing_rule='ZORUNLU: 5 feature (rip3 dahil). rip3 yoksa model yok (S1_BASIC kayıtlı değil). Dondurulmuş imputer kullanılmaz.')

MODELS['htn_M1'] = dict(
    disease='Hipertansiyon', disease_key='hypertension', role='primary', phase_of_origin='phase_xxxvii',
    model_path='phase_xxxvii/models/htn3_M1.joblib', extra_sys_path=None, venv='focused',
    fit_environment_evidence='phase_xxxvii/PHASE_XXXVII_REPORT.md §5.9: geliştirme ve test Focused 2026 .venv ile (XXXII ile aynı sklearn ve imbalanced-learn)',
    lock=dict(kind='lock_json', path='phase_xxxvii/config/model_lock.json', model_key='M1', section='models', thr_primary='threshold_primary', thr_secondary={'secondary_fpr015': 'threshold_secondary'}),
    family='Lojistik regresyon (RandomOverSampler; imblearn Pipeline)', calibration_status='yok (ROS nedeniyle olasılıklar yüksek; gözlenen/tahmin 0,88)', features=HTN_FEATS,
    target_definition='Tek ziyarette ölçülen kan basıncı ≥ 140/90 mmHg VEYA antihipertansif ilaç kullanımı (mevcut durum; ölçülen tansiyon girdi DEĞİL).',
    population='NHANES ≥ 18 yaş, gebe değil, ≥2 geçerli BP okuması. Geliştirme P+L (2017–2023), test C (2003–04).',
    input_source_note='Laboratuvar gerektirir: HbA1c, total kolesterol, HDL, kreatinin (eGFR), idrar albümini ve kreatinini (UACR).',
    evidence=dict(
        highest_tier='zamansal test (C 2003–04; ölçüm yöntemi kaymalı: auskültatuvar vs oskilometrik) — bağımsız kurum doğrulaması DEĞİL',
        internal_test=None,
        temporal=dict(source='Phase XXXVII (NHANES C 2003–04, kilitli tek sefer; hiçbir hedefte önceden kullanılmamış kişiler)', **M(2798, 1001, ci(0.702, 0.675, 0.729), ci(0.766, 0.739, 0.791), ci(0.181, 0.164, 0.199), ci(0.875, 0.862, 0.887), 0.5397445646616527),
                      secondary_threshold=M(2798, 1001, ci(0.744, 0.715, 0.772), ci(0.665, 0.636, 0.694), ci(0.127, 0.113, 0.144), None, 0.645872880615415),
                      delta_auc_vs_age_sex_bmi=ci(0.012, 0.007, 0.018)),
        external=None,
        research_target_note='Hiçbir eşikte üçlü hedef sağlanmadı (birincil: FPR 0,181; ikincil: Recall 0,665).'),
    limitations=['Yaş+cinsiyet+BMI baseline\'ına katkı yalnız +0,012 AUC (GA +0,007…+0,018): ML katkısı çok küçük; tek eşik pratikte yaş kuralı gibi çalışıyor (≥60 yaşta FPR 0,85, <60 yaşta Recall 0,31).',
                 'Test etiketi auskültatuvar (hekim, cıvalı) — geliştirme oskilometrik (Omron): etiket ölçeği kayması ölçülmedi. Test 14–20 yıl önce.',
                 'Tek ziyaret fenotipi; beyaz önlük/maskeli HTN ayırt edilemez. Test kümesi seçilmiş C alt kümesi.',
                 'Kalibrasyon: ROS nedeniyle olasılıklar yüksek (O/E 0,88). Klinik olasılık değildir.',
                 'Ölçülen tansiyon girdi DEĞİL: kullanıcının tansiyonu biliniyorsa doğrudan ≥140/90 kuralı kullanılmalı.',
                 'Bu kayıtta laboratuvarsız HTN modeli YOK: M1 (kullanıcı ön seçimi) beş laboratuvar girdisi ister; phase_xxxii modelleri kayda alınmadı (L testi CONTAMINATED etiketli, phase_xxxvi §2).'],
    app_feasibility='Laboratuvar sonuçları gerekir (HbA1c, TC, HDL, kreatinin, idrar albümin/kreatinin). Laboratuvarsız kullanıcı için tahmin üretilmez.',
    missing_rule='ZORUNLU: 13 feature. Sigara/alkol eksikse (C testinde medyan/mod ile doldurulmuştu) uygulamada TAHMİN ÜRETİLMEZ. race_ethnicity yanıtsızsa ABSTAIN. Dondurulmuş imputer kullanılmaz.')

MODELS['fibrosis_final'] = dict(
    disease='Karaciğer fibrozisi (LSM ≥ 8 kPa)', disease_key='liver_fibrosis', role='primary', phase_of_origin='phase_xxxi',
    model_path='phase_xxxi/models/fibrosis_final.joblib', extra_sys_path=None, venv='focused',
    fit_environment_evidence='phase_xxxi: CatBoost 1.2.10 gerektirir (yalnız Focused/New 2026 .venv); lightgbm/xgboost kullanılmaz',
    lock=dict(kind='lock_json', path='phase_xxxi/config/fibrosis_model_lock.json', model_key=None, thr_primary='threshold', thr_secondary={'female_secondary': ('sex_specific_thresholds_secondary', 'female'), 'male_secondary': ('sex_specific_thresholds_secondary', 'male'), 'fib4_matched_secondary': ('fib4_matched_secondary', 'model_threshold')}),
    family='CatBoost (imblearn Pipeline, strateji yok)', calibration_status='yok (ham skor)', features=FIB_FEATS,
    target_definition='FibroScan karaciğer sertliği (LSM) ≥ 8,0 kPa (AASLD 2023 VCTE bandı) olması; histolojik ≥F2 ile birebir değil (mevcut durum).',
    population='NHANES ≥ 20 yaş, gebe değil, FibroScan kalitesi tam (LUAXSTAT=1), ALT/AST/trombosit/albümin/BMI mevcut. Açlık şartı aranmadı.',
    input_source_note='Biyokimya (ALT, AST, GGT, ALP, albümin, glukoz, TG, HDL), HbA1c, trombosit + antropometri + alkol.',
    evidence=dict(
        highest_tier='iç test (NHANES L 2021–23; PREVIOUSLY_EXPOSED: kişiler CAP hedefi için görülmüş)',
        internal_test=dict(source='Phase XXXI (NHANES L, kilitli tek sefer)', **M(4714, None, ci(0.240, 0.221, 0.260), ci(0.768, 0.733, 0.801), ci(0.346, 0.332, 0.361), ci(0.794, 0.773, 0.813), 0.06149696006866034),
                           prevalence=0.125, npv=ci(0.952, 0.943, 0.959), n_pos_note='n_pos BULUNAMADI (raporda yalnız prevalans 0,125); FIB-4 AUC 0,597, NFS AUC 0,698 (aynı kişiler)'),
        temporal=None, external=None,
        research_target_note='Üçlü hedef sağlanmadı; eşik Recall ≥ 0,85 hedefiyle seçilmişti, testte 0,768 (tarama hedefi 0,85 altında). Yönlendirme oranı 0,399.'),
    limitations=['CV AUC 0,835 → test AUC 0,794: kayma işareti. Test PREVIOUSLY_EXPOSED; bağımsız dış doğrulama ve zamansal doğrulama yok.',
                 'Açlıksız serum glukoz/TG kullanıldı (protokolde gerekçeli sapma). LSM ≥ 8 kPa histolojik fibrozisle birebir değildir; hedef ölçüm (LSM) girdi DEĞİL.',
                 'FIB-4\'e göre ΔAUC +0,197, NFS\'ye göre +0,096 (ikisi de anlamlı), ancak FIB-4/NFS bu hedef için kalibre edilmemiş basit baseline\'lardır.',
                 'Düşük P (0,24) ve FPR 0,35: yalnız ön tarama sıralayıcısı. Cinsiyete özgü eşikler yalnız ikincil.',
                 'Hepatit B/C ve alkol dışı etiyoloji ayrımı yok. Klinik tanı DEĞİL.'],
    app_feasibility='Biyokimya + CBC (trombosit) + HbA1c sonuçları gerekir; formla doldurulabilir ama 17 alan.',
    missing_rule='ZORUNLU: 17 feature. Dondurulmuş imputer kullanılmaz. Diyabet durumu (told/insulin/pills) yanıtlanmamışsa tahmin yok.')

MODELS['osteo_final'] = dict(
    disease='Osteoporoz (DXA femur T-skoru ≤ −2,5)', disease_key='osteoporosis', role='primary', phase_of_origin='phase_xxx (kilitli; klinik fayda phase_xxxi)',
    model_path='phase_xxx/models/osteo_final.joblib', extra_sys_path=None, venv='root', fit_environment_evidence='Yalnız LR (sklearn 1.8.0); venv kaydı BULUNAMADI',
    lock=dict(kind='lock_json', path='phase_xxx/config/osteo_model_lock.json', model_key=None, thr_primary='threshold', thr_secondary={}),
    family='Lojistik regresyon (imblearn Pipeline; strateji yok)', calibration_status='yok (ham skor; Phase XXXI: eğim 0,98, O/E 1,17)', features=OSTEO_FEATS,
    target_definition='DXA ile min(femur boynu, total femur) T-skoru ≤ −2,5 (NHANES III 20–29 yaş beyaz kadın referansı) olması (mevcut durum; DXA girdi DEĞİL).',
    population='NHANES ≥ 50 yaş, geçerli femur DXA; erkek ve kadın (kadın referansla). Osteoporoz prevalansı %7 civarı.',
    input_source_note='FRAX benzeri öykü girdileri + kilo/boy/BMI; laboratuvar ve DXA gerekmez.',
    evidence=dict(
        highest_tier='zamansal test (NHANES J 2017–18; DXA etiketi ilk kez) — bağımsız kurum doğrulaması DEĞİL',
        internal_test=None,
        temporal=dict(source='Phase XXX (NHANES J, kilitli tek sefer)', **M(2275, 164, ci(0.208, 0.178, 0.242), ci(0.780, 0.711, 0.837), ci(0.230, 0.213, 0.249), ci(0.849, 0.818, 0.880), 0.0602885709255003),
                      delta_auc_vs_OST=ci(0.025, 0.012, 0.038), male_recall=0.48),
        external=None,
        research_target_note='Üçlü hedef (ve tarama hedefi Recall ≥ 0,85) sağlanmadı; eşik Recall ≥ 0,85 için seçilmişti, testte 0,780.'),
    limitations=['Cinsiyetler arası Recall çok farklı: erkeklerde 0,48 (tek eşik). Cinsiyete özgü eşik yok.',
                 'Düşük P (0,21; prevalans düşük). CV havuzlu OOF OST\'yi geçemedi; testte OST\'ye göre ΔAUC +0,025 (küçük ama anlamlı). Phase XXXI: eşit Recall\'da yönlendirme farkları GA 0\'ı içeriyor.',
                 'DXA cihaz/yazılım çapraz kalibrasyonu BULUNAMADI (yalnız-H duyarlılık modeli benzer sonuç). Romatoid artrit/ikincil osteoporoz girdisi BULUNAMADI. Kadın OST eşiği ikincil kaynaktan.',
                 'Alkol harmonizasyonu (D–H: ALQ120Q/U×ALQ130; J: ALQ121×ALQ130) sabit tabloyla; uygulamada alkol ≥3 içki/gün sorusu doğrudan sorulmalı.',
                 'Hedef osteoporoz DXA tanımıdır, kırık riski değil. KNHANES doğrulaması yapılamadı (steroid ve ebeveyn kalça kırığı girdisi yok).'],
    app_feasibility='Formla doldurulabilir (laboratuvarsız). Yaş 50–80 ve cinsiyete özgü sorular gerekir.',
    missing_rule='ZORUNLU: 16 feature. Kadında no_period_12m/hrt_ever yanıtı zorunlu; erkekte \'na_male\' otomatik. age_last_period: yalnız adeti kesilmiş kadında zorunlu, diğerlerinde yapısal boş. Yaş < 50 → model uygulanmaz.')

MODELS['ckd_A'] = dict(
    disease='Böbrek (farkında olunmayan tek ziyaret renal anormalliği)', disease_key='kidney', role='primary', phase_of_origin='phase_xxxv',
    model_path='phase_xxxv/models/ckd_A_final.joblib', extra_sys_path=None, venv='root',
    fit_environment_evidence='phase_xxxv/PHASE_XXXV_REPORT.md: lightgbm 4.6.0 kök .venv\'e kuruldu ve kullanıldı',
    lock=dict(kind='lock_json', path='phase_xxxv/config/model_lock.json', model_key='A', section='models', thr_primary='threshold_primary', thr_secondary={'referral_matched': 'threshold_referral_matched'}),
    family='LightGBM (imputer + LGBM)', calibration_status='yok (ham skor)', features=CKD_A_FEATS,
    target_definition='Farkında olmayan erişkinde tek ziyaret eGFR < 60 (CKD-EPI 2021) VEYA UACR ≥ 30 mg/g (böbrek hastalığı tanısı DEĞİL; KDIGO 3 ay şartı karşılanmaz).',
    population='NHANES ≥ 20 yaş, gebe/diyaliz değil, "doktor zayıf/başarısız böbrek dedi mi" = Hayır. Prevalans ≈ %15.',
    input_source_note='Laboratuvarsız: antropometri, tansiyon, hipertansiyon/diyabet/KKH/KY/inme öyküsü, ilaçlar, sigara.',
    evidence=dict(
        highest_tier='iç test (NHANES I 2015–16; PREVIOUSLY_EXPOSED başka hedef; zamansal değil)',
        internal_test=dict(source='Phase XXXV (NHANES I, kilitli tek sefer)', **M(4812, 716, ci(0.293, 0.273, 0.314), ci(0.767, 0.734, 0.796), ci(0.323, 0.309, 0.337), ci(0.791, 0.773, 0.809), 0.12660209600798616),
                           npv=ci(0.943, 0.934, 0.951), referral_rate=ci(0.389, 0.375, 0.403), delta_auc_vs_modified_SCORED=ci(0.032, 0.020, 0.043)),
        temporal=None, external=None,
        research_target_note='Hiçbir model ve eşikte sağlanmadı (P 0,29–0,31, FPR 0,29–0,32; %15 prevalansta P ≥ 0,70 yapısal olarak zor).'),
    limitations=['Kazanç esas olarak yalnız-UACR pozitiflerinde ve < 60 yaşta; ≥ 60 yaşta tarama kuralı fiilen "yaşa göre herkese test" (FPR 0,74–0,90).',
                 'Etiket tek ziyaret; geçici albüminüri dışlanamaz; KIQ022 öz-bildirim. Yaş ve cinsiyet eGFR denkleminin girdisidir (hedef bileşeniyle mekanik bağ).',
                 'Modifiye SCORED karşılaştırması orijinal yayınla karşılaştırılamaz (PVD/proteinüri yok; SCORED puanları birincil metinle doğrulanamadı).',
                 'Test tek dönem (2015–16), PREVIOUSLY_EXPOSED; bağımsız dış doğrulama yok. Survey tasarımı kullanılmadı.',
                 'Kullanıcı biliyorsa eGFR/UACR doğrudan kullanılmalı (hedefi tanımlar).'],
    app_feasibility='Formla doldurulabilir (laboratuvarsız; ölçüm gerektiren: boy/kilo/bel/tansiyon).',
    missing_rule='ZORUNLU: 20 feature (htn_med, dm_insulin, dm_pills: yapısal atlama kurallarıyla 0). Tanılı böbrek hastalığı/diyaliz varsa model uygulanmaz. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.')

MODELS['ckd_B'] = dict(
    disease='Böbrek — laboratuvarlı', disease_key='kidney', role='secondary (laboratuvar varsa)', phase_of_origin='phase_xxxv',
    model_path='phase_xxxv/models/ckd_B_final.joblib', extra_sys_path=None, venv='root',
    fit_environment_evidence='phase_xxxv/PHASE_XXXV_REPORT.md: lightgbm 4.6.0 kök .venv',
    lock=dict(kind='lock_json', path='phase_xxxv/config/model_lock.json', model_key='B', section='models', thr_primary='threshold_primary', thr_secondary={'referral_matched': 'threshold_referral_matched'}),
    family='LightGBM', calibration_status='yok (ham skor)', features=CKD_A_FEATS + CKD_B_EXTRA,
    target_definition='Model A ile aynı.', population='Model A ile aynı.',
    input_source_note='Model A + serum glukoz, HbA1c, total kolesterol, HDL, hemoglobin (kreatinin, albümin/UACR, ürik asit girdi olamaz).',
    evidence=dict(
        highest_tier='iç test (NHANES I; PREVIOUSLY_EXPOSED)',
        internal_test=dict(source='Phase XXXV (NHANES I, kilitli tek sefer)', **M(4812, 716, ci(0.313, 0.291, 0.335), ci(0.754, 0.721, 0.784), ci(0.290, 0.276, 0.304), ci(0.805, 0.788, 0.823), 0.13832509192715003),
                           npv=ci(0.943, 0.934, 0.951), referral_rate=ci(0.359, 0.345, 0.373), delta_auc_B_minus_A=ci(0.015, 0.009, 0.021)),
        temporal=None, external=None,
        research_target_note='Hiçbir eşikte sağlanmadı.'),
    limitations=['Model A\'nın tüm sınırlılıkları geçerli. Rutin lab katkısı küçük: B−A ΔAUC +0,015.',
                 'Hemoglobin yalnız B\'de (SCORED anemi bileşeni lab olduğu için).'],
    app_feasibility='Rutin laboratuvar sonuçları gerekir.',
    missing_rule='ZORUNLU: 25 feature. Lab eksikse B üretilmez; A\'ya düşülür. Dondurulmuş imputer kullanılmaz. race_ethnicity yanıtsızsa ABSTAIN.')

# Uygulamaya alma ÖNERİSİ (kullanıcı kararı bekler) — kayıtta model olarak yer almaz
CANDIDATES = {
    'fatty_liver': dict(
        disease='Karaciğer yağlanması', recommendation='ALMA (şimdilik)',
        candidate='phase_xxx/models/liver_final.joblib (XGBoost, FibroScan CAP ≥ 274)',
        rationale=['Test etiketi CONTAMINATED (L CAP etiketleri V2 başlangıcı ve Focused fazında model/eşik seçiminde kullanılmış); bağımsız test sayılamaz.',
                   'FLI baseline\'ına testte ΔAUC +0,005 (−0,003…+0,013): anlamlı katkı yok; HSI\'ya göre var. TG ile FLI zaten formülle hesaplanabilir.',
                   'Açık dış CAP verisi BULUNAMADI (KNHANES/CHARLS/CHNS dahil); dış doğrulama yolu şimdilik yok.',
                   'Üçlü hedef sağlanmadı (P 0,720, R 0,648, FPR 0,166).'],
        evidence_summary='Phase XXX test (CONTAMINATED): AUC 0,845; P 0,720; R 0,648; FPR 0,166.'),
    'lipid': dict(
        disease='Lipid bozukluğu (dislipidemi)', recommendation='ALMA',
        candidate='Phase21/Phase24 dyslipidemia modelleri (kilitli son model yok; phase_xxix_b yalnız CV)',
        rationale=['Lipidler hedefi tanımladığı için girdi olamıyor; kalan rutin girdilerle AUC ≈ 0,70 (CV) ve P ≥ 0,70 eşiğinde Recall ≈ 0,17.',
                   'Doğrudan lipid ölçümü varken ML\'in klinik katkısı yok; tarama değeri kanıtlanmadı. Phase XXIX-B sonrası kilitli/test edilmiş yeni model YOK.',
                   "Eski modeller Phase25'te daha önce kullanılmamış A döngüsü holdout'unda değerlendirildi: üçlü hedef karşılanmadı; sonraki iyileştirme yalnız CV aday (Phase XXIX-B)."],
        evidence_summary='Phase XXIX-B CV aday (test değil): AUC 0,70; en iyi aday P 0,67 / R 0,17 / FPR 0,08.'),
    'asthma': dict(
        disease='Astım', recommendation='ALMA',
        candidate='All_Disease_Improvement_Phase21/models/asthma_S1_BASIC.joblib (yaş, cinsiyet, sigara)',
        rationale=['Veri çok küçük (n=253; Exasens vaka-kontrol, saliva/klinik gruplar); yaş+cinsiyet LR\'ye göre ΔAUC +0,001 (GA 0\'ı içeriyor).',
                   'Spirometri/semptom/geri dönüşlülük verisi yok; hedef kaynak-grubu (astım vs HC/enfeksiyon) genel popülasyona taşınmaz.',
                   'Dış doğrulama yok.'],
        evidence_summary='Phase XXIX-B CV aday: AUC 0,758; P 0,74 / R 0,49 / FPR 0,06 (test değil).'),
    'gallstone': dict(
        disease='Safra taşı', recommendation='ALMA',
        candidate='phase_xxx/models/gallstone_final.joblib (CatBoost, NHANES III ultrason)',
        rationale=['Test AUC 0,751; P 0,174 (prevalans %9,4), FPR 0,365; yaş+cinsiyet+BMI LR\'ye göre ΔAUC yalnız +0,012 (+0,004…+0,019).',
                   'Veri 1988–94 (NHANES III); 20 feature\'ın çoğu laboratuvar (CRP, GFR, kreatinin, LDL…); zamansal test aynı kaynak içinde; kişiler karaciğer hedefi için görülmüş.',
                   'Üçlü hedef sağlanmadı; klinik karar değeri düşük (çok yüksek yanlış pozitif).'],
        evidence_summary='Phase XXX zamansal test: AUC 0,751; P 0,174; R 0,741; FPR 0,365.'),
}


# Uygulama görünürlüğü / modu (kullanıcı kararı, Phase XLIII sonrası)
APP = {
    'mi_model': dict(app_visible=False, app_mode='registry_only', reason="feature üretim pipeline'ı yok; yalnız iç test"),
    'hf_S2_BASIC_LAB': dict(app_visible=False, app_mode='registry_only', reason='RIP3 özel assay; n=37; dış doğrulama yok'),
    'cad_DEVICE': dict(app_visible=True, app_mode='clinical_mode', reason='efor testi/EKG girdisi; klinik ortamda girilir'),
    'copd_S4_DEVICE': dict(app_visible=True, app_mode='clinical_mode', reason='kaliteli pre-BD spirometri; dar hedef popülasyon'),
    'af_S4_DEVICE': dict(app_visible=True, app_mode='ecg_upload_demo', reason='EKG yükleme + kilitli Octave pipeline; demo'),
}
for _k in MODELS:
    APP.setdefault(_k, dict(app_visible=True, app_mode='standard', reason='kullanıcı formu / laboratuvar girdisi'))
for _k, _c in CANDIDATES.items():
    _c['user_decision'] = 'ALMA (kullanıcı onayladı, Phase XLIII sonrası)'
