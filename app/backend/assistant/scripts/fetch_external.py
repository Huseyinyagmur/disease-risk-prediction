"""Phase XLVIII — dış bilgi tabanı metinlerini resmi kaynaklardan indirir (yeniden çalıştırılabilir).

Yalnız yeniden kullanımı açıkça serbest olan kamu malı içerik METİN olarak alınır:
  * MedlinePlus (NLM): sağlık konusu özetleri ve tıbbi test sayfaları — kamu malı (A.D.A.M. ansiklopedisi ve ilaç
    monografları telifli olduğu için ALINMAZ). Atıf: "Source: MedlinePlus, National Library of Medicine."
  * CDC: kamu malı; atıf ("Source: CDC"), onay anlamına gelmediği notu, içerik değiştirilmeden, ücretsiz erişim notu.
  * NIDDK: "copyright free"; değiştirilmeden yeniden üretilirse NIDDK kaynak olarak belirtilir.
NHLBI (sitede yeniden kullanım/telif beyanı BULUNAMADI) ve WHO (kopyalanmaz) yalnız BAĞLANTI olarak listelenir.

Metin seçimi: sayfadaki başlık bölümleri değiştirilmeden alınır; tedavi / ilaç / doz bölümleri (başlıkta treat, medicine,
medication, drug, dose, therapy, surgery, manage, transplant) asistan kuralları gereği DIŞARIDA bırakılır (alıntı seçimi;
metin değiştirilmez). Her parça için ham yanıt ve çıkarılan metnin SHA256'sı kb/sources.json'a yazılır.

Kullanım (ağ gerekir; yalnız bu betik dış ağa çıkar, sunucu çıkmaz):
  app/backend/.venv/Scripts/python.exe -B -I app/backend/assistant/scripts/fetch_external.py [--accessed YYYY-MM-DD]
Sayfalar zamanla güncellenebilir: yeniden çalıştırmada SHA değişirse yeni sürüm olarak kaydedilir ve indeks yeniden
kurulmalıdır (build_index.py). Kilitli sürüm kb/sources.json + kb/external/*.md'dir.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ASSIST = Path(__file__).resolve().parents[1]           # app/backend/assistant
KB = ASSIST / 'kb'
EXT = KB / 'external'
UA = 'Mozilla/5.0 (research-kb-fetch)'                  # genel istemci adı (kişisel bilgi yok)

LIC = {
    'medlineplus': dict(publisher='MedlinePlus, U.S. National Library of Medicine (NLM)', license='public domain (U.S. federal work); MedlinePlus "Linking to and Using Content" — health topic summaries and medical test information are not copyrighted',
                        attribution='Source: MedlinePlus, National Library of Medicine.',
                        policy_url='https://medlineplus.gov/about/using/usingcontent/'),
    'cdc': dict(publisher='Centers for Disease Control and Prevention (CDC)', license='public domain (U.S. federal work); CDC "Use of Agency Materials": attribution, non-endorsement disclaimer, substantive content unchanged, free-availability statement',
                attribution='Source: CDC. Materials developed by CDC; available on the agency website for no charge. Use does not imply endorsement by CDC, HHS or the U.S. Government.',
                policy_url='https://www.cdc.gov/other/agencymaterials.html'),
    'niddk': dict(publisher='National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK), NIH', license='copyright free (NIDDK "Copyright": content reproduced without changes should acknowledge NIDDK as the source)',
                  attribution='Source: National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK), NIH. Content reproduced without changes; does not imply endorsement.',
                  policy_url='https://www.niddk.nih.gov/copyright'),
}

# id, kaynak, tür, adres/terim, hastalık anahtarı
SOURCES = [
    ('mp_af', 'medlineplus', 'topic', 'Atrial Fibrillation', 'af'),
    ('mp_cirrhosis', 'medlineplus', 'topic', 'Cirrhosis', 'liver_fibrosis'),
    ('mp_steatotic_liver', 'medlineplus', 'topic', 'Steatotic Liver Disease', 'liver_fibrosis'),
    ('mp_osteoporosis', 'medlineplus', 'topic', 'Osteoporosis', 'osteoporosis'),
    ('mp_diabetes', 'medlineplus', 'topic', 'Diabetes', 'diabetes'),
    ('mp_ckd', 'medlineplus', 'topic', 'Chronic Kidney Disease', 'kidney'),
    ('mp_hbp', 'medlineplus', 'topic', 'High Blood Pressure', 'hypertension'),
    ('mp_anemia', 'medlineplus', 'topic', 'Anemia', 'anemia'),
    ('mp_copd', 'medlineplus', 'topic', 'COPD', 'copd'),
    ('mp_cad', 'medlineplus', 'topic', 'Coronary Artery Disease', 'cad'),
    ('mp_test_a1c', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/', 'diabetes'),
    ('mp_test_cbc', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/complete-blood-count-cbc/', 'anemia'),
    ('mp_test_lft', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/liver-function-tests/', 'liver_fibrosis'),
    ('mp_test_ecg', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/electrocardiogram/', 'af'),
    ('mp_test_lung', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/lung-function-tests/', 'copd'),
    ('mp_test_egfr', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/estimated-glomerular-filtration-rate-egfr-and-gfr-tests/', 'kidney'),
    ('mp_test_uacr', 'medlineplus', 'page', 'https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/', 'kidney'),
    ('cdc_diabetes', 'cdc', 'page', 'https://www.cdc.gov/diabetes/about/index.html', 'diabetes'),
    ('cdc_ckd', 'cdc', 'page', 'https://www.cdc.gov/kidney-disease/about/index.html', 'kidney'),
    ('cdc_hbp', 'cdc', 'page', 'https://www.cdc.gov/high-blood-pressure/about/index.html', 'hypertension'),
    ('cdc_cad', 'cdc', 'page', 'https://www.cdc.gov/heart-disease/about/coronary-artery-disease.html', 'cad'),
    ('cdc_copd', 'cdc', 'page', 'https://www.cdc.gov/copd/about/index.html', 'copd'),
    ('cdc_af', 'cdc', 'page', 'https://www.cdc.gov/heart-disease/about/atrial-fibrillation.html', 'af'),
    ('niddk_diabetes', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes', 'diabetes'),
    ('niddk_ckd', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/what-is-chronic-kidney-disease', 'kidney'),
    ('niddk_nafld', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash/definition-facts', 'liver_fibrosis'),
    ('niddk_nafld_dx', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash/diagnosis', 'liver_fibrosis'),
    ('niddk_cirrhosis', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/liver-disease/cirrhosis/definition-facts', 'liver_fibrosis'),
    ('niddk_a1c', 'niddk', 'page', 'https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test', 'diabetes'),
]

LINK_ONLY = [
    dict(id='nhlbi_af', url='https://www.nhlbi.nih.gov/health/atrial-fibrillation', publisher='NHLBI, NIH', reason='NHLBI sitesinde yeniden kullanım/telif beyanı BULUNAMADI; metin kopyalanmadı'),
    dict(id='nhlbi_copd', url='https://www.nhlbi.nih.gov/health/copd', publisher='NHLBI, NIH', reason='NHLBI sitesinde yeniden kullanım/telif beyanı BULUNAMADI; metin kopyalanmadı'),
    dict(id='nhlbi_anemia', url='https://www.nhlbi.nih.gov/health/anemia', publisher='NHLBI, NIH', reason='NHLBI sitesinde yeniden kullanım/telif beyanı BULUNAMADI; metin kopyalanmadı'),
    dict(id='nhlbi_hbp', url='https://www.nhlbi.nih.gov/health/high-blood-pressure', publisher='NHLBI, NIH', reason='NHLBI sitesinde yeniden kullanım/telif beyanı BULUNAMADI; metin kopyalanmadı'),
    dict(id='nhlbi_chd', url='https://www.nhlbi.nih.gov/health/coronary-heart-disease', publisher='NHLBI, NIH', reason='NHLBI sitesinde yeniden kullanım/telif beyanı BULUNAMADI; metin kopyalanmadı'),
    dict(id='who_diabetes', url='https://www.who.int/news-room/fact-sheets/detail/diabetes', publisher='World Health Organization', reason='WHO metinleri kopyalanmaz (görev kuralı); yalnız bağlantı'),
    dict(id='who_hypertension', url='https://www.who.int/news-room/fact-sheets/detail/hypertension', publisher='World Health Organization', reason='WHO metinleri kopyalanmaz (görev kuralı); yalnız bağlantı'),
    dict(id='who_copd', url='https://www.who.int/news-room/fact-sheets/detail/chronic-obstructive-pulmonary-disease-(copd)', publisher='World Health Organization', reason='WHO metinleri kopyalanmaz (görev kuralı); yalnız bağlantı'),
]

EXCLUDE_HEADING = re.compile(r'(?i)\b(treat\w*|medicine\w*|medication\w*|drugs?|dos(e|es|age|ing)|therap\w*|surger\w*|'
                             r'manag\w*|transplant\w*|clinical trials?|resources?|related|references?|more information|'
                             r'sources?|on this page|keep reading|what can i do|take action|living with|'
                             r'eating, diet|nutrition|cope|coping|support)\b')
SKIP_TAGS = {'script', 'style', 'nav', 'aside', 'footer', 'form', 'button', 'svg', 'noscript', 'iframe', 'header', 'figure', 'sup'}
SKIP_CLASS = re.compile(r'(?i)(breadcrumb|share|social|related|toc|on-this-page|feedback|page-tools|'
                        r'last-?(reviewed|updated)|resources|sidebar|signup|subscribe|dfe-section-related|cdc-dfe-card)')
BLOCK = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'dt', 'dd', 'td', 'th', 'blockquote'}


class MainText(HTMLParser):
    """<main> (yoksa <article>/<body>) içindeki başlık ve paragraf/madde metinleri; gezinme ve paylaşım blokları atlanır."""
    def __init__(self, root_tag):
        super().__init__(convert_charrefs=True)
        self.root_tag = root_tag
        self.depth_root = 0
        self.skip = []           # yığın: atlanan etiket derinlikleri
        self.stack = []
        self.blocks = []
        self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append(tag)
        if tag == self.root_tag:
            self.depth_root += 1
        if self.depth_root == 0:
            return
        cls = (a.get('class') or '') + ' ' + (a.get('id') or '')
        if self.skip or tag in SKIP_TAGS or SKIP_CLASS.search(cls) or a.get('aria-hidden') == 'true':
            self.skip.append(len(self.stack))
            return
        if tag in BLOCK:
            self._flush()
            self.cur = [tag, []]
        elif tag == 'br' and self.cur:
            self.cur[1].append(' ')

    def handle_endtag(self, tag):
        if tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            if self.skip and self.skip[-1] > len(self.stack):
                self.skip.pop()
            if t == self.root_tag:
                self.depth_root -= 1
            if t in BLOCK and self.cur and self.cur[0] == t:
                self._flush()
            if t == tag:
                break

    def handle_data(self, data):
        if self.depth_root and not self.skip and self.cur is not None:
            self.cur[1].append(data)

    def _flush(self):
        if self.cur:
            txt = re.sub(r'\s+', ' ', ''.join(self.cur[1])).strip()
            if txt:
                self.blocks.append((self.cur[0], txt))
        self.cur = None


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xml'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.geturl(), r.read()


def html_blocks(raw):
    s = raw.decode('utf8', errors='replace')
    for root in ('main', 'article', 'body'):
        if f'<{root}' in s:
            p = MainText(root)
            p.feed(s)
            p._flush()
            if sum(len(t) for _, t in p.blocks) > 400:
                return p.blocks
    return []


def medlineplus_topic(title):
    """MedlinePlus web servisi (wsearch.nlm.nih.gov) — tam başlık eşleşen sağlık konusu, FullSummary (kamu malı)."""
    q = urllib.parse.urlencode({'db': 'healthTopics', 'term': f'title:"{title}"', 'retmax': 10})
    url = 'https://wsearch.nlm.nih.gov/ws/query?' + q
    _, raw = fetch(url)
    s = raw.decode('utf8')
    for m in re.finditer(r'<document rank="\d+" url="([^"]+)">(.*?)</document>', s, re.S):
        doc_url, body = m.group(1), m.group(2)
        t = re.search(r'<content name="title">(.*?)</content>', body, re.S)
        t = re.sub(r'<[^>]+>', '', html.unescape(t.group(1))).strip() if t else ''
        if t.lower() != title.lower():
            continue
        fs = re.search(r'<content name="FullSummary">(.*?)</content>', body, re.S)
        if not fs:
            continue
        frag = html.unescape(fs.group(1))
        frag = re.sub(r'<span class="qt\d">(.*?)</span>', r'\1', frag)
        # FullSummary: başlıklar düz metin, paragraflar <p>/<li>; başlık satırlarını ayır
        frag = re.sub(r'(</p>|</ul>|</ol>|^)\s*([^<][^<]*?\?)\s*(?=<p>|<ul>)', r'\1<h3>\2</h3>', frag)
        p = MainText('body')
        p.feed('<body>' + frag + '</body>')
        p._flush()
        return url, doc_url, raw, p.blocks
    raise RuntimeError(f'MedlinePlus konu bulunamadı: {title}')


def sections(blocks):
    """Başlıklara göre bölümler [(başlık, [satırlar])]; ilk başlıktan önceki metin 'Overview'."""
    out, head, lines = [], 'Overview', []
    for tag, txt in blocks:
        if tag in ('h1', 'h2', 'h3', 'h4'):
            if lines:
                out.append((head, lines))
            head, lines = txt, []
        else:
            lines.append(('- ' if tag == 'li' else '') + txt)
    if lines:
        out.append((head, lines))
    return out


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf8')).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--accessed', default=dt.date.today().isoformat())
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    EXT.mkdir(parents=True, exist_ok=True)
    rows = []
    for sid, src, kind, ref, dkey in SOURCES:
        if a.only and sid not in a.only:
            continue
        lic = LIC[src]
        if kind == 'topic':
            fetched_url, url, raw, blocks = medlineplus_topic(ref)
        else:
            url, raw = fetch(ref)
            fetched_url = url
            blocks = html_blocks(raw)
        secs = sections(blocks)
        kept = [(h, ls) for h, ls in secs if not EXCLUDE_HEADING.search(h)]
        dropped = [h for h, _ in secs if EXCLUDE_HEADING.search(h)]
        title = next((t for tg, t in blocks if tg == 'h1'), ref if kind == 'topic' else sid)
        body = '\n\n'.join(f'## {h}\n\n' + '\n'.join(ls) for h, ls in kept)
        md = (f'---\nid: {sid}\ntitle: {json.dumps(title, ensure_ascii=False)}\nurl: {url}\npublisher: {lic["publisher"]}\n'
              f'accessed: {a.accessed}\nlicense: {json.dumps(lic["license"], ensure_ascii=False)}\n'
              f'attribution: {json.dumps(lic["attribution"], ensure_ascii=False)}\ndisease_key: {dkey}\n---\n\n'
              f'# {title}\n\n{body}\n')
        f = EXT / f'{sid}.md'
        f.write_text(md, encoding='utf8', newline='\n')
        rows.append(dict(id=sid, publisher=lic['publisher'], url=url, fetched_via=fetched_url, accessed=a.accessed,
                         license=lic['license'], attribution=lic['attribution'], policy_url=lic['policy_url'],
                         disease_key=dkey, title=title, sections_kept=[h for h, _ in kept], sections_excluded=dropped,
                         raw_sha256=sha(raw), text_file=f'kb/external/{sid}.md', text_sha256=sha(md.encode('utf8')),
                         chars=len(body)))
        print(f'{sid:18s} {len(body):6d} karakter  bölüm {len(kept)} (+{len(dropped)} dışarıda)', flush=True)
        time.sleep(0.5)
    if a.only:
        return
    out = dict(phase='XLVIII', generated_by='app/backend/assistant/scripts/fetch_external.py', accessed=a.accessed,
               note='Metin parçaları kaynak sayfadan değiştirilmeden alındı; tedavi/ilaç/doz bölümleri asistan kuralları '
                    'gereği seçilmedi. WHO ve NHLBI yalnız bağlantıdır.',
               text_sources=rows, link_only=LINK_ONLY)
    (KB / 'sources.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf8', newline='\n')
    print('sources.json yazıldı:', len(rows), 'metin kaynağı,', len(LINK_ONLY), 'yalnız bağlantı')


if __name__ == '__main__':
    sys.exit(main())
