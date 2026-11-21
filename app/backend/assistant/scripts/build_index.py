"""Phase XLVIII — asistan bilgi tabanı: iç belgeleri üretir, tüm belgeleri parçalar, yerel Ollama gömme modeliyle gömer.

Adımlar (yeniden çalıştırılabilir; ağ gerekmez, yalnız 127.0.0.1:11434):
  1. İç belgeler (kb/internal/*.md): app_config.json > ui (terim sözlüğü, "Ne yapmalıyım?", kanıt açıklamaları, analiz
     gereksinimleri), Hakkında sayfası metni (frontend/src/pages/About.tsx'ten çıkarılır), 13 model kartı
     (app/docs/model_cards/*.md; seçili bölümler). Metin UYDURULMAZ: yalnız bu kaynaklardan kopyalanır.
  2. Dış belgeler: kb/external/*.md (fetch_external.py; kb/sources.json'daki SHA256 doğrulanır).
  3. Parçalama: '## ' bölümleri, en çok MAX_CHARS karakter (satır sınırında bölünür).
  4. Gömme: assistant_lock.json > embed_model (ad + digest doğrulanır). Vektörler L2-normalize, float32.
Çıktı: kb/index/chunks.jsonl, kb/index/embeddings.f32 (ham little-endian float32, satır = parça), kb/index/manifest.json
(her dosyanın SHA256'sı, model digest'i, parametreler). Sunucu başlangıçta manifest SHA'larını doğrular.

Kullanım: app/backend/.venv/Scripts/python.exe -B app/backend/assistant/scripts/build_index.py [--internal-only]
"""
import argparse
import hashlib
import json
import re
import sys
from array import array
from pathlib import Path

import httpx

ASSIST = Path(__file__).resolve().parents[1]               # app/backend/assistant
BACKEND = ASSIST.parent
APP = BACKEND.parent
KB = ASSIST / 'kb'
INT = KB / 'internal'
IDX = KB / 'index'
LOCK = ASSIST / 'assistant_lock.json'
CARDS = APP / 'docs' / 'model_cards'
ABOUT_TSX = APP / 'frontend' / 'src' / 'pages' / 'About.tsx'
APP_CONFIG = BACKEND / 'config' / 'app_config.json'
OLLAMA = 'http://127.0.0.1:11434'
MAX_CHARS = 1200
# model kartlarından alınan bölümler (numara önekleri); dosya yolları/TRIPOD/etik/alt grup tabloları ve sayısal eşik (10)
# ile kalibrasyon (11) bölümleri alınmaz (uygulama eşik değeri ve olasılık göstermez; Phase XLVIII geliştirme kararı)
CARD_SECTIONS = ('0.', '1.', '2.', '3.', '4.', '5.', '7.', '12.', '13.', '15.', '16.')


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf8')).hexdigest()


def front(meta):
    return '---\n' + ''.join(f'{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, str) and (":" in v or "\"" in v) else v}\n'
                             for k, v in meta.items()) + '---\n\n'


def write(path, meta, body):
    path.write_text(front(meta) + body.rstrip() + '\n', encoding='utf8', newline='\n')


# ------------------------------------------------------------------ 1. iç belgeler
def about_text():
    """About.tsx: <h2> başlıkları ve <li>/<p> metinleri (JSX ifadeleri ve etiketler çıkarılır; yalnız sabit metin)."""
    s = ABOUT_TSX.read_text(encoding='utf8')
    out = []
    for m in re.finditer(r'<(h2|li|p)\b[^>]*>(.*?)</\1>', s, re.S):
        tag, inner = m.group(1), m.group(2)
        if '{' in inner and '}' in inner:
            inner = re.sub(r'\{[^{}]*\}', '', inner)
        txt = re.sub(r'<[^>]+>', '', inner)
        txt = re.sub(r'\s+', ' ', txt).strip()
        if not txt or txt in ('Yükleniyor…',):
            continue
        out.append(('## ' if tag == 'h2' else '- ' if tag == 'li' else '') + txt)
    return out


