"""Phase XLIII — 01_model_selection.md'yi registry/models.json'dan üretir (sayılar kayıttan; gerekçe metni burada elle).
Çalıştırma: python -B -I phase_xliii/scripts/make_selection_doc.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import registry_lib as L  # noqa: E402
import registry_spec as S  # noqa: E402

reg = json.load(open(L.PHASE / 'registry' / 'models.json', encoding='utf8'))
M = reg['models']


def fv(x, d=3):
    if x is None:
        return '—'
    if isinstance(x, dict):
        return f"{x['value']:.{d}f} ({x['ci95'][0]:.{d}f}–{x['ci95'][1]:.{d}f})".replace('.', ',')
    return f'{x:.{d}f}'.replace('.', ',')


def headline(e):
    ev = M[e]['evidence']
    for tier, label in (('external', 'dış doğrulama'), ('temporal', 'zamansal'), ('internal_test', 'iç test')):
        t = ev.get(tier)
        if t and 'n' in t:
            return label, t
    return None, None


RATIONALE = {
    'af_S4_DEVICE': 'AF için tek kilitli model; kilitli AF-ECGDELI-OCTAVE-v1 pipeline ile bağımsız 4 kaynakta (Challenge 2021) test edilen tek model. İç testte üç hedef GA ile sağlandı; RR_iqr/RR_mean kuralına göre çok değişkenli katkı kanıtlı (ΔAUC: iç +0,021; dış havuz A2 +0,021, B +0,035).',
    'mi_model': 'EKG\'de MI için kilitli tek ML modeli (diğer kayıt B1 yaş+cinsiyet baseline\'ıdır). Yaş+cinsiyete göre ΔAUC +0,155. YALNIZ iç test; kural baseline\'ı geçersiz; feature üretim pipeline\'ı yok → uygulamaya alınamaz.',
    'cad_DEVICE': 'V2 kök CAD paneli. Düzeltilmiş (phase_xli) teknik tekrarı olan tek CAD paneli; BASIC/LAB panellerinin dış sonuçları geçersiz ve yeniden skorlanmadı (phase_xlii/ERRATA_CAD_V2.md). Efor testi girdisi ister; kanıt iç test (n=61) + seçilmiş teknik tekrar.',
    'dm_A': 'Laboratuvarsız tarama modeli; kilitli tek sefer testte ADA/Bang 2009 skoruna göre ΔAUC +0,042 (+0,028…+0,055). Eski CCN3 S3 (insülin tabanlı) dış doğrulamada AUC 0,965→0,81 ve donmuş eşikte FPR 0,45 verdiği için bu hedef için phase_xlii modeli tercih edilir (phase_xl).',
    'dm_B': 'Rutin laboratuvar varsa ikincil: B−A ΔAUC +0,025 (+0,014…+0,036), FPR 0,236 (A: 0,292). HbA1c/glukoz girdi olamaz (hedefi tanımlar).',
    'anemia_LR16': 'Phase XL\'de dört NHANES döngüsünde (11.171 kişi) dış değerlendirilen kilitli model (AUC 0,991). UYARI: Hct_proxy kuralına göre ΔAUC +0,004; model Hb\'yi hemogramdan yeniden hesaplıyor — ML katkısı pratikte yok.',
    'copd_S4_DEVICE': 'KOAH için zamansal tekrarı (F, E) olan tek kilitli model. Pre-BD FEV1/FVC<0,70 kuralına eşdeğer (ΔAUC +0,009); hedef popülasyon dar (pre-BD obstrüksiyonlu, BD testine alınmış 40–79 yaş).',
    'hf_S2_BASIC_LAB': 'Kalp yetmezliği için kilitli tek model (Phase21; XXVII\'de teyit). n=37 test, dış doğrulama YAPILAMADI (uyumlu RIP3 verisi BULUNAMADI); RIP3 tek başına modele eşdeğer. Araştırma amaçlı.',
    'htn_M1': 'Kirlenmemiş (hiçbir hedefte önceden kullanılmamış) kişilerde zamansal testi olan HTN modeli (C 2003–04; XXXII\'nin L testi CONTAMINATED). M2 (diyet Na/K) katkı vermedi. Yaş+cinsiyet+BMI\'ye katkı yalnız +0,012; beş laboratuvar girdisi ister.',
    'fibrosis_final': 'Fibrozis için kilitli tek model. FIB-4\'e göre ΔAUC +0,197, NFS\'ye göre +0,096. Test PREVIOUSLY_EXPOSED; CV→test düşüşü (0,835→0,794); Recall 0,768 (hedef 0,85 altında).',
    'osteo_final': 'Osteoporoz için kilitli model; zamansal test (J 2017–18) ve OST\'ye göre ΔAUC +0,025 (+0,012…+0,038). Laboratuvarsız. Erkeklerde Recall 0,48; P 0,21.',
    'ckd_A': 'Laboratuvarsız böbrek taraması; modifiye SCORED\'a göre ΔAUC +0,032 (+0,020…+0,043); Recall 0,767, NPV 0,943. P 0,29, FPR 0,32 (hedefler yok).',
    'ckd_B': 'Rutin laboratuvar varsa ikincil: B−A ΔAUC +0,015 (+0,009…+0,021); FPR 0,290 (A: 0,323).',
}
FEAS = {mid: m['app_feasibility'] for mid, m in M.items()}
SHORT_FEAS = {'af_S4_DEVICE': 'EKG + Octave pipeline', 'mi_model': 'ALINAMAZ (pipeline yok)', 'cad_DEVICE': 'Efor testi + EKG', 'dm_A': 'Form', 'dm_B': 'Form + lab', 'anemia_LR16': 'Lab (CBC + biyokimya)',
              'copd_S4_DEVICE': 'Spirometri (dar popülasyon)', 'hf_S2_BASIC_LAB': 'ALINAMAZ (RIP3 özel assay)', 'htn_M1': 'Lab (5 test)', 'fibrosis_final': 'Lab', 'osteo_final': 'Form', 'ckd_A': 'Form', 'ckd_B': 'Form + lab'}

lines = ['# Phase XLIII — 01: Hastalık başına son model seçimi', '',
         'Kaynak: önceki faz raporları ve kilit dosyaları (yalnız okuma). Sayılar `registry/models.json`\'dan otomatik üretilmiştir (`scripts/make_selection_doc.py`). '
         'Tüm modellerde `clinical_probability_eligibility=false`: skorlar araştırma skorudur, klinik olasılık değildir. '
         'Kanıt satırı, **o modelin en yüksek kanıt düzeyindeki** sonucudur (dış > zamansal > iç); "en iyi görünen" sonuç seçilmemiştir. Diğer düzeyler `models.json > evidence` içindedir.', '',
         '## 1. Seçim tablosu', '',
         '| Hastalık | Seçilen model (rol) | Gerekçe | En yüksek kanıt düzeyi — P / R / FPR / AUC | Uygulama girdisi |', '|---|---|---|---|---|']
for mid, m in M.items():
    label, t = headline(mid)
    p = fv(t.get('precision')) if t.get('precision') else ('prevalansa bağlı (raporlanmaz)' if mid == 'af_S4_DEVICE' else '—')
    ev = f"**{label}** (n={t['n']:,}".replace(',', '.') + (f"; poz={t['n_pos']:,}".replace(',', '.') if t.get('n_pos') else '') + f") — P {p} / R {fv(t.get('recall'))} / FPR {fv(t.get('fpr'))} / AUC {fv(t.get('auc'))}"
    lines.append(f"| {m['disease']} | `{mid}` ({m['role']}) — `{m['model_file']['path']}` | {RATIONALE[mid]} | {ev} | {SHORT_FEAS[mid]}; **app: {'görünür' if m['app_visible'] else 'GİZLİ (app_visible=false)'}, mod={m['app_mode']}** |")
lines += ['', '## 2. Kanıt düzeyi ayrımı (iç test / zamansal / dış doğrulama)', '',
          '| Model | İç test | Zamansal | Dış doğrulama | Üç hedef (P≥0,70, R≥0,75, FPR≤0,15) |', '|---|---|---|---|---|']
for mid, m in M.items():
    ev = m['evidence']

    def cell(t):
        if not t:
            return 'YOK'
        if 'n' not in t:
            parts = [f"{k}: n={v['n']}; P {fv(v.get('precision'))} / R {fv(v.get('recall'))} / FPR {fv(v.get('fpr'))}" for k, v in t.items() if isinstance(v, dict) and 'n' in v]
            return '; '.join(parts) + ' (teknik tekrar; seçilmiş eksiksiz-vaka, bağımsız DEĞİL)'
        return f"n={t['n']}; P {fv(t.get('precision')) if t.get('precision') else '—'} / R {fv(t.get('recall'))} / FPR {fv(t.get('fpr'))}"
    lines.append(f"| `{mid}` | {cell(ev.get('internal_test'))} | {cell(ev.get('temporal'))} | {cell(ev.get('external'))} | {ev['research_target_note']} |")
lines += ['', 'Notlar: dış doğrulama hücreleri yalnız bağımsız veya "önceden görülmüş ama farklı kaynak/döngü" testleri içerir; her satırın etiketi (PREVIOUSLY_EXPOSED, aynı anket programı vb.) `models.json > evidence > *.source` alanındadır. '
          'CV sonuçları bu tabloda YOKTUR (CV = aday; model seçiminin kanıtı değil).', '',
          '## 3. Ön seçimle ilgili bulgular (karar kullanıcıya aittir)', '',
          'Ön seçimlerin hiçbiri önceki faz raporlarıyla çelişmedi; her model dosyası bulundu ve SHA256\'sı kilit/manifest ile birebir eşleşti (`registry_check` C1). Model dosyası veya kilit açısından BULUNAMADI durumu yoktur; yalnız bazı alt bilgiler BULUNAMADI olarak kayıtlıdır (bazı modellerde fit venv kaydı ve eşik kural metni). Aşağıdakiler uygulamaya taşırken önemli kısıtlardır:', '',
          '1. **MI (`mi_model`) uygulamaya alınamaz**: 168 lead bazlı ECGDeli feature\'ını üretecek kilitli pipeline yok (AF-ECGDELI-OCTAVE-v1 yalnız 10 global aralık üretir). Yalnız iç test; kural baseline\'ı geçersiz. Kayıtta tutuldu, `app_feasibility` alanında işaretli.',
          '2. **Kalp yetmezliği (`hf_S2_BASIC_LAB`) uygulamaya alınamaz**: RIP3 özel ELISA değeri gerekir; test n=37; sağlıklı-kontrol vaka-kontrol tasarımı; dış doğrulama yok.',
          '3. **AF** yalnız EKG sinyali + Octave pipeline ile çalışır (≈3,6 s/kayıt); form girdisiyle üretilemez. **CAD** efor testi/EKG ister; **KOAH** kaliteli pre-BD spirometri ve dar hedef popülasyon (pre-BD obstrüksiyonlu 40–79 yaş) ister.',
          '4. **Hipertansiyon M1** beş laboratuvar girdisi ister (HbA1c, TC, HDL, kreatinin→eGFR, idrar albümin/kreatinin→UACR); laboratuvarsız HTN modeli seçilmedi. ML katkısı +0,012 AUC.',
          '5. **Anemi LR16**: ML katkısı Hct kuralına eşdeğer (ΔAUC +0,004); Hb ölçülmüşse doğrudan Hb eşiği kullanılmalı.',
          '6. **Formla doldurulabilen** modeller yalnız: `dm_A`, `ckd_A`, `osteo_final` (ve laboratuvar girilirse `dm_B`, `ckd_B`, `fibrosis_final`, `htn_M1`, `anemia_LR16`).',
          '7. **Eksik veri politikası**: Phase26 manifesti Phase21/25 modelleri için "kısmi eksik satırda dondurulmuş imputer kullanılabilir" diyordu; bu kayıtta CLAUDE.md\'ye uygun daha katı kural uygulandı: zorunlu alan eksikse model tahmin üretmez (yapısal atlama kuralları hariç). Bu bir tasarım kararıdır; gevşetilecekse kullanıcı onayı gerekir.',
          '8. **Sürüm bağımlılığı** (kayıtlı venv, `registry_check` ile doğrulandı): `Focused_Current_Disease_Improvement_2026/.venv` → AF, MI, KOAH, HTN, KY, fibrozis; kök `.venv` → CAD, DM A/B, anemi, osteo, KBH A/B. Kök `.venv` içinde catboost/xgboost yok (fibrozis ve KY yalnız Focused içinde yüklenir). Kayıtlı fit ortamı: AF lightgbm 4.7.0 (Phase21 environment.json), KBH lightgbm 4.6.0 (kök .venv); diğerleri için BULUNAMADI veya yalnız-LR (`models.json > runtime.fit_environment_evidence`).',
          '', '## 4. Uygulamaya alınıp alınmayacağı: ÖNERİ → KARAR: dördü de ALMA (kullanıcı onayladı)', '',
          '| Hastalık | Öneri | Aday | Gerekçe | Kanıt özeti |', '|---|---|---|---|---|']
for k, c in S.CANDIDATES.items():
    lines.append(f"| {c['disease']} | **{c['recommendation']}** | {c['candidate']} | " + ' '.join(f'({i + 1}) {r}' for i, r in enumerate(c['rationale'])) + f" | {c['evidence_summary']} |")
lines += ['', 'Bu dört hastalık için `models.json`\'da model kaydı AÇILMAMIŞTIR (`candidates_not_registered` altında yalnız öneri vardır). Kullanıcı "al" derse ayrı bir faz/kayıt genişletmesi gerekir; model dosyası/eşik değiştirilmeden kayıt eklenir.', '',
          '## 5. Eşikler ve kalibrasyon (özet)', '', '| Model | Birincil eşik | Kural | Ek eşikler | Kalibrasyon |', '|---|---|---|---|---|']
for mid, m in M.items():
    th = m['thresholds']
    sec = '; '.join(f'{k}={v:.4f}' for k, v in th['secondary'].items()) or '—'
    lines.append(f"| `{mid}` | {th['primary']['value']:.6f} | {th['primary']['rule']} | {sec} | {m['calibration']['status']} |")
(L.PHASE / '01_model_selection.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('01_model_selection.md yazıldı', len(lines), 'satır')
