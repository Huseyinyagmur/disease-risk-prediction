"""Phase XLVI — Görev 4: app/docs/experiment_tables.md (tüm hastalıklar, tek tablo). Elle değer yazılmaz.

Kaynaklar (salt okunur):
- registry'deki 13 model: phase_xlvi/results/card_metrics.json (kayıtlı sonuç dosyalarından çıkarılmış, registry ile
  çapraz kontrollü) + registry metinleri (research_target_note, app_mode).
- registry dışı 4 hastalık (kullanıcı kararı "ALMA"): phase_xxx/results/liver_test_results.csv,
  phase_xxx/results/gallstone_test_results.csv, phase_xxix_b/results/summary.csv (CV — ADAY) ve registry
  `candidates_not_registered` gerekçeleri.
Kullanım: python -X utf8 -B -I phase_xlvi/scripts/build_experiment_tables.py
"""
import json
import re
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REG = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
CFG = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
MET = json.loads((V2 / 'phase_xlvi/results/card_metrics.json').read_text(encoding='utf8'))
TIER = {'internal_test': 'iç test', 'temporal': 'zamansal', 'external': 'dış', 'technical_replication': 'teknik tekrar*'}
ORDER = ['af_S4_DEVICE', 'fibrosis_final', 'osteo_final', 'cad_DEVICE', 'dm_A', 'dm_B', 'anemia_LR16', 'copd_S4_DEVICE',
         'htn_M1', 'ckd_A', 'ckd_B', 'mi_model', 'hf_S2_BASIC_LAB']


def f3(x):
    return '—' if x is None or (isinstance(x, float) and pd.isna(x)) else f'{x:.3f}'.replace('.', ',')


def ci(t):
    return '—' if t is None else f'{f3(t[0])} [{f3(t[1])}–{f3(t[2])}]'


def status(mid):
    m = REG['models'][mid]
    if not m['app_visible']:
        return 'uygulamada değil (registry_only)'
    lab = CFG['module_labels'].get(mid, CFG['module_labels']['_default'])
    return {'ana modül': 'ana', 'araştırma modülü': 'araştırma', 'deneysel': 'deneysel'}[lab]


def data_of(row):
    s = row['label']
    return s.split('— ', 1)[1] if '— ' in s else s


def registered_rows():
    out = []
    for mid in ORDER:
        m = REG['models'][mid]
        for r in MET[mid]:
            if r['tier'] not in TIER:
                continue
            tier = TIER[r['tier']]
            if mid == 'anemia_LR16' and r['tier'] == 'external':
                tier = 'farklı döngüler (aynı program)'
            prec = r.get('precision_reportable', True)
            d = r.get('delta', [])
            dd = '; '.join(f"{x['label']}: {ci(x['dAUC'])}" for x in d[:2]) if d else 'BULUNAMADI'
            tri = ('değerlendirilemez' if not prec else
                   ('evet' if r['precision'][0] >= .70 and r['recall'][0] >= .75 and r['fpr'][0] <= .15 else 'hayır'))
            out.append(dict(key=m['disease_key'], hastalik=m['disease'], model=f'`{mid}`', veri=data_of(r), test=tier, n=f"{r['n']} ({r['n_pos']})",
                            P=ci(r['precision']) if prec else 'raporlanmaz', R=ci(r['recall']), FPR=ci(r['fpr']), AUC=ci(r['auc']),
                            dAUC=dd, hedef=tri, durum=status(mid)))
    return out


def unregistered_rows():
    out = []
    cand = REG['candidates_not_registered']
    lv = pd.read_csv(V2 / 'phase_xxx/results/liver_test_results.csv')
    p = lv[lv.analiz.str.startswith('BİRİNCİL')].iloc[0]
    b = lv[lv.analiz.str.startswith('Baseline FLI')].iloc[0]
    out.append(dict(key='fatty_liver', hastalik=cand['fatty_liver']['disease'], model='liver_final (XGBoost)', veri='NHANES L (CONTAMINATED test etiketi)',
                    test='iç test (CONTAMINATED)', n=f'{int(p.n)} ({int(p.pos)})', P=ci([p.P, p.P_lo, p.P_hi]), R=ci([p.R, p.R_lo, p.R_hi]),
                    FPR=ci([p.FPR, p.FPR_lo, p.FPR_hi]), AUC=ci([p.ROC_AUC, p.ROC_AUC_lo, p.ROC_AUC_hi]) if 'ROC_AUC' in lv else _auc(lv, p),
                    dAUC=f'model − FLI: {ci([b.dAUC, b.dAUC_lo, b.dAUC_hi])}', hedef='hayır', durum='uygulamada değil (ALMA)'))
    gs = pd.read_csv(V2 / 'phase_xxx/results/gallstone_test_results.csv')
    p = gs[gs.analiz.str.startswith('BİRİNCİL')].iloc[0]
    b = gs[gs.analiz.str.startswith('Baseline')].iloc[0]
    out.append(dict(key='gallstone', hastalik=cand['gallstone']['disease'], model='gallstone_final (CatBoost)', veri='NHANES III Faz 2',
                    test='zamansal', n=f'{int(p.n)} ({int(p.pos)})', P=ci([p.P, p.P_lo, p.P_hi]), R=ci([p.R, p.R_lo, p.R_hi]),
                    FPR=ci([p.FPR, p.FPR_lo, p.FPR_hi]), AUC=_auc(gs, p),
                    dAUC=f'model − LR(yaş, cinsiyet, BMI): {ci([b.dAUC, b.dAUC_lo, b.dAUC_hi])}', hedef='hayır',
                    durum='uygulamada değil (ALMA)'))
    sm = pd.read_csv(V2 / 'phase_xxix_b/results/summary.csv')
    for key, name in (('lipid', 'Lipid bozukluğu'), ('asthma', 'Astım')):
        r = sm[sm['Hastalık'] == name].iloc[0]
        prf = re.findall(r'[\d.]+', str(r['En iyi AUC / P-R-FPR']))
        n, prev = re.findall(r'[\d.]+', str(r['n (prev)']))
        out.append(dict(key=key, hastalik=cand[key]['disease'], model=str(r['En iyi aday (PR-AUC)']), veri='Phase XXIX-B geliştirme',
                        test='**CV — ADAY** (test yok)', n=f'{n} (prevalans {prev.replace(".", ",")})',
                        P=prf[1].replace('.', ','), R=prf[2].replace('.', ','), FPR=prf[3].replace('.', ','), AUC=prf[0].replace('.', ','),
                        dAUC=f"{r['Birincil baseline AUC']} → {r['ΔAUC vs baseline (GA)']} (CV)".replace('.', ','), hedef='hayır',
                        durum='uygulamada değil (ALMA)'))
    return out


