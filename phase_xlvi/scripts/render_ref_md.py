"""Phase XLVI — Görev 3 raporu: phase_xlvi/01_reference_score_analysis.md.
Tablolar yalnız results/reference_score_analysis.csv, reference_score_gate.json ve reference_score_meta.json'dan üretilir;
elle sayı yazılmaz. Kaynak/eşik tablosu birincil kaynak özetlerinden (phase_xlvi/data/refs/*.json, Europe PMC) okunur.
Kullanım: python -B -I phase_xlvi/scripts/render_ref_md.py
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

V2 = Path(__file__).resolve().parents[2]
P46 = V2 / 'phase_xlvi'
RES = P46 / 'results'


def f3(x):
    return '—' if x is None or (isinstance(x, float) and pd.isna(x)) else f'{x:.3f}'.replace('.', ',')


def ci(v, lo, hi):
    return f'{f3(v)} [{f3(lo)}–{f3(hi)}]'


def pv(p):
    if pd.isna(p):
        return '—'
    return '< 0,001' if p < 0.001 else f'{p:.3f}'.replace('.', ',')


def ref_meta():
    out = {}
    for n in ('sterling2006', 'shah2009', 'angulo2007', 'koh2001'):
        p = P46 / 'data/refs' / f'{n}.json'
        r = json.loads(p.read_text(encoding='utf8'))['resultList']['result'][0]
        out[n] = dict(pmid=r['pmid'], doi=r.get('doi'), title=r['title'], year=r['pubYear'],
                      journal=r.get('journalInfo', {}).get('journal', {}).get('isoabbreviation')
                      or r.get('journalInfo', {}).get('journal', {}).get('title'),
                      sha=hashlib.sha256(p.read_bytes()).hexdigest()[:12])
    p = V2 / 'phase_xxx/data/docs/epmc_12934782.json'
    r = json.loads(p.read_text(encoding='utf8'))
    r = r.get('resultList', {}).get('result', [r])[0]
    out['adler2003'] = dict(pmid=r['pmid'], doi=r.get('doi'), title=r['title'], year=r['pubYear'], journal='Mayo Clin Proc',
                            sha=hashlib.sha256(p.read_bytes()).hexdigest()[:12])
    return out


def scheme_table(d, disease, group):
    x = d[(d.hastalik == disease) & (d.grup == group) & d.karsilastirma.str.startswith('eşit')]
    lines = ['| karşılaştırma | taraf | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |',
             '|---|---|---|---|---|---|---|---|']
    mc = ['| karşılaştırma | pozitiflerde yalnız model / yalnız referans yakaladı (McNemar p) | negatiflerde yalnız model / yalnız referans yönlendirdi (McNemar p) |',
          '|---|---|---|']
    recs = list(x.itertuples(index=False))
    assert len(recs) % 3 == 0
    for i in range(0, len(recs), 3):                      # betik sırası: model, referans, fark (compare())
        m, r_, f = recs[i:i + 3]
        assert (m.taraf, r_.taraf, f.taraf) == ('model', 'referans', 'fark (model − referans)')
        assert m.karsilastirma == r_.karsilastirma == f.karsilastirma
        sc = m.karsilastirma
        for r in (m, r_):
            kural = r.kural.replace('.', ',')
            lines.append(f'| {sc} | {r.taraf} | {kural} | {int(r.TP)}/{int(r.FP)}/{int(r.TN)}/{int(r.FN)} | '
                         f'{ci(r.P, r.P_lo, r.P_hi)} | {ci(r.R, r.R_lo, r.R_hi)} | {ci(r.FPR, r.FPR_lo, r.FPR_hi)} | '
                         f'{f3(r.yonlendirme_orani)} ({int(r.yonlendirilen)}) |')
        mc.append(f'| {sc} — {r_.kural.replace(".", ",")} | {int(f.mcnemar_pozitif_model_yalniz)} / {int(f.mcnemar_pozitif_ref_yalniz)} '
                  f'(p {pv(f.mcnemar_pozitif_p)}) | {int(f.mcnemar_negatif_model_yalniz)} / {int(f.mcnemar_negatif_ref_yalniz)} '
                  f'(p {pv(f.mcnemar_negatif_p)}) |')
    notes = [n for n in x.not_.dropna().drop_duplicates() if n]
    return '\n'.join(lines) + '\n\n' + '\n'.join(mc) + ('\n\nNot: ' + '; '.join(notes) if notes else '')


def delta_table(d, disease):
    x = d[(d.hastalik == disease) & d.karsilastirma.str.startswith('ΔAUC')]
    lines = ['| grup | n (pozitif) | karşılaştırma | AUC model [%95 GA] | AUC referans [%95 GA] | ΔAUC [%95 GA] |',
             '|---|---|---|---|---|---|']
    for _, r in x.iterrows():
        lines.append(f'| {r.grup} | {int(r.n)} ({int(r.pos)}) | {r.kural} | {ci(r.AUC_model, r.AUC_model_lo, r.AUC_model_hi)} | '
                     f'{ci(r.AUC_ref, r.AUC_ref_lo, r.AUC_ref_hi)} | {ci(r.dAUC, r.dAUC_lo, r.dAUC_hi)} |')
    return '\n'.join(lines)


def high_table(d):
    x = d[(d.hastalik == 'fibrozis') & (d.karsilastirma == 'referans yüksek eşik (tek başına)')]
    lines = ['| grup | kural | TP/FP/TN/FN | P | R | FPR | yönlendirme |', '|---|---|---|---|---|---|---|']
    for _, r in x.iterrows():
        lines.append(f'| {r.grup} | {r.kural} | {int(r.TP)}/{int(r.FP)}/{int(r.TN)}/{int(r.FN)} | {ci(r.P, r.P_lo, r.P_hi)} | '
                     f'{ci(r.R, r.R_lo, r.R_hi)} | {ci(r.FPR, r.FPR_lo, r.FPR_hi)} | {f3(r.yonlendirme_orani)} |')
    return '\n'.join(lines)


def main():
    d = pd.read_csv(RES / 'reference_score_analysis.csv')
    gate = json.loads((RES / 'reference_score_gate.json').read_text(encoding='utf8'))
    meta = json.loads((RES / 'reference_score_meta.json').read_text(encoding='utf8'))
    rm = ref_meta()
    interp = (P46 / 'config/ref_interpretation.md').read_text(encoding='utf8') if (P46 / 'config/ref_interpretation.md').exists() else '_(yorum henüz yazılmadı)_'
    g_ok = sum(g['ok'] for g in gate['gates'])
    md = f"""# Phase XLVI — 01: Fibrozis ve osteoporozda referans skor karşılaştırması

