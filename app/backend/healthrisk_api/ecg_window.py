"""EKG ön adımı: "ilk 10 saniye" penceresi — kilitli AF-ECGDELI-OCTAVE-v1 pipeline'ının ÖNÜNDE ayrı adım.

Kaynak (birebir kopya, kullanıcı kararı Phase XLIV):
  phase_xxxiii/scripts/t3_extract.py :: read_first10s (satır 61–68)
    dosya SHA256     2abc9e677a6ac6760e03bdb25a272d3b4a898676c08e5bfe117e58932a293dca
    fonksiyon SHA256 4818ea0622a496813d388143c41725582685c396ed4a70a40f3bb3f01dfd8471 (ast kaynak parçası)
  Aynı mantık: phase_xxix/scripts/t3_extract.py :: read_first10s (satır 38–45; dosya SHA256 58687dba…c19a99,
  fonksiyon SHA256 4054f472…db1ce1) — iki gövde yalnız kayıt yolu satırında farklıdır.
Tek değişiklik: kayıt yolu fazın `record_base(rel)` yardımcısı yerine doğrudan `record_path` argümanıdır; kilitli modül
(`pl`) ise argüman olarak verilir. Gövdenin geri kalanı karakter karakter aynıdır ve başlangıçta (verify_source) kaynak
dosyadan ast ile okunan gövdeyle karşılaştırılır; uyuşmazlıkta /ecg/af devre dışı kalır.
wfdb: kilitli pipeline'ın vendored wfdb 4.3.1'i (pl.WFDB_VENDOR), Phase XXIX/XXXIII'te olduğu gibi.
Kilit dosyası (phase_xxviii/config/af_pipeline_lock.json) ve af_pipeline_v1.py DEĞİŞTİRİLMEZ."""
import ast
import hashlib
import inspect
import textwrap

from .paths import V2

SOURCE_FILE = 'phase_xxxiii/scripts/t3_extract.py'
SOURCE_FILE_SHA256 = '2abc9e677a6ac6760e03bdb25a272d3b4a898676c08e5bfe117e58932a293dca'
SOURCE_FUNC_SHA256 = '4818ea0622a496813d388143c41725582685c396ed4a70a40f3bb3f01dfd8471'
SOURCE_LINES = (61, 68)
XXIX_FILE = 'phase_xxix/scripts/t3_extract.py'
XXIX_FILE_SHA256 = '58687dbaa7280b7eed736c73c30df93396f2303c951a5626f3a5feff47c19a99'
XXIX_FUNC_SHA256 = '4054f472352ef6afd9f46caee349af594e429bbd6cfb3c96e2800bc965db1ce1'
PATH_SUBSTITUTION = ('str(record_base(rel))', 'str(record_path)')


def read_first10s(record_path, pl):
    """Phase XXIX sarmalayıcısıyla aynı: ilk 5000 örnek; kilitli read_wfdb_500 ile aynı kontroller."""
    import wfdb
    sig, f = wfdb.rdsamp(str(record_path), sampto=5000)
    assert f['fs'] == pl.FS and sig.shape == (5000, 12), (f['fs'], sig.shape)
    assert [u.lower() for u in f['units']] == ['mv'] * 12
    assert [n.upper() for n in f['sig_name']] == [l.upper() for l in pl.LEADS], f['sig_name']
    return sig


def _func_segment(path, name):
    src = (V2 / path).read_text(encoding='utf8')
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(src, fn), fn


def _body_lines(seg):
    return [l.strip() for l in seg.splitlines()[1:] if l.strip()]       # imza satırı hariç


def verify_source():
    """Döner: sorun listesi (boş = doğrulandı)."""
    probs = []
    for rel, fsha, fn_sha in ((SOURCE_FILE, SOURCE_FILE_SHA256, SOURCE_FUNC_SHA256), (XXIX_FILE, XXIX_FILE_SHA256, XXIX_FUNC_SHA256)):
        p = V2 / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != fsha:
            probs.append(f'{rel} SHA256 belgelenen değerle uyuşmuyor')
            continue
        seg, _ = _func_segment(rel, 'read_first10s')
        if hashlib.sha256(seg.encode()).hexdigest() != fn_sha:
            probs.append(f'{rel} read_first10s SHA256 uyuşmuyor')
    if probs:
        return probs
    seg, fn = _func_segment(SOURCE_FILE, 'read_first10s')
    if (fn.lineno, fn.end_lineno) != SOURCE_LINES:
        probs.append('kaynak fonksiyon satır aralığı değişti')
    src_body = [l.replace(*PATH_SUBSTITUTION) for l in _body_lines(seg)]
    mine = _body_lines(textwrap.dedent(inspect.getsource(read_first10s)))
    if src_body != mine:
        probs.append('ön adım gövdesi kaynak fonksiyonla birebir değil')
    return probs
