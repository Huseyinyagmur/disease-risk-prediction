"""Phase XLIX — final rapor girdileri derlemesi.

Üretir: phase_xlix/model_results.csv, phase_xlix/final_report_inputs.md, results/references_found.csv.
Sayılar YALNIZ önceki fazların kayıtlı dosyalarından okunur (yeni tahmin, yeni test açılışı yok). Her tablonun
altında kaynak dosya ve seçici (satır/anahtar) yazılıdır. Bulunamayan değer: BULUNAMADI.
Ön koşul: af_overlap_check.py ve uci_cad_availability.py çalıştırılmış olmalı (results/*.json).
Kullanım: .venv/Scripts/python.exe -B phase_xlix/scripts/build_inputs.py
"""
import csv
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
P49 = V2 / 'phase_xlix'
sys.path.insert(0, str(V2 / 'phase_xlvi/scripts'))
import card_spec  # noqa: E402  (salt okunur; Phase XLVI metin spesifikasyonu)

REG_P = V2 / 'phase_xliii/registry/models.json'
CM_P = V2 / 'phase_xlvi/results/card_metrics.json'
CFG_P = V2 / 'app/backend/config/app_config.json'
REG = json.loads(REG_P.read_text(encoding='utf8'))['models']
CM = json.loads(CM_P.read_text(encoding='utf8'))
CFG = json.loads(CFG_P.read_text(encoding='utf8'))
X33 = V2 / 'phase_xxxiii/results'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def f3(x, d=3):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 'BULUNAMADI'
    return f'{x:.{d}f}'.replace('.', ',')


def ci(t, d=3):
    if not t or t[0] is None:
        return 'BULUNAMADI'
    return f'{f3(t[0], d)} [{f3(t[1], d)}–{f3(t[2], d)}]'


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float('nan'),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def module_label(mid):
    if not REG[mid]['app_visible']:
        return 'registry_only (uygulamada yok)'
    lab = CFG['module_labels'].get(mid, CFG['module_labels']['_default'])
    if REG[mid]['app_mode'] == 'clinical_mode':
        lab += ' + klinik mod'
    return lab


TIER_TR = {'internal_test': 'iç test', 'internal_test_subset': 'iç test (temiz alt küme)',
           'external': 'dış', 'external_source': 'dış (kaynak başına)',
           'external_secondary': 'dış — ikincil (AF vs SR + diğer ritimler)',
           'technical_replication': 'teknik tekrar (PREVIOUSLY_EXPOSED; bağımsız dış DEĞİL)',
           'temporal': 'zamansal', 'temporal_secondary': 'zamansal (ikincil döngü)',
           'temporal_subgroup': 'zamansal (alt grup)'}


def test_kind(mid, tier):
    if mid == 'anemia_LR16' and tier.startswith('external'):
        return 'farklı NHANES döngüleri (aynı program; bağımsız kurum DEĞİL)'
    return TIER_TR.get(tier, tier)


# ---------------------------------------------------------------- 1a model_results.csv
def build_model_results():
    rows = []
    for mid, tiers in CM.items():
        m, sp = REG[mid], card_spec.SPEC[mid]
        data_txt = ' || '.join(f'{a}: {b} ({c})' for a, b, c in sp['data'])
        for r in tiers:
            prev = r['n_pos'] / r['n'] if r.get('n_pos') else None
            g = lambda k, i: (r.get(k) or [None] * 3)[i]
            rows.append(dict(
                model_id=mid, hastalik=m['disease'], rol=m['role'], modul_etiketi=module_label(mid),
                app_mode=m['app_mode'], app_visible=m['app_visible'], kume=r['label'],
                test_turu=test_kind(mid, r['tier']), kanit_tier=r['tier'], veri_seti_kume=r.get('dataset', ''),
                veri_kaynaklari=data_txt, hedef=m['target_definition'], populasyon=m['population'],
                n_oznitelik=len(m['features']), oznitelikler=';'.join(f['name'] for f in m['features']),
                bolme=sp['split'], esik=m['thresholds']['primary']['value'], esik_kurali_registry=m['thresholds']['primary']['rule'],
                esik_kurali_kaynak=sp['threshold'], n=r['n'], n_pos=r['n_pos'], prevalans=prev,
                TP=r.get('TP'), FP=r.get('FP'), TN=r.get('TN'), FN=r.get('FN'),
                P=g('precision', 0), P_lo=g('precision', 1), P_hi=g('precision', 2),
                P_raporlanabilir=r.get('precision_reportable', True),
                R=g('recall', 0), R_lo=g('recall', 1), R_hi=g('recall', 2),
                FPR=g('fpr', 0), FPR_lo=g('fpr', 1), FPR_hi=g('fpr', 2),
                NPV=g('npv', 0), NPV_lo=g('npv', 1), NPV_hi=g('npv', 2), NPV_kaynak=r.get('npv_source', ''),
                AUC=g('auc', 0), AUC_lo=g('auc', 1), AUC_hi=g('auc', 2),
                kanit_notu_registry=m['evidence']['highest_tier'], not_=r.get('note', ''),
                kaynak_dosya=r['source'], kaynak_secici=r.get('selector', ''), kaynak_sha256=r.get('source_sha256', ''),
                derleme_kaynagi='phase_xlvi/results/card_metrics.json (extract_metrics.py; registry çapraz kontrol 236/0)'))
    df = pd.DataFrame(rows)
    df.to_csv(P49 / 'model_results.csv', index=False, encoding='utf-8')
    return df


# ---------------------------------------------------------------- yardımcı tablolar
def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def sec_1a(df):
    L = ['## 1a. Modeller (registry: `phase_xliii/registry/models.json`)', '',
         'Tam satırlar (her kanıt düzeyi ayrı satır, kaynak dosya + seçici + SHA256): **`phase_xlix/model_results.csv`**. '
         'Hedef, popülasyon, öznitelik listesi ve eşik değeri registry `models.<id>`; veri seti, bölme ve eşik kuralı metni '
         '`phase_xlvi/scripts/card_spec.py > SPEC.<id>`; modül etiketi `app/backend/config/app_config.json > module_labels` '
         '(+ `app_mode = clinical_mode` → "klinik mod"; `app_visible = false` → registry_only).', '']
    meta = []
    for mid in CM:
        m, sp = REG[mid], card_spec.SPEC[mid]
        meta.append([f'`{mid}`', m['disease'], module_label(mid), '; '.join(a + ': ' + b.replace(card_spec.NHANES, 'NHANES').split('; Wagner')[0] for a, b, _ in sp['data']),
                     len(m['features']), sp['split'].split('. ')[0], f"{m['thresholds']['primary']['value']:.6g}"])
    L.append(md_table(['model', 'hastalık', 'modül', 'veri seti (rol: kaynak)', 'öznitelik', 'bölme (özet)', 'eşik'], meta))
    L += ['', 'Eşik seçim kuralının tam metni ve hedef tanımı CSV\'de (`esik_kurali_kaynak`, `hedef`). Registry\'de 5 modelde '
          '"kural BULUNAMADI" yazar; kuralları Phase XLVI kaynağında bulundu (AF/KOAH/KY: Phase21 BALANCED; anemi: Phase25; '
          'CAD: `src/evaluation/metrics.py :: choose_threshold`) — `phase_xlvi/PHASE_XLVI_REPORT.md` Görev 1.', '',
          '### Performans (donmuş model + donmuş eşik; oranlar Wilson %95 GA, AUC bootstrap %95 GA)', '']
    rows = []
    for _, r in df.iterrows():
        p = ci([r.P, r.P_lo, r.P_hi]) if r.P_raporlanabilir is not False else 'raporlanmaz (örneklem prevalansı)'
        rows.append([f'`{r.model_id}`', r.kume, r.test_turu, f'{r.n} ({r.n_pos})', f3(r.prevalans),
                     f'{r.TP}/{r.FP}/{r.TN}/{r.FN}', p, ci([r.R, r.R_lo, r.R_hi]), ci([r.FPR, r.FPR_lo, r.FPR_hi]),
                     ci([r.NPV, r.NPV_lo, r.NPV_hi]), ci([r.AUC, r.AUC_lo, r.AUC_hi]), f'`{r.kaynak_dosya}`'])
    L.append(md_table(['model', 'küme', 'test türü', 'n (poz.)', 'prevalans', 'TP/FP/TN/FN', 'Precision', 'Recall', 'FPR',
                       'NPV', 'AUC', 'kaynak'], rows))
    L += ['', 'NPV kaynakta yoksa Phase XLVI kayıtlı TN/FN\'den hesapladı (`npv_source`). AF dış satırlarında ve prevalansı '
          'örneklemle belirlenen kümelerde Precision hedef karşılaştırmasında kullanılmaz (registry `precision_note`). '
          'CV sonuçları bu tabloda yoktur ("aday" sonuçlar kanıt sayılmaz).', '']
    return L