def _auc(df, p):
    for a in ('AUC', 'ROC_AUC'):
        if a in df.columns and not pd.isna(p.get(a)):
            return ci([p[a], p[a + '_lo'], p[a + '_hi']])
    return 'BULUNAMADI'


def main():
    rows = registered_rows() + unregistered_rows()
    cols = [('hastalik', 'hastalık'), ('model', 'model'), ('veri', 'veri'), ('test', 'test türü'), ('n', 'n (pozitif)'),
            ('P', 'Precision'), ('R', 'Recall'), ('FPR', 'FPR'), ('AUC', 'AUC'), ('dAUC', 'baseline ΔAUC [%95 GA]'),
            ('hedef', 'üç hedef'), ('durum', 'uygulamada')]
    tbl = ['| ' + ' | '.join(c for _, c in cols) + ' |', '|' + '---|' * len(cols)]
    tbl += ['| ' + ' | '.join(str(r[k]).replace('|', '/') for k, _ in cols) + ' |' for r in rows]
    diseases = list(dict.fromkeys(r['key'] for r in rows))
    why = []
    for mid in ORDER:
        m = REG['models'][mid]
        why.append(f"- **{m['disease']} (`{mid}`; {status(mid)})** — {m['evidence']['research_target_note']}"
                   + (f" Uygulama: {m['app_feasibility']}" if not m['app_visible'] else ''))
    for k, c in REG['candidates_not_registered'].items():
        why.append(f"- **{c['disease']} (uygulamada değil; karar: {c.get('user_decision', c['recommendation'])})** — {c['rationale']}")
    md = f"""# Deney tabloları — tüm hastalıklar

Üretim: `phase_xlvi/scripts/build_experiment_tables.py` (Phase XLVI). **Elle değer yazılmadı.** Registry'deki modeller için
değerler kayıtlı test sonuç dosyalarından (`phase_xlvi/results/card_metrics.json`; registry ile 3 ondalıkta çapraz kontrol:
236 kontrol, 0 uyuşmazlık, 2 yuvarlama farkı); registry dışı adaylar için ilgili faz sonuç dosyalarından okundu.

Tabloda **{len(diseases)} hastalık** vardır: registry'de 11 hastalık (13 model) ve registry'ye alınmayan 4 aday
(karaciğer yağlanması, lipid, astım, safra taşı). Görev tanımında "14 hastalık" yazıyordu; proje kayıtlarında 15 hastalık
bulunduğu için tümü gösterildi.

**Okuma kuralları**
- İç test, zamansal doğrulama, dış doğrulama ve teknik tekrar ayrı satırlardır; aynı model birden çok satırda görünebilir.
- CV sonuçları yalnız test edilmemiş adaylarda ve "CV — ADAY" etiketiyle yer alır.
- Oranlar Wilson %95 GA, AUC bootstrap %95 GA. AF dış doğrulamasında Precision prevalansa bağlı olduğu için raporlanmaz.
- "Üç hedef": P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 aynı eşikte (nokta tahmini). Araştırma hedefidir, klinik onay kriteri değildir.
- \\* Teknik tekrar (CAD Hungarian/VA): düzeltilmiş yeniden skorlama, seçilmiş eksiksiz vaka; bağımsız dış doğrulama değildir.
- Uygulamadaki durum: ana / araştırma / deneysel modül (`app_config.json > module_labels`) veya uygulamada değil.

{chr(10).join(tbl)}

## Başarısız veya sınırlı modeller — kısa gerekçe

Metinler registry'den (`research_target_note`, `app_feasibility`, `candidates_not_registered.rationale`) aynen alınmıştır.

{chr(10).join(why)}

Model başına ayrıntı: [model kartları](model_cards/README.md).
"""
    out = V2 / 'app/docs/experiment_tables.md'
    out.write_text(md, encoding='utf8')
    print('satır', len(rows), 'hastalık', len(diseases))


if __name__ == '__main__':
    main()
