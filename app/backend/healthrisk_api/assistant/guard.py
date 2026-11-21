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


# ------------------------------------------------------------------ v3: ortak anahtar normalizasyonu + kural dili
# Ünsüz yumuşaması katlama (soluk/soluğum → soluk…/soluk…; göğüs → kokus): kurala ve girdiye AYNI fonksiyon uygulanır.
_FOLD = str.maketrans({'g': 'k', 'd': 't', 'b': 'p'})
GAP = '…'


def key(s: str) -> str:
    """v3 eşleşme anahtarı: norm() (küçük harf, Türkçe→ASCII, boşluk) + g→k, d→t, b→p katlama. Başta/sonda boşluk."""
    return norm(s).translate(_FOLD)


def _kw(w: str) -> str:
    """Anahtar kelime (baş/son boşlukları anlamlı olabilir: 'doz ', 'alt ') için aynı dönüşüm, boşluk korunarak."""
    lead, trail = w[:len(w) - len(w.lstrip())], w[len(w.rstrip()):]
    return lead + key(w).strip() + trail


def compile_rule(rule: str):
    """'göğs|göğüs … ağrı|sıkış' → düzenli ifade. Boşluk: bitişik kelime; '…': araya en çok 4 sözcük;
    her parça kelime başı kökü (\\w* ile çekim); '|': seçenek. Parçalar key() ile normalleştirilir."""
    segs = []
    for seg in rule.split(GAP):
        words = []
        for tok in seg.split():
            alts = sorted({key(a).strip() for a in tok.split('|') if a.strip()}, key=len, reverse=True)
            words.append(r'\b(?:' + '|'.join(re.escape(a) for a in alts) + r")[\w']*")
        segs.append(r'\s+'.join(words))
    return re.compile(r'(?:\s+\S+){0,4}\s+'.join(segs))


class Rules:
    """assistant_config.json'daki v3 kural kümeleri (derlenmiş)."""
    def __init__(self, cfg: dict):
        self.emergency = [compile_rule(r) for r in cfg.get('emergency_rules', []) + [x['rule'] for x in cfg.get('red_flag_rules', [])]]
        self.self_harm = [compile_rule(r) for r in cfg.get('self_harm_rules', [])]
        self.medical = [compile_rule(r) for r in cfg.get('medical_rules', [])]
        self.medical_exclude = [key(x).strip() for x in cfg.get('medical_exclude', [])]
        t = cfg.get('emergency_tier', {})
        self.current = [_kw(x) for x in t.get('current', [])]
        self.past = [_kw(x) for x in t.get('past', [])]
        self.relatives = [key(x).strip() for x in t.get('relatives', [])]
        self.self_words = {key(x).strip() for x in t.get('self_words', [])}
        self.general = [_kw(x) for x in t.get('general', [])]
        self.fp_exclude = {key(x).strip() for x in t.get('first_person_exclude', [])}


# 1. tekil/çoğul çekim veya iyelik (katlanmış biçimde: -ım/-im/-um → im/um; -dım → tim; -yorum; miyim/muyum …)
_FIRST = re.compile(r'^\w{2,}(?:iyorum|uyorum|iyoruz|uyoruz|imiz|umuz|miyim|muyum|miyiz|muyuz|yim|yum|im|um|tim|tum|sim|sum)'
                    r'(?:te|ta|ten|tan|e|a|i|u|ı|la|le|tir|tur|ki|ten)?$')


def emergency_tier(question: str, rules: Rules) -> str:
    """'personal' (LLM yok, sabit 112) veya 'general' (112 uyarı kutusu + RAG). Belirsiz → 'personal'."""
    k = key(question)
    words = re.findall(r"[a-z']+", k)
    current = any(c in k for c in rules.current)
    past = any(p in k for p in rules.past)
    relative = any(w.startswith(r) for w in words for r in rules.relatives)
    self_word = any(w in rules.self_words for w in words)
    first = any(_FIRST.match(w.replace("'", '')) and w not in rules.fp_exclude for w in words)
    personal = current or relative or self_word or (first and not past)
    general = any(g in k for g in rules.general)
    return 'general' if general and not personal else 'personal'


def classify(question: str, kw: dict, rules: 'Rules' = None, skip_emergency: bool = False) -> tuple:
    """Döner (rota, eşleşen_sayısı). rota: emergency_self_harm | emergency | emergency_general | injection |
    probability | medical | off_topic | None. Tüm eşleşmeler key() normalizasyonuyla (v3). Kendine zarar kademesizdir.
    Eşleşen kelimeler döndürülmez/loglanmaz (gizlilik); yalnız sayısı."""
    n = key(question)
    r = rules
    if r is not None:
        sh = [x for x in r.self_harm if x.search(n)]
        if sh:
            return 'emergency_self_harm', len(sh)
    if not skip_emergency:
        em = [x for x in (r.emergency if r else []) if x.search(n)] + hits(n, [_kw(w) for w in kw['emergency']])
        if em:
            return ('emergency_general' if r is not None and emergency_tier(question, r) == 'general' else 'emergency'), len(em)
    for route, k in (('injection', 'injection'), ('probability', 'probability')):
        h = hits(n, [_kw(w) for w in kw[k]])
        if h:
            return route, len(h)
    nm = n
    for ex in (r.medical_exclude if r else []):
        nm = nm.replace(ex, ' ')
    med = hits(nm, [_kw(w) for w in kw['medical_request']]) + [x for x in (r.medical if r else []) if x.search(nm)]
    if med:
        return 'medical', len(med)
    off = hits(n, [_kw(w) for w in kw['off_topic']])
    if off and not hits(n, [_kw(w) for w in kw['domain']]):
        return 'off_topic', len(off)
    return None, 0


def expansions(question: str, table: dict) -> str:
    """Türkçe terim → İngilizce kaynak terimi (yalnız erişim sorgusu; LLM'e giden soru değişmez)."""
    n = norm(question)
    return ' '.join(v for k, v in table.items() if k in n)


def has_domain(question: str, kw: dict) -> bool:
    return bool(hits(key(question), [_kw(w) for w in kw['domain']]))


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