def sec_1b():
    L = ['## 1b. Referans / klinik baseline karşılaştırmaları (aynı test kişileri)', '',
         'ΔAUC = AUC(model) − AUC(referans), aynı kişilerde paired bootstrap (kaynak fazın tohumu). Kaynak: '
         '`phase_xlvi/results/card_metrics.json > <model>[].delta` (her satırda özgün dosya).', '']
    rows = []
    for mid, tiers in CM.items():
        for r in tiers:
            for d in r.get('delta', []):
                rows.append([f'`{mid}`', r['label'], d['label'], f3(d.get('baseline_auc')), ci(d['dAUC']),
                             d.get('note') or '', f"`{d['source']}` ({d.get('selector', '')})"])
    L.append(md_table(['model', 'küme', 'karşılaştırma', 'referans AUC', 'ΔAUC [%95 GA]', 'not', 'kaynak'], rows))
    ref = pd.read_csv(V2 / 'phase_xlvi/results/reference_score_analysis.csv')
    es = ref[ref.karsilastirma.str.startswith('eşit duyarlılık')]
    L += ['', '### Aynı duyarlılıkta FPR / yönlendirme (fibrozis, osteoporoz) — POST-HOC TANIMLAYICI', '',
          'Kaynak: `phase_xlvi/results/reference_score_analysis.csv` (karsilastirma = "eşit duyarlılık …"); ayrıntı ve '
          'eşit-yönlendirme şemaları `phase_xlvi/01_reference_score_analysis.md` §3–4. McNemar kesin binom (negatiflerde).', '']
    rows = []
    es = es.reset_index(drop=True)
    for i in range(0, len(es), 3):  # üçlüler: model, referans, fark (model − referans)
        mrow, rr, dd = es.iloc[i], es.iloc[i + 1], es.iloc[i + 2]
        assert (mrow.taraf, rr.taraf) == ('model', 'referans') and dd.taraf.startswith('fark'), (i, mrow.taraf)
        rows.append([mrow.hastalik, mrow.grup, rr.kural, f3(mrow.R), f"{f3(mrow.FPR)} / {f3(rr.FPR)}",
                     f"{int(mrow.yonlendirilen)} / {int(rr.yonlendirilen)}",
                     f"{int(dd.mcnemar_negatif_model_yalniz)} / {int(dd.mcnemar_negatif_ref_yalniz)}",
                     '< 0,001' if dd.mcnemar_negatif_p < 0.001 else f3(dd.mcnemar_negatif_p)])
    L.append(md_table(['hastalık', 'grup', 'referans kuralı (testte eşlenmiş)', 'Recall (ortak)', 'FPR model / ref',
                       'yönlendirilen model / ref', 'negatifte yalnız model / yalnız ref', 'McNemar p'], rows))
    liver = pd.read_csv(V2 / 'phase_xxx/results/liver_test_results.csv')
    lb = liver[liver.analiz.str.startswith('Baseline')]
    L += ['', '### Uygulamada olmayan modellerde referans karşılaştırmaları', '']
    rows = [['Karaciğer yağlanması (CAP ≥ 274; CONTAMINATED)', r.analiz, f'{r.n} ({r.pos})', ci([r.AUC, r.AUC_lo, r.AUC_hi]),
             ci([r.dAUC, r.dAUC_lo, r.dAUC_hi]), '`phase_xxx/results/liver_test_results.csv`'] for r in lb.itertuples()]
    gs = pd.read_csv(V2 / 'phase_xxx/results/gallstone_test_results.csv')
    for r in gs[gs.analiz.str.startswith('Baseline')].itertuples():
        rows.append(['Safra taşı (NHANES III Faz 2)', r.analiz, f'{r.n} ({r.pos})', ci([r.AUC, r.AUC_lo, r.AUC_hi]),
                     ci([r.dAUC, r.dAUC_lo, r.dAUC_hi]), '`phase_xxx/results/gallstone_test_results.csv`'])
    L.append(md_table(['model', 'referans', 'n (poz.)', 'referans AUC', 'ΔAUC (model − ref)', 'kaynak'], rows))
    L += ['', 'SCORED: `ckd_A` satırındaki "modified SCORED" (Phase XXXV; değiştirilmiş sürüm, ayrıntı `phase_xxxv/03_test_results.md`). '
          'Listede olmayan referanslar (ör. AF için CHARGE-AF; KOAH için CAPTURE) projede uygulanmadı: BULUNAMADI.', '']
    return L


def read33(name):
    return pd.read_csv(X33 / f'{name}.csv')


def sec_1c():
    L = ['## 1c. AF — dış doğrulama ayrıntısı (Phase XXXIII; donmuş model + kilitli pipeline)', '']
    a2 = read33('a2_results')
    a2 = a2[(a2.skor == 'MODEL') & a2.analiz.str.startswith('A2 — birincil')]
    b = read33('b_results')
    b = b[(b.skor == 'MODEL') & b.analiz.str.startswith('B — birincil')]
    mx = read33('mixture_results')
    mx = mx[mx.analiz.str.startswith('Karışım — birincil')]
    rows = []
    for k in a2.kapsam:
        ra, rb, rm = a2[a2.kapsam == k].iloc[0], b[b.kapsam == k].iloc[0], mx[mx.kapsam == k].iloc[0]
        rows.append([k, f'{ra.n} ({ra.pos})', ci([ra.R, ra.R_lo, ra.R_hi]), ci([ra.FPR, ra.FPR_lo, ra.FPR_hi]),
                     ci([ra.AUC, ra.AUC_lo, ra.AUC_hi]), ci([rb.FPR, rb.FPR_lo, rb.FPR_hi]),
                     ci([rm.P, rm.P_lo, rm.P_hi]), ci([rm.FPR, rm.FPR_lo, rm.FPR_hi]), f3(rm.prev),
                     'evet' if rm.uc_hedef else 'hayır'])
    L.append(md_table(['kaynak', 'A2 n (AF)', 'Recall (A2)', 'FPR AF vs SR (A2)', 'AUC (A2)', 'FPR AF vs diğer ritim (B)',
                       'Precision (karışım)', 'FPR (karışım)', 'ağırlıklı prevalans', 'üç hedef (karışım)'], rows))
    L += ['', 'Kaynak: `phase_xxxiii/results/a2_results.csv` (analiz = "A2 — birincil", skor = MODEL), `b_results.csv` '
          '("B — birincil"), `mixture_results.csv` ("Karışım — birincil"). A2 Precision örneklem prevalansına bağlı olduğu için '
          'raporlanmaz; üç hedef yalnız karışımda değerlendirilir (karışım ağırlıkları hastane arşivi oranlarıdır, toplum '
          'prevalansı değil; `phase_xxxiii/01_data_flow.md` notlar).', '']
    rf = read33('b_rhythm_fpr')
    rf = rf[rf.kapsam.str.startswith('Havuz')]
    L += ['### Diğer ritimlerde yanlış pozitif oranı (havuz)', '',
          md_table(['ritim', 'n', 'FP', 'FPR model', 'FPR baseline (RR_iqr/RR_mean)'],
                   [[r.ritim, r.n, r.FP, ci([r.FPR, r.FPR_lo, r.FPR_hi]), ci([r.base_FPR, r.base_FPR_lo, r.base_FPR_hi])]
                    for r in rf.itertuples() if r.n > 0]),
          '', 'Kaynak: `phase_xxxiii/results/b_rhythm_fpr.csv` (kapsam = Havuz). Kaynak başına satırlar aynı dosyada.', '']
    afl = read33('afl_results')
    afl = afl[afl.analiz.str.startswith('AFL — birincil')]
    L += ['### AFL kayıtlarında AF kararı', '',
          md_table(['kaynak', 'n', 'AF kararı', 'oran model', 'oran baseline'],
                   [[r.kapsam, r.n, r.AF_karari, ci([r.oran, r.oran_lo, r.oran_hi]),
                     ci([r.base_oran, r.base_oran_lo, r.base_oran_hi])] for r in afl.itertuples()]),
          '', 'Kaynak: `phase_xxxiii/results/afl_results.csv`.', '',
          '### CPSC-Extra: 4 negatif', '',
          'Tekilleştirmeden sonra CPSC-Extra\'da uygun SR kaydı **4** (AF 78). A2\'de FPR 0,000 [0,000–0,490] ve AUC '
          '**yorumlanamaz** (XXXIII protokol sapması 2: SR n < 30 → "YORUMLANAMAZ"; kural model çıktısı görülmeden eklendi). '
          'CPSC-Extra\'daki 152 header-uygun AF kaydının 74\'ü CPSC 2018 kopyasıydı. Aynı kaynakta diğer ritim negatifi 492; '
          'B ve karışımda yorumlanabilir. Kaynak: `phase_xlvi/af_validation_dossier.md` §4.1, §5.2; `phase_xxxiii/01_data_flow.md`.', '']
    # ABSTAIN / pipeline başarısızlığı (phase_xxxiii/01_data_flow.md satır 55–67; kaynak sütun sırası CPSC, Extra, Chapman, Georgia)
    fail = {'CPSC 2018': (1, 1, 0, 0), 'CPSC-Extra': (0, 0, 0, 0), 'Chapman-Shaoxing': (1, 0, 3, 0), 'Georgia': (1, 1, 0, 0)}
    ok = {'CPSC 2018': (1087, 818, 493, 0), 'CPSC-Extra': (78, 4, 492, 46), 'Chapman-Shaoxing': (1777, 1803, 496, 438),
          'Georgia': (555, 1695, 499, 167)}
    rows, tf, tn = [], 0, 0
    for k in fail:
        nf, n = sum(fail[k]), sum(fail[k]) + sum(ok[k])
        tf, tn = tf + nf, tn + n
        rows.append([k, n, nf, ci(wilson(nf, n), 4)])
    rows.append(['Havuz', tn, tf, ci(wilson(tf, tn), 4)])
    L += ['### ABSTAIN (pipeline başarısızlığı → tahmin üretilmez) oranları', '',
          md_table(['kaynak', 'işlenen kayıt (AF+SR+diğer+AFL)', 'başarısız (zero_beats / ecgdeli_error / feature_error)',
                    'oran [Wilson %95 GA]'], rows),
          '', 'Kaynak: `phase_xxxiii/01_data_flow.md` satır 55–67 ("− pipeline başarısız" ve "= Birincil analiz" satırları; '
          'tür dağılımı `phase_xxxiii/PHASE_XXXIII_REPORT.md` satır 12–21). Phase XXIX (1.882 kayıt) başarısızlık 0 '
          '(`phase_xxix/01_data_flow.md` satır 61). Teknik uygunluk (fs ≠ 500 Hz, < 10 sn, yaş/cinsiyet eksik) bu orana dahil '
          'değildir; uygulamada bunlar da ABSTAIN üretir (`app/docs/architecture.md` §4).', '']
    return L