**Etiket: POST-HOC TANIMLAYICI.** Bu analiz kilitli test sonucu değildir ve model, eşik ya da feature seçimi için
kullanılmaz. Model yeniden fit edilmedi; eşik, feature sırası ve test kümesi değişmedi. Birincil (kilitli) sonuçlar
Phase XXXI (fibrozis) ve Phase XXX (osteoporoz) raporlarındaki sonuçlardır.

Üretim: `scripts/ref_score_analysis.py` (Focused venv, Python {meta['python']}) → `results/reference_score_analysis.csv`;
bu belge `scripts/render_ref_md.py` ile CSV'den üretildi (elle sayı yazılmadı).

## 0. Yöntem notu: teknik yeniden skorlama ve kapı

Phase XXX/XXXI kişi düzeyi test tahminlerini ve referans skor değerlerini dosyaya kaydetmemişti; yalnız toplu
sonuçlar vardı. McNemar ve paired bootstrap kişi düzeyi veri ister. Kullanıcı kararıyla (2026-11-20) donmuş model ve
kilitli eşik, **önceden açılmış** test dosyası üzerinde deterministik olarak yeniden skorlandı (Phase XXVII "rescore" ve
Phase XXXI 01 ile aynı yöntem). Referans skor formülleri özgün faz betiklerinden salt okunur içe aktarıldı:
`phase_xxxi/scripts/t3_fib_dev.py :: fib4, nfs`, `phase_xxx/scripts/t2_dev.py :: ost`; metrik işlevleri
`phase_xxx/scripts/p30_engine.py`.

**Kapı:** kayıtlı TP/FP/TN/FN, AUC ve ΔAUC (özgün tohum {meta['p30_engine_seed']}) değerleri birebir yeniden
üretilmeden analiz yapılmaz. Sonuç: **{g_ok}/{len(gate['gates'])} birebir** (`results/reference_score_gate.json`;
AUC ve ΔAUC farkı < 1e-12).

| | fibrozis | osteoporoz |
|---|---|---|
| test | NHANES L 2021–23, n = {meta['fibrosis']['n']} | NHANES J 2017–18, n = {meta['osteo']['n']} |
| model SHA256 | `{meta['fibrosis']['model_sha256'][:16]}…` | `{meta['osteo']['model_sha256'][:16]}…` |
| kilitli eşik | {meta['fibrosis']['threshold']:.6f} | {meta['osteo']['threshold']:.6f} |
| test dosyası SHA256 | `{meta['fibrosis']['test_file_sha256'][:16]}…` | `{meta['osteo']['test_file_sha256'][:16]}…` |

## 1. Referans skorlar: formül, kaynak eşikleri ve özgün hedef popülasyon

Kaynak: Europe PMC kayıtları (`data/refs/*.json`, PubMed özetleri). Yalnız özette okunabilen bilgi yazıldı; tam metin
okunmadı. Özette doğrulanamayan bilgi BULUNAMADI.

