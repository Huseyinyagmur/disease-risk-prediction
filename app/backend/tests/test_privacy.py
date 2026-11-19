"""Danışman isteği 7a/7c: istek gövdeleri ve sağlık verileri hiçbir log'a yazılmaz, diske saklanmaz; yalnız anonim
sayaç/süre tutulur. Her yanıtta (hata yanıtları dahil) sabit uyarı bulunur.
Hem süreç içi (caplog/capsys, tüm logger'lar DEBUG) hem gerçek sunucu süreci (run_server.py stdout/stderr) denenir."""
import logging
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

from conftest import BACKEND, base_person

MARK_NUM = 87.654321          # bel çevresi işaret değeri
MARK_CAT = 'ZZQX_PRIVACY_MARKER'
MARK_FILE = 'zzqxmarker'
MARKERS = (MARK_CAT, str(MARK_NUM), MARK_FILE, '87.65', '67.654321')
DISCLAIMER_START = 'Araştırma prototipidir;'


def _snapshot(root):
    out = set()
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ('.venv', '__pycache__')]
        out |= {os.path.join(d, f) for f in files}
    return out


def _af_tmp():
    return {p for p in Path(tempfile.gettempdir()).glob('hr_af_*')}


def _requests(c):
    """Sağlık verisi işaretleriyle: normal (şema dışı kategori), 422 aralık, bilinmeyen alan, bozuk gövde, AF hatalı
    yükleme (işaretli dosya adı, yaş, cinsiyet), diğer uç noktalar ve 404."""
    hea = f'{MARK_FILE} 12 500 5000\n'.encode()
    return [c.post('/predict', json={'fields': base_person(waist_cm=MARK_NUM, smoking_status=MARK_CAT)}),
            c.post('/predict', json={'fields': base_person(waist_cm=MARK_NUM, age_years=150)}),
            c.post('/predict', json={'fields': {MARK_CAT: MARK_NUM}}),
            c.post('/predict', json={'bozuk': MARK_CAT}),
            c.post('/ecg/af', files={'header_file': (f'{MARK_FILE}.hea', hea), 'signal_file': (f'{MARK_FILE}.dat', b'\x00' * 64)},
                   data={'age_years': str(MARK_NUM - 20), 'sex': MARK_CAT}),
            # Phase XLV: canlı panel uç noktası (normal, aralık dışı, bilinmeyen alan)
            c.post('/eligibility', json={'fields': base_person(waist_cm=MARK_NUM, smoking_status=MARK_CAT)}),
            c.post('/eligibility', json={'fields': base_person(waist_cm=MARK_NUM, age_years=150)}),
            c.post('/eligibility', json={'fields': {MARK_CAT: MARK_NUM}}),
            c.get('/health'), c.get('/models'), c.get('/schema'), c.get('/yok')]


def test_no_health_data_in_logs_inprocess(client, caplog, capsys):
    caplog.set_level(logging.DEBUG)
    for name in ('', 'uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi', 'starlette', 'healthrisk_api'):
        logging.getLogger(name).setLevel(logging.DEBUG)
    before = _af_tmp()
    rs = _requests(client)
    out = capsys.readouterr()
    text = caplog.text + out.out + out.err
    for m in MARKERS:
        assert m not in text, m
    for r in rs:                                      # 7c: her yanıtta sabit uyarı (hata yanıtları dahil)
        assert r.json()['disclaimer'].startswith(DISCLAIMER_START), (r.status_code, r.text[:200])
    assert {r.status_code for r in rs} >= {200, 404, 422}
    assert _af_tmp() == before                        # geçici AF klasörü kalmadı


def test_422_does_not_echo_raw_input(client):
    r = client.post('/predict', json={'bozuk': MARK_CAT})
    assert r.status_code == 422 and MARK_CAT not in r.text


def test_stats_are_anonymous(client):
    client.post('/predict', json={'fields': base_person(waist_cm=MARK_NUM)})
    h = client.get('/health').json()
    st = h['request_stats']
    assert st['/predict']['count'] >= 1 and 'mean_seconds' in st['/predict']
    flat = repr(st)
    assert MARK_CAT not in flat and str(MARK_NUM) not in flat and 'waist' not in flat
    assert set(st) <= {'/health', '/models', '/schema', '/predict', '/eligibility', '/ecg/af', 'other'}  # /eligibility: Phase XLV
    assert h['privacy']


def test_non_localhost_403_has_disclaimer(service):
    from fastapi.testclient import TestClient
    from healthrisk_api import main
    main._SERVICE = service
    r = TestClient(main.app, client=('203.0.113.7', 5000)).post('/predict', json={'fields': {'waist_cm': MARK_NUM}})
    assert r.status_code == 403 and r.json()['disclaimer'].startswith(DISCLAIMER_START)


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def test_no_health_data_in_real_server_logs_or_disk(tmp_path):
    """Gerçek sunucu süreci: stdout/stderr'de işaretler yok; app/backend altında yeni dosya yok; geçici AF klasörü yok."""
    port = _free_port()
    log = tmp_path / 'server_stdout_stderr.txt'
    before = _snapshot(BACKEND)
    tmp_before = _af_tmp()
    with open(log, 'w', encoding='utf8') as fh:
        proc = subprocess.Popen([sys.executable, '-B', str(BACKEND / 'run_server.py'), '--port', str(port)],
                                cwd=str(BACKEND), stdout=fh, stderr=subprocess.STDOUT)
        try:
            c = httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=60)
            for _ in range(240):
                try:
                    if c.get('/health').status_code == 200:
                        break
                except httpx.TransportError:
                    time.sleep(0.25)
            rs = _requests(c)
            assert all(r.json().get('disclaimer', '').startswith(DISCLAIMER_START) for r in rs)
        finally:
            proc.terminate()
            proc.wait(timeout=30)
    text = log.read_text(encoding='utf8', errors='replace')
    assert 'Uvicorn running on http://127.0.0.1' in text
    for m in MARKERS + ('"fields"',):
        assert m not in text, m
    assert _snapshot(BACKEND) == before
    assert _af_tmp() == tmp_before