def sec_1d():
    L = ['## 1d. Kirlenme / erratum kayıtları', '',
         md_table(['model / sonuç', 'ne oldu', 'nasıl ele alındı', 'kaynak'], [
             ['HTN (Phase XXXII)', 'Test L 2021–23 kişileri daha önce iki testte kullanılmıştı (XXX karaciğer CAP: CONTAMINATED; '
              'XXXI fibrozis: PREVIOUSLY_EXPOSED) → sonuç "bağımsız test" sayılamaz (AUC 0,833, ΔAUC +0,028).',
              'Phase XXXVII: 13 öznitelikle uyumlaştırılmış yeni model, hiçbir hedefte kullanılmamış NHANES C 2003–04\'te tek '
              'sefer test: AUC 0,875 [0,862–0,887], ΔAUC (yaş+cinsiyet+BMI) +0,012 [0,007–0,018]. Registry `htn_M1` bu modeldir. '
              'XXXII AUC\'sinin şiştiğine dair kanıt yok (L OOF AUC 0,834).',
              '`phase_xxxii/00_inventory.md` satır 49; `phase_xxxii/PHASE_XXXII_REPORT.md`; `phase_xxxvii/PHASE_XXXVII_REPORT.md` §6'],
             ['CAD V2 dış skorlama (Hungarian, Switzerland, VA)', 'Kategorik kodlama hatası: Cleveland\'da `\'0.0\'/\'1.0\'` öğrenildi, dış '
              'merkezlerde `\'0\'/\'1\'` geldi → one-hot blokları sıfırlandı (sex, cp; VA\'da restecg). Ayrıca eksik girdiler eğitim '
              'imputer\'ıyla dolduruldu (kurala aykırı). V2 DEVICE: Hungarian R 0,509, VA R 0,514 GEÇERSİZ.',
              'Phase XLI: biçim düzeltmesi + eksiksiz-vaka teknik tekrar (Hungarian n=95 AUC 0,852; VA n=64 AUC 0,667), '
              'PREVIOUSLY_EXPOSED, bağımsız dış doğrulama DEĞİL. Phase XLII: errata belgesi; eski dosyalar değiştirilmedi '
              '(kullanıcı kararı: errata yok, prepare.py değişmez, BASIC/LAB yeniden skorlanmaz). Switzerland YAPILAMAZ (chol %100 eksik).',
              '`phase_xlii/ERRATA_CAD_V2.md` §1–2; `phase_xli/01_cad_rescore.md`; `phase_xli/results/cad_v2_rescore.json`'],
             ['Karaciğer yağlanması CAP (Phase XXX)', 'L CAP etiketleri V2 başlangıcı ve Focused fazında model/eşik seçiminde kullanılmıştı.',
              'Test sonucu CONTAMINATED etiketli; model uygulamaya alınmadı.', '`phase_xxx/03_test_results.md` satır 5'],
             ['MI (Phase XXXVIII)', 'Test kişilerinin 1.106\'sı (%75) AF eşik seçiminde görülmüştü (başka hedef).',
              'PREVIOUSLY_EXPOSED; temiz alt küme (n=368) ayrıca raporlandı.', 'registry `mi_model.evidence`; `phase_xxxviii/03_test_results.md`'],
         ]), '', '### PREVIOUSLY_EXPOSED / önceden açılmış test etiketleri (registry `evidence`)', '']
    rows = []
    for mid, m in REG.items():
        ev = m['evidence']
        srcs = [ev.get(k, {}) and ev[k].get('source', '') for k in ('internal_test', 'temporal', 'external') if ev.get(k)]
        txt = ' · '.join([ev['highest_tier']] + [s for s in srcs if s])
        flag = 'evet' if re.search(r'PREVIOUSLY_EXPOSED|önceden', txt) else ('hayır (kayıtta "hiçbir hedefte önceden kullanılmamış")'
                                                                             if 'önceden kullanılmamış' in txt else 'kayıtta belirtilmemiş')
        if 'önceden kullanılmamış' in txt:
            flag = 'hayır (kayıtta "hiçbir hedefte önceden kullanılmamış")'
        rows.append([f'`{mid}`', flag, txt])
    L.append(md_table(['model', 'önceden görülmüş/maruz test kişisi', 'registry metni (highest_tier + kaynaklar)'], rows))
    L += ['', 'Kaynak: `phase_xliii/registry/models.json > models.<id>.evidence`. "kayıtta belirtilmemiş" = registry metninde '
          'maruziyet ifadesi yok; bu, maruziyet olmadığı anlamına gelmez (faz raporuna bakılmalı).', '']
    return L