| skor | formül (projede) | kaynak eşik | özgün geliştirme popülasyonu ve hedef | kaynak |
|---|---|---|---|---|
| FIB-4 (formül) | yaş × AST / (trombosit × √ALT) | < 1,45 / > 3,25 | HIV/HCV ko-enfeksiyonlu 832 hasta, biyopsi; Ishak 4–6 (ilerlemiş fibrozis) | Sterling ve ark. {rm['sterling2006']['year']}, {rm['sterling2006']['journal']}, PMID {rm['sterling2006']['pmid']}, doi:{rm['sterling2006']['doi']} |
| FIB-4 (NAFLD eşikleri) | aynı | ≤ 1,30 (NPV %90) / ≥ 2,67 (PPV %80) | NAFLD'li 541 erişkin (ABD ulusal veri tabanı), biyopsi; ilerlemiş fibrozis | Shah ve ark. {rm['shah2009']['year']}, {rm['shah2009']['journal']}, PMID {rm['shah2009']['pmid']}, doi:{rm['shah2009']['doi']} |
| NFS | −1,675 + 0,037·yaş + 0,094·BMI + 1,13·IFG/diyabet + 0,99·AST/ALT − 0,013·trombosit − 0,66·albümin | < −1,455 (dışlama) / > 0,676 (yüksek) | Biyopsiyle kanıtlı NAFLD'li 733 hasta (480 geliştirme, 253 doğrulama); ilerlemiş fibrozis | Angulo ve ark. {rm['angulo2007']['year']}, {rm['angulo2007']['journal']}, PMID {rm['angulo2007']['pmid']}, doi:{rm['angulo2007']['doi']} |
| OST(A) | 0,2 × (kilo kg − yaş) | özetten: üç risk kategorisi; sayısal eşik BULUNAMADI | Asya'da 8 ülkeden **postmenopozal Asyalı kadınlar**; femur boynu T ≤ −2,5. Doğrulama: postmenopozal Japon kadınlar | Koh ve ark. {rm['koh2001']['year']}, {rm['koh2001']['journal']}, PMID {rm['koh2001']['pmid']}, doi:{rm['koh2001']['doi']} |
| OST, erkek | aynı | ≤ 3 (duyarlılık %93, özgüllük %66); kategoriler ≥ 4 / −1…3 / ≤ −2 | ABD gaziler hastanesi (göğüs ve romatoloji kliniği) 181 erkek; omurga/total kalça/femur boynu T ≤ −2,5 | Adler ve ark. {rm['adler2003']['year']}, {rm['adler2003']['journal']}, PMID {rm['adler2003']['pmid']}, doi:{rm['adler2003']['doi']} |
| OST, kadın eşiği < 2 | aynı | < 2 | Birincil kaynak özetinde BULUNAMADI. Phase XXX protokolü bu eşiği USPSTF kanıt özetinden (model-çıkarımlı özet) almıştır | `phase_xxx/config/protocol_osteo.md` §6 |

**Bu projedeki hedeflerle fark (önemli):**
- Fibrozis hedefi **FibroScan LSM ≥ 8 kPa**dır; FIB-4 ve NFS ise **biyopside ilerlemiş fibrozis** (F3–F4 / Ishak 4–6) için
  geliştirildi. Popülasyon da farklıdır: kaynaklar karaciğer kliniği hastalarıdır (HIV/HCV, NAFLD); burada genel NHANES
  erişkin popülasyonu (≥ 20 yaş, gebe değil) vardır. Skorların bu hedefte düşük performansı kısmen bu uyumsuzluktan
  gelir; skorların kendi amaçları için yetersiz olduğu anlamına gelmez.
- Shah 2009'da düşük eşik "≤ 1,30" olarak verilir. Phase XXXI'de karar `FIB-4 ≥ 1,3` = yönlendir, yani 1,30 tam değerindeki
  kişi yönlendirilir. Kaynakta 1,30 "düşük risk" tarafındadır. Sınır değerdeki kişi sayısı bu analizde ayrıca sayılmadı.
- OST(A) **postmenopozal Asyalı kadınlarda** geliştirildi. NHANES J testi ≥ 50 yaş kadın ve erkekleri, çoğunluğu Asyalı
  olmayan kişileri içerir; menopoz durumu OST kararı için ayrıca kullanılmadı. **Erkekler OST'nin özgün popülasyonu
  dışındadır.** Erkek eşiği (≤ 3) Adler 2003'ün küçük, klinik erkek örneklemine dayanır. Bu yüzden kadın ve erkek ayrı
  değerlendirildi ve erkek sonuçları ayrıca bu notla okunmalıdır.