def build_internal(out=None):
    out = Path(out) if out else INT
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(APP_CONFIG.read_text(encoding='utf8'))
    ui = cfg['ui']
    dn = ui['disease_names_tr']
    common = dict(publisher='HealthRisk AI Research V2 (proje içi belge)', accessed='—', license='proje içi (MIT)')
    docs = []

    # terim sözlüğü + durum terimleri
    b = ['# Terim sözlüğü', '']
    for g in ui['glossary_tr']:                       # her terim ayrı bölüm (ayrı parça) — erişimde seyrelmesin
        b += [f'## {g["term"]} ({g["code"]})', '', f'{g["term"]}: {g["text"]}', '']
    b += ['## Sonuç kartındaki durum adları', '']
    for kind, title in (('result', 'Sonuç durumu'), ('decision', 'Araştırma sınıflaması'), ('eligibility', 'Canlı panel durumu')):
        b += [f'- {title} {code}: "{txt}"' for code, txt in ui['terms_tr'][kind].items()]
    b += ['', '## Karar kutusu notu', '', ui['text_tr']['decision_note'], ui['text_tr']['results_sub']]
    docs.append(('int_glossary', 'Terim sözlüğü', 'app_config.json > ui.glossary_tr / terms_tr', None, b))

    # "Ne yapmalıyım?" yönlendirmeleri
    names = {'ESIK_USTU': 'eşik üstü', 'ESIK_ALTI': 'eşik altı', 'ABSTAIN': 'sonuç üretilmedi', 'NOT_APPLICABLE': 'uygun değil'}
    b = ['# "Ne yapmalıyım?" yönlendirmeleri', '', 'Sonuç kartındaki "Ne yapmalıyım?" kutusunun metinleri. Tanı veya tedavi önerisi değildir.', '']
    b += ['## Genel (tüm analizler)', ''] + [f'- {names[k]}: {v}' for k, v in ui['next_steps_tr']['_default'].items()]
    for dk, d in ui['next_steps_tr'].items():
        if dk == '_default':
            continue
        b += ['', f'## {dn.get(dk, dk)}', ''] + [f'- {names[k]}: {v}' for k, v in d.items()]
    docs.append(('int_next_steps', '"Ne yapmalıyım?" yönlendirmeleri', 'app_config.json > ui.next_steps_tr', None, b))

    # kanıt düzeyleri
    b = ['# Kanıt düzeyleri ve modül etiketleri', '', '## Kanıt düzeyi türleri', '']
    b += [f'- {g["term"]}: {g["text"]}' for g in ui['glossary_tr'] if g['code'] in ('internal_test', 'temporal', 'external', 'module_label')]
    b += ['', '## Modül grupları', ''] + [f'- {g["title"]} ({g["module_label"]}): {g["description"]}' for g in ui['analysis_groups_tr']]
    for mid, txt in ui['evidence_plain_tr'].items():
        b += ['', f'## {ui["model_names_tr"].get(mid, mid)} — kanıt düzeyi', '', f'Modül etiketi: {cfg["module_labels"].get(mid, cfg["module_labels"]["_default"])}.', txt]
    docs.append(('int_evidence', 'Kanıt düzeyi açıklamaları', 'app_config.json > ui.evidence_plain_tr / analysis_groups_tr', None, b))

    # analiz gereksinimleri
    b = ['# Analizler ve gerekli bilgiler', '']
    for dk, nm in dn.items():
        b += [f'## {nm}', '', ui['disease_hints_tr'].get(dk, 'BULUNAMADI'), '']
    b += ['## EKG ile AF', '', ui['text_tr']['af_form_note']]
    docs.append(('int_analyses', 'Analizler ve gerekli bilgiler', 'app_config.json > ui.disease_hints_tr', None, b))

    # Hakkında
    b = ['# Hakkında', ''] + about_text() + ['', '## Araştırma uyarısı', '', cfg['disclaimer_tr'], '', '## Sunucu gizlilik politikası', '', cfg['privacy']['policy']]
    docs.append(('int_about', 'Hakkında', 'frontend/src/pages/About.tsx + app_config.json', None, b))

    for did, title, src, dkey, lines in docs:
        write(out / f'{did}.md', dict(id=did, title=title, source_ref=src, **common), '\n'.join(lines))

    # model kartları (13)
    n = 0
    for f in sorted(CARDS.glob('*.md')):
        if f.name == 'README.md':
            continue
        mid = f.stem
        s = f.read_text(encoding='utf8')
        title = s.splitlines()[0].lstrip('# ').strip()
        parts = re.split(r'(?m)^## ', s)
        keep = [p for p in parts[1:] if p.startswith(CARD_SECTIONS)]
        body = f'# {title}\n\n' + '\n'.join('## ' + p.rstrip() + '\n' for p in keep)
        write(out / f'mc_{mid}.md', dict(id=f'mc_{mid}', title=title, source_ref=f'app/docs/model_cards/{mid}.md',
                                         card_sha256=sha(f.read_bytes()), **common), body)
        n += 1
    print('iç belgeler:', len(docs), '+ model kartı', n)


