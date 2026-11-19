"""FastAPI uygulaması. Yalnız localhost'tan gelen istekler kabul edilir (bkz. run_server.py).

Gizlilik (danışman isteği): istek gövdeleri ve sağlık verileri hiçbir log'a yazılmaz, diske saklanmaz. Yalnız anonim
sayaçlar (uç nokta × durum kodu sayısı, süre) bellekte tutulur ve /health'te döner. Beklenmeyen hatada yalnız hata TÜRÜ
loglanır (mesaj/değer değil). Her JSON yanıtı sabit araştırma uyarısını (`disclaimer`) taşır."""
import ipaddress
import logging
import threading
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__
from .ecg_af import MAX_UPLOAD_BYTES
from .service import Service
from .validation import ValidationError422

_SERVICE: Optional[Service] = None
_LOG = logging.getLogger('healthrisk_api')
KNOWN_PATHS = {'/health', '/models', '/schema', '/predict', '/eligibility', '/ecg/af'}


def get_service() -> Service:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = Service()
    return _SERVICE


def disclaimer() -> str:
    return get_service().disclaimer


class _Stats:
    """Anonim istek sayaçları: yalnız uç nokta yolu (bilinmeyen yollar 'other'), durum kodu ve süre."""
    def __init__(self):
        self.lock = threading.Lock()
        self.by = {}

    def add(self, path, status, seconds):
        key = path if path in KNOWN_PATHS else 'other'
        with self.lock:
            d = self.by.setdefault(key, dict(count=0, status_counts={}, total_seconds=0.0))
            d['count'] += 1
            d['status_counts'][str(status)] = d['status_counts'].get(str(status), 0) + 1
            d['total_seconds'] += seconds

    def snapshot(self):
        with self.lock:
            return {k: dict(count=v['count'], status_counts=dict(v['status_counts']),
                            mean_seconds=round(v['total_seconds'] / v['count'], 4) if v['count'] else None)
                    for k, v in self.by.items()}


STATS = _Stats()

app = FastAPI(title='HealthRisk AI Research V2 — araştırma tahmin sunucusu (Phase XLIV)', version=__version__,
              description='Araştırma prototipidir; klinik karar aracı DEĞİLDİR. Model olasılığı dönülmez '
                          '(clinical_probability_eligibility=false). Yalnız localhost.')


def _err(status, detail):
    return JSONResponse(status_code=status, content={'detail': detail, 'disclaimer': disclaimer(),
                                                     'clinical_probability_eligibility': False})


@app.middleware('http')
async def localhost_and_stats(request: Request, call_next):
    t0 = time.monotonic()
    host = request.client.host if request.client else None
    ok = host in ('testclient',)                      # FastAPI TestClient
    if not ok and host:
        try:
            ok = ipaddress.ip_address(host).is_loopback
        except ValueError:
            ok = host == 'localhost'
    if not ok:
        resp = _err(403, 'yalnız localhost istemcileri kabul edilir')
    else:
        try:
            resp = await call_next(request)
        except Exception as ex:                        # gövde/değer loglanmaz; yalnız hata türü
            _LOG.error('beklenmeyen hata: %s', type(ex).__name__)
            resp = _err(500, 'iç hata (ayrıntı gizlilik nedeniyle loglanmaz/dönülmez)')
    STATS.add(request.url.path, resp.status_code, time.monotonic() - t0)
    return resp


@app.exception_handler(StarletteHTTPException)
async def http_exc(request: Request, exc: StarletteHTTPException):
    return _err(exc.status_code, exc.detail)


@app.exception_handler(RequestValidationError)
async def req_validation(request: Request, exc: RequestValidationError):
    # FastAPI varsayılanı girdi değerini ('input') yanıta yansıtır; burada yalnız konum ve tür döner
    return _err(422, [dict(loc=list(e.get('loc', [])), msg=e.get('msg', ''), type=e.get('type', '')) for e in exc.errors()])


class PredictRequest(BaseModel):
    fields: Dict[str, Any]


def _wrap(d):
    d['disclaimer'] = disclaimer()
    return d


@app.get('/health')
def health():
    h = get_service().health()
    h['request_stats'] = STATS.snapshot()
    h['privacy'] = get_service().config['privacy']['policy']
    return _wrap(h)


@app.get('/models')
def models():
    return _wrap(get_service().models_public())


@app.get('/schema')
def schema():
    return _wrap(get_service().schema_public())


@app.post('/predict')
def predict(req: PredictRequest):
    try:
        return _wrap(get_service().predict(req.fields))
    except ValidationError422 as ex:
        raise HTTPException(status_code=422, detail=ex.errors)


@app.post('/eligibility')
def eligibility(req: PredictRequest):
    """Phase XLV: canlı yönlendirme paneli. Yalnız uygunluk / eksik alan durumu; model ÇALIŞTIRILMAZ.
    Alan hataları 422 yerine `field_errors` listesinde döner (form altında gösterilir)."""
    try:
        return _wrap(get_service().eligibility(req.fields))
    except ValidationError422 as ex:
        raise HTTPException(status_code=422, detail=ex.errors)


async def _read_limited(f: UploadFile):
    data = await f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail='dosya boyutu sınırı aşıldı')
    return data


@app.post('/ecg/af')
async def ecg_af(header_file: UploadFile = File(..., description='WFDB başlığı (<kayıt>.hea)'),
                 signal_file: UploadFile = File(..., description='başlığın gösterdiği sinyal dosyası (.mat veya .dat)'),
                 age_years: Optional[float] = Form(None), sex: Optional[str] = Form(None)):
    from starlette.concurrency import run_in_threadpool
    hb, sb = await _read_limited(header_file), await _read_limited(signal_file)
    raw = {'age_years': age_years, 'sex': sex}
    svc = get_service()
    try:
        r, feats = await run_in_threadpool(svc.predict_af, header_file.filename or '', hb, signal_file.filename or '', sb, raw)
    except ValidationError422 as ex:
        raise HTTPException(status_code=422, detail=ex.errors)
    if r.get('busy'):
        raise HTTPException(status_code=429, detail=r['reasons'])
    r['pipeline']['features_ms'] = feats
    return _wrap(dict(result=r, clinical_probability_eligibility=False,
                      note='AF modeli: donmuş model + kilitli pipeline; karar "araştırma sınıflaması"dır.'))
