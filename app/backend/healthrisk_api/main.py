"""FastAPI uygulaması. Yalnız localhost'tan gelen istekler kabul edilir (bkz. run_server.py).

Gizlilik (danışman isteği): istek gövdeleri ve sağlık verileri hiçbir log'a yazılmaz, diske saklanmaz. Yalnız anonim
sayaçlar (uç nokta × durum kodu sayısı, süre) bellekte tutulur ve /health'te döner. Beklenmeyen hatada yalnız hata TÜRÜ
loglanır (mesaj/değer değil). Her JSON yanıtı sabit araştırma uyarısını (`disclaimer`) taşır."""
import ipaddress
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__
from .ecg_af import MAX_UPLOAD_BYTES
from .service import Service
from .validation import ValidationError422

_SERVICE: Optional[Service] = None
_LOG = logging.getLogger('healthrisk_api')
KNOWN_PATHS = {'/health', '/models', '/schema', '/predict', '/eligibility', '/ecg/af', '/assistant/ask'}  # + Phase XLVIII


def get_service() -> Service:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = Service()
    return _SERVICE


def disclaimer() -> str:
    return get_service().disclaimer


_ASSISTANT = None


def get_assistant():
    """Phase XLVIII: açıklama asistanı (tembel kurulum). Kurulamazsa None; uygulamanın geri kalanı etkilenmez."""
    global _ASSISTANT
    if _ASSISTANT is None:
        from .assistant import Assistant
        svc = get_service()
        fui = svc.config['form'].get('field_ui_tr', {})

        def field_label(name):
            if name in fui:
                return fui[name]['label']
            f = svc.schema['fields'].get(name)
            return f['label_tr'] if f else svc.config['form']['virtual_field_labels_tr'].get(name)
        _ASSISTANT = Assistant(svc.disclaimer, svc.config['ui']['disease_names_tr'], field_label)
    return _ASSISTANT


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
    try:
        h['assistant'] = get_assistant().status()          # Phase XLVIII: genel 'status'u etkilemez
    except Exception as ex:                                 # yapılandırma hatası: yalnız tür
        h['assistant'] = dict(enabled=False, reason=f'asistan kurulamadı: {type(ex).__name__}')
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


# ---------------------------------------------------------------- Phase XLVIII: açıklama asistanı
class ResultLabel(BaseModel):
    """Oturumdaki sonuç ETİKETİ (kapalı sözlük). Ham sağlık değeri alanı yoktur; bilinmeyen anahtarlar yok sayılır."""
    model_config = ConfigDict(extra='ignore')
    disease_key: str = Field(max_length=40)
    outcome: str = Field(max_length=20)
    missing_fields: List[str] = Field(default_factory=list, max_length=40)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')              # ör. 'fields' gönderilse bile bağlama girmez
    question: str = Field(min_length=1, max_length=2000)
    results: List[ResultLabel] = Field(default_factory=list, max_length=40)


@app.post('/assistant/ask')
def assistant_ask(req: AskRequest):
    """Soru → güvenlik ön filtresi → RAG → yerel LLM (127.0.0.1:11434) → yanıt + kaynaklar + sabit uyarı.
    Soru/yanıt loglanmaz, saklanmaz. Ollama yoksa 503 (gerekçe /health > assistant)."""
    from .assistant import AssistantBusy, AssistantUnavailable
    try:
        a = get_assistant()
    except Exception as ex:
        raise HTTPException(status_code=503, detail=f'asistan kurulamadı: {type(ex).__name__}')
    try:
        r = a.ask(req.question, [x.model_dump() for x in req.results])
    except AssistantUnavailable as ex:
        raise HTTPException(status_code=503, detail=f'asistan devre dışı: {ex}')
    except AssistantBusy:
        raise HTTPException(status_code=429, detail='asistan meşgul; birkaç saniye sonra yeniden deneyin')
    r.pop('retrieval', None)                                 # iç ayrıntı: yalnız değerlendirme betiklerinde
    r.pop('violations', None)
    r['clinical_probability_eligibility'] = False
    return _wrap(r)
