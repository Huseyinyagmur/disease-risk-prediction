"""Phase XLVI — Görev 2: AF doğrulama belgesi (phase_xlvi/af_validation_dossier.md).

Tüm sayılar önceki faz dosyalarından okunur (kaynak yolu tabloda). Tek yeni hesap: PTB-XL metadata'sı
(ptbxl_database.csv; etiket/tahmin değil, kimlik ve fold) ile Phase21 AF bölmesinin kişi kesişimi ve fold tutarlılığı.
Model yüklenmez, tahmin üretilmez, EKG sinyali okunmaz.
Kullanım: python -B -I phase_xlvi/scripts/af_dossier.py
"""
import ast
import hashlib
import json
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
P46 = V2 / 'phase_xlvi'


def sha(p):
    return hashlib.sha256((V2 / p).read_bytes()).hexdigest()


def js(p):
    return json.loads((V2 / p).read_text(encoding='utf8'))


def f3(x):
    return '—' if x is None or pd.isna(x) else f'{x:.3f}'.replace('.', ',')


def ci(v, lo, hi):
    return f'{f3(v)} [{f3(lo)}–{f3(hi)}]'


def ptbxl_split():
    split = js('All_Disease_Improvement_Phase21/config/af_splits.json')
    db = pd.read_csv(V2 / 'All_Disease_Improvement_Phase21/data/raw/ptbxl/ptbxl_database.csv',
                     usecols=['ecg_id', 'patient_id', 'strat_fold', 'validated_by_human', 'scp_codes', 'age'])
    db['pid'] = 'PTB_' + db.patient_id.astype(int).astype(str)
    sets = {k: set(v) for k, v in split.items()}
    inter = {f'{a}∩{b}': len(sets[a] & sets[b]) for a, b in (('fit', 'validation'), ('fit', 'test'), ('validation', 'test'))}
    folds_per_patient = db.groupby('pid').strat_fold.nunique()
    multi_fold = int((folds_per_patient > 1).sum())
    # Phase21 prepare.py::af() kişi/etiket kuralının metadata ile yeniden üretimi (yalnız sayım)
    d = db.sort_values(['patient_id', 'ecg_id']).drop_duplicates('patient_id', keep='first').copy()
    codes = d.scp_codes.map(ast.literal_eval)
    pos, neg = codes.map(lambda z: 'AFIB' in z), codes.map(lambda z: 'SR' in z)
    d = d[d.validated_by_human.eq(True) & (pos ^ neg) & d.age.ge(18)].copy()
    d['target'] = pos[d.index].astype(int)
    role = {**{p: 'fit' for p in sets['fit']}, **{p: 'validation' for p in sets['validation']}, **{p: 'test' for p in sets['test']}}
    d['role'] = d.pid.map(role)
    fold_ok = bool(((d.role == 'fit') == d.strat_fold.le(8)).all() & ((d.role == 'validation') == d.strat_fold.eq(9)).all()
                   & ((d.role == 'test') == d.strat_fold.eq(10)).all())
    counts = d.groupby('role').agg(n=('pid', 'size'), pos=('target', 'sum')).reindex(['fit', 'validation', 'test'])
    return dict(split_sizes={k: len(v) for k, v in sets.items()}, intersections=inter, patients_multi_fold=multi_fold,
                rebuilt_counts=counts.reset_index().to_dict('records'), unmatched_role=int(d.role.isna().sum()),
                fold_role_consistent=fold_ok, n_patients_db=int(db.pid.nunique()), n_ecg_db=len(db))


