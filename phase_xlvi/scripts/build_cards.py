"""Phase XLVI — Görev 1: model kartları (TRIPOD+AI eşlemeli) ve TRIPOD+AI kontrol listesi.

Girdiler (salt okunur): phase_xliii/registry/models.json, phase_xliv/registry/input_schema_v2.json,
app/backend/config/app_config.json, results/card_metrics.json (extract_metrics.py), card_spec.py (kaynaklı metin),
alt grup CSV'leri (önceki fazlar), PTB-XL metadata (yalnız recording_date), data/refs/tripod_ai_table2.json.
Çıktılar: phase_xlvi/model_cards/<model_id>.md, phase_xlvi/tripod_ai_checklist.md; kopya app/docs/model_cards/.
Kullanım: python -X utf8 -B -I phase_xlvi/scripts/build_cards.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
P46 = V2 / 'phase_xlvi'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_spec import APP_ELIG, SPEC  # noqa: E402

REG = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
MODELS = REG['models']
SCH = json.loads((V2 / 'phase_xliv/registry/input_schema_v2.json').read_text(encoding='utf8'))
CFG = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
MET = json.loads((P46 / 'results/card_metrics.json').read_text(encoding='utf8'))
CHK = json.loads((P46 / 'results/card_metrics_check.json').read_text(encoding='utf8'))
Z = 1.959963984540054
ORDER = ['af_S4_DEVICE', 'fibrosis_final', 'osteo_final', 'cad_DEVICE', 'dm_A', 'dm_B', 'anemia_LR16', 'copd_S4_DEVICE',
         'htn_M1', 'ckd_A', 'ckd_B', 'mi_model', 'hf_S2_BASIC_LAB']


def f3(x):
    if x is None or (isinstance(x, float) and (math.isnan(x))):
        return '—'
    return f'{x:.3f}'.replace('.', ',')


def ci(t):
    return '—' if t is None else f'{f3(t[0])} [{f3(t[1])}–{f3(t[2])}]'


def wilson(k, n):
    if not n:
        return None
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [p, max(0, c - h), min(1, c + h)]


def module_label(mid):
    m = MODELS[mid]
    if not m['app_visible']:
        return 'uygulamada değil (registry_only)'
    return CFG['module_labels'].get(mid, CFG['module_labels']['_default'])


def ptbxl_dates():
    d = pd.read_csv(V2 / 'All_Disease_Improvement_Phase21/data/raw/ptbxl/ptbxl_database.csv', usecols=['recording_date'])
    s = pd.to_datetime(d.recording_date, errors='coerce')
    return f'{s.min():%Y-%m-%d} – {s.max():%Y-%m-%d} (PTB-XL `recording_date`, tüm veri tabanı; metadata)'


TIER_HEAD = {'internal_test': 'İç test', 'internal_test_subset': 'İç test',
             'temporal': 'Zamansal doğrulama', 'temporal_secondary': 'Zamansal doğrulama', 'temporal_subgroup': 'Zamansal doğrulama',
             'external': 'Dış doğrulama', 'external_source': 'Dış doğrulama', 'external_secondary': 'Dış doğrulama',
             'technical_replication': 'Teknik tekrar (bağımsız dış doğrulama DEĞİL)'}
EXT_HEAD = {'af_S4_DEVICE': 'Bağımsız dış doğrulama (farklı kaynaklar; donmuş model + kilitli pipeline)',
            'anemia_LR16': 'Farklı NHANES döngüleri — aynı program (bağımsız kurum doğrulaması DEĞİL)'}


def perf_tables(mid):
    rows = MET[mid]
    out, seen = [], []
    for r in rows:
        h = TIER_HEAD[r['tier']]
        if h == 'Dış doğrulama':
            h = EXT_HEAD.get(mid, h)
        if h not in seen:
            seen.append(h)
    for h in seen:
        out.append(f'#### {h}\n')
        out.append('| küme | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | NPV | AUC | üç hedef (nokta) |')
        out.append('|---|---|---|---|---|---|---|---|---|')
        for r in rows:
            hh = TIER_HEAD[r['tier']]
            hh = EXT_HEAD.get(mid, hh) if hh == 'Dış doğrulama' else hh
            if hh != h:
                continue
            prec_ok = r.get('precision_reportable', True)
            P = ci(r['precision']) if prec_ok else 'raporlanmaz (prevalansa bağlı)'
            tri = ('değerlendirilemez' if not prec_ok else
                   ('evet' if r['precision'][0] >= .70 and r['recall'][0] >= .75 and r['fpr'][0] <= .15 else 'hayır'))
            note = f" — {r['note']}" if r.get('note') and 'YORUMLANAMAZ' in str(r.get('note')) else ''
            NPV = ci(r['npv']) if prec_ok else 'raporlanmaz (prevalansa bağlı)'
            out.append(f"| {r['label']}{note} | {r['n']} ({r['n_pos']}) | {r['TP']} / {r['FP']} / {r['TN']} / {r['FN']} | {P} | "
                       f"{ci(r['recall'])} | {ci(r['fpr'])} | {NPV} | {ci(r['auc'])} | {tri} |")
        out.append('')
    src = sorted({(r['source'], r['source_sha256'][:12]) for r in rows})
    out.append('Kaynak dosyalar (kayıtlı sonuçlar; yeni tahmin yok): ' + '; '.join(f'`{s}` (SHA256 `{h}…`)' for s, h in src) + '.')
    npv_der = any(r['npv_source'].startswith('kayıtlı TN/FN') for r in rows)
    out.append('Oranlar Wilson %95 GA (kaynak dosyadaki değerler); AUC GA kaynak fazın bootstrap\'ı.'
               + (' NPV ve GA\'sı kayıtlı TN/FN sayılarından bu fazda hesaplandı (kaynakta NPV yoktu).' if npv_der else ''))
    rnd = [c for c in CHK['rounding'] if c['model'] == mid]
    if rnd:
        out.append('Not: ' + '; '.join(f"{c['metric']}: kaynak dosyada ham değer {c['raw']:.5f} → {f3(c['raw'])}; registry ve uygulama "
                                       f"{f3(c['registry'])} gösterir (kaynak rapordaki çift yuvarlama)" for c in rnd) + '.')
    return '\n'.join(out)


def delta_table(mid):
    rows = [(r['label'], d) for r in MET[mid] for d in r.get('delta', [])]
    if not rows:
        return 'BULUNAMADI'
    out = ['| küme | karşılaştırma | baseline AUC | ΔAUC [%95 GA] | not | kaynak |', '|---|---|---|---|---|---|']
    for lab, d in rows:
        out.append(f"| {lab} | {d['label']} | {f3(d['baseline_auc'])} | {ci(d['dAUC'])} | {d.get('note') or ''} | `{d['source']}` |")
    return '\n'.join(out) + '\n\nΔAUC = AUC(model) − AUC(baseline), aynı kişilerde paired bootstrap (kaynak fazın tohumu ve tekrar sayısı).'


def sub_rows(df, label_col, n_col='n', pos_col='pos'):
    out = []
    for _, r in df.iterrows():
        has = all(c in r and not pd.isna(r[c]) for c in ('TP', 'FP', 'TN', 'FN'))
        if has:
            P, R, F = wilson(r.TP, r.TP + r.FP), wilson(r.TP, r.TP + r.FN), wilson(r.FP, r.FP + r.TN)
            cnt = f"{int(r.TP)} / {int(r.FP)} / {int(r.TN)} / {int(r.FN)}"
        else:
            P, F, cnt = None, None, '—'
            R = [r.R, r.R_lo, r.R_hi] if 'R' in r and not pd.isna(r.R) else None
        auc = f3(r.AUC) if 'AUC' in r and not pd.isna(r.get('AUC')) else '—'
        n = int(r[n_col]) if n_col in r and not pd.isna(r[n_col]) else '—'
        pos = int(r[pos_col]) if pos_col in r and not pd.isna(r[pos_col]) else '—'
        out.append(f'| {r[label_col]} | {n} ({pos}) | {cnt} | {ci(P)} | {ci(R)} | {ci(F)} | {auc} |')
    return out


def subgroups(mid):
    sp = SPEC[mid]
    if 'subgroups_text' in sp:
        return sp['subgroups_text']
    key = sp['subgroups_src']
    head = ['| alt grup | n (pozitif) | TP / FP / TN / FN | Precision | Recall | FPR | AUC |', '|---|---|---|---|---|---|---|']
    if key == 'mi':
        src = 'phase_xxxviii/results/test_subgroups.csv'
        d = pd.read_csv(V2 / src)
        d = d[(d.kume == 'birincil_tum_test') & (d.model == 'MODEL')].copy()
        d['pos'] = d.pos.fillna(d.n_pos)
        rows = sub_rows(d, 'altgrup')
    elif key in ('dm_A', 'dm_B'):
        src = 'phase_xlii/results/test_subgroups.csv'
        d = pd.read_csv(V2 / src)
        d = d[d.kural == ('Model A' if key == 'dm_A' else 'Model B')].copy()
        d['alt'] = d.grup + ': ' + d.duzey.astype(str)
        rows = sub_rows(d, 'alt')
    elif key == 'htn':
        src = 'phase_xxxvii/results/test_subgroups.csv'
        d = pd.read_csv(V2 / src)
        rows = sub_rows(d[d.model == 'M1'], 'altgrup')
    elif key in ('ckd_A', 'ckd_B'):
        src = 'phase_xxxv/results/test_subgroups_age.csv'
        d = pd.read_csv(V2 / src)
        m = 'Model A (birincil)' if key == 'ckd_A' else 'Model B (birincil)'
        rows = sub_rows(d[d.karar == m], 'alt_grup')
        src2 = 'phase_xxxv/results/test_recall_by_positive_type.csv'
        d2 = pd.read_csv(V2 / src2)
        cols = list(d2.columns)
        lab = cols[0]
        dd = d2[d2[cols[1]] == m] if len(cols) > 1 else d2
        for _, r in dd.iterrows():
            rr = [r[c] for c in cols]
            rows.append(f'| {rr[0]} (yalnız Recall) | — ({int(r.iloc[2])}) | — | — | {f3(r.R)} [{f3(r.R_lo)}–{f3(r.R_hi)}] | — | — |'
                        if 'R_lo' in cols else f'| {rr[0]} | — | — | — | {rr} | — | — |')
        src = f'{src}, {src2}'
    elif key == 'fibrosis':
        src = 'phase_xxxi/results/fibrosis_test_results.csv'
        d = pd.read_csv(V2 / src)
        d = d[d.analiz.isin(['female: birincil tek eşik', 'male: birincil tek eşik', 'Duyarlılık: LSM≥12 (aynı model/eşik)',
                             'Duyarlılık: açlık alt örneklemi'])]
        rows = sub_rows(d, 'analiz')
    elif key == 'osteo':
        return ('Kadın ve erkek sonuçları performans tablosunda ayrı satırlardır (kilitli eşik; Phase XXX). Erkekte Recall 0,484, '
                'P 0,113. OST karşılaştırması cinsiyete göre: `phase_xlvi/01_reference_score_analysis.md` §4.')
    elif key == 'anemia':
        src = 'Clinical_Optimization_Phase25/results/anemia_subgroup_metrics.csv'
        d = pd.read_csv(V2 / src)
        d = d[d.model_role == 'MATCHED_SCHEMA_LR'].rename(columns=dict(tp='TP', fp='FP', tn='TN', fn='FN', positive='pos', roc_auc='AUC'))
        rows = sub_rows(d, 'subgroup')
        rows.append('| dış: döngü başına | — | — | — | — | — | performans tablosu |')
    else:
        return 'BULUNAMADI'
    return ('Tanımlayıcı (önceden tanımlı karar kuralı yok; çoklu karşılaştırma düzeltmesi yok). Kilitli eşik.\n\n'
            + '\n'.join(head + rows) + f'\n\nKaynak: `{src}`. Oran GA\'ları kayıtlı TP/FP/TN/FN sayılarından Wilson ile hesaplandı '
            '(sayımlar yoksa kaynak dosyadaki değer).')


def features(mid):
    m = MODELS[mid]
    ch = {c['feature']: c for c in SCH['changes_from_v1'] if c.get('model') == mid}
    out = ['| # | öznitelik | tip | birim | izin verilen aralık / kategoriler | uygulama alanı | dönüşüm (şema v2) |', '|---|---|---|---|---|---|---|']
    for i, f in enumerate(m['features'], 1):
        rng = f.get('allowed_range') or f.get('allowed_values')
        rng = '—' if rng is None else (f'{rng[0]} – {rng[1]}' if f['type'] == 'numeric' else ', '.join(map(str, rng)))
        tr = f.get('transform', '—')
        if f['name'] in ch:
            tr = f"{ch[f['name']]['new_transform']} (v1: {ch[f['name']]['old_transform']})"
        out.append(f"| {i} | `{f['name']}` | {f['type']} | {f.get('unit', '—')} | {rng} | `{f.get('input_field', '—')}` | `{tr}` |")
    out.append(f"\nSıra ve kategoriler: `{m['feature_order_source']}` (registry_check ile model nesnesine karşı doğrulandı, Phase XLIII/XLIV). "
               'Öznitelik ölçüm yöntemi ve kaynağı: NHANES modellerinde ilgili döngünün CDC veri sözlüğü; EKG modellerinde ECGDeli; '
               'CAD\'de UCI kodları; KY\'de kaynak veri seti. Aralıklar fiziksel makullük sınırıdır, eğitim kapsamı değildir.')
    return '\n'.join(out)


def samples(mid):
    out = ['| küme | n | pozitif | kaynak |', '|---|---|---|---|']
    for lab, n, pos, src in SPEC[mid]['samples']:
        out.append(f'| {lab} | {n} | {pos} | `{src}` |' if '/' in src or '.' in src else f'| {lab} | {n} | {pos} | {src} |')
    return '\n'.join(out) + f"\n\n{SPEC[mid]['sample_size_note']}"


def thresholds(mid):
    t = MODELS[mid]['thresholds']
    sec = ', '.join(f'{k} = {v:.4f}' for k, v in t['secondary'].items()) or 'yok'
    return (f"- Birincil (uygulamada kullanılan) eşik: **{t['primary']['value']:.10f}** (`{t['source']}`); karar `skor ≥ eşik` → "
            f"\"eşik üstü\" (araştırma sınıflaması). Eşik değeri uygulama yanıtında gösterilmez.\n"
            f"- Registry kural metni: {t['primary']['rule']}\n- Seçim kuralı (kaynak): {SPEC[mid]['threshold']}\n- İkincil eşikler (yalnız raporlama): {sec}")


def card(mid):
    m, sp = MODELS[mid], SPEC[mid]
    ev = m['evidence']
    data_rows = '\n'.join(f'| {a} | {b} | {c} |' for a, b, c in sp['data'])
    dates = ''
    if mid in ('af_S4_DEVICE', 'mi_model'):
        dates = f'\n\nPTB-XL kayıt tarihleri: {ptbxl_dates()}.'
    lim = '\n'.join(f'- {x}' for x in m['limitations'] + sp.get('extra_limits', []))
    tri = TRIPOD_STATUS(mid)
    title = f"# Model kartı — {m['disease']} (`{mid}`)"
    return f"""{title}