def sec_1e():
    nh = ('Kamuya açık ABD federal verisi; NCHS Veri Kullanıcı Sözleşmesi (README "Veri kaynakları ve lisanslar")')
    rows = [
        ['NHANES (CDC/NCHS)', 'döngüler: A 1999–2000, C 2003–04, D 2005–06, E 2007–08, F 2009–10, G 2011–12, H 2013–14, I 2015–16, '
         'J 2017–18, P 2017–Mar 2020, L Ağu 2021–Ağu 2023; ABD genel nüfus', 'model başına `model_results.csv`', nh,
         'dm_A/B, ckd_A/B, htn_M1, fibrosis_final, osteo_final, anemia_LR16, copd_S4_DEVICE'],
        ['NHANES III (1988–94)', 'Faz 1 1988–91 (geliştirme), Faz 2 1991–94 (test); ABD', 'safra kesesi US: 14.645 final tanılı; '
         'analiz 6.287 / 6.528', nh, 'safra taşı (uygulamada değil)'],
        ['PTB-XL 1.0.3 (+ PTB-XL+ ECGDeli öznitelikleri)', 'PTB (Physikalisch-Technische Bundesanstalt), Almanya; tek kurum arşivi',
         '21.799 EKG / 18.869 hasta; AF kohortu 12.025', 'CC BY 4.0', 'af_S4_DEVICE (geliştirme, iç test), mi_model'],
        ['PhysioNet/CinC Challenge 2021 1.0.3', 'CPSC 2018 + CPSC-Extra (Çin, çeşitli), Chapman-Shaoxing (Shaoxing, Çin), '
         'Georgia/G12EC (Emory, Atlanta, ABD)', 'kullanılan 10.456 kayıt (AF 3.500, SR 4.322, diğer 1.983, AFL 651)', 'CC BY 4.0',
         'af_S4_DEVICE (dış doğrulama)'],
        ['UCI Heart Disease', 'Cleveland Clinic Foundation (eğitim); Hungarian Institute of Cardiology, Budapeşte; University Hospital Zürich ve '
         'Basel (Switzerland); V.A. Medical Center, Long Beach CA (teknik tekrar / uyumluluk); bağış Temmuz 1988 (`heart-disease.names` satır 47)', 'Cleveland 303; Hungarian 294; Switzerland 123; VA 200 '
         '(dosya satırı)', 'CC BY 4.0', 'cad_DEVICE'],
        ['Mendeley Data 7v4w66wxj8.1 (RIP3 HF)', 'kurum/ülke/dönem proje dosyalarında BULUNAMADI (birincil yayın Hu X ve ark. 2020, §1h)',
         '186 satır → analiz 184 (HF 89 / kontrol 95); fit 110, val 37, test 37', 'CC BY 4.0', 'hf_S2_BASIC_LAB (registry_only)'],
        ['UCI Gallstone (id 1150)', 'Ankara VM Medical Park, Haziran 2022–Haziran 2023', '319 (161/158); test 64', 'CC BY 4.0',
         'eski safra taşı sonucu (Phase21/25; uygulamada değil)'],
    ]
    return ['## 1e. Veri setleri', '', md_table(['veri seti', 'dönem / merkez', 'n', 'erişim / lisans', 'model(ler)'], rows), '',
            'Kaynak: `README.md` "Veri kaynakları ve lisanslar"; `phase_xlvi/af_validation_dossier.md` §3–4; '
            '`phase_xxx/01_gallstone_sources.md`; `phase_xxx/results/nhanes3_gallbladder_counts.json`; '
            '`All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 140, 171, 211–213; `phase_xlix/results/af_overlap_check.json`; '
            '`phase_xlix/results/uci_cad_feature_availability.json`. UCI merkez kurumları `heart-disease.names` belgesinden '
            '(`phase_xxxix/data/uci_45_redownload/x/heart-disease.names`). NHANES kullanılan bileşen dosyaları: §1h.', '']


def count_junit(p):
    r = ET.parse(p).getroot()
    s = r if r.tag == 'testsuite' else r
    tot = int(s.get('tests', 0)) if s.get('tests') else sum(int(t.get('tests', 0)) for t in r.iter('testsuite'))
    fail = sum(int(t.get('failures', 0)) for t in r.iter('testsuite'))
    err = sum(int(t.get('errors', 0)) for t in r.iter('testsuite'))
    skip = sum(int(t.get('skipped', 0)) for t in r.iter('testsuite'))
    return tot, fail, err, skip


def sec_1f():
    be = count_junit(P49 / 'results/pytest_backend_full.xml')
    vi = count_junit(V2 / 'phase_xlviii/results/vitest_junit.xml')
    pw = count_junit(V2 / 'phase_xlviii/results/playwright/playwright_junit.xml')
    axe = json.loads((V2 / 'phase_xlviii/results/axe_results.json').read_text(encoding='utf8'))
    nviol = sum(len(s.get('violations', [])) for s in axe['screens'])
    eps = re.findall(r"@app\.(get|post)\('([^']+)'\)", (V2 / 'app/backend/healthrisk_api/main.py').read_text(encoding='utf8'))
    L = ['## 1f. Yazılım', '',
         '**Mimari bileşenler** (`app/docs/architecture.md` §1): React + TypeScript + Tailwind arayüz (form `/schema`\'dan üretilir, '
         'durum yalnız bellekte) · FastAPI backend (yalnız 127.0.0.1; gövde loglanmaz) · Service (birim dönüşümü → doğrulama → '
         'uygunluk → 46 dönüşüm) · registry + şema v2 (SHA256 başlangıçta doğrulanır) · model yükleyici (dosya SHA256 = registry, '
         'yüklemeden önce) · kanıta duyarlı yönlendirme · AF yolu (ilk 10 sn → kilitli Octave/ECGDeli) · açıklama asistanı '
         '(Ollama gemma3:4b + bge-m3 RAG; Phase XLVIII).', '',
         '**Uç noktalar** (`app/backend/healthrisk_api/main.py`): ' + ', '.join(f'`{m.upper()} {p}`' for m, p in eps) + '.', '',
         md_table(['test paketi', 'sonuç', 'kaynak'], [
             ['Backend pytest (tam: AF uçtan uca + gerçek Ollama)', f'{be[0]} test: {be[0] - be[3] - be[1] - be[2]} geçti, '
              f'{be[3]} xfail/skip, {be[1]} başarısız, {be[2]} hata (bu faz, 2026-11-25)', '`phase_xlix/results/pytest_backend_full.xml`, `phase_xlix/logs/pytest_full.log`'],
             ['Vitest', f'{vi[0]} test, {vi[1]} başarısız', '`phase_xlviii/results/vitest_junit.xml`'],
             ['Playwright (canlı backend + üretim derlemesi)', f'{pw[0]} test, {pw[1]} başarısız, {pw[3]} skip',
              '`phase_xlviii/results/playwright/playwright_junit.xml`'],
             ['axe-core (WCAG 2/2.1 A+AA)', f'{len(axe["screens"])} ekran, {nviol} ihlal', '`phase_xlviii/results/axe_results.json`'],
         ]), '',
         'Backend 5 xfail: belgelenmiş BMI/osteo sınırlılığı (strict xfail; kullanıcı onaylı, Phase XLIV). Vitest/Playwright/axe '
         'bu fazda yeniden koşulmadı (XLVIII sonrası `app/` değişmedi; bu fazın SHA kontrolüne bakınız).', '',
         '**Kanıta duyarlı yönlendirme kuralları** (`app/docs/architecture.md` §3): birim/aralık hatası → `/predict` 422, '
         '`/eligibility` alan hatası; model devre dışı → ABSTAIN ("Karar verilemez"); popülasyon dışı (yaş, gebelik, tanı, diyaliz, '
         'FEV1/FVC) → NOT_APPLICABLE ("Kapsam dışı"); zorunlu alan eksik → ABSTAIN ("Eksik: alanlar"); şema dışı kategori / gebelik '
         '"bilmiyorum" → ABSTAIN; hazır → donmuş eşik → ESIK_USTU/ESIK_ALTI + kanıt katmanları + sınırlılıklar + hedef-tanımlayan '
         'girdi uyarısı; dm_B/ckd_B çalışamazsa A modeline düşer. Eksik veri doldurulmaz; ırk yanıtsızsa ırk kullanan 5 model ABSTAIN. '
         'AF `/predict`\'te her zaman NOT_APPLICABLE, yalnız `/ecg/af`. Model kuralları: `phase_xlvi/scripts/card_spec.py > APP_ELIG`.', '',
         '**Senaryo testlerinin yeri** (`app/backend/tests/test_scenarios.py`; işaretlerle seçilir, `pytest -m <işaret>`):', '']
    rows = []
    for mk, desc, line in [('scenario_normal', 'normal girdi', 34), ('scenario_missing', 'eksik girdi', 96),
                           ('scenario_unit', 'birim hatası / birim dönüşümü', 164), ('scenario_out_of_scope', 'kapsam dışı', 201)]:
        rows.append([desc, f'`{mk}`', f'`app/backend/tests/test_scenarios.py:{line}`', SCEN.get(mk, 'BULUNAMADI')])
    L.append(md_table(['senaryo', 'pytest işareti', 'tanım satırı', 'toplanan test sayısı (bu faz)'], rows))
    L += ['', 'Ek: birim/aralık doğrulama birim testleri `app/backend/tests/test_validation_units.py`; dönüşümler '
          '`test_transforms.py`; gizlilik `test_privacy.py` + `app/frontend/e2e/privacy.spec.ts`; uçtan uca senaryolar '
          '`app/frontend/e2e/scenarios.spec.ts`; erişilebilirlik `app/frontend/e2e/a11y.spec.ts`; AF panel `test_phase46_af_panel.py`; '
          'asistan `test_phase48_assistant.py` + `app/frontend/e2e/assistant.spec.ts`.', '']
    return L


SCEN = {}


def lines(p, a, b):
    return (V2 / p).read_text(encoding='utf8').splitlines()[a - 1:b]