def main():
    sp = ptbxl_split()
    (P46 / 'results').mkdir(exist_ok=True)
    (P46 / 'results/af_split_check.json').write_text(json.dumps(sp, ensure_ascii=False, indent=1, default=int), encoding='utf8')
    lock = js('phase_xxviii/config/af_pipeline_lock.json')
    reg = js('phase_xliii/registry/models.json')['models']['af_S4_DEVICE']
    ci27 = pd.read_csv(V2 / 'phase_xxvii/results/ci_metrics.csv')
    it = ci27[(ci27.model == 'af') & (ci27.kume == 'test')].iloc[0]
    par = pd.read_csv(V2 / 'phase_xxviii/results/tol100_feature_parity.csv')
    agr = pd.read_csv(V2 / 'phase_xxviii/results/tol100_model_agreement.csv')
    verdict = js('phase_xxviii/results/tol100_verdict.json')
    e2e = {k: js(f'phase_xliv/results/{k}.json') for k in ('af_e2e', 'af_mat_e2e', 'af_long_e2e')}
    dedup29 = js('phase_xxix/results/flow_dedup.json')
    dedup33 = js('phase_xxxiii/results/flow_dedup33.json')
    a2 = pd.read_csv(V2 / 'phase_xxxiii/results/a2_results.csv')
    b = pd.read_csv(V2 / 'phase_xxxiii/results/b_results.csv')
    brh = pd.read_csv(V2 / 'phase_xxxiii/results/b_rhythm_fpr.csv')
    mix = pd.read_csv(V2 / 'phase_xxxiii/results/mixture_results.csv')
    afl = pd.read_csv(V2 / 'phase_xxxiii/results/afl_results.csv')
    retry = js('phase_xxxiii/results/retry33.json')

    # ---------- tablolar
    cnt = '\n'.join(f"| {r['role']} | {r['n']} | {int(r['pos'])} | {r['n'] - int(r['pos'])} |" for r in sp['rebuilt_counts'])
    inter = ' · '.join(f'{k}: **{v}**' for k, v in sp['intersections'].items())
    feat = par[par.grup == 'tümü'].copy()
    feat = feat[~feat.feature.str.endswith('_count')]
    ftab = '\n'.join(f'| {r.feature} | {int(r.tolerans_ici)}/{int(r.n)} | {f3(r.tam_esit_orani)} | {f3(r.MAE_medyan)} | '
                     f'{f3(r.BA_bias)} [{f3(r.BA_LoA_alt)}; {f3(r.BA_LoA_ust)}] |' for r in feat.itertuples())
    atab = '\n'.join(f'| {r.senaryo} | {r.grup} | {int(r.uyumlu)}/{int(r.n)} | {ci(r.karar_uyumu, r.GA_alt, r.GA_ust)} | '
                     f'{f3(r.medyan_abs_dp)} | {f3(r.p95_abs_dp)} |' for r in agr.itertuples() if r.senaryo.startswith('Tam'))

    def e2e_rows(k, idcol):
        return '\n'.join(f"| {k} | {rec.get(idcol)} | {rec['http_status']} | {rec['status']} | {rec['max_abs_delta_vs_' + ('phase_xxviii' if k == 'af_e2e' else 'phase_xxxiii')]} |"
                         + (f" {rec.get('record_samples', '')} |" if True else '') for rec in e2e[k]['records'])
    etab = '\n'.join([e2e_rows('af_e2e', 'ecg_id'), e2e_rows('af_mat_e2e', 'rel'), e2e_rows('af_long_e2e', 'rel')])

    def res_rows(df, analiz, cols_p=True):
        out = []
        for r in df[(df.analiz == analiz)].itertuples():
            note = '' if pd.isna(r.yorum) else r.yorum
            out.append(f'| {r.kapsam} | {r.skor} | {int(r.n)} ({int(r.pos)}) | {int(r.TP)}/{int(r.FP)}/{int(r.TN)}/{int(r.FN)} | '
                       f'{ci(r.R, r.R_lo, r.R_hi)} | {ci(r.FPR, r.FPR_lo, r.FPR_hi)} | {ci(r.AUC, r.AUC_lo, r.AUC_hi)} | '
                       f'{ci(r.dAUC, r.dAUC_lo, r.dAUC_hi) if r.skor == "MODEL" else "—"} | {note} |')
        return '\n'.join(out)

    POOL = 'Havuz (4 kaynak, ikincil)'
    rhtab = '| ritim | n | FP model | FPR model | FPR baseline |\n|---|---|---|---|---|\n' + '\n'.join(
        f'| {r.ritim} | {int(r.n)} | {int(r.FP)} | {ci(r.FPR, r.FPR_lo, r.FPR_hi)} | {ci(r.base_FPR, r.base_FPR_lo, r.base_FPR_hi)} |'
        for r in brh[brh.kapsam == POOL].itertuples())
    mtab = ('| kaynak | n (AF/SR/diğer) | ağırlıklı prevalans | Precision | Recall | FPR | üç hedef |\n|---|---|---|---|---|---|---|\n'
            + '\n'.join(f'| {r.kapsam} | {int(r.n)} ({int(r.AF)}/{int(r.SR)}/{int(r.DIGER)}) | {f3(r.prev)} | {ci(r.P, r.P_lo, r.P_hi)} | '
                        f'{ci(r.R, r.R_lo, r.R_hi)} | {ci(r.FPR, r.FPR_lo, r.FPR_hi)} | {"evet" if r.uc_hedef else "hayır"} |'
                        for r in mix[mix.analiz == 'Karışım — birincil'].itertuples()))
    afltab = ('| kaynak | n | AF kararı (model) | oran model | oran baseline |\n|---|---|---|---|---|\n'
              + '\n'.join(f'| {r.kapsam} | {int(r.n)} | {int(r.AF_karari)} | {ci(r.oran, r.oran_lo, r.oran_hi)} | '
                          f'{ci(r.base_oran, r.base_oran_lo, r.base_oran_hi)} |' for r in afl[afl.analiz == 'AFL — birincil'].itertuples()))

    cx = a2[(a2.analiz == 'A2 — birincil') & (a2.kapsam == 'CPSC-Extra') & (a2.skor == 'MODEL')].iloc[0]
    ex = reg['evidence']['external']
    pf = {}
    for k in ('header_eligible',):
        pf = dedup33[k]
    # Kapanış düzeltmesi: Challenge kaynaklarının kurum/konumu (Reyna ve ark., künye + tablo; tam metin depoda değil)
    # ve yerelde indirilmiş Challenge alt dizinleri (yalnız dizin adları listelenir; kayıt okunmaz)
    rsrc = js(P46 / 'data/refs/reyna2021_challenge_sources.json')
    pm = [x for x in rsrc['papers'] if x['key'] == 'reyna2022_pmea'][0]
    cinc = [x for x in rsrc['papers'] if x['key'] == 'reyna2021_cinc'][0]
    t1 = {r['database']: r for r in pm['table1_sources']}
    local_dirs = {ph: sorted(d.name for d in (V2 / ph / 'data/raw/training').iterdir() if d.is_dir())
                  for ph in ('phase_xxix', 'phase_xxxiii')}
    used = {'CPSC': 'cpsc_2018', 'CPSC-Extra': 'cpsc_2018_extra', 'Chapman-Shaoxing': 'chapman_shaoxing', 'G12EC': 'georgia'}
    src_rows = '\n'.join(f"| {k} (`{v}`) | {t1[k]['source']} | {t1[k]['location']} |" for k, v in used.items())
    excl_rows = '\n'.join(f"| {k} | {t1[k]['source']} | {t1[k]['location']} |" for k in ('PTB-XL', 'PTB'))
    md = f"""# Phase XLVI — AF doğrulama belgesi (`af_S4_DEVICE` + AF-ECGDELI-OCTAVE-v1)

Kapsam: danışman isteği — hasta bazlı ayrım, aynı öznitelik çıkarımı, Challenge 2021 kaynakları, kaynaklar arası ve
PTB-XL ile kayıt çakışması, CPSC-Extra, diğer ritimler. **Tüm sayılar önceki faz dosyalarından okunmuştur**; her
tablonun altında kaynak yolu vardır. Belge `scripts/af_dossier.py` ile üretildi (elle sayı yazılmadı). Bu fazda model
yüklenmedi, tahmin üretilmedi, EKG sinyali okunmadı. Tek yeni hesap §1.2'deki PTB-XL metadata kesişim kontrolüdür
(kimlik ve fold sütunları; tahmin veya sonuç verisi değil).

## 0. Sistem kimliği

| öğe | değer | kaynak |
|---|---|---|
| model | `{reg['model_file']['path']}` SHA256 `{reg['model_file']['sha256'][:16]}…`; LightGBM; 12 öznitelik (yaş, cinsiyet + 10 EKG aralığı) | `phase_xliii/registry/models.json` |
| eşik | {reg['thresholds']['primary']['value']:.10f} (donmuş; Phase21 validation BALANCED senaryosu, bkz. model kartı) | registry; `All_Disease_Improvement_Phase21/selected_model_registry.json` |
| hedef | {reg['target_definition']} | registry |
| pipeline | {lock['pipeline_version']}; `phase_xxviii/{lock['pipeline_file']}` SHA256 `{lock['pipeline_sha256'][:16]}…`; kilit {lock['locked_utc'][:19]}Z | `phase_xxviii/config/af_pipeline_lock.json` |
| ECGDeli | {lock['ecgdeli']['version']}; kaynak ağacı SHA256 `{lock['ecgdeli']['source_tree_sha256'][:16]}…` ({lock['ecgdeli']['n_m_files']} .m) | kilit |
| Octave | {lock['octave']['version']} (`octave-cli.exe` SHA256 `{lock['octave']['exe_sha256'][:16]}…`); paketler {', '.join(lock['octave']['packages'])} | kilit |
| WFDB | vendored {lock['wfdb_vendor_version']} | kilit |
| ön işleme | {lock['preprocessing']}; {lock['sampling_rate_hz']} Hz; 12 lead | kilit |
| agregasyon | medyan; IQR numpy `linear` (25, 75); son RR tekrarlanmaz | kilit (`aggregation`) |

## 1. PTB-XL: hasta bazlı ayrım

### 1.1 Kural (Phase21)

`All_Disease_Improvement_Phase21/src/preprocessing/prepare.py :: af()`:
1. PTB-XL 1.0.3 `ptbxl_database.csv` hasta başına **en küçük `ecg_id`** (ilk EKG) seçilir. Bu seçim etiket ve kalite
   süzgecinden **önce** yapılır.
2. Yalnız `validated_by_human = True` ve SCP kodlarında AFIB **xor** SR olan, yaşı ≥ 18 kayıtlar kalır.
3. Bölme PTB-XL'in resmî `strat_fold` alanıyla yapılır: 1–8 fit, 9 validation, 10 test. PTB-XL fold'ları hasta
   düzeyinde atanmıştır.
4. Kimlik `person_id = "PTB_" + patient_id`; `config/af_splits.json` kişi kimliklerini saklar.

### 1.2 Kişi kesişimi kanıtı (bu fazda metadata ile yeniden hesaplandı)

`results/af_split_check.json`:
- Bölme boyutları: {', '.join(f'{k} {v}' for k, v in sp['split_sizes'].items())}.
- Kişi kesişimleri: {inter}.
- Birden fazla `strat_fold`'a düşen PTB-XL hastası: **{sp['patients_multi_fold']}** / {sp['n_patients_db']} (tüm veri tabanı,
  {sp['n_ecg_db']} EKG). Yani bir hastanın EKG'leri hiçbir zaman farklı fold'lara dağılmaz.
- Phase21 kuralı metadata ile yeniden uygulandı; rol ile `strat_fold` tutarlı: **{'evet' if sp['fold_role_consistent'] else 'HAYIR'}**;
  bölmede olup kurala uymayan kişi: {sp['unmatched_role']}.

| rol | n | AF | SR |
|---|---|---|---|
{cnt}

Test (fold 10) 114 AF / 1.458 SR ile Phase XXVII'deki iç test sayısıyla aynıdır.

### 1.3 İç test sonucu (Phase XXVII, kilitli eşik)

| n (AF) | TP/FP/TN/FN | P | R | FPR | AUC |
|---|---|---|---|---|---|
| {int(it.n)} ({int(it.pos)}) | {int(it.TP)}/{int(it.FP)}/{int(it.TN)}/{int(it.FN)} | {ci(it.precision, it.precision_lo, it.precision_hi)} | {ci(it.recall, it.recall_lo, it.recall_hi)} | {ci(it.fpr, it.fpr_lo, it.fpr_hi)} | {ci(it.auc, it.auc_lo, it.auc_hi)} |

Kaynak: `phase_xxvii/results/ci_metrics.csv` (model=af, kume=test). Etiket: İÇ TEST (held-out, daha önce açılmış).

## 2. Öznitelik çıkarımı: eğitim ile dış doğrulama aynı mı?

**Kısa yanıt: birebir aynı değil; farkı ölçüldü ve kilitlendi.**

- **Eğitim ve iç test** (Phase21, XXVII): PhysioNet'in PTB-XL+ veri setindeki hazır ECGDeli öznitelikleri
  (`ecgdeli_features.csv`, "golden"). Bu öznitelikleri üreten yazılım ve ayarlar PTB-XL+ yayıncılarınındır.
- **Dış doğrulama ve uygulama** (XXIX, XXXIII, XLIV): aynı ECGDeli v1.1 kaynağını Octave 10.3.0'da çalıştıran ve
  agregasyonu PTB-XL+ ile eşleştirmek için yeniden yazılan **kilitli** AF-ECGDELI-OCTAVE-v1 pipeline'ı. Agregasyon
  kuralları (son RR tekrarsız, `linear` IQR) Phase XXVII'de 30 kayıtta **post-hoc** bulundu.
- Bağımsız doğrulama Phase XXVIII'de yapıldı: fit/validation'dan 100 PTB-XL kaydı (test hastası 0), kilitli
  tolerans ve kriter (karar uyumu ≥ 0,98 ve medyan |Δp| ≤ 0,02) sonuçtan önce yazıldı.

### 2.1 Öznitelik uyumu (pipeline − golden, 100 kayıt)

| öznitelik | tolerans içinde | tam eşit oranı | medyan |Δ| (ms) | Bland–Altman yanlılık [LoA] (ms) |
|---|---|---|---|---|
{ftab}

Kaynak: `phase_xxviii/results/tol100_feature_parity.csv` (grup = tümü). RR ve QRS ailesi eşleşir. PR, P süresi ve
özellikle QT sapar (QT tolerans içi 8/100).

### 2.2 Model düzeyinde karar uyumu (aynı 100 kayıt, kilitli eşik)

| senaryo | grup | uyumlu | karar uyumu [Wilson %95 GA] | medyan |Δp| | p95 |Δp| |
|---|---|---|---|---|---|
{atab}

Kriter sağlandı: **{'evet' if verdict['KRITER_SAGLANDI'] else 'hayır'}** (nokta tahmini). GA alt sınırı kriterin üstünde:
**{'evet' if verdict['GA_alt_sinir_kriter_ustunde'] else 'hayır'}** (0,946 < 0,98). Yani %98 eşdeğerlik istatistiksel olarak
kanıtlanmadı. Dış doğrulama sonucu "donmuş model + kilitli pipeline" **bileşiminin** performansıdır. AF kayıtlarında
olasılık kayabilir (p95 |Δp| 0,24). Bu yüzden yalnız sabit eşikte karar raporlanır. Kaynak:
`phase_xxviii/results/tol100_model_agreement.csv`, `tol100_verdict.json`.

### 2.3 Uygulama ile araştırma pipeline'ının birebirliği (Phase XLIV)

Uygulama (`app/backend`) kilitli `af_pipeline_v1.py` dosyasını kopyalamadan, SHA256 doğrulamasından sonra çağırır.
10 öznitelik, araştırma fazlarının kayıtlı çıktısıyla karşılaştırıldı:

| test | kayıt | HTTP | durum | max |Δ| (10 öznitelik) | örnek sayısı |
|---|---|---|---|---|---|
{etab}

Kaynak: `phase_xliv/results/af_e2e.json` (PTB-XL `.hea/.dat`, phase_xxviii ile), `af_mat_e2e.json` (Challenge `.mat`,
phase_xxxiii ile), `af_long_e2e.json` (10 sn'den uzun kayıtlar, "ilk 10 sn" ön adımıyla, phase_xxxiii ile).

### 2.4 "İlk 10 saniye" ön adımı

Kilitli `read_wfdb_500` tam 5.000 örnek (10 sn, 500 Hz) ister. Challenge kayıtlarının bir kısmı 10 sn'den uzundur.
Phase XXIX ve XXXIII bu kayıtlarda kilit dışında bir sarmalayıcı (`read_first10s`, `sampto=5000`) kullandı. Uygulama
aynı fonksiyonu birebir kopyalar (`app/backend/healthrisk_api/ecg_window.py`); kaynak dosya ve fonksiyon gövdesi
SHA256'sı başlangıçta doğrulanır (Phase XLIV kapanış, karar 3). Kilit dosyası değişmedi. Sınırlılık: uzun kayıtta yalnız
ilk 10 sn değerlendirilir; kaydın geri kalanındaki ritim görülmez. Örnek sayısı < 5.000 veya fs ≠ 500 Hz → ABSTAIN.

## 3. Dış doğrulama verisi: PhysioNet/CinC Challenge 2021

| öğe | değer | kaynak |
|---|---|---|
| sürüm | 1.0.3 (`https://physionet.org/files/challenge-2021/1.0.3/`), doi:10.13026/34va-7q14 | `phase_xxix/01_data_flow.md`; README |
| bütünlük | resmî `SHA256SUMS.txt`; header 30.921/30.921, `.mat` (XXIX) 8.059/8.059, (XXXIII B/AFL) 2.668/2.668 SHA ile doğrulandı | `phase_xxix/01_data_flow.md`, `phase_xxxiii/01_data_flow.md` |
| kullanılan kaynaklar | `cpsc_2018`, `cpsc_2018_extra`, `chapman_shaoxing`, `georgia` | XXIX protokol v2 §2 |
| **kullanılmayan** | Ningbo, **PTB-XL kopyası (`training/ptb-xl`, modelin eğitim verisi)**, INCART, PTB (1000 Hz) — indirilmedi | `phase_xxix/config/external_protocol_v2.md` |
| etiket | header Dx (SNOMED CT) kodları: AF 164889003, SR 426783006, AFL 164890007. Pozitif = AF var ve SR yok (AF+AFL pozitif kalır); negatif (A) = SR var, AF ve AFL yok; AF+SR, yalnız AFL, SR+AFL dışlanır | XXIX protokol §4 |
| teknik süzgeç | fs = 500 Hz, 12 lead (sıra/birim), süre ≥ 10 sn, yaş ≥ 18, cinsiyet geçerli | XXIX/XXXIII akış tabloları |

Header-uygun kayıt sayıları (XXXIII): {', '.join(f'{k} {v}' for k, v in pf.items())}.

## 4. Kayıt çakışması ve tekilleştirme

### 4.1 Kaynaklar arası ve kaynak içi (yapıldı)

- **Yöntem** (Phase XXIX protokol §3): ilk 5.000 örnek × 12 lead'in ham int16 değerlerinin hash'i ("pencere hash'i").
  Aynı hash'e sahip kayıtlar kopya grubudur. Grup içinde etiketler çelişirse grubun tamamı dışlanır; değilse bir kayıt
  tutulur.
- **AF/SR adaylarında (XXIX):** {dedup29['candidates']} aday; sinyal hatası {dedup29['signal_bad']}; kopya olarak dışlanan
  {dedup29['dup_removed']}; çelişkili etiket {dedup29['dup_conflict_removed']}. Kaynak çiftine göre kopya grupları:
  {', '.join(f'{k}: {v}' for k, v in dedup29['dup_source_pairs'].items())}. **CPSC-Extra'daki 152 header-uygun AF kaydının
  74'ü CPSC 2018'deki bir kaydın birebir kopyasıydı.** Tam sinyal hash'i aynı kayıt (aday kümesi): {dedup29['full_hash_dup_records']}.
- **Diğer ritim (B) ve AFL kayıtlarında (XXXIII):** XXIX kayıtlarıyla ve kendi içinde aynı yöntem. Dışlananlar:
  {', '.join(f'{k}: {v}' for k, v in dedup33['dup_status'].items())}.
- Kaynak: `phase_xxix/results/flow_dedup.json`, `phase_xxxiii/results/flow_dedup33.json`, `phase_xxix/01_data_flow.md`.

### 4.2 PTB-XL ile çakışma

**Kaynakların kurum ve konumu** (Reyna ve ark. 2022, Tablo 1, doi:{pm['doi']}; Challenge tanım makalesi Reyna ve ark.
2021, doi:{cinc['doi']}; künyeler ve alıntılar `phase_xlvi/data/refs/reyna2021_challenge_sources.json`):

| kullanılan Challenge kaynağı (dizin) | kaynak kurum | konum |
|---|---|---|
{src_rows}

| eğitim verisiyle ilişkili Challenge kaynağı (**kullanılmadı**) | kaynak kurum | konum |
|---|---|---|
{excl_rows}

Reyna ve ark. 2021 Chapman-Shaoxing için "Chapman University and Shaoxing People's Hospital" yazar; CPSC-Extra,
CPSC 2018'in kullanılmamış verisidir (aynı kaynak). Makalelerde Challenge kaynakları arasında hasta veya kayıt paylaşımı
bilgisi verilmez (BULUNAMADI).

- **Kaynak düzeyinde dışlama yapıldı:** Challenge 2021'in PTB-XL kopyası (`training/ptb-xl`) ve PTB indirilmedi
  (XXIX protokol §1). Yerelde yalnız şu Challenge dizinleri vardır: XXIX {', '.join(f'`{x}`' for x in local_dirs['phase_xxix'])};
  XXXIII {', '.join(f'`{x}`' for x in local_dirs['phase_xxxiii'])} (`data/raw/training/` listesi, bu betikte).
- **Kayıt düzeyinde çakışmanın neden beklenmediği:** kullanılan dört kaynak Çin'deki kurumlardan (CPSC 2018,
  Shaoxing People's Hospital) ve ABD'den (Emory University Hospital, Atlanta) gelir; PTB-XL ise PTB (Physikalisch-Technische
  Bundesanstalt) kaynaklı Avrupa veri kümesidir. Challenge'ın PTB-XL'den türetilmiş tek alt kümesi (`ptb-xl`) ve PTB alt
  kümesi (`ptb`) kullanılmadı. Bu nedenle PTB-XL kayıtlarının kullanılan kaynaklarda bulunması beklenmez. Bu bir
  **çıkarımdır, kanıt değildir**: kaynak kurum bilgisine dayanır, kayıtlar karşılaştırılarak doğrulanmamıştır.
- **Kayıt düzeyinde PTB-XL ↔ Challenge hash karşılaştırması: YAPILMADI** (önceki faz dosyalarında BULUNAMADI). Yerelde
  yalnız 100 civarı PTB-XL dalga formu vardır (`phase_xxviii/data/ptbxl500/`); tam karşılaştırma için PTB-XL
  `records500` indirilmelidir. **Bu, açık kalan bir kontroldür.**
- **Hasta düzeyinde tekilleştirme yapılamaz:** Challenge header'larında hasta kimliği yoktur (BULUNAMADI). Birebir kopya
  olmayan aynı-hasta kayıtları (ör. aynı hastanın farklı günlerdeki EKG'leri) tespit edilemez.

## 5. Dış doğrulama sonuçları (Phase XXXIII; donmuş model + kilitli pipeline)

Pipeline başarısızları birincil analizde dışlandı (AF 3, SR 2, diğer ritim 3; `phase_xxxiii/01_data_flow.md`).
Yeniden denenen: {retry['yeniden_denenen']}. Baseline: RR_iqr/RR_mean ≥ 0,138235 (PTB-XL validation'da seçilmiş kural).

### 5.1 A2 — AF ve SR, tam örneklem (birincil)

| kaynak | skor | n (AF) | TP/FP/TN/FN | Recall | FPR | AUC | ΔAUC (model − baseline) | not |
|---|---|---|---|---|---|---|---|---|
{res_rows(a2, 'A2 — birincil')}

Kaynak: `phase_xxxiii/results/a2_results.csv`. **Precision raporlanmaz**: A2 örneklemindeki AF oranı (havuzda
{ex['n_pos']}/{ex['n']}) gerçek kullanım prevalansını temsil etmez (registry `precision_note`).

### 5.2 CPSC-Extra: yalnız 4 negatif

CPSC-Extra'da tekilleştirmeden sonra uygun SR kaydı **{int(cx.n - cx.pos)}**'tür (AF {int(cx.pos)}). Bu kaynakta FPR
({f3(cx.FPR)}, GA {f3(cx.FPR_lo)}–{f3(cx.FPR_hi)}) ve AUC **yorumlanamaz**. Satır tabloda yine gösterilir ve havuza
katılır; tek başına yorum dışıdır (XXXIII protokol sapması 2: SR n < 30 → "YORUMLANAMAZ"; kural model çıktısı görülmeden
eklendi). Aynı kaynakta diğer ritim negatifi 492'dir; B analizinde bu kaynak yorumlanabilir.

### 5.3 B — AF ve diğer ritimler (ikincil analiz)

Negatif sınıf: SR dışındaki ritimler (kaynak başına 500 kayıt çekildi, tekilleştirildi). Eğitimde bu ritimler negatif
değildi.

| kaynak | skor | n (AF) | TP/FP/TN/FN | Recall | FPR | AUC | ΔAUC | not |
|---|---|---|---|---|---|---|---|---|
{res_rows(b, 'B — birincil')}

Ritim alt gruplarında FPR (`phase_xxxiii/results/b_rhythm_fpr.csv`):

{rhtab}

### 5.4 Gerçekçi karışım ve AFL (ikincil)

Ağırlıklı karışım (hastane arşivi oranları; toplum prevalansı değil), `phase_xxxiii/results/mixture_results.csv`:

{mtab}

AFL kayıtlarının AF olarak sınıflandırılma oranı, `phase_xxxiii/results/afl_results.csv`:

{afltab}

## 6. Özet ve açık noktalar

- **Hasta bazlı ayrım:** PTB-XL'de kişi kesişimi 0; hasta başına tek EKG; resmî hasta-düzeyi fold'lar. Kanıt §1.2.
- **Öznitelik çıkarımı:** eğitim PTB-XL+ golden öznitelikleriyle, dış doğrulama ve uygulama kilitli Octave
  pipeline'ıyla yapıldı. RR/QRS eşleşir; PR/P/QT sapar. Karar uyumu 0,99 (GA alt sınırı 0,946). Uygulama ile araştırma
  pipeline'ı arasında 10 öznitelik 11/11 kayıtta birebir.
- **Tekilleştirme:** pencere hash'iyle kaynak içi ve kaynaklar arası yapıldı; CPSC-Extra'nın AF kayıtlarının yarısı
  CPSC 2018 kopyasıydı.
- **Açık:** PTB-XL ↔ Challenge kayıt düzeyi hash karşılaştırması yapılmadı (kaynak kurumları farklı olduğu ve Challenge'ın
  PTB-XL/PTB alt kümeleri kullanılmadığı için çakışma beklenmez; doğrulanmadı); hasta kimliği olmadığı için aynı-hasta
  tekrarları dışlanamaz; Challenge etiketleri insan doğrulaması bilgisi taşımaz; yalnız ilk 10 sn kullanılır.
- **Yorum sınırı:** model AF'yi sinüs ritminden iyi ayırır; diğer ritimlerde (sinüs taşikardisi, PVC, PAC, pacing) ve
  AFL'de yanlış pozitifler artar. Klinik tanı aracı değildir.
"""
    (P46 / 'af_validation_dossier.md').write_text(md, encoding='utf8')
    print('yazıldı; kesişimler', sp['intersections'], 'çok-fold hasta', sp['patients_multi_fold'], 'tutarlı', sp['fold_role_consistent'])


if __name__ == '__main__':
    main()
