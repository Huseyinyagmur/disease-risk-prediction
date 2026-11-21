"""Phase XLVIII — asistan güvenlik filtreleri (LLM'den ÖNCE ve SONRA, kod düzeyinde).

Ön filtre sırası: acil durum → komut enjeksiyonu → olasılık sorusu → tanı/tedavi/doz isteği → kapsam dışı.
Ön filtreye takılan soru LLM'e hiç gitmez; sabit yanıt döner (assistant_config.json > texts_tr).
Son kontrol: yasak ifadeler (doz birimi, "tanınız", "kesinlikle" …), kaynakta olmayan sayı, kaynak dışı URL → güvenli yanıt.
Bağlam etiketleri: yalnız kapalı sözlükten (hastalık anahtarı × durum kodu × şema alan adı) üretilir; ham değer giremez.
"""
import re
import unicodedata

_TR = str.maketrans({'ı': 'i', 'İ': 'i', 'I': 'i', 'ş': 's', 'Ş': 's', 'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
                     'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c', 'â': 'a', 'î': 'i', 'û': 'u', '’': "'", '‘': "'"})


def norm(s: str) -> str:
    """Türkçe sadeleştirme + küçük harf + boşluk birleştirme; eşleşme için başa/sona boşluk eklenir."""
    s = (s or '').translate(_TR)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r'[\s​]+', ' ', s)
    return f' {s.strip()} '


def hits(text_norm: str, words) -> list:
    return [w for w in words if w in text_norm]


_RX_CACHE = {}


def _rx(patterns):
    key = tuple(patterns)
    if key not in _RX_CACHE:
        _RX_CACHE[key] = [re.compile(p) for p in patterns]
    return _RX_CACHE[key]


def classify(question: str, kw: dict, patterns: dict = None) -> tuple:
    """Döner (rota, eşleşen_sayısı). rota: emergency_self_harm | emergency | injection | probability | medical |
    off_topic | None. Acil: anahtar kelime VEYA genel kalıp (Phase XLVIII v2: assistant_config > emergency_patterns,
    self_harm_patterns). Eşleşen kelimeler döndürülmez/loglanmaz (gizlilik); yalnız sayısı."""
    n = norm(question)
    pt = patterns or {}
    sh = [r for r in _rx(pt.get('self_harm', [])) if r.search(n)]
    if sh:
        return 'emergency_self_harm', len(sh)
    em = [r for r in _rx(pt.get('emergency', [])) if r.search(n)]
    if em:
        return 'emergency', len(em)
    for route, key in (('emergency', 'emergency'), ('injection', 'injection'), ('probability', 'probability'),
                       ('medical', 'medical_request')):
        h = hits(n, kw[key])
        if h:
            return route, len(h)
    off = hits(n, kw['off_topic'])
    if off and not hits(n, kw['domain']):
        return 'off_topic', len(off)
    return None, 0


def expansions(question: str, table: dict) -> str:
    """Türkçe terim → İngilizce kaynak terimi (yalnız erişim sorgusu; LLM'e giden soru değişmez)."""
    n = norm(question)
    return ' '.join(v for k, v in table.items() if k in n)


def has_domain(question: str, kw: dict) -> bool:
    return bool(hits(norm(question), kw['domain']))


# Sayı maskeleme: soru metnindeki sayısal değerler (ör. "ALT 85", "HbA1c 6,4") LLM bağlamına girmez.
# "tip 1 / tip 2" diyabet ve "112" korunur.
_NUM = re.compile(r'(?<![\w])(?!(?<=tip )\d\b)(?!112\b)\d+(?:[.,]\d+)?(?:\s?(?:%|mg/dl|mg/l|mmol/l|g/dl|u/l|kpa|mmhg|kg|cm|yas|yaşında|yaşındayım))?',
                  re.IGNORECASE)


def mask_numbers(q: str) -> tuple:
    out, n = _NUM.subn('[sayı]', q)
    return out, n


