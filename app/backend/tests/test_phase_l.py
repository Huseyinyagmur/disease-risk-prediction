"""Phase L: asistan yanıt hatası düzeltmeleri ve arayüz metin yapılandırması.

1. Bilgi tabanı: "eşik üstü" ve "eşik altı" ayrı parçalarda; "dışlamaz" yalnız eşik altı parçalarında.
2. Bağlam sabitleme (label_pins): bir etiketin durumuna AİT OLMAYAN yönlendirme parçası bağlama girmez.
3. Son kontrol: eşik üstüne "dışlamaz" bağlayan yanıt reddedilir; cümleye bağlanmayan / yinelenen atıflar temizlenir.
4. app_config: AF eşik üstü yönlendirmesi ve ritim bazlı ek sınırlılıklar (kaynak phase_xxxiii)."""
import json

import pytest

from healthrisk_api.assistant import guard
from healthrisk_api.assistant.engine import ASSIST_DIR, _renumber

from test_phase48_assistant import FakeOllama, _assistant  # noqa: F401  (aynı sahte Ollama)
from healthrisk_api import main

CFG = json.loads((ASSIST_DIR / 'assistant_config.json').read_text(encoding='utf8'))
CHUNKS = [json.loads(x) for x in (ASSIST_DIR / 'kb/index/chunks.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
INTERNAL = [c for c in CHUNKS if c['doc_id'] in ('int_glossary', 'int_next_steps')]


@pytest.fixture(autouse=True, scope='module')
def _restore_globals():
    """API testi sayaç ve asistan nesnesini değiştirir; test_privacy'nin bilinen yol kümesi etkilenmesin (XLVIII ile aynı)."""
    by = dict(main.STATS.by)
    old = main._ASSISTANT
    yield
    main.STATS.by = by
    main._ASSISTANT = old


def _n(s):
    return guard.norm(s)


# ------------------------------------------------------------------ 1. bilgi tabanı parçaları
def test_kb_threshold_terms_are_separate_chunks():
    secs = {c['section'] for c in CHUNKS if c['doc_id'] == 'int_glossary'}
    assert any(s.startswith('Eşik üstü (') for s in secs) and any(s.startswith('Eşik altı (') for s in secs)
    assert not any('Eşik üstü / Eşik altı' in s for s in secs)


def test_kb_no_chunk_mixes_above_with_excludes():
    """'dışlamaz' içeren hiçbir iç parça 'eşik üstü' ifadesi taşımaz (yalnız eşik altı bağlamı)."""
    for c in INTERNAL:
        t = _n(c['text'] + ' ' + (c['section'] or ''))
        if 'dislamaz' in t:
            assert 'esik ustu' not in t, c['chunk_id']


def test_kb_next_steps_one_outcome_per_chunk():
    for c in (c for c in CHUNKS if c['doc_id'] == 'int_next_steps' and c['section']):
        outcomes = [o for o in ('esik ustu', 'esik alti', 'sonuc uretilmedi', 'uygun degil') if o in _n(c['text'])]
        assert len(outcomes) <= 1, (c['chunk_id'], outcomes)


# ------------------------------------------------------------------ 2. bağlam sabitleme
@pytest.fixture()
def asst(service, monkeypatch):
    a = _assistant(service)
    monkeypatch.setattr(a, 'ollama', FakeOllama(a.kb))
    return a


def test_pins_af_above_threshold_has_no_below_threshold_text(asst):
    pins = asst._pins([dict(disease_key='af', outcome='ESIK_USTU', missing_fields=[])])
    txt = _n(' '.join(c['text'] for c in pins))
    assert 'esik ustu' in txt and 'dislamaz' not in txt and 'esik alti' not in txt


def test_pins_below_threshold_keeps_does_not_exclude(asst):
    pins = asst._pins([dict(disease_key='osteoporosis', outcome='ESIK_ALTI', missing_fields=[])])
    assert 'dislamaz' in _n(' '.join(c['text'] for c in pins))


# ------------------------------------------------------------------ 3. son kontrol
def test_postcheck_rejects_excludes_attached_to_above_threshold():
    ctx = 'Eşik altı: Bu sonuç hastalığı dışlamaz.'
    assert 'threshold_polarity' in guard.postcheck('Eşik üstü sonuç hastalığı dışlamaz [1].', ctx, set())
    # AF hatası: eşik üstü açıklanırken ayrı cümlede "Bu sonuç ... dışlamaz" (eşik altından hiç söz edilmeden)
    bad = 'Eşik üstü, modelin sınıflamasıdır [1]. Bu sonuç hastalığı dışlamaz; belirtileriniz varsa hekiminize danışın [2].'
    assert 'threshold_polarity' in guard.postcheck(bad, ctx, set())


def test_postcheck_allows_excludes_for_below_threshold():
    ctx = 'Eşik altı: Bu sonuç hastalığı dışlamaz.'
    assert guard.postcheck('Eşik altı sonuç hastalığı dışlamaz [1].', ctx, set()) == []
    ok = 'Eşik üstü sonuçta hekiminize danışın [1]. Eşik altı sonuç ise hastalığı dışlamaz [2].'
    assert guard.postcheck(ok, ctx, set()) == []
    assert guard.postcheck('Negatif sonuç hastalığı dışlamaz [1].', ctx, set()) == []


def test_orphan_and_repeated_citations_are_removed():
    good = [dict(doc_id='a'), dict(doc_id='b'), dict(doc_id='c')]
    ans, used = _renumber('Eşik üstü bir sınıflamadır [1].\n\n[3]', good)
    assert ans == 'Eşik üstü bir sınıflamadır [1].' and [c['doc_id'] for c in used] == ['a']
    ans, used = _renumber('Gerekli bilgiler [3], [3], [3], [3] sayfasında.', good)
    assert ans == 'Gerekli bilgiler [1] sayfasında.' and [c['doc_id'] for c in used] == ['c']
    ans, _ = _renumber('[2]\nMetin [1].', good)
    assert ans == 'Metin [1].'


def test_polarity_violation_returns_fixed_answer(client, monkeypatch, service):
    a = _assistant(service)
    fake = FakeOllama(a.kb, answer='Eşik üstü bir sınıflamadır [1]. Bu sonuç hastalığı dışlamaz [1].')
    monkeypatch.setattr(a, 'ollama', fake)
    monkeypatch.setattr(main, '_ASSISTANT', a)
    r = client.post('/assistant/ask', json={'question': 'Eşik üstü ne demek?'}).json()
    assert r['route'] == 'postcheck_fail' and 'dışlamaz' not in r['answer'].replace(service.disclaimer, '')


# ------------------------------------------------------------------ 4. app_config metinleri
def test_af_above_threshold_mentions_other_rhythms(service):
    ns = service.config['ui']['next_steps_tr']['af']['ESIK_USTU']
    assert 'ekstrasistol' in ns and 'flutter' in ns and 'hızlı kalp atımı' in ns


def test_af_extra_limitations_match_phase_xxxiii(service):
    """Ek sınırlılık sayıları phase_xxxiii havuz satırlarından (FP/n) birebir alınmıştır."""
    import csv
    from conftest import V2
    rows = {r['ritim']: r for r in csv.DictReader(open(V2 / 'phase_xxxiii/results/b_rhythm_fpr.csv', encoding='utf8'))
            if r['kapsam'].startswith('Havuz')}
    afl = next(r for r in csv.DictReader(open(V2 / 'phase_xxxiii/results/afl_results.csv', encoding='utf8'))
               if r['analiz'] == 'AFL — birincil' and r['kapsam'].startswith('Havuz'))
    txt = ' '.join(service.config['ui']['limitations_extra_tr']['af_S4_DEVICE'])
    for k in ('Sinüs taşikardisi', 'PAC/SVPB', 'PVC', 'Pacing', 'Diğer'):
        assert f"{rows[k]['FP']}/{rows[k]['n']}" in txt, k
    assert f"{afl['AF_karari']}/{afl['n']}" in txt


def test_postcheck_rejects_unnegated_probability_claim():
    """Phase L yoklaması: 'Sadece bir olasılık gösterir' (uygulama olasılık göstermez; sistem istemi kural 4)."""
    ctx = 'Tanı değildir; olasılık gösterilmez.'
    assert 'probability_claim' in guard.postcheck('Eşik üstü sonuç sadece bir olasılık gösterir [2].', ctx, set())
    assert guard.postcheck('Tanı değildir; olasılık gösterilmez [1].', ctx, set()) == []
    assert guard.postcheck('Model olasılığı klinik olasılık değildir [1].', ctx, set()) == []
    assert guard.postcheck('Bu uygulama olasılık göstermez [1].', ctx, set()) == []
