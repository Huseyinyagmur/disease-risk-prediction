"""Phase L2: app_config.json'a arayüz metinleri (yalnız sunum; model, eşik, uygunluk mantığı değişmez).
- form.field_ui_tr[*].short: TÜM form alanları için kısa ad (aralık/geçersiz yanıt mesajlarında; soru biçimli etiket yerine)
- ui.text_tr: durum paneli, asistan sohbet görünümü, kısa uyarı satırı, örnek profil bölümü metinleri
Tekrar çalıştırılabilir. Kullanım (V2 kökünden): python -B phase_l2/scripts/patch_app_config_l2.py"""
import json
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
P = V2 / 'app/backend/config/app_config.json'
cfg = json.loads(P.read_text(encoding='utf8'))
fui, ui = cfg['form']['field_ui_tr'], cfg['ui']

SHORT = {
    'age_years': 'Yaş', 'sex': 'Cinsiyet', 'race_ethnicity': 'Irk / etnik köken', 'pregnant': 'Gebelik',
    'height_cm': 'Boy', 'weight_kg': 'Kilo', 'waist_cm': 'Bel çevresi',
    'sbp_1_mmhg': 'Büyük tansiyon (1. ölçüm)', 'dbp_1_mmhg': 'Küçük tansiyon (1. ölçüm)',
    'sbp_2_mmhg': 'Büyük tansiyon (2. ölçüm)', 'dbp_2_mmhg': 'Küçük tansiyon (2. ölçüm)',
    'sbp_3_mmhg': 'Büyük tansiyon (3. ölçüm)', 'dbp_3_mmhg': 'Küçük tansiyon (3. ölçüm)',
    'smoking_status': 'Sigara kullanımı', 'alcohol_drinks_per_day': 'Günlük alkollü içki',
    'told_hypertension': 'Yüksek tansiyon tanısı', 'on_bp_medication': 'Tansiyon ilacı', 'told_diabetes': 'Diyabet tanısı',
    'on_insulin': 'İnsülin kullanımı', 'on_diabetes_pills': 'Şeker hapı kullanımı', 'hx_coronary_disease': 'Koroner kalp hastalığı',
    'hx_heart_failure': 'Kalp yetmezliği', 'hx_stroke': 'İnme öyküsü', 'family_hx_diabetes': 'Ailede diyabet',
    'gestational_diabetes_hx': 'Gebelik diyabeti öyküsü', 'recreational_activity': 'Düzenli egzersiz',
    'glucocorticoid_ge1month': 'Kortizon kullanımı', 'fracture_hip': 'Kalça kırığı', 'fracture_wrist': 'El bileği kırığı',
    'fracture_spine': 'Omurga kırığı', 'fracture_after_age20': '20 yaş sonrası kırık', 'parent_hip_fracture': 'Ebeveynde kalça kırığı',
    'menses_absent_12m': 'Adetin kesilmesi', 'hrt_ever': 'Hormon tedavisi', 'age_last_period_years': 'Son adet yaşı',
    'hba1c_pct': 'HbA1c', 'glucose_serum_mgdl': 'Kan şekeri', 'glucose_fasting_mgdl': 'Açlık kan şekeri',
    'total_chol_mgdl': 'Total kolesterol', 'hdl_mgdl': 'HDL kolesterol', 'tg_mgdl': 'Trigliserit', 'alt_ul': 'ALT', 'ast_ul': 'AST',
    'ggt_ul': 'GGT', 'alp_ul': 'ALP', 'albumin_gdl': 'Albümin', 'platelets_k_ul': 'Trombosit', 'uric_acid_mgdl': 'Ürik asit',
    'creatinine_mgdl': 'Kreatinin', 'urine_albumin_mgl': 'İdrarda albümin', 'urine_creatinine_mgdl': 'İdrarda kreatinin',
    'wbc_k_ul': 'Lökosit (WBC)', 'rbc_m_ul': 'Eritrosit (RBC)', 'mcv_fl': 'MCV', 'rdw_pct': 'RDW', 'hemoglobin_gdl': 'Hemoglobin',
    'rip3_pgml': 'RIP3', 'fev1_pre_ml': 'FEV1', 'fvc_pre_ml': 'FVC', 'cad_chest_pain_type': 'Göğüs ağrısı tipi',
    'cad_resting_ecg': 'Dinlenme EKG sonucu', 'cad_max_hr_bpm': 'Efor testinde en yüksek nabız',
    'cad_exercise_angina': 'Efor sırasında göğüs ağrısı', 'cad_st_depression_mm': 'Efor testinde ST çökmesi',
    'cad_st_slope': 'Efor testinde ST eğimi', 'told_weak_failing_kidneys': 'Böbrek hastalığı tanısı', 'on_dialysis': 'Diyaliz',
}
missing = [k for k in fui if k not in SHORT]
assert not missing, f'kısa adı olmayan alan: {missing}'
for k, s in SHORT.items():
    if k in fui:
        fui[k]['short'] = s
cfg['form']['field_ui_source'] += ' Phase L2: short = hata/uyarı mesajlarında kullanılan kısa ad (soru biçimli etiket yerine).'

# aralık ve geçersiz yanıt kuralları kısa adı kullanır
for r in ui['field_error_rules_tr']:
    r['text'] = r['text'].replace('{label}', '{short}')
for r in ui['reason_rules_tr']:
    if 'text' in r:
        r['text'] = r['text'].replace('({label})', '({short})')
for r in ui.get('unit_note_rules_tr', []):
    r['text'] = r['text'].replace('{label}', '{short}')

tx = ui['text_tr']
tx.update({
    # durum paneli
    'panel_sub': 'Girdikçe güncellenir. Analiz çalıştırılmaz; yalnız hangisinin sonuç verebileceği gösterilir.',
    'panel_not_started': 'Henüz bilgi girilmedi',
    'panel_progress': '{a}/{n} bilgi girildi',
    'panel_show_missing': 'Eksikleri göster',
    'panel_common': 'Birden fazla analiz için geçerli: {x}',
    'footer': 'HealthRisk AI Research V2 · Phase L2 arayüzü · yalnız localhost · klinik karar aracı değildir',
    'panel_ready_hint': 'Bilgiler bu analiz için yeterli.',
    # örnek profiller (formun altına, katlı)
    'profile_toggle': 'Örnek profillerle dene (sentetik)',
    # asistan: sohbet görünümü
    'asst_welcome': 'Merhaba. Uygulamadaki terimleri ve sonuç kartlarını kaynaklara dayanarak açıklarım. Tanı koymam; ilaç veya doz önermem.',
    'asst_typing': 'Asistan yazıyor',
    'asst_disclaimer_short': 'Araştırma prototipi: mevcut durumu sınıflar, tanı değildir; negatif sonuç hastalığı dışlamaz.',
    'asst_new_chat': 'Yeni sohbet',
})
ui['text_tr_l2_source'] = 'Phase L2: phase_l2/scripts/patch_app_config_l2.py'
P.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
print('ok kısa ad', len(SHORT))
