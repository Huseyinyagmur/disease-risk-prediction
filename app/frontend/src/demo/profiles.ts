// SENTETİK demo profilleri — elle üretilmiştir, GERÇEK KİŞİ VERİSİ DEĞİLDİR.
// Alan adları şemada olmalıdır (src/demo/profiles.test.ts bunu /schema örneğine karşı denetler); form tanımı
// buradan değil /schema'dan üretilir. Beklenen panel durumları backend'in /eligibility yanıtıyla Playwright'ta sınanır.
import type { FormValues } from '../lib/form';

export interface DemoProfile {
  id: string;
  title: string;
  description: string;
  values: FormValues;
}

const n = (value: number | string, unit?: string) => ({ value: String(value), ...(unit ? { unit } : {}) });
const b = (value: boolean | string) => ({ value });

const commonHistory: FormValues = {
  smoking_status: b('never'),
  alcohol_drinks_per_day: n(0.3),
  told_hypertension: b(false),
  told_diabetes: b(false),
  on_insulin: b(false),
  on_diabetes_pills: b(false),
  hx_coronary_disease: b(false),
  hx_heart_failure: b(false),
  hx_stroke: b(false),
  family_hx_diabetes: b(false),
  recreational_activity: b(true),
  told_weak_failing_kidneys: b(false),
  on_dialysis: b(false),
  glucocorticoid_ge1month: b(false),
  fracture_hip: b(false),
  fracture_wrist: b(false),
  fracture_spine: b(false),
  fracture_after_age20: b(false),
  parent_hip_fracture: b(false),
};

export const DEMO_PROFILES: DemoProfile[] = [
  {
    id: 'fibrosis_ready',
    title: 'Fibrozis için çalışabilir profil',
    description: '58 yaş erkek; form + karaciğer laboratuvarları tam. Fibrozis modeli "Çalışabilir" olmalı.',
    values: {
      age_years: n(58),
      sex: b('male'),
      race_ethnicity: b('nh_white'),
      height_cm: n(176),
      weight_kg: n(92),
      waist_cm: n(104),
      sbp_1_mmhg: n(132), dbp_1_mmhg: n(84),
      sbp_2_mmhg: n(130), dbp_2_mmhg: n(82),
      sbp_3_mmhg: n(128), dbp_3_mmhg: n(82),
      ...commonHistory,
      alt_ul: n(48),
      ast_ul: n(41),
      ggt_ul: n(62),
      alp_ul: n(88),
      albumin_gdl: n(4.2),
      platelets_k_ul: n(210),
      glucose_serum_mgdl: n(104),
      hba1c_pct: n(5.6),
      tg_mgdl: n(180),
      hdl_mgdl: n(42),
    },
  },
  {
    id: 'missing',
    title: 'Eksik alanlı profil',
    description: '47 yaş kadın; yalnız temel bilgiler ve boy/kilo. Modeller "Eksik: …" göstermeli.',
    values: {
      age_years: n(47),
      sex: b('female'),
      pregnant: b(false),
      height_cm: n(162),
      weight_kg: n(70),
    },
  },
  {
    id: 'out_of_scope',
    title: 'Kapsam dışı profil',
    description: '30 yaş, gebe kadın. Gebelik dışlaması olan modeller ve yaş sınırlı modeller "Kapsam dışı" olmalı.',
    values: {
      age_years: n(30),
      sex: b('female'),
      pregnant: b(true),
      race_ethnicity: b('other_hispanic'),
      height_cm: n(165),
      weight_kg: n(68),
      waist_cm: n(84),
      sbp_1_mmhg: n(112), dbp_1_mmhg: n(72),
      sbp_2_mmhg: n(110), dbp_2_mmhg: n(70),
      sbp_3_mmhg: n(110), dbp_3_mmhg: n(71),
      ...commonHistory,
      gestational_diabetes_hx: b(false),
      menses_absent_12m: b(false),
      hrt_ever: b(false),
    },
  },
  {
    id: 'unit_error',
    title: 'Birim hatalı profil',
    description:
      'Glukoz 5,4 ve kreatinin 80 değerleri mmol/L ve µmol/L iken varsayılan mg/dL biriminde girilmiş. Alan altında aralık hatası görünmeli; birimi düzeltince kaybolmalı.',
    values: {
      age_years: n(52),
      sex: b('male'),
      race_ethnicity: b('nh_black'),
      height_cm: n(180),
      weight_kg: n(85),
      waist_cm: n(96),
      sbp_1_mmhg: n(126), dbp_1_mmhg: n(80),
      sbp_2_mmhg: n(124), dbp_2_mmhg: n(80),
      sbp_3_mmhg: n(124), dbp_3_mmhg: n(78),
      ...commonHistory,
      glucose_serum_mgdl: n(5.4, 'mg/dL'),
      creatinine_mgdl: n(80, 'mg/dL'),
    },
  },
];