> Araştırma prototipi. Model **mevcut durumu** sınıflandırır; gelecek risk tahmini değildir. Skor klinik olasılık değildir
> (`clinical_probability_eligibility = false`). Kanıt düzeyleri ayrı tablolardadır; CV sonuçları kanıt olarak kullanılmaz.
> TRIPOD+AI (Collins ve ark., BMJ 2024;385:e078378, doi:10.1136/bmj-2023-078378) maddelerine eşleme her başlıkta [köşeli
> parantez] içindedir. Üretim: `phase_xlvi/scripts/build_cards.py` (Phase XLVI). Bulunamayan bilgi: BULUNAMADI.

## 0. Özet

| alan | değer |
|---|---|
| model kimliği | `{mid}` ({m['role']}) |
| hastalık / hedef | {m['disease']} |
| uygulamadaki durum | {module_label(mid)}; mod `{m['app_mode']}`; `app_visible = {str(m['app_visible']).lower()}` |
| model ailesi | {m['family']} |
| en yüksek kanıt düzeyi | {ev['highest_tier']} |
| model dosyası | `{m['model_file']['path']}` (SHA256 `{m['model_file']['sha256'][:16]}…`) |
| çalışma ortamı | Python {m['runtime']['python']}; sklearn {m['runtime']['packages']['sklearn']}, lightgbm {m['runtime']['packages']['lightgbm']}; kayıtlı venv `{m['runtime']['required_venv']}` (uygulama venv'inde bit düzeyinde eşdeğer, Phase XLIV) |
| köken fazı | {m['phase_of_origin']} |

## 1. Amaç ve kullanım bağlamı [3a, 3b, 4]

{sp['purpose']}

- **Tanısal / prognostik:** tanısal (mevcut durum). Zaman ufku yok: hedef aynı ziyaret/kayıttaki ölçümdür.
- **Hedeflenen kullanıcı:** araştırmacılar ve eğitim. Klinik karar desteği olarak onaylı değildir.
- **Sağlık eşitsizlikleri [3c]:** kaynak veride sosyodemografik eşitsizlik analizi yapılmadı (BULUNAMADI); alt grup sonuçları §14.

## 2. Veri kaynağı ve sürümü [5a, 5b]

| rol | kaynak / sürüm / DOI | not |
|---|---|---|
{data_rows}{dates}

NHANES döngü yılları CDC döngü adlarıdır (ör. G = 2011–2012, L = Ağustos 2021–Ağustos 2023, P = 2017–Mart 2020).

## 3. Ortam ve uygunluk ölçütleri [6a, 6b, 6c]

- **Ortam:** {sp['setting']}
- **Popülasyon (registry):** {m['population']}
- **Uygunluk (kaynak):** {sp['eligibility']}
- **Tedaviler [6c]:** hedefi değiştirebilecek tedaviler uygunluk/hedef tanımında ele alındı (registry popülasyon metni); başka
  tedavi ayarlaması yapılmadı.

## 4. Hedef tanımı ve ölçüm yöntemi [8a, 8b, 8c]

- **Hedef (registry):** {m['target_definition']}
- **Ölçüm:** {sp['target_method']}
- **Körleme [8c]:** raporlanmadı. Hedef ölçümleri modelden önce ve modelden bağımsız yapılmıştır (ikincil veri).
- Hedefi tanımlayan ölçüm veya doğrudan türevi girdi değildir (proje kuralı; registry feature listesi).

## 5. Öznitelikler [9a, 9b, 9c, 12b]

{features(mid)}

## 6. Örnek sayıları [10, 20a, 21]

{samples(mid)}

## 7. Eksik veri [11]

- **Geliştirme:** {sp['missing']}
- **Uygulama (registry kuralı):** {m['missing_input_rule']}
- Dondurulmuş imputer uygulamada kullanılmaz; yapısal boşluklar (ör. erkekte menopoz soruları) eğitimdeki kuralla işlenir
  (şema v2 `policy.structural_blanks`).

## 8. Bölme yöntemi [12a, 16]

{sp['split']}

## 9. Model ailesi, seçim kuralı ve sınıf dengesizliği [12c, 13]

- **Seçim:** {sp['family']}
- **Sınıf dengesizliği:** {sp['imbalance']}

## 10. Karar eşiği ve seçim kuralı [15]

{thresholds(mid)}

## 11. Kalibrasyon [12e]

- Registry: {m['calibration']['status']}.
- {sp['calibration']}

## 12. Performans — kanıt düzeyine göre ayrı tablolar [23a, 12e]

Değerler donmuş model ve donmuş eşikte, kilitli tek seferlik testlerdir. CV (aday) sonuçları bu tablolarda yoktur.

{perf_tables(mid)}

**Araştırma hedefleri** (P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15; klinik onay kriteri değildir). Registry notu: {ev['research_target_note']}

## 13. Klinik baseline karşılaştırması (ΔAUC) [12e, 23a]

{delta_table(mid)}

## 14. Alt gruplar [14, 23a, 23b]

{subgroups(mid)}

Adalet (fairness) için özel bir yöntem uygulanmadı; yalnız alt grup performansı raporlandı.

## 15. Sınırlılıklar [26]

{lim}

## 16. Uygulama modu, ABSTAIN ve NOT_APPLICABLE kuralları [27a, 27b, 12g]

- **Mod:** `{m['app_mode']}` — {m.get('app_mode_reason', '')}. Modül etiketi: {module_label(mid)}.
- **Uygulanabilirlik:** {m.get('app_feasibility', '—')}
- **Kurallar:** {APP_ELIG[mid]}
- Karar yalnız "eşik üstü / eşik altı — araştırma sınıflaması"dır; olasılık ve eşik değeri yanıtta yoktur. Model dosyası SHA256'sı
  yüklemeden önce registry ile doğrulanır; uyuşmazlıkta model devre dışı kalır (`/health`).
- Tahmin hesaplama: `app/backend/healthrisk_api/` (registry feature sırası → `predict_proba` → donmuş eşik); API: `app/docs/api.md`.
- Kullanıcı etkileşimi [27b]: form/EKG yükleme; birim seçimi; uzmanlık gerektiren girdiler (spirometri, efor testi, laboratuvar)
  sağlık profesyonelince ölçülmelidir.

## 17. Etik, gizlilik ve açık bilim [17, 18a–f, 19]

- **Etik [17]:** proje, kamuya açık ve kimliksizleştirilmiş verinin ikincil analizidir. Veri toplamanın etik onayı veri
  sağlayıcısınındır (kaynak belgelerinde). Bu proje için ayrı bir etik kurul onayı: BULUNAMADI.
- **Gizlilik (uygulama):** istek gövdesi ve sağlık verisi loglanmaz ve diske yazılmaz; tarayıcıda kalıcı saklama yok; sunucu yalnız
  127.0.0.1 (Phase XLIV `test_privacy.py`, Phase XLV Playwright gizlilik testleri).
- **Fon [18a] / çıkar çatışması [18b]:** BULUNAMADI.
- **Protokol [18c]:** kilitli protokol ve model kilidi dosyaları kaynak fazda (bkz. §18). **Kayıt [18d]:** çalışma kaydı yapılmadı.
- **Veri paylaşımı [18e]:** veriler kaynaklarından açık erişimle alınabilir (lisanslar README). **Kod [18f]:** uygulama ve registry
  GitHub deposunda; faz betiklerinin tamamı depoda değildir.
- **Hasta/halk katılımı [19]:** yapılmadı.

## 18. Kaynak dosyalar

{chr(10).join(f'- `{s}`' for s in sp['sources'])}
- `phase_xliii/registry/models.json` (registry), `phase_xliv/registry/input_schema_v2.json` (şema v2)
- `phase_xlvi/results/card_metrics.json` (bu karttaki sayıların çıkarımı; registry ile çapraz kontrol: `card_metrics_check.json`)

## TRIPOD+AI kapsamı (özet)

{tri}
"""


# ------------------------------------------------------------------ TRIPOD+AI durumları
SEC = {'1': 'başlık', '2': '§0', '3a': '§1', '3b': '§1', '3c': '§1', '4': '§1', '5a': '§2', '5b': '§2', '6a': '§3', '6b': '§3',
       '6c': '§3', '7': '§7', '8a': '§4', '8b': '§4', '8c': '§4', '9a': '§5', '9b': '§5', '9c': '§5', '10': '§6', '11': '§7',
       '12a': '§8', '12b': '§5', '12c': '§9', '12d': '§12/§14', '12e': '§11–13', '12f': '§11', '12g': '§16', '13': '§9',
       '14': '§14', '15': '§10', '16': '§8', '17': '§17', '18a': '§17', '18b': '§17', '18c': '§17–18', '18d': '§17', '18e': '§17',
       '18f': '§17', '19': '§17', '20a': '§6', '20b': '§3/§18', '20c': '§2', '21': '§6', '22': '§0/§5', '23a': '§12–14',
       '23b': '§12/§14', '24': '§11', '25': '§12/§15', '26': '§15', '27a': '§16', '27b': '§16', '27c': '§15'}
ECG = {'af_S4_DEVICE', 'mi_model'}
MULTI = {'af_S4_DEVICE', 'anemia_LR16', 'dm_A', 'dm_B', 'copd_S4_DEVICE', 'cad_DEVICE'}
NODATES = {'cad_DEVICE', 'hf_S2_BASIC_LAB'}


def status(mid, item):
    """(durum, gerekçe). karşılandı / kısmen / yok / uygulanamaz."""
    s = {'1': ('kısmen', 'kart başlığı model ve hedefi adlandırır; çalışma raporu değildir'),
         '2': ('kısmen', 'özet tablo; TRIPOD+AI for Abstracts uygulanmadı'),
         '3a': ('karşılandı', ''), '3b': ('karşılandı', ''), '3c': ('yok', 'eşitsizlik analizi yok'), '4': ('karşılandı', ''),
         '5a': ('karşılandı', ''),
         '5b': ('kısmen', 'veri toplama tarihleri BULUNAMADI') if mid in NODATES else ('karşılandı', 'döngü yılları / kayıt tarihleri'),
         '6a': ('karşılandı', ''), '6b': ('karşılandı', ''), '6c': ('kısmen', 'yalnız uygunluk/hedef içinde'),
         '7': ('kısmen', 'ön işleme pipeline\'da; sosyodemografik gruplar arası karşılaştırma yok'),
         '8a': ('karşılandı', ''),
         '8b': ('kısmen', 'insan doğrulamalı okuma; değerlendirici demografisi BULUNAMADI') if mid in ECG else
               (('yok', 'BULUNAMADI') if mid in ('cad_DEVICE', 'hf_S2_BASIC_LAB') else ('uygulanamaz', 'objektif ölçüm (lab/cihaz)')),
         '8c': ('kısmen', 'körleme raporlanmadı; ikincil veri'),
         '9a': ('kısmen', 'panel tanımı protokolde; ön seçim gerekçesi kısmen'), '9b': ('karşılandı', ''),
         '9c': ('yok', 'klinik değerlendirici bilgisi yok') if mid == 'cad_DEVICE' else ('uygulanamaz', 'otomatik/objektif ya da öz bildirim'),
         '10': ('kısmen', 'sayılar var; örneklem büyüklüğü hesabı yok'), '11': ('karşılandı', ''), '12a': ('karşılandı', ''),
         '12b': ('kısmen', 'dönüşümler listelendi; ölçekleme pipeline içinde'), '12c': ('karşılandı', ''),
         '12d': ('kısmen', 'kaynak/döngü başına sonuç') if mid in MULTI else ('yok', 'tek kaynak'),
         '12e': ('karşılandı', ''), '12f': ('karşılandı', 'güncelleme yok (donmuş model)'), '12g': ('karşılandı', ''),
         '13': ('karşılandı', ''), '14': ('kısmen', 'yalnız alt grup raporu'), '15': ('karşılandı', ''),
         '16': ('karşılandı', '') if (MODELS[mid]['evidence'].get('external') or MODELS[mid]['evidence'].get('temporal')) else ('kısmen', 'yalnız iç test'),
         '17': ('kısmen', 'proje etik onayı BULUNAMADI'), '18a': ('yok', 'BULUNAMADI'), '18b': ('yok', 'BULUNAMADI'),
         '18c': ('kısmen', 'kök V2: seçim kilidi, protokol dosyası yok') if mid == 'cad_DEVICE' else ('karşılandı', 'kilitli protokol dosyası'),
         '18d': ('yok', 'kayıt yok'), '18e': ('karşılandı', 'açık kaynak veri'), '18f': ('kısmen', 'uygulama kodu açık; faz betiklerinin tamamı depoda değil'),
         '19': ('yok', ''), '20a': ('kısmen', 'sayılar; akış tablosu kaynak fazda'),
         '20b': ('kısmen', 'karakteristikler kaynak faz raporunda'), '20c': ('kısmen', 'yalnız seçilmiş karşılaştırmalar') if mid in ('af_S4_DEVICE', 'htn_M1') else ('yok', ''),
         '21': ('karşılandı', ''), '22': ('kısmen', 'donmuş nesne + SHA; açık formül yok'), '23a': ('karşılandı', ''),
         '23b': ('kısmen', 'kaynak/döngü başına') if mid in MULTI else ('yok', 'tek kaynak'), '24': ('uygulanamaz', 'güncelleme yok'),
         '25': ('kısmen', 'kart; tartışma bölümü değil'), '26': ('karşılandı', ''),
         '27a': ('karşılandı', 'ABSTAIN kuralları') if MODELS[mid]['app_visible'] else ('kısmen', 'uygulamada değil'),
         '27b': ('karşılandı', '') if MODELS[mid]['app_visible'] else ('kısmen', 'uygulamada değil'),
         '27c': ('kısmen', 'açık noktalar sınırlılıklarda')}
    return s[item]


def items():
    rows = json.loads((P46 / 'data/refs/tripod_ai_table2.json').read_text(encoding='utf8'))
    out, sec = [], None
    for r in rows[1:]:
        if len(r) == 1:
            sec = r[0]
            continue
        if len(r) == 4:
            topic, it, de, txt = r
        else:
            it, de, txt = r
            topic = out[-1][1] if out else ''
        out.append((sec, topic, it, de, txt))
    return out


def TRIPOD_STATUS(mid):
    c = {'karşılandı': 0, 'kısmen': 0, 'yok': 0, 'uygulanamaz': 0}
    for _, _, it, _, _ in items():
        c[status(mid, it)[0]] += 1
    return (f"{sum(c.values())} madde: karşılandı {c['karşılandı']}, kısmen {c['kısmen']}, yok {c['yok']}, uygulanamaz "
            f"{c['uygulanamaz']}. Madde madde durum: `phase_xlvi/tripod_ai_checklist.md`.")


def checklist():
    its = items()
    head = '| bölüm | madde | D/E | TRIPOD+AI maddesi (kısaltılmış) | kartta | ' + ' | '.join(f'`{m}`' for m in ORDER) + ' |'
    sep = '|' + '---|' * (5 + len(ORDER))
    code = {'karşılandı': '✔', 'kısmen': '◐', 'yok': '✘', 'uygulanamaz': '—'}
    lines = [head, sep]
    for sec, topic, it, de, txt in its:
        t = txt if len(txt) <= 110 else txt[:107] + '…'
        lines.append(f'| {topic} | {it} | {de} | {t} | {SEC[it]} | ' + ' | '.join(code[status(m, it)[0]] for m in ORDER) + ' |')
    notes = []
    for _, _, it, _, _ in its:
        reasons = {}
        for m in ORDER:
            st, why = status(m, it)
            if st != 'karşılandı' and why:
                reasons.setdefault(f'{st}: {why}', []).append(m)
        if reasons:
            notes.append(f'- **{it}** — ' + '; '.join(f"{k} ({', '.join(v) if len(v) < len(ORDER) else 'tüm modeller'})" for k, v in reasons.items()))
    tot = {m: {k: 0 for k in code} for m in ORDER}
    for _, _, it, _, _ in its:
        for m in ORDER:
            tot[m][status(m, it)[0]] += 1
    summ = ['| model | karşılandı | kısmen | yok | uygulanamaz |', '|---|---|---|---|---|'] + \
           [f"| `{m}` | {v['karşılandı']} | {v['kısmen']} | {v['yok']} | {v['uygulanamaz']} |" for m, v in tot.items()]
    return f"""# Phase XLVI — TRIPOD+AI kontrol listesi × model

Kaynak: Collins GS ve ark. TRIPOD+AI statement. *BMJ* 2024;385:e078378. doi:10.1136/bmj-2023-078378 (PMID 38626948).
Madde metinleri makalenin Tablo 2'sinden (Europe PMC tam metni, CC BY; `data/refs/collins2024_full.xml`,
`data/refs/tripod_ai_table2.json`) otomatik alınmıştır; tabloda kısaltıldı. D = geliştirme, E = değerlendirme.

