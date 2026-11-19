"""README görselleri ve metrik tablosu — phase_xliii/registry/models.json ve AF için phase_xxxiii/results
(b_results.csv, b_rhythm_fpr.csv, a2_results.csv) dosyalarından; yeniden hesaplama YOK, değerler aynen okunur.
Çıktılar: docs/assets/model_metrics.png, docs/assets/metrics_table.md (tablo + dipnotlar).
Kullanım: python -B build_readme_assets.py"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

V2 = Path(__file__).resolve().parents[2]
OUT = V2 / 'docs' / 'assets'
OUT.mkdir(parents=True, exist_ok=True)
reg = json.loads((V2 / 'phase_xliii/registry/models.json').read_text(encoding='utf8'))
cfg = json.loads((V2 / 'app/backend/config/app_config.json').read_text(encoding='utf8'))
LBL = cfg['module_labels']
RANK = {'ana modül': 0, 'araştırma modülü': 1}
SHORT = {'af_S4_DEVICE': 'Atriyal fibrilasyon (EKG)', 'fibrosis_final': 'Karaciğer fibrozisi', 'osteo_final': 'Osteoporoz',
         'cad_DEVICE': 'Koroner arter hastalığı', 'dm_A': 'Diyabet A (form)', 'dm_B': 'Diyabet B (+lab)', 'anemia_LR16': 'Anemi',
         'copd_S4_DEVICE': 'KOAH', 'htn_M1': 'Hipertansiyon', 'ckd_A': 'Böbrek A (form)', 'ckd_B': 'Böbrek B (+lab)'}
TIER = {'internal_test': 'iç test', 'temporal': 'zamansal', 'external': 'dış doğrulama'}
MARK = {'iç test': 'o', 'zamansal': 's', 'dış doğrulama': '^', 'teknik tekrar*': 'D'}
# Etiket düzeltmesi (kullanıcı kararı): anemi dış katmanı farklı NHANES döngüleridir, bağımsız kurum doğrulaması değil.
LABEL_OVERRIDE = {('anemia_LR16', 'dış doğrulama'): 'farklı döngüler (aynı program; bağımsız kurum değil)'}
P33 = V2 / 'phase_xxxiii' / 'results'


def _csv(name):
    with open(P33 / name, encoding='utf8', newline='') as fh:
        return list(csv.DictReader(fh))


def _m(r, k):
    return dict(value=float(r[k]), ci95=[float(r[k + '_lo']), float(r[k + '_hi'])])


B_POOL = next(r for r in _csv('b_results.csv') if r['analiz'] == 'B — birincil' and r['skor'] == 'MODEL'
              and r['kapsam'].startswith('Havuz'))
RHY = {r['ritim']: r for r in _csv('b_rhythm_fpr.csv') if r['kapsam'].startswith('Havuz')}
A2_EXTRA = next(r for r in _csv('a2_results.csv') if r['analiz'] == 'A2 — birincil' and r['skor'] == 'MODEL'
                and r['kapsam'] == 'CPSC-Extra')
METRICS = [('precision', 'Precision', 0.70, '≥'), ('recall', 'Recall', 0.75, '≥'), ('fpr', 'FPR', 0.15, '≤'), ('auc', 'AUC', None, None)]

rows = []
for mid, e in sorted(((m, e) for m, e in reg['models'].items() if e.get('app_visible')),
                     key=lambda t: (RANK.get(LBL.get(t[0], LBL['_default']), 2), list(SHORT).index(t[0]))):
    for k, t in TIER.items():
        b = e['evidence'].get(k)
        if not b:
            continue
        if mid == 'cad_DEVICE' and k == 'external':              # alt kohortlar; registry: bağımsız dış doğrulama DEĞİL
            for sub, name in (('hungarian', 'Hungarian'), ('va', 'VA')):
                rows.append(dict(mid=mid, tier='teknik tekrar*', sub=name, src=b['source'], **{m: b[sub].get(m) for m, *_ in METRICS},
                                 n=b[sub].get('n'), n_pos=b[sub].get('n_pos')))
            continue
        rows.append(dict(mid=mid, tier=t, sub=None, src=b.get('source'), **{m: b.get(m) for m, *_ in METRICS},
                         n=b.get('n'), n_pos=b.get('n_pos'), label=LABEL_OVERRIDE.get((mid, t))))
        if mid == 'af_S4_DEVICE' and k == 'external':             # Phase XXXIII B: diğer ritimler negatif sınıfta
            rows.append(dict(mid=mid, tier='dış doğrulama', sub=None, label='diğer ritimler dahil (Phase XXXIII B)**',
                             src='Phase XXXIII B (Challenge 2021, 4 kaynak havuz, ikincil analiz; AF vs SR + diğer ritimler)',
                             precision=None, recall=_m(B_POOL, 'R'), fpr=_m(B_POOL, 'FPR'), auc=_m(B_POOL, 'AUC'),
                             n=int(B_POOL['n']), n_pos=int(B_POOL['pos'])))

val = lambda m: (m or {}).get('value') if isinstance(m, dict) else m
ci = lambda m: (m or {}).get('ci95') if isinstance(m, dict) else None

# ------------------------------------------------------------------ grafik
INK, MUTED, GRID, TARGET = '#1e293b', '#64748b', '#e2e8f0', '#b45309'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
fig, axes = plt.subplots(1, 4, figsize=(13, 0.36 * len(rows) + 1.6), sharey=True)
ys = list(range(len(rows)))[::-1]
def tier_text(r):
    return r.get('label') or (r['tier'] + (' ' + r['sub'] if r['sub'] else ''))


labels = [f"{SHORT[r['mid']]} — {tier_text(r)}" for r in rows]
for ax, (m, title, tgt, op) in zip(axes, METRICS):
    for y, r in zip(ys, rows):
        v, c = val(r[m]), ci(r[m])
        if v is None:
            ax.text(0.5, y, '—', ha='center', va='center', color=MUTED)
            continue
        if c:
            ax.plot(c, [y, y], color=INK, lw=1.4, solid_capstyle='round')
        ax.plot(v, y, MARK[r['tier']], color=INK, ms=8 if MARK[r['tier']] == '^' else 6.5, mec='white', mew=1.0)
    if tgt is not None:
        ax.axvline(tgt, color=TARGET, ls='--', lw=1)
        ax.text(tgt, len(rows) - 0.3, f'hedef {op} {tgt:.2f}'.replace('.', ','), color=TARGET, ha='center', fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_title(title, loc='left', fontsize=10, color=INK)
    ax.grid(axis='x', color=GRID)
    ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
# ana modül / araştırma / deneysel ayırıcıları
mods = [LBL.get(r['mid'], LBL['_default']) for r in rows]
for i in range(1, len(rows)):
    if mods[i] != mods[i - 1]:
        for ax in axes:
            ax.axhline(ys[i] + 0.5, color='#cbd5e1', lw=0.8)
axes[0].set_yticks(ys)
axes[0].set_yticklabels(labels, color=INK)
axes[0].set_ylim(-0.7, len(rows) - 0.1)
handles = [Line2D([], [], marker=mk, ls='', color=INK, mec='white', label=t) for t, mk in MARK.items()]
fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.035), ncol=4, frameon=False, fontsize=9,
           title='kanıt düzeyi (nokta = değer, çizgi = %95 GA; "—" = registry\'de değer yok)', title_fontsize=8)
fig.suptitle('Kilitli test metrikleri — donmuş model ve donmuş eşik (registry: phase_xliii/registry/models.json; '
             'AF B: phase_xxxiii/results)',
             x=0.01, ha='left', fontsize=11, color=INK)
fig.text(0.01, 0.005, '* CAD Hungarian/VA: düzeltilmiş teknik tekrar, bağımsız dış doğrulama DEĞİL (registry notu). '
         '** AF B: negatif sınıfta diğer ritimler de var. Ayırıcı çizgiler: ana modül / araştırma modülü / deneysel.',
         fontsize=7.5, color=MUTED)
fig.tight_layout(rect=(0, 0.11, 1, 0.96))
fig.savefig(OUT / 'model_metrics.png', dpi=150, facecolor='white')

# ------------------------------------------------------------------ tablo
f3 = lambda x: '—' if x is None else f'{x:.3f}'.replace('.', ',')
def cell(m):
    v, c = val(m), ci(m)
    return '—' if v is None else f3(v) + (f' [{f3(c[0])}–{f3(c[1])}]' if c else '')
def hedef(r):
    p, rc, fp = val(r['precision']), val(r['recall']), val(r['fpr'])
    if None in (p, rc, fp):
        return 'değerlendirilemez'
    return 'evet' if (p >= 0.70 and rc >= 0.75 and fp <= 0.15) else 'hayır'
lines = ['| model | modül | kanıt düzeyi | kaynak | n (pozitif) | Precision | Recall | FPR | AUC | üç hedef (nokta) |', '|---|---|---|---|---|---|---|---|---|---|']
for r in rows:
    lines.append(f"| {SHORT[r['mid']]} (`{r['mid']}`) | {LBL.get(r['mid'], LBL['_default'])} | {tier_text(r)} | "
                 f"{(r['src'] or 'BULUNAMADI').replace('|', '/')} | {r['n'] if r['n'] is not None else '—'} ({r['n_pos'] if r['n_pos'] is not None else '—'}) | "
                 f"{cell(r['precision'])} | {cell(r['recall'])} | {cell(r['fpr'])} | {cell(r['auc'])} | {hedef(r)} |")
pct = lambda r: f3(float(r['FPR'])) + f' [{f3(float(r["FPR_lo"]))}–{f3(float(r["FPR_hi"]))}]'
st, pvc = RHY['Sinüs taşikardisi'], RHY['PVC']
neg_extra = int(A2_EXTRA['TN']) + int(A2_EXTRA['FP'])
lines += ['', r'\* CAD Hungarian/VA satırları düzeltilmiş teknik tekrardır; kişiler önceden görülmüştür ve bu satırlar bağımsız '
          'dış doğrulama **değildir** (registry notu).',
          '', r'\*\* AF Phase XXXIII B: negatif sınıfta sinüs ritminin yanında diğer ritimler de vardır (havuz, ikincil analiz; '
          'kaynak `phase_xxxiii/results/b_results.csv`). '
          f'Ritim bazında FPR: sinüs taşikardisi {pct(st)} (n = {st["n"]}), PVC {pct(pvc)} (n = {pvc["n"]}) '
          '(`b_rhythm_fpr.csv`). Precision örneklem bileşimine bağlı olduğu için, registry\'nin A2 satırındaki kuralla '
          'aynı şekilde raporlanmaz.',
          '', f'AF dış doğrulama (A2) havuzunda CPSC-Extra kaynağında yalnız {neg_extra} negatif (SR) kayıt vardır; bu kaynak tek '
          f'başına yorumlanamaz (`a2_results.csv`: "{A2_EXTRA["yorum"]}").']
(OUT / 'metrics_table.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
print('rows', len(rows), '->', OUT)