def sec_1g():
    L = ['## 1g. Açıklama asistanı (Phase XLVIII)', '',
         '**Model seçimi (kilitli)** (`phase_xlviii/01_model_selection.md` §4, satır 57–64): sohbet `gemma3:4b`, gömme `bge-m3:latest`. '
         'Gerekçe (kaynak metin): en yüksek Türkçe akıcılık ve kaynağa sadakat, her yanıtta atıf, ~4× hızlı (tamamen GPU), Latin dışı '
         'karaktere geçiş yok. llama3 ve qwen2.5:7b elendi (qwen2.5 6 GB VRAM\'e sığmadı; bir yanıtının çoğu Çince). Adaylar (satır '
         '17–23) ve karşılaştırma (satır 42–47):', '']
    L += lines('phase_xlviii/01_model_selection.md', 17, 23) + [''] + lines('phase_xlviii/01_model_selection.md', 42, 47) + ['']
    L += ['**Ana değerlendirme — 67 soru, 1. çalıştırma: 62/67** (`phase_xlviii/03_eval.md` satır 19–27):', '']
    L += lines('phase_xlviii/03_eval.md', 19, 27) + ['']
    L += ['**v2 — acil filtresi düzeltmesi sonrası ayrı kilitli set** (`03_eval.md` satır 87–92; R grubu yeni değerlendiriciyle '
          'ayrı sütunda 9/10, satır 97–99):', ''] + lines('phase_xlviii/03_eval.md', 87, 92) + ['']
    L += ['**v3 — son tur** (`03_eval.md` satır 138–145):', ''] + lines('phase_xlviii/03_eval.md', 138, 145) + ['']
    L += ['**Kırmızı bayrak eklemesi (v3 sonrası, bağımsız setle DOĞRULANMADI):** 14 kaynak temelli kural (MedlinePlus kalp krizi, '
          'NHLBI kalp krizi belirtileri, MedlinePlus inme BE-FAST, MedlinePlus baş ağrısı); kaynak URL\'leri '
          '`app/backend/config/assistant_config.json > red_flag_rules`; v3\'te kaçan P-02 artık sabit 112 rotasında (yalnız rota '
          'kontrolü). Kaynak: `03_eval.md` satır 163–180.', '',
          '**Diğer ölçümler:** tekrarlanabilirlik karar 66/67, metin 50/67 (LLM 19/36); LLM\'e giden ortalama 4,41 sn, en uzun 7,59 sn; '
          'elle inceleme 18 yanıt (tek, kör olmayan değerlendirici): doğruluk 1,61/2, sadakat 1,83/2, Türkçe 4,44/5; 1 kritik (G4-04) — '
          '`03_eval.md` satır 181–226.', '',
          '**Sınırlılıklar** (`03_eval.md` §9, satır 230+): elle puanlar tek ve kör olmayan değerlendirici; gemma3:4b seyrek ama klinik '
          'anlamı değiştiren çeviri hataları; son kontrol anlam hatası yakalamaz; ön filtreler kural tabanlı; genel bilgi sorusunda uyarı '
          'kutusu 7/12; kuralları ve doğrulama cümlelerini aynı yazar yazdı; GPU kaynaklı metin belirlenimsizliği; test seti küçük (67) '
          've sentetik.', '']
    return L


DOI_RE = re.compile(r'10\.\d{4,9}/[^\s\)\]\}>"\'`|,;<]+')
PMID_RE = re.compile(r'PMID[:\s]*?(\d{6,9})')