# ------------------------------------------------------------------ 2–3. parçalama
def parse_md(path):
    s = path.read_text(encoding='utf8')
    m = re.match(r'---\n(.*?)\n---\n\n', s, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(': ')
        meta[k] = json.loads(v) if v.startswith('"') else v
    return meta, s[m.end():]


def split_long(text, limit):
    out, cur = [], ''
    for line in text.split('\n'):
        while len(line) > limit:                        # çok uzun tek satır: cümle sınırında böl
            cut = line.rfind('. ', 0, limit)
            cut = cut + 1 if cut > limit // 3 else limit
            if cur:
                out.append(cur)
                cur = ''
            out.append(line[:cut].strip())
            line = line[cut:].strip()
        if len(cur) + len(line) + 1 > limit and cur:
            out.append(cur)
            cur = ''
        cur = (cur + '\n' + line) if cur else line
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out if x.strip()]


def chunk_doc(path, kind):
    meta, body = parse_md(path)
    title = meta.get('title', path.stem)
    secs = re.split(r'(?m)^## ', body)
    chunks = []
    head0 = secs[0].strip()
    items = [('', head0)] if head0 and not re.fullmatch(r'#[^\n]*', head0) else []
    for p in secs[1:]:
        h, _, t = p.partition('\n')
        items.append((h.strip(), t.strip()))
    for h, t in items:
        t = re.sub(r'(?m)^# .*$', '', t).strip()
        if not t:
            continue
        for i, piece in enumerate(split_long(t, MAX_CHARS)):
            chunks.append(dict(doc_id=meta['id'], kind=kind, title=title, section=h, part=i,
                               url=meta.get('url'), source_ref=meta.get('source_ref'), publisher=meta.get('publisher'),
                               attribution=meta.get('attribution'), disease_key=meta.get('disease_key'), text=piece))
    return chunks


def embed(texts, model):
    out = []
    with httpx.Client(base_url=OLLAMA, timeout=300) as c:
        for i in range(0, len(texts), 16):
            r = c.post('/api/embed', json=dict(model=model, input=texts[i:i + 16], keep_alive='5m'))
            r.raise_for_status()
            out += r.json()['embeddings']
    return out


def norm(v):
    s = sum(x * x for x in v) ** 0.5
    return [x / s for x in v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--internal-only', action='store_true')
    a = ap.parse_args()
    build_internal()
    if a.internal_only:
        return
    lock = json.loads(LOCK.read_text(encoding='utf8'))
    em = lock['embed_model']
    tags = httpx.get(OLLAMA + '/api/tags', timeout=10).json()['models']
    have = {m['name']: m['digest'] for m in tags}
    if have.get(em['name']) != em['digest']:
        sys.exit(f'DUR: gömme modeli digest uyuşmuyor: {em["name"]} {have.get(em["name"])} != {em["digest"]}')
    src = json.loads((KB / 'sources.json').read_text(encoding='utf8'))
    for r in src['text_sources']:                         # dış metinler kilitli sürümle aynı mı
        h = sha((ASSIST / r['text_file']).read_bytes())
        if h != r['text_sha256']:
            sys.exit(f'DUR: {r["text_file"]} SHA256 sources.json ile uyuşmuyor')
    chunks = []
    for f in sorted(INT.glob('*.md')):
        chunks += chunk_doc(f, 'internal')
    for f in sorted((KB / 'external').glob('*.md')):
        chunks += chunk_doc(f, 'external')
    for i, c in enumerate(chunks):
        c['chunk_id'] = f'{c["doc_id"]}#{i:04d}'
    # gömülen metin: belge başlığı + bölüm + parça (bağlam için); yanıtta yalnız 'text' kullanılır
    vecs = [norm(v) for v in embed([f'{c["title"]} — {c["section"]}\n{c["text"]}' for c in chunks], em['name'])]
    IDX.mkdir(parents=True, exist_ok=True)
    cj = ''.join(json.dumps(c, ensure_ascii=False, sort_keys=True) + '\n' for c in chunks).encode('utf8')
    (IDX / 'chunks.jsonl').write_bytes(cj)
    arr = array('f', [x for v in vecs for x in v])
    if sys.byteorder != 'little':
        arr.byteswap()
    (IDX / 'embeddings.f32').write_bytes(arr.tobytes())
    docs = sorted({c['doc_id'] for c in chunks})
    man = dict(phase='XLVIII', generated_by='app/backend/assistant/scripts/build_index.py', embed_model=em,
               dim=len(vecs[0]), n_chunks=len(chunks), n_docs=len(docs), max_chars=MAX_CHARS,
               files={'chunks.jsonl': sha(cj), 'embeddings.f32': sha(arr.tobytes()),
                      '../sources.json': sha((KB / 'sources.json').read_bytes())},
               documents={f'{k}/{p.name}': sha(p.read_bytes()) for k in ('internal', 'external') for p in sorted((KB / k).glob('*.md'))})
    (IDX / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf8', newline='\n')
    print('parça', len(chunks), 'belge', len(docs), 'boyut', man['dim'])


if __name__ == '__main__':
    main()