Değerlendirme birimi: model kartı (`model_cards/<model_id>.md`) + kartın gösterdiği kaynak faz dosyaları. Kartlar bir dergi
makalesi değildir; "başlık", "özet" ve "tartışma" maddeleri kart biçimine göre kısmen karşılanır. Durumlar
`scripts/build_cards.py :: status()` içinde kural olarak tanımlıdır.

Simgeler: ✔ karşılandı · ◐ kısmen · ✘ yok · — uygulanamaz.

## Özet

{chr(10).join(summ)}

## Madde × model

{chr(10).join(lines)}

## Tam/olmayan maddelerin gerekçeleri

{chr(10).join(notes)}

## Başlıca eksikler (tüm modeller)

- **3c, 14:** sağlık eşitsizlikleri ve adalet için yöntem yok; yalnız alt grup performansı.
- **10:** örneklem büyüklüğü hesabı yapılmadı; KOAH, KY ve CAD'de test kümeleri çok küçük.
- **17, 18a, 18b, 18d, 19:** proje düzeyinde etik onay, fon, çıkar beyanı, çalışma kaydı ve hasta/halk katılımı BULUNAMADI.
- **22:** model açık formül olarak değil, donmuş nesne (joblib + SHA256) olarak paylaşılır.
"""


def main():
    od = P46 / 'model_cards'
    ad = V2 / 'app/docs/model_cards'
    od.mkdir(exist_ok=True)
    ad.mkdir(parents=True, exist_ok=True)
    assert set(ORDER) == set(MODELS) == set(SPEC) == set(MET)
    idx = ['# Model kartları\n', 'Phase XLVI, TRIPOD+AI eşlemeli. Üretim: `phase_xlvi/scripts/build_cards.py`.\n',
           '| model | hastalık | uygulamadaki durum | en yüksek kanıt |', '|---|---|---|---|']
    for mid in ORDER:
        txt = card(mid)
        (od / f'{mid}.md').write_text(txt, encoding='utf8')
        shutil.copyfile(od / f'{mid}.md', ad / f'{mid}.md')
        idx.append(f"| [`{mid}`]({mid}.md) | {MODELS[mid]['disease']} | {module_label(mid)} | {MODELS[mid]['evidence']['highest_tier']} |")
    idx.append('\nTRIPOD+AI kontrol listesi: `phase_xlvi/tripod_ai_checklist.md`.')
    (od / 'README.md').write_text('\n'.join(idx) + '\n', encoding='utf8')
    shutil.copyfile(od / 'README.md', ad / 'README.md')
    (P46 / 'tripod_ai_checklist.md').write_text(checklist(), encoding='utf8')
    print('kart', len(ORDER), 'kontrol listesi maddesi', len(items()))


if __name__ == '__main__':
    main()
