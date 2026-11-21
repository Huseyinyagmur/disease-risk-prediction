"""Yalnız loopback Ollama istemcisi. Adres 127.0.0.1 dışına çıkamaz (kod düzeyinde denetlenir).
İstek/yanıt gövdeleri loglanmaz; httpx/httpcore günlükleri yalnız yöntem/URL/durum içerir."""
import ipaddress
import urllib.parse

import httpx


class OllamaError(Exception):
    pass


def assert_loopback(url: str) -> str:
    u = urllib.parse.urlparse(url)
    host = u.hostname or ''
    try:
        ok = ipaddress.ip_address(host).is_loopback
    except ValueError:
        ok = False
    if u.scheme != 'http' or not ok:
        raise ValueError('Ollama adresi yalnız 127.0.0.1 / ::1 olabilir')
    return url.rstrip('/')


class Ollama:
    def __init__(self, url: str, timeout_s: float = 180):
        self.url = assert_loopback(url)
        self.timeout_s = timeout_s

    def _client(self, timeout):
        # trust_env=False: sistem HTTP(S)_PROXY değişkenleri yok sayılır (istek vekile/dış ağa gitmez)
        return httpx.Client(base_url=self.url, timeout=timeout, trust_env=False)

    def tags(self, timeout=2.0) -> dict:
        try:
            with self._client(timeout) as c:
                r = c.get('/api/tags')
                r.raise_for_status()
                return {m['name']: m for m in r.json().get('models', [])}
        except (httpx.HTTPError, ValueError) as ex:
            raise OllamaError(type(ex).__name__) from None

    def embed(self, model: str, texts: list) -> list:
        try:
            with self._client(60) as c:
                r = c.post('/api/embed', json=dict(model=model, input=texts, keep_alive='30m'))
                r.raise_for_status()
                return r.json()['embeddings']
        except (httpx.HTTPError, ValueError, KeyError) as ex:
            raise OllamaError(type(ex).__name__) from None

    def chat(self, model: str, messages: list, options: dict) -> str:
        try:
            with self._client(self.timeout_s) as c:
                r = c.post('/api/chat', json=dict(model=model, messages=messages, stream=False, options=options,
                                                  keep_alive='30m'))
                r.raise_for_status()
                return r.json()['message']['content']
        except (httpx.HTTPError, ValueError, KeyError) as ex:
            raise OllamaError(type(ex).__name__) from None
