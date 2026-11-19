"""Phase XLIV — input_schema v2 (kullanıcı kararları, 2026-11-19). Kaynak v1: phase_xliii/registry/input_schema.json
(salt okunur, değiştirilmez). Çıktı: phase_xliv/registry/input_schema_v2.json (+ .sha256).
İlke (kullanıcı): şema metni ile eğitim kodu ayrışırsa EĞİTİM KODU kazanır. Her değişiklik changes_from_v1'de gerekçe ve
kanıtla listelenir. models.json (model, eşik, feature sırası) DEĞİŞMEZ; yalnız uygulama dönüşüm tanımları güncellenir.
Kullanım: python -B -I build_schema_v2.py"""
import copy
import hashlib
import json
from pathlib import Path

P44 = Path(__file__).resolve().parents[1]
V2 = P44.parent
SRC = V2 / 'phase_xliii/registry/input_schema.json'
OUT = P44 / 'registry/input_schema_v2.json'
BMI_R1 = ['dm_A', 'dm_B', 'copd_S4_DEVICE', 'htn_M1', 'fibrosis_final', 'osteo_final', 'ckd_A', 'ckd_B', 'hf_S2_BASIC_LAB']
BMI_R2 = ['anemia_LR16']


def main():
    v1 = json.loads(SRC.read_text(encoding='utf8'))
    s = copy.deepcopy(v1)
    s['schema_version'] = '2.0'
    s['phase'] = 'XLIV'
    s['created_utc'] = '2026-11-19'
    s['base_schema'] = dict(path='phase_xliii/registry/input_schema.json', sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),
                            version=v1['schema_version'])
    s['policy']['v2_principle'] = ('Şema metni ile eğitim kodu ayrışırsa eğitim kodu kazanır (kullanıcı kararı, Phase XLIV). '
                                   'Değişiklikler changes_from_v1 içinde; models.json değişmedi.')
    s['policy']['pregnancy'] = ('Gebelik sorusu kadında, yaşı gebelik dışlaması gerektiren en az bir modelin yaş aralığındaysa '
                                '(≥ 18) ZORUNLUDUR. Yanıt "unknown" (bilmiyorum) veya yanıtsız -> o modeller ABSTAIN; true -> '
                                'NOT_APPLICABLE (katı yorum, kullanıcı onayı). İlgili modeller: dm_A, dm_B, ckd_A, ckd_B, htn_M1, '
                                'fibrosis_final, anemia_LR16. Not: eğitimde yalnız anemi "gebe olmadığı doğrulanmış" '
                                '(RIDEXPRG=2) şartı koymuştu; diğerleri yalnız RIDEXPRG=1 dışlamıştı — katı yorum bilinçli '
                                'olarak daha muhafazakârdır.')
    s['policy']['diabetes_meds'] = ('on_insulin ve on_diabetes_pills HERKESE sorulur (v1: yalnız tanı varsa). Eğitim kodlarında '
                                    'bu sorular tanısız/sınırda kişilerde de yanıtlanmıştı (ckd: phase_xxxv t1_data; dm '
                                    'dışlaması: phase_xlii t1_data on_med = DIQ050==1 | hap==1).')
    f = s['fields']
    for k in ('on_insulin', 'on_diabetes_pills'):
        f[k].pop('ask_when', None)
        f[k]['note'] = 'v2: herkese sorulur (sınırda/tanısız kişiler dahil; eğitim kodlarıyla aynı).'
    f['told_diabetes']['note'] = 'Sınırda (borderline) = hayır (NHANES DIQ010=3). İlaç soruları buna bakılmaksızın sorulur (v2).'
    f['pregnant'] = dict(label_tr='Şu an gebe mi', type='boolean', input_source='kullanici', categories=[True, False, 'unknown'],
                         ask_when='sex = female', required_when='sex = female ve age_years ≥ 18',
                         note='"unknown" = bilmiyorum -> ilgili modeller ABSTAIN. Uygunluk sorusudur, model feature\'ı DEĞİL. '
                              'v2 ile eklendi (Phase XLIV uygulama uygunluk sorusundan resmileştirildi).')
    f['told_weak_failing_kidneys'] = dict(label_tr='Doktor "zayıf/başarısız böbrek" (böbrek hastalığı) dedi mi (NHANES KIQ022)',
                                          type='boolean', input_source='kullanici', categories=[True, False],
                                          note='ckd_A/ckd_B popülasyonu KIQ022 = Hayır. Yanıtsız -> ABSTAIN; true -> NOT_APPLICABLE. '
                                               'Uygunluk sorusu, feature değil (v2).')
    f['on_dialysis'] = dict(label_tr='Son 12 ayda diyaliz aldı mı (NHANES KIQ025)', type='boolean', input_source='kullanici',
                            categories=[True, False],
                            note='true -> ckd_A/ckd_B NOT_APPLICABLE. KIQ025 eğitimde KIQ022 = 1\'e koşulluydu '
                                 '(phase_xxxiv/02_ckd_readiness.md); yanıtsızlık tek başına ABSTAIN nedeni değildir (v2).')
    t = s['transforms']
    for old in ('bmi_kgm2', 'dm_insulin_rule', 'dm_pills_rule', 'egfr_ckdepi2021'):
        t[old] = t[old] + ' [v1; v2 model_usage\'da kullanılmaz — changes_from_v1]'
    t['bmi_kgm2_r1'] = ('yuvarla_yarım_yukarı(weight_kg / (height_cm/100)^2, 1 ondalık). NHANES BMXBMI (2011–12 ve sonrası '
                        'döngüler) ile aynı hassasiyet.')
    t['bmi_kgm2_r2'] = ('yuvarla_yarım_yukarı(weight_kg / (height_cm/100)^2, 2 ondalık). NHANES BMXBMI (2009–10 ve önceki '
                        'döngüler) ile aynı hassasiyet; yalnız tüm eğitim BMI\'si 2 ondalıklı olan model(ler)de.')
    t['dm_insulin_train'] = ('on_insulin yanıtlanmışsa bool01 (tanı durumundan bağımsız); yanıtsız ve told_diabetes=false -> 0.0; '
                             'yanıtsız ve told_diabetes=true -> eksik (ABSTAIN). phase_xxxv/scripts/t1_data.py: '
                             'ins = yn(DIQ050); ins[ins.isna() & dm_told==0] = 0.')
    t['dm_pills_train'] = ('on_diabetes_pills yanıtlanmışsa bool01 (tanı durumundan bağımsız); yanıtsız ve told_diabetes=false -> '
                           '0.0; yanıtsız ve told_diabetes=true -> eksik. phase_xxxv/scripts/t1_data.py: pills = yn(DID070|DIQ070); '
                           'pills[pills.isna() & dm_told==0] = 0.')
    t['egfr_ckdepi2021_cap80'] = ('CKD-EPI 2021 (ırksız), yaş = min(age_years, 80): phase_xxxvii/scripts/t1_data.py '
                                  'egfr_ckdepi2021(LBXSCR, age, female) çağrısında age = RIDAGEYR.clip(upper=80). Diğer '
                                  'katsayılar egfr_ckdepi2021 ile aynı. v1 metnindeki "ham yaş" ifadesi eğitim koduyla '
                                  'çelişiyordu (P/L 80\'de tepe kodlu olduğundan geliştirme verisinde sayısal fark 0).')
    changes = []

    def swap(mid, feat, new, reason, evidence):
        for u in s['model_usage'][mid]:
            if u['model_feature'] == feat:
                changes.append(dict(model=mid, feature=feat, old_transform=u['transform'], new_transform=new,
                                    reason=reason, evidence=evidence))
                u['transform'] = new
                return
        raise KeyError((mid, feat))

    ev_bmi = 'phase_xliv/03_tests.md (parity v1: BMI farkının tamamı BMXBMI kaynak yuvarlaması)'
    for m in BMI_R1:
        swap(m, 'bmi', 'bmi_kgm2_r1', 'Kullanıcı kararı 1: 0,1\'e yuvarla (NHANES BMXBMI). Eğitim BMI\'si BMXBMI idi.', ev_bmi)
    for m in BMI_R2:
        swap(m, 'bmi', 'bmi_kgm2_r2', 'Eğitim kodu kazanır: anemi eğitim verisi (NHANES D 2005–06 + A 1999–2000) BMXBMI\'si '
             'tümüyle 2 ondalıklıdır; 0,1 yuvarlaması eğitim tanımından |Δ| ≤ 0,05 uzaklaştırırdı. Kullanıcının "0,1" '
             'talimatından bu model için sapma — onay gerektirir.', ev_bmi + '; döngü hassasiyet analizi 03_tests.md')
    for m in ('ckd_A', 'ckd_B'):
        swap(m, 'dm_insulin', 'dm_insulin_train', 'Kullanıcı kararı 3: eğitim kodundaki tanım (yanıt varsa tanıdan bağımsız).',
             'parity v1: ckd geliştirme havuzunda 145/20.059 kişi tanısız/sınırda + hap/insülin=1')
        swap(m, 'dm_pills', 'dm_pills_train', 'Kullanıcı kararı 3: eğitim kodundaki tanım.', 'aynı')
    swap('htn_M1', 'egfr', 'egfr_ckdepi2021_cap80', 'Kullanıcı kararı 5: eğitim kodundaki yaş tanımı (80\'de kırpılmış).',
         'phase_xxxvii/scripts/t1_data.py build(): age = d.RIDAGEYR.clip(upper=80); egfr_ckdepi2021(d.LBXSCR, age, female)')
    s['changes_from_v1'] = changes
    for m in ('ckd_A', 'ckd_B'):
        s['model_missing_rule'][m]['rule'] += (' [v2: dm_insulin/dm_pills eğitim tanımıyla (dm_*_train): yanıt varsa '
                                               'kullanılır; yanıtsız ve tanı yoksa 0.]')
    s['model_missing_rule']['htn_M1']['rule'] += ' [v2: egfr yaşı 80\'de kırpılır (egfr_ckdepi2021_cap80).]'
    s['known_limitations_v2'] = [
        dict(model='osteo_final', feature='age', transform='age_cap80',
             note='Kullanıcı kararı 2: age_cap80 korunur. Eğitimde NHANES D (2005–06) yaşı 85\'te kodlu ve kırpılmamış '
                  '(geliştirme havuzunda 201/8.635 kişi 81–85), E/F/H 80\'de kodlu. 80 üstü kullanıcıda model 80 görür; '
                  'eğitimdeki D kişilerinden farklıdır. Hiçbir tek dönüşüm iki kodlamayı birden yeniden üretemez.'),
        dict(models=['dm_A', 'dm_B', 'ckd_A', 'ckd_B', 'osteo_final'], feature='bmi', transform='bmi_kgm2_r1',
             note='Eğitim BMI\'si döngüye göre karışık hassasiyetlidir (≤ 2009–10 döngüleri 2 ondalık, sonrası 1 ondalık). '
                  '0,1 yuvarlaması 1 ondalıklı döngülerle birebir, 2 ondalıklılarla |Δ| ≤ 0,05 uyumludur.')]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    (P44 / 'registry/input_schema_v2.sha256').write_text(h + '\n', encoding='utf8')
    print(h, len(changes), 'değişiklik', len(s['transforms']), 'dönüşüm', len(s['fields']), 'alan')


if __name__ == '__main__':
    main()
