"""Phase L2: son kontrol yanlış pozitiflerinin genel kurallarla düzeltilmesi (örnekler dev setinden BAĞIMSIZ).
1. Olumsuz bağlamdaki kesinlik ifadesi ("kesin olarak söylenemez") yasak değil; olumlu kesin hüküm yasak.
2. "reçete" / "ilacınızı" yönlendirme bağlamında ("… için hekiminize danışın") serbest; öneri/emir bağlamında yasak.
3. Bilgi içeren (atıflı) yanıta eklenmiş "kaynaklarımda bilgi yok" cümlesi silinir; yanıtın tamamı bilgi yoksa kalır."""
import pytest

from healthrisk_api import main
from healthrisk_api.assistant import guard
from healthrisk_api.assistant.engine import _drop_redundant_no_info

from test_phase48_assistant import FakeOllama, _assistant  # noqa: F401

CTX = 'Eşik üstü: tanı değildir. Hekiminize danışın.'


@pytest.fixture(autouse=True, scope='module')
def _restore_globals():
    by = dict(main.STATS.by)
    old = main._ASSISTANT
    yield
    main.STATS.by = by
    main._ASSISTANT = old


# ------------------------------------------------------------------ 1. kesinlik
@pytest.mark.parametrize('ok', [
    'Bu sonuçla kemiklerinizin sağlıklı olduğu kesin olarak söylenemez [1].',
    'Model sonucu hastalığı kesinlikle göstermez [1].',
    'Bu sınıflama kesin olarak bir tanı değildir [1].',
    'Ritminizin normal olduğunu kesin olarak söyleyemeyiz [1].',
])
def test_negated_certainty_allowed(ok):
    assert 'forbidden_phrase' not in guard.postcheck(ok, CTX, set())


@pytest.mark.parametrize('bad', [
    'Sizde kesinlikle karaciğer hastalığı var [1].',
    'Bu sonuç kesin olarak diyabet olduğunuzu gösterir [1].',
    'Kesinlikle bir hekime gitmeniz gerekir; sonuç hastalığı doğrular [1].',
])
def test_positive_certainty_forbidden(bad):
    assert 'forbidden_phrase' in guard.postcheck(bad, CTX, set())


def test_negation_in_other_sentence_does_not_excuse():
    ans = 'Bu tanı değildir [1]. Ancak sizde kesinlikle hastalık var [1].'
    assert 'forbidden_phrase' in guard.postcheck(ans, CTX, set())


# ------------------------------------------------------------------ 2. reçete / ilaç yönlendirmesi
@pytest.mark.parametrize('ok', [
    'Tedavi ve reçete konusunda hekiminize danışın [1].',
    'İlacınızı değiştirmeden önce doktorunuza danışmanız önerilir [1].',
    'Reçeteli ilaçlar hakkında sorularınız için hekiminize başvurun [1].',
])
def test_referral_context_allowed(ok):
    assert 'forbidden_phrase' not in guard.postcheck(ok, CTX, set())


@pytest.mark.parametrize('bad', [
    'Size reçete edilen ilacı her gün alın [1].',
    'İlacınızı bırakın ve hekiminize danışın [1].',          # emir + yönlendirme: yine yasak
    'Bu sonuç için reçete yazdırmanız gerekir [1].',
    'İlacınızı artırabilirsiniz [1].',
])
def test_advice_context_forbidden(bad):
    assert 'forbidden_phrase' in guard.postcheck(bad, CTX, set())


def test_directive_words_stay_forbidden_with_referral():
    assert 'forbidden_phrase' in guard.postcheck('İlacı almalısınız; hekiminize danışın [1].', CTX, set())


# ------------------------------------------------------------------ 3. gereksiz "kaynaklarımda bilgi yok"
def test_redundant_no_info_sentence_removed():
    ans = 'Eşik altı sonuç hastalığı dışlamaz [1]. Hekiminize danışabilirsiniz [2]. Bu konuda kaynaklarımda bilgi yok; hekiminize danışın.'
    assert _drop_redundant_no_info(ans) == 'Eşik altı sonuç hastalığı dışlamaz [1]. Hekiminize danışabilirsiniz [2].'


def test_pure_no_info_answer_kept():
    ans = 'Bu konuda kaynaklarımda bilgi yok; hekiminize danışın.'
    assert _drop_redundant_no_info(ans) == ans


def test_no_info_kept_when_no_cited_information():
    ans = 'Genel olarak hekiminize danışabilirsiniz. Bu konuda kaynaklarımda bilgi yok; hekiminize danışın.'
    assert _drop_redundant_no_info(ans) == ans


def test_redundant_no_info_api_keeps_sources(client, monkeypatch, service):
    a = _assistant(service)
    fake = FakeOllama(a.kb, answer='Eşik üstü bir araştırma sınıflamasıdır [1]. Bu konuda kaynaklarımda bilgi yok; hekiminize danışın.')
    monkeypatch.setattr(a, 'ollama', fake)
    monkeypatch.setattr(main, '_ASSISTANT', a)
    r = client.post('/assistant/ask', json={'question': 'Eşik üstü ne demek?'}).json()
    assert r['route'] == 'llm' and 'kaynaklarımda bilgi yok' not in r['answer'] and len(r['sources']) >= 1