# ------------------------------------------------------------------ son kontrol
# doz birimi (ör. "500 mg"); laboratuvar birimleri (mg/dL, mg/L, mL/dk) doz sayılmaz
DOSE_RE = re.compile(r'\d+(?:[.,]\d+)?\s?(?:mg|mcg|µg|μg|miligram|mikrogram|ml|mililitre|iu|ünite|unite|units?|tablet|kapsül|kapsul|damla)(?![/\w])',
                     re.IGNORECASE)
FORBIDDEN = ['tanınız', 'tanin ', 'teşhisiniz', 'kesinlikle', 'kesin olarak', 'hastasınız', 'hastalığınız var',
             'hastalığınız vardır', 'ilacınızı', 'almalısınız', 'kullanmalısınız', 'başlamalısınız', 'bırakmalısınız',
             'dozunu', 'dozu ', 'dozajı', 'reçete', 'olasılığınız', 'olasılık değeri', 'yüzde ']
URL_RE = re.compile(r'https?://[^\s)\]>"]+', re.IGNORECASE)


def _nums(s: str) -> set:
    out = set()
    for m in re.finditer(r'\d+(?:[.,]\d+)?', s):
        v = m.group(0).replace(',', '.')
        v = v.rstrip('0').rstrip('.') if '.' in v else v
        out.add(v)
    return out


_PCT = re.compile(r'%\s?(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s?%')


def _pcts(s: str) -> set:
    return {(m.group(1) or m.group(2)).replace(',', '.') for m in _PCT.finditer(s)}


def postcheck(answer: str, context_text: str, allowed_urls: set) -> list:
    """Yanıt kurallara uyuyor mu? Döner: ihlal kodları (boş = uygun). Metin içeriği döndürülmez."""
    v = []
    low = answer.lower()
    if DOSE_RE.search(answer):
        v.append('dose_unit')
    for w in FORBIDDEN:
        if w in low:
            v.append('forbidden_phrase')
            break
    # yüzde yalnız kaynakta aynı değerle geçiyorsa (ör. "%95 GA"); aksi halde olasılık izlenimi riski → ihlal
    ctx_pct = _pcts(context_text)
    ans_pct = _pcts(answer)
    if (ans_pct - ctx_pct) or ('%' in answer and not ans_pct):
        v.append('percent')
    extra = _nums(answer) - _nums(context_text) - {'112'}
    extra = {x for x in extra if not re.fullmatch(r'[1-9]', x)}          # [1]–[9] kaynak numaraları ve tek basamak
    if extra:
        v.append('number_not_in_sources')
    for u in URL_RE.findall(answer):
        if u.rstrip('.,;') not in allowed_urls:
            v.append('url_not_in_kb')
            break
    return v


# ------------------------------------------------------------------ bağlam etiketleri
OUTCOMES = {'ESIK_USTU': 'eşik üstü', 'ESIK_ALTI': 'eşik altı', 'ABSTAIN': 'sonuç üretilmedi',
            'NOT_APPLICABLE': 'bu analiz uygun değil', 'ECG_REQUIRED': 'EKG kaydı gerekiyor'}


def context_labels(results, disease_names: dict, field_label) -> list:
    """Yalnız kapalı sözlük: bilinmeyen hastalık/durum düşer; eksik alanlar şema alan adıysa sade etikete çevrilir,
    değilse düşer. Sayı veya serbest metin bağlama giremez."""
    out = []
    for r in results:
        dk, oc = r.get('disease_key'), r.get('outcome')
        if dk not in disease_names or oc not in OUTCOMES:
            continue
        line = f'{disease_names[dk]}: {OUTCOMES[oc]}'
        miss = [field_label(f) for f in (r.get('missing_fields') or []) if isinstance(f, str)]
        miss = [m for m in miss if m]
        if miss and oc in ('ABSTAIN', 'NOT_APPLICABLE', 'ECG_REQUIRED'):
            line += ' — eksik: ' + ', '.join(dict.fromkeys(miss))
        out.append(line)
    return list(dict.fromkeys(out))