def scan_refs():
    files = [V2 / 'README.md', V2 / 'FINAL_RESEARCH_REPORT.md']
    for pat in ['phase_*/*.md', 'phase_*/config/*.md', 'phase_*/model_cards/*.md', 'app/docs/**/*.md', '*/00_MASTER_RESULTS.md',
                'app/backend/assistant/kb/**/*.md', 'phase_xlvi/data/refs/*.json']:
        files += [f for f in V2.glob(pat) if 'node_modules' not in f.parts and 'phase_xlix' not in f.parts]
    found = {}
    for f in sorted(set(files)):
        rel = f.relative_to(V2).as_posix()
        for i, ln in enumerate(f.read_text(encoding='utf8', errors='replace').splitlines(), 1):
            for d in DOI_RE.findall(ln):
                d = d.rstrip('.').rstrip('*')
                k = ('DOI', d.lower())
                found.setdefault(k, [d, 0, f'{rel}:{i}'])[1] += 1
            for pm in PMID_RE.findall(ln):
                k = ('PMID', pm)
                found.setdefault(k, [pm, 0, f'{rel}:{i}'])[1] += 1
    rows = sorted([(t, v[0], v[1], v[2]) for (t, _), v in found.items()], key=lambda r: (r[0], r[1].lower()))
    with open(P49 / 'results/references_found.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['tur', 'kimlik', 'gecis_sayisi', 'ilk_gecis'])
        w.writerows(rows)
    return rows, len(set(files))


NHANES_PHASES = {'phase_xxx': 'osteo_final (D,E,F,H,J), karaciğer CAP, safra taşı', 'phase_xxxvii': 'htn_M1 (P, L, C)',
                 'phase_xlii': 'dm_A, dm_B (E–J)', 'All_Disease_Improvement_Phase21': 'copd_S4_DEVICE (F, G, E), Phase21 adayları',
                 'Focused_Current_Disease_Improvement_2026': 'fibrosis_final geliştirme (P) ve test (L) verisinin indirildiği faz',
                 'phase_xxxiv': 'ckd_A, ckd_B (E–I; phase_xxxv bu envanteri okur)', 'Clinical_Optimization_Phase25': 'anemia_LR16 (NHANES A ve çeşitli döngüler)'}


def nhanes_components():
    pat = re.compile(r'(?<![A-Za-z0-9])((?:P_)?[A-Z][A-Z0-9]{1,8}(?:_[A-L])?)\.(?:xpt|XPT)')
    out = []
    for ph, use in NHANES_PHASES.items():
        fs = [f for f in (V2 / ph).rglob('*.json') if re.search('manifest|download|inventory_meta', f.name, re.I)
              and 'sha256' not in f.name and '.venv' not in f.parts]
        s = set()
        for f in fs:
            s |= set(pat.findall(f.read_text(encoding='utf8', errors='replace')))
        out.append([ph, use, ', '.join(sorted(s)) or 'BULUNAMADI (manifestte .xpt adı yok)',
                    ', '.join(f'`{f.relative_to(V2).as_posix()}`' for f in fs[:4]) or '—'])
    return out


def sec_1h():
    rows, nfiles = scan_refs()
    L = ['## 1h. Kaynakça', '',
         f'Repoda geçen tüm DOI ve PMID\'ler otomatik tarandı ({nfiles} belge: README, FINAL_RESEARCH_REPORT, faz raporları ve '
         f'konfigürasyon belgeleri, model kartları, `app/docs`, asistan bilgi tabanı, `phase_xlvi/data/refs`). **{len(rows)} tekil kimlik** '
         '(ilk geçtiği dosya:satır ile): `phase_xlix/results/references_found.csv`. Ana atıflar:', '',
         md_table(['kaynak', 'künye', 'kimlik', 'repoda'], [
             ['PTB-XL', 'Wagner P ve ark. Sci Data 2020; PhysioNet 1.0.3 (2022)', 'doi:10.1038/s41597-020-0495-6; doi:10.13026/kfzx-aw45', 'README'],
             ['Challenge 2021', 'Reyna MA ve ark. CinC 2021; Physiol Meas 2022; PhysioNet 1.0.3', 'doi:10.23919/CinC53138.2021.9662687; doi:10.1088/1361-6579/ac79fd; doi:10.13026/34va-7q14', 'README, XLVI belge'],
             ['UCI Heart Disease', 'Janosi A, Steinbrunn W, Pfisterer M, Detrano R. 1989', 'doi:10.24432/C52P4X', 'README'],
             ['ECGDeli', 'Pilia N ve ark. SoftwareX 2021;13:100639', 'doi:10.1016/j.softx.2020.100639', 'README'],
             ['PhysioNet', 'Pollard T ve ark. Nature Health 2026', 'doi:10.1038/s44360-026-00096-z', 'README'],
             ['TRIPOD+AI', 'Collins GS ve ark. BMJ 2024;385:e078378', 'doi:10.1136/bmj-2023-078378', 'model kartları'],
             ['FIB-4', 'Sterling RK ve ark. Hepatology 2006', 'PMID 16729309; doi:10.1002/hep.21178', 'XLVI 01'],
             ['FIB-4 NAFLD eşikleri', 'Shah AG ve ark. Clin Gastroenterol Hepatol 2009', 'PMID 19523535; doi:10.1016/j.cgh.2009.05.033', 'XLVI 01'],
             ['NFS', 'Angulo P ve ark. Hepatology 2007', 'PMID 17393509; doi:10.1002/hep.21496', 'XLVI 01'],
             ['OST(A)', 'Koh LK ve ark. Osteoporos Int 2001', 'PMID 11580084; doi:10.1007/s001980170070', 'XLVI 01'],
             ['OST erkek', 'Adler RA ve ark. Mayo Clin Proc 2003', 'PMID 12934782; doi:10.4065/78.6.723', 'XLVI 01'],
             ['UCI Gallstone', 'Esen İ ve ark. Medicine 2024', 'doi:10.1097/md.0000000000037258; PMID 38394521', 'FINAL_RESEARCH_REPORT'],
         ]), '', '### Eksikler — bu fazda arandı', '',
         md_table(['eksik', 'bulunan (doğrulama yolu, 2026-11-25)'], [
             ['NHANES 2017–Mart 2020 P_LUX', '"Liver Ultrasound Transient Elastography (P_LUX)", veri dosyası `P_LUX.xpt`, NHANES '
              '2017–March 2020 Pre-pandemic; ilk yayım Ocak 2022, son revizyon NA. https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_LUX.htm '
              '(sayfa okundu). FibroScan 502 V2 Touch (M/XL prob). Prosedür el kitabı: '
              'https://wwwn.cdc.gov/nchs/data/nhanes/public/2017/manuals/2018_Liver_Ultrasound_Elastography_Procedures_Manual.pdf (arama sonucu; açılmadı).'],
             ['Tansiyon kılavuzu (ESC/ESH)', 'Williams B, Mancia G, Spiering W ve ark. 2018 ESC/ESH Guidelines for the management of '
              'arterial hypertension. Eur Heart J 2018;39(33):3021–3104. doi:10.1093/eurheartj/ehy339; PMID 30165516. · Mancia G, Kreutz R, '
              'Brunström M ve ark. 2023 ESH Guidelines for the management of arterial hypertension. J Hypertens 2023;41(12):1874–2071. '
              'doi:10.1097/HJH.0000000000003480; PMID 37345492. (Europe PMC REST; projede kullanım `phase_xxxii/config/protocol_htn.md` satır 39)'],
             ['RIP3 veri DOI 10.17632/7v4w66wxj8.1', 'DOI çözülüyor: https://doi.org/10.17632/7v4w66wxj8.1 → HTTP 302 → '
              'https://data.mendeley.com/datasets/7v4w66wxj8/1 (sayfa açıldı). Başlık "Data for: Plasma Level of Receptor-Interacting '
              'Protein Kinase-3 as a Potential Biomarker for Diagnosis and Prognosis in Heart Failure"; katkıda bulunan Shuyang Zhang; '
              'V1, 26 Haziran 2020; CC BY 4.0; açıklama: 91 HF + 95 sağlıklı. Birincil yayın: Hu X, Li H, Chen X, Liu H, Zuo W, Zhang Y, '
              'Zhang S. Plasma concentration of receptor-interacting protein kinase-3 as a potential biomarker for diagnosis and prognosis '
              'in heart failure. Clin Chim Acta 2020;509:273–279. doi:10.1016/j.cca.2020.06.039; PMID 32598878.'],
             ['CCN3 makalesi yazar/sayfa', 'Li JY, Wang YD, Qi XY, Ran L, Hong T, Yang J, Yan B, Liao ZZ, Liu JH, Xiao XH. Serum CCN3 levels '
              'are increased in type 2 diabetes mellitus and associated with obesity, insulin resistance and inflammation. Clin Chim Acta '
              '2019;494:52–57. doi:10.1016/j.cca.2019.03.006; PMID 30876855. Veri: Mendeley 10.17632/6vcccg428f.1 (CC BY-NC 3.0; '
              '`All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 109). Not: CCN3 diyabet modeli registry\'de değil.'],
         ]), '',
         'PubMed sayfaları otomatik erişimi engelledi (çerez kontrolü); künyeler Europe PMC REST API\'den (`resultType=core`) alındı.', '',
         '### Kullanılan NHANES bileşenleri (dosya adları; faz indirme/manifest dosyalarından otomatik)', '',
         md_table(['faz', 'model(ler)', 'NHANES .xpt bileşenleri', 'manifest'], nhanes_components()), '',
         'Döngü son ekleri: A 1999–2000 (ek yok / LAB##), B 2001–02, C 2003–04, D 2005–06, E 2007–08, F 2009–10, G 2011–12, H 2013–14, '
         'I 2015–16, J 2017–18, P_ 2017–Mar 2020, L 2021–23. NHANES III: `exam.dat` (GUPFDX1R) — `Clinical_Model_Improvement_Phase24/data/raw/nhanesIII/`. '
         'Manifest bir fazın indirdiği tüm dosyaları listeler; her dosyanın modelde girdi olduğu anlamına gelmez (girdi listesi registry). '
         'Phase25 manifesti NHANES A/B dosyalarını (LAB##, L##_B) içerir. NHANES genel atfı: README "Veri kaynakları" (NCHS sayfasında doğrulanamadı).', '']
    return L


def nhanes3_phase_check():
    """exam.dat: SEQN 1–5, SDPPHASE 40 (phase_xxx/scripts/t2_gallstone_data.py satır 14). Yalnız kimlik + faz okunur."""
    p = V2 / 'Clinical_Model_Improvement_Phase24/data/raw/nhanesIII/exam.dat'
    seq = {}
    with open(p, 'rb') as fh:
        for ln in fh:
            seq.setdefault(ln[0:5], set()).add(ln[39:40])
    from collections import Counter
    c = Counter(b''.join(sorted(v)).decode() for v in seq.values())
    out = dict(file=p.relative_to(V2).as_posix(), sha256=sha(p), rows=sum(1 for _ in open(p, 'rb')), unique_seqn=len(seq),
               seqn_in_both_phases=sum(len(v) > 1 for v in seq.values()), phase_counts=dict(c))
    (P49 / 'results/nhanes3_phase_disjoint.json').write_text(json.dumps(out, indent=1), encoding='utf8')
    return out


def sec_2():
    n3 = nhanes3_phase_check()
    a2 = read33('a2_results')
    a2 = a2[(a2.skor == 'MODEL') & a2.analiz.str.startswith('A2 — birincil')].set_index('kapsam')
    b = read33('b_results')
    b = b[(b.skor == 'MODEL') & b.analiz.str.startswith('B — birincil')].set_index('kapsam')
    mx = read33('mixture_results')
    mx = mx[mx.analiz.str.startswith('Karışım — birincil')].set_index('kapsam')
    rows = []
    for k in a2.index:
        x, y, z = a2.loc[k], b.loc[k], mx.loc[k]
        miss = [n for n, ok in [('P', z.P >= .70), ('R', z.R >= .75), ('FPR', z.FPR <= .15)] if not ok]
        rows.append([k, '%' + f3(x.FPR * 100, 2) + f' ({int(x.FP)}/{int(x.FP + x.TN)})' + (' YORUMLANAMAZ, SR n=4' if k == 'CPSC-Extra' else ''),
                     '%' + f3(y.FPR * 100, 1) + f' ({int(y.FP)}/{int(y.FP + y.TN)})', '%' + f3(z.FPR * 100, 1), f3(z.P), f3(z.R), 'evet' if not miss else 'hayır (' + ', '.join(miss) + ')'])
    gs = pd.read_csv(V2 / 'phase_xxx/results/gallstone_test_results.csv')
    g0 = gs.iloc[0]
    dev = json.loads((V2 / 'phase_xxx/results/gallstone_dev_summary.json').read_text(encoding='utf8'))
    uP, uR, uF = wilson(29, 47), wilson(29, 32), wilson(18, 32)
    L = ['# 2. Ara rapordaki bilinen hatalar — doğru değerler', '',
         '## 2.1 AF genel tablo: "FPR ≤ %0,3" yerine kaynak başına gerçek değerler', '',
         md_table(['kaynak', 'FPR AF vs SR (A2)', 'FPR AF vs diğer ritimler (B)', 'FPR karışım', 'Precision karışım',
                   'Recall', 'üç hedef (karışım: P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15)'], rows), '',
         'Kaynak: `phase_xxxiii/results/a2_results.csv`, `b_results.csv`, `mixture_results.csv` (birincil, MODEL). Doğru ifade: '
         '"Yalnız sinüs ritmine karşı FPR kaynak başına %0,18–0,37 (havuz %0,25 = 11/4.320); CPSC 2018\'de %0,37 olduğundan '
         '\"FPR ≤ %0,3\" ifadesi her kaynak için doğru değildir. Diğer ritimler negatife katılınca FPR '
         '%3,3–11,5 (havuz %7,2; sinüs taşikardisinde %18,1, PVC\'de %30,6). Üç hedef gerçekçi karışımda yalnız CPSC 2018 ve '
         'Chapman-Shaoxing\'de sağlandı; Georgia (P 0,451) ve CPSC-Extra (P 0,421) ile havuzda (P 0,661) sağlanmadı; Georgia Recall '
         '0,764 (sınırda)." A2\'de Precision prevalans nedeniyle raporlanmaz.', '',
         '## 2.2 Safra taşı', '',
         f'**Ana (güncel) sonuç — NHANES III safra kesesi ultrasonu, Phase XXX, kilitli tek sefer:** n = {g0.n} ({g0.pos} pozitif; prevalans '
         f'{f3(g0.prevalans)}), TP/FP/TN/FN {int(g0.TP)}/{int(g0.FP)}/{int(g0.TN)}/{int(g0.FN)}; Precision {ci([g0.P, g0.P_lo, g0.P_hi])}, '
         f'Recall {ci([g0.R, g0.R_lo, g0.R_hi])}, FPR {ci([g0.FPR, g0.FPR_lo, g0.FPR_hi])}, AUC {ci([g0.AUC, g0.AUC_lo, g0.AUC_hi])}; '
         'yaş+cinsiyet+BMI LR\'ye göre ΔAUC +0,012 [0,004–0,019]; üç hedef hayır. Model CatBoost, 20 öznitelik, eşik "kademe3_Youden" '
         '(0,0826). Uygulamaya alınmadı (ALMA kararı). Kaynak: `phase_xxx/results/gallstone_test_results.csv` satır 2; '
         '`phase_xxx/03_test_results.md` "Safra taşı"; `phase_xliii/01_model_selection.md` satır 63.', '',
         '**Dönemler ve ayrıklık:** bölme `SDPPHASE` ile zamansal: Faz 1 (1988–91) geliştirme, Faz 2 (1991–94) test '
         '(`phase_xxx/config/protocol_gallstone.md` satır 12). NHANES III\'ün iki fazı ayrı ulusal olasılık örneklemleridir. **Bu fazda '
         f'doğrulandı:** muayene dosyasında {n3["rows"]} satır = {n3["unique_seqn"]} tekil SEQN; iki fazda birden görünen SEQN '
         f'**{n3["seqn_in_both_phases"]}** (Faz 1 {n3["phase_counts"].get("1")}, Faz 2 {n3["phase_counts"].get("2")}) → geliştirme ve test '
         'kişileri ayrıktır (`phase_xlix/results/nhanes3_phase_disjoint.json`). Not: aynı kişiler Phase24/25\'te karaciğer ultrasonu '
         'hedefi için görülmüştü (safra kesesi etiketi ilk kez açıldı) → etiket "ZAMANSAL TEST … kişiler karaciğer hedefinde görüldü".', '',
         f'**Gerçek sınıf dağılımı:** geliştirme (Faz 1) n = {dev["n"]}, pozitif {dev["secilen_CV_metrik"]["pos"]} '
         f'(%{f3(dev["prevalans"]["agirliksiz"] * 100, 1)}; ağırlıklı %{f3(dev["prevalans"]["agirlikli"] * 100, 1)}); test (Faz 2) n = {g0.n}, '
         f'pozitif {g0.pos} (%{f3(g0.prevalans * 100, 1)}); tüm final tanılı 20–74 yaş: taş (kod 3–5) 1.149, normal 11.666, '
         'kolesistektomi 870 (`phase_xxx/results/nhanes3_gallbladder_counts.json`; `gallstone_dev_summary.json`).', '',
         '**Eski sonuç (ayrı tutulmalı) — UCI Gallstone (Ankara, hastane olgu-kontrol):** 319 kişi (161 taş / 158 kontrol, %50,5); '
         'test n = 64 (32/32). HistGradientBoosting / LAB: Precision 0,617, Recall 0,906, FPR 0,563, AUC 0,809 '
         '(`All_Disease_Improvement_Phase21/00_MASTER_RESULTS.md` satır 43; `Clinical_Optimization_Phase25/00_MASTER_RESULTS.md` satır 396; '
         'PREVIOUSLY_EXPOSED). Bu fazda Recall/FPR/Precision kesirlerinden geri hesaplanan sayımlar TP/FP/TN/FN = 29/18/14/3 '
         f'(29/32 = 0,906; 18/32 = 0,5625; 29/47 = 0,617) ve Wilson GA: Precision {ci(uP)}, Recall {ci(uR)}, FPR {ci(uF)}. '
         'İki sonuç aynı hedefi ölçmez (hastane olgu-kontrol vs toplum taraması); NHANES III sonucu UCI modelinin dış doğrulaması değildir '
         '(`phase_xxx/01_gallstone_sources.md` §4).', '',
         '**"Sınıf dengesi recall artışını açıklar" iddiası neden yanlış/eksik:**', '',
         '1. Recall = TP / (TP + FN) yalnız pozitifler içinde hesaplanır; sınıf oranı (prevalans) Recall\'un tanımına girmez. Prevalans '
         'Precision\'ı (ve PR-AUC\'yi) değiştirir, Recall\'u doğrudan değiştirmez.',
         '2. UCI\'deki yüksek Recall (0,906) eşiğin çok gevşek seçilmesinin sonucudur: aynı eşikte FPR 0,563 (negatiflerin yarısından fazlası '
         'pozitif sınıflandı). Recall–FPR ödünleşimi eşik seçimidir, sınıf dengesi değil. NHANES III\'te eşik ayrı kuralla seçildi '
         '(Recall 0,741, FPR 0,365).',
         '3. UCI test kümesi küçük (32 pozitif): Recall GA ' + ci(uR) + '; NHANES III Recall GA 0,705–0,774 ile örtüşür. Fark '
         'istatistiksel olarak ayrışmaz.',
         '4. Veri setleri farklı: hedef/popülasyon (hastane polikliniği olgu-kontrol vs toplum taraması), öznitelikler (UCI: biyoempedans, '
         'D vitamini; NHANES III: rutin laboratuvar), dönem (2022–23 vs 1988–94), ayırt edicilik (AUC 0,809 vs 0,751). Recall farkı '
         'bunların ve eşiğin birleşik sonucudur.',
         '5. Sınıf dengesinin dolaylı etkisi (eğitimde dengeli örneklem → olasılık ölçeği) olabilir; ancak her iki çalışmada eşik kendi '
         'verisinde seçildiği için bu etki eşik seçimine absorbe olur. Doğru ifade: "Dengeli örneklem Precision\'ı yükseltir; Recall farkı '
         'eşik seçimi ve veri setleri arası farktan kaynaklanır."', '']
    return L


def sec_3():
    af = json.loads((P49 / 'results/af_overlap_check.json').read_text(encoding='utf8'))
    uc = json.loads((P49 / 'results/uci_cad_feature_availability.json').read_text(encoding='utf8'))
    A, B, C, D, PC = af['A_identifier'], af['B_metadata_fingerprint'], af['C_signal_hash'], af['D_near_duplicate'], af['D_positive_control']
    L = ['# 3. Hoca maddeleri', '', '## 3a. AF: hasta bazlı ayrım ve kayıt/hasta çakışması', '',
         '**Önceden yapılmış (kanıt):** PTB-XL fit/validation/test kişi kesişimi 0/0/0; birden fazla fold\'a düşen hasta 0/18.869; hasta '
         'başına tek (ilk) EKG — `phase_xlvi/results/af_split_check.json`, `phase_xlvi/af_validation_dossier.md` §1. Challenge kaynakları '
         'arası ve kaynak içi birebir kopya tekilleştirmesi (pencere hash\'i): XXIX 226 kopya dışlandı (CPSC-Extra AF\'lerinin 74\'ü CPSC 2018 '
         'kopyası), XXXIII 20 kopya/çelişkili grup — `phase_xxix/results/flow_dedup.json`, `phase_xxxiii/results/flow_dedup33.json`.', '',
         '**Bu fazda yapılan (PTB-XL ↔ Challenge; kimlik/başlık meta verisi + sinyal hash) — `phase_xlix/results/af_overlap_check.json`:**', '',
         md_table(['kontrol', 'sonuç'], [
             ['A. Kimlik ad alanı', f'Kullanılan {A["used_records"]} Challenge kaydının önekleri ' + ', '.join(f'{k} {v}' for k, v in A['used_prefixes'].items()) + f'; Challenge\'ın PTB-XL '
              f'kopyası öneki (HR) taşıyan: **{A["used_with_HR_prefix_(Challenge_PTB-XL_copy)"]}**. 4 kaynağın tüm {A["headers_scanned_all_4_sources"]} '
              f'başlığında ptb-xl/ptb kaynaklı: **{A["headers_from_ptb-xl_or_ptb_source"]}**.'],
             ['B. Başlık meta verisi (yaş+cinsiyet+ritim+5000 örnek @500 Hz)', f'{B["challenge_AF_SR_used_len5000_fs500"]} Challenge AF/SR kaydının '
              f'{B["challenge_records_with_>=1_match"]}\'i en az bir PTB-XL AF-kohortu kaydıyla aynı parmak izini taşıyor (kayıt başına ort. '
              f'{f3(B["mean_candidates_per_matched_challenge_record"], 1)} aday). Meta veri ayırt edici değil: çakışmayı ne kanıtlar ne dışlar.'],
             ['C. Sinyal pencere hash\'i (yerel PTB-XL dalga formları)', f'{C["local_ptbxl_waveforms_unique"]} PTB-XL kaydı (AF rolleri: ' + ', '.join(f'{k} {v}' for k, v in C['local_ptbxl_by_af_role'].items()) + f') × {C["challenge_hashes_compared"]} Challenge hash\'i → eşleşme **{C["window_hash_matches"]}**. '
              'Kapsam sınırlı: PTB-XL records500 indirilmediği için 21.799 kaydın yalnız bu kadarı karşılaştırıldı.'],
             ['D. Challenge içi yakın kopya (lead II korelasyonu, r ≥ 0,99)', f'Aynı yaş / cinsiyet / Dx / uzunluk gruplarında {D["pairs_tested_cross_source"]} '
              f'kaynaklar arası ve {D["pairs_tested_within_source"]} kaynak içi çift → işaretlenen **{D["flagged_cross_source"]} / {D["flagged_within_source"]}**. '
              f'Pozitif kontrol: bilinen {PC["pairs"]} kopya çiftinin {PC["detected_r>=thr"]}\'i yakalandı (min r {f3(PC["min_r"])}).'],
         ]), '',
         '**Sonuç:** kullanılan Challenge kayıtlarında PTB-XL kimliği veya kaynağı yok; yerelde karşılaştırılabilen 103 PTB-XL kaydında '
         'sinyal eşleşmesi yok; kalan Challenge kayıtlarında kaynaklar arası yakın kopya bulunmadı. **Açık kalan:** tüm PTB-XL kayıtlarıyla '
         'sinyal düzeyi karşılaştırma (records500 ≈ 1,7 GB indirme gerektirir; disk/onay kuralı nedeniyle yapılmadı) ve aynı hastanın '
         'farklı kayıtlarının tespiti (Challenge başlıklarında hasta kimliği yok; yapılamaz).', '',
         '## 3b. Fibrozis ve osteoporoz: aynı duyarlılıkta FPR / yönlendirme', '',
         'Phase XLVI\'da yapıldı (kullanıcı onaylı post-hoc yeniden skorlama; kapı 24/24 birebir; McNemar + paired bootstrap ΔAUC). '
         'Tablo: §1b "Aynı duyarlılıkta FPR"; ayrıntı `phase_xlvi/01_reference_score_analysis.md` §3–4. Referans eşikleri ve hedef '
         'popülasyonlar aynı belge §1 (FIB-4 1,45/3,25 Sterling 2006 HIV/HCV; 1,30/2,67 Shah 2009 NAFLD; NFS −1,455/0,676 Angulo 2007 '
         'NAFLD; OST(A) Koh 2001 postmenopozal Asyalı kadınlar; OST erkek ≤ 3 Adler 2003; kadın OST < 2 eşiğinin birincil kaynağı '
         'BULUNAMADI). Hedef farkı: FIB-4/NFS biyopside ilerlemiş fibrozis için geliştirildi; projede hedef LSM ≥ 8 kPa.', '',
         '## 3c. OST erkeklerde ayrı', '',
         'Phase XLVI §4.2 + Phase XXX: erkek n = 1.193, pozitif **31** (küçük); model AUC 0,817 [0,730–0,886], −OST AUC 0,802 '
         '[0,713–0,878], ΔAUC +0,015 [−0,008–0,044] (GA 0\'ı içerir). Aynı duyarlılıkta (Recall 0,484 — modelin kilitli eşiği): FPR model '
         '0,102 / OST 0,066 (negatiflerde yalnız model 41 / yalnız OST 0, McNemar p < 0,001; şema OST lehine iyimser). Eşit yönlendirmede '
         'fark yok. OST\'nin özgün popülasyonu postmenopozal Asyalı kadınlardır (Koh 2001); erkek eşiği 181 erkeklik klinik örnekleme dayanır '
         '(Adler 2003). Erkekte güvenilir üstünlük sonucu çıkarılamaz.', '',
         '## 3d. UCI KAH: 4 merkezde 11 özniteliğin varlığı (yalnız uyumluluk raporu)', '']
    w = uc['missing_rate_wide']
    cents = list(next(iter(w.values())).keys())
    L.append(md_table(['öznitelik'] + [f'{c} eksik oranı' for c in cents],
                      [[f] + [f3(w[f][c]) for c in cents] for f in uc['features']]))
    s = uc['summary']
    L += ['', md_table(['merkez', 'dosya satırı', 'birebir yinelenen satır', 'pozitif (num > 0)', 'prevalans', '11 öznitelik eksiksiz', 'eksiksiz oranı',
                        'eksiksizde pozitif'],
                       [[c, v['n'], v['birebir_yinelenen_satir'], v['pozitif_num_gt0'], f3(v['prevalans']), v['eksiksiz_11'],
                         f3(v['eksiksiz_oran']), v['eksiksiz_pozitif']] for c, v in s.items()]), '',
          'Eksik = UCI "?" kodu + fizyolojik olmayan 0 (age/trestbps/chol/thalach; V2 kuralı `src/datasets/prepare.py` satır 91). '
          'Cleveland kategori kümesi dışında değer: 0. Ayrıntı (? ve 0 ayrı sütunlarda): `phase_xlix/results/uci_cad_feature_availability.csv`. '
          'Kaynak dosyalar `data/raw/uci_45/processed.*.data` (SHA256 JSON\'da; `phase_xxxix` yeniden indirmesiyle birebir aynı). '
          'Eksiksiz vaka sayıları Phase XLI teknik tekrarıyla aynıdır (Hungarian 95/68, VA 64/54). V2 işlenmiş tablolarda 293/199 satır '
          'vardır: `save_task` birebir yinelenen satırı düşürür. Switzerland\'da chol %100 eksik (0 kodlu) → model uygulanamaz; slope '
          'Hungarian\'da %64,6, VA\'da %51 eksik; VA\'da trestbps/chol/thalach/exang/oldpeak %26–29 eksik. Eksiksiz alt kümede prevalans '
          'merkezin tamamından yüksek (Hungarian 0,716 vs 0,361) → seçilim yanlılığı. Model yeniden eğitilmedi, skor üretilmedi.', '']
    return L


def main():
    df = build_model_results()
    # senaryo test sayıları: bu fazın pytest XML'inden işaret bilgisi yok; pytest --collect-only çıktısı logs/scenario_counts.txt
    sc = P49 / 'logs/scenario_counts.txt'
    if sc.exists():
        for ln in sc.read_text(encoding='utf8').splitlines():
            k, v = ln.split(' ', 1)
            SCEN[k] = v
    head = ['# Phase XLIX — Final rapor girdileri', '',
            'Derleme; **yeni test açılışı yok, model yeniden fit edilmedi, yeni tahmin üretilmedi.** Her sayı kaynak dosya yolu '
            '(+ satır/anahtar) ile verilir; repoda bulunamayan değer "BULUNAMADI". Üretim: `phase_xlix/scripts/build_inputs.py` '
            '(+ `af_overlap_check.py`, `uci_cad_availability.py`). Model olasılıkları klinik olasılık değildir '
            '(`clinical_probability_eligibility = false`). Araştırma hedefleri (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15) klinik onay kriteri değildir.',
            '', f'Kaynak SHA256: registry `{sha(REG_P)[:16]}…`, card_metrics `{sha(CM_P)[:16]}…`, app_config `{sha(CFG_P)[:16]}…`.', '',
            'İçindekiler: 1a modeller · 1b referans karşılaştırmaları · 1c AF ayrıntısı · 1d kirlenme/erratum · 1e veri setleri · '
            '1f yazılım · 1g asistan · 1h kaynakça · 2 ara rapor düzeltmeleri · 3 hoca maddeleri', '']
    body = head + sec_1a(df) + sec_1b() + sec_1c() + sec_1d() + sec_1e() + sec_1f() + sec_1g() + sec_1h() + sec_2() + sec_3()
    (P49 / 'final_report_inputs.md').write_text('\n'.join(body) + '\n', encoding='utf-8')
    print('model_results rows', len(df), '| md lines', len(body))


if __name__ == '__main__':
    main()