- Osteoporoz hedefi min(femur boynu, total femur) T ≤ −2,5'tir (NHANES III 20–29 yaş Hispanik olmayan beyaz kadın
  referansı, erkeklerde de kadın referansı). Adler 2003'te omurga da dahildir.

## 2. Karşılaştırma şemaları

Hepsi test verisinde yapılır; bu yüzden **iyimser ve tanımlayıcıdır** (eşleştirme testte seçildi).

1. **Eşit duyarlılık:** model kilitli eşikte. Referans skorun eşiği, testte modelin Recall'una eşit veya üstünde
   Recall veren **en yüksek** eşik olarak seçildi (`p30_engine.threshold_recall` kuralı). Karşılaştırma FPR ve
   yönlendirme üzerinedir.
2. **Eşit yönlendirme (a):** model kilitli eşikte k kişiyi yönlendirir; referans skorun en yüksek k kişisi alınır.
3. **Eşit yönlendirme (b):** referans skor kendi standart eşiğinde (FIB-4 ≥ 1,30; NFS ≥ −1,455; kadında OST < 2,
   erkekte OST ≤ 3) k kişiyi yönlendirir; modelin en yüksek k kişisi alınır.

Eşitlikler kararlı sırayla (veri sırası) kırıldı; sınırdaki eşit skor sayısı tablo notlarındadır.

**İstatistik:**
- Oranlar Wilson %95 GA.
- **McNemar:** aynı kişilerde eşleştirilmiş kararlar. Pozitiflerde (Recall farkı) ve negatiflerde (FPR farkı) ayrı
  ayrı, uyumsuz çiftler üzerinde kesin iki yönlü binom testi. Eşit duyarlılık şemasında Recall farkı tasarım gereği
  ~0'dır; anlamlı olan negatiflerdeki testtir. Eşit yönlendirme şemasında iki test birlikte okunur.
- **ΔAUC:** AUC(model) − AUC(referans), aynı kişilerde pozitif/negatif tabakalı paired bootstrap, {meta['n_boot']} tekrar,
  seed {meta['seed']}. OST için skor −OST'dir (düşük OST = yüksek risk). Çoklu karşılaştırma düzeltmesi yapılmadı.

## 3. Fibrozis (LSM ≥ 8 kPa) — model vs FIB-4 ve NFS

### 3.1 Tümü
{scheme_table(d, 'fibrozis', 'tümü')}

### 3.2 Kadın
{scheme_table(d, 'fibrozis', 'kadın')}

### 3.3 Erkek
{scheme_table(d, 'fibrozis', 'erkek')}

### 3.4 Yüksek eşikler (tek başına; karşılaştırma şeması yok)
{high_table(d)}

### 3.5 ΔAUC
{delta_table(d, 'fibrozis')}

## 4. Osteoporoz (DXA T ≤ −2,5) — model vs OST, kadın ve erkek ayrı

### 4.1 Kadın
{scheme_table(d, 'osteoporoz', 'kadın')}

### 4.2 Erkek (OST'nin özgün popülasyonu dışında)
{scheme_table(d, 'osteoporoz', 'erkek')}

### 4.3 ΔAUC
{delta_table(d, 'osteoporoz')}

"Tümü" satırı yalnız bağlam içindir: cinsiyete özgü eşiklerin birleşimidir ve tek bir OST eşiğine karşılık gelmez.

## 5. Yorum (tanımlayıcı)

{interp}

## 6. Sınırlılıklar

- Post-hoc ve tanımlayıcıdır. Eşleştirme eşikleri test verisinde seçildi; bu yüzden iki tarafa da iyimser.
- Önceki fazlarda aynı testler ve benzer eşit-Recall analizleri (Phase XXXI 01) raporlandı; bu analiz yeni bir test
  değildir. Fibrozis testi PREVIOUSLY_EXPOSED etiketlidir.
- Çoklu karşılaştırma (2 hastalık × 3 grup × 3 şema × 2 test) için p değerleri düzeltilmedi. p değerleri karar kuralı
  olarak kullanılmamalı.
- NHANES tasarım ağırlıkları kullanılmadı (ağırlıksız; birincil analizlerle aynı).
- Referans skorların hedefi ve popülasyonu bu projeninkinden farklıdır (§1).
- Erkeklerde osteoporoz pozitif sayısı küçüktür; GA'lar geniştir.
- OST formülü ve kadın eşiği (< 2) birincil kaynak özetinde doğrulanamadı (BULUNAMADI); Phase XXX protokolündeki tanım
  kullanıldı.
- Model skorları klinik olasılık değildir (`clinical_probability_eligibility = false`).
"""
    (P46 / '01_reference_score_analysis.md').write_text(md, encoding='utf8')
    print('yazıldı', len(md))


if __name__ == '__main__':
    main()
