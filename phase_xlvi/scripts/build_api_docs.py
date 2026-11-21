"""Phase XLVI — Görev 4: app/docs/openapi.json ve app/docs/api.md.

OpenAPI: FastAPI `app.openapi()` (kod ile birebir). Örnekler süreç içi TestClient ile gerçek backend'den alınır;
kişiler sentetiktir. Model olasılığı hiçbir yanıtta yoktur (yanıtta 'proba'/'probability' anahtarı kontrol edilir).
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlvi/scripts/build_api_docs.py
"""
import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))
sys.path.insert(0, str(V2 / 'app/backend/tests'))

from fastapi.testclient import TestClient  # noqa: E402

from conftest import LABS, base_person  # noqa: E402
from healthrisk_api import main  # noqa: E402

DOCS = V2 / 'app/docs'


def short(obj, n=1400):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    return s if len(s) <= n else s[:n] + '\n… (kısaltıldı)'


def no_proba(obj):
    s = json.dumps(obj).lower()
    assert 'predict_proba' not in s and '"probability"' not in s and '"proba"' not in s


def main_():
    DOCS.mkdir(parents=True, exist_ok=True)
    spec = main.app.openapi()
    (DOCS / 'openapi.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    c = TestClient(main.app)
    svc = main.get_service()
    h = c.get('/health').json()
    ms = c.get('/models').json()
    sc = c.get('/schema').json()
    person = base_person()
    el = c.post('/eligibility', json={'fields': person}).json()
    el_err = c.post('/eligibility', json={'fields': dict(person, glucose_fasting_mgdl=5.4)}).json()
    pr = c.post('/predict', json={'fields': person}).json()
    pr_lab = c.post('/predict', json={'fields': {**person, **LABS, 'total_chol_mgdl': {'value': 5.2, 'unit': 'mmol/L'}}}).json()
    r422 = c.post('/predict', json={'fields': dict(person, age_years=150)})
    for x in (h, ms, sc, el, pr, pr_lab):
        no_proba(x)
    # AF ortamı yok örneği (Phase XLVI Görev 5) — yalnız bu süreçte
    import healthrisk_api.ecg_af as A
    real_af, real_lock = svc.af, A.AF_LOCK
    A.AF_LOCK = A.V2 / 'yok' / 'af_pipeline_lock.json'
    svc.af = A.AFPipeline()
    el_noenv = c.post('/eligibility', json={'fields': person}).json()
    el_noenv95 = c.post('/eligibility', json={'fields': {'age_years': 95, 'sex': 'female', 'pregnant': False}}).json()
    svc.af, A.AF_LOCK = real_af, real_lock
    af_row = [m for m in el['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
    af_row_noenv = [m for m in el_noenv['models'] if m['model_id'] == 'af_S4_DEVICE'][0]
    af_row_noenv95 = [m for m in el_noenv95['models'] if m['model_id'] == 'af_S4_DEVICE'][0]

    def tbl(rows, cols):
        return '\n'.join(['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)] +
                         ['| ' + ' | '.join(str(r.get(k, '')).replace('|', '/') for k in cols) + ' |' for r in rows])

    el_rows = [dict(model=m['model_id'], durum=m['state'], eksik=', '.join(m['missing_fields']),
                    gerekce='; '.join(m['reasons'])[:120]) for m in el['models']]
    pr_rows = [dict(model=r['model_id'], status=r['status'],
                    karar=(r.get('decision') or {}).get('research_class', ''),
                    not_=('fallback_from ' + r['fallback_from']['model_id']) if r.get('fallback_from') else '')
               for r in pr['results']]
    pr_one = copy.deepcopy([r for r in pr['results'] if r['model_id'] in ('dm_A', 'dm_B')][0])
    pr_one['evidence'] = {'highest_tier': pr_one['evidence'].get('highest_tier'), 'tiers': '… (registry kanıt katmanları)'}
    pr_one['limitations'] = ['… (registry sınırlılıkları)']
    paths = sorted(spec['paths'])
    md = f"""# API belgesi (app/backend)

Sürüm: {spec['info']['version']} · OpenAPI {spec['openapi']} · makine tarafından okunur şema: [`openapi.json`](openapi.json)
(FastAPI `app.openapi()` çıktısı; `phase_xlvi/scripts/build_api_docs.py` ile üretildi). Bu belge
`phase_xliv/02_api.md`'nin güncel hâlidir (Phase XLV `/eligibility` ve Phase XLVI AF-ortamı kuralı dahil).
Örnek yanıtlar aynı betikte **gerçek backend'den** (süreç içi TestClient) alındı; tüm kişiler sentetiktir.

> Araştırma prototipidir; klinik karar aracı değildir. Model olasılığı hiçbir yanıtta yoktur
> (`clinical_probability_eligibility = false`). Sunucu yalnız `127.0.0.1`'e bağlanır; loopback dışı istemci → 403.

## Genel ilkeler

- Modeller yalnız `phase_xliii/registry/models.json` üzerinden yüklenir; her model dosyasının SHA256'sı **yüklemeden önce**
  doğrulanır. Dönüşümler şema v2'den (`phase_xliv/registry/input_schema_v2.json`) gelir.
- Karar yalnız `research_class: ESIK_USTU | ESIK_ALTI` (donmuş birincil eşik, `skor ≥ eşik`). Eşiğin sayısal değeri dönülmez.
- Her JSON yanıtında `disclaimer` (tek kaynak: `app/backend/config/app_config.json > disclaimer_tr`).
- İstek gövdesi ve sağlık verisi loglanmaz/saklanmaz; `/health > request_stats` yalnız uç nokta sayacı ve süredir.
- Alan değeri doğrudan (`"age_years": 55`) veya birimle (`{{"value": 5.2, "unit": "mmol/L"}}`) verilir.

## Uç noktalar

| yöntem ve yol | özet | HTTP kodları |
|---|---|---|
| `GET /health` | durum (`ok`/`degraded`), devre dışı modeller ve nedenleri, paket sürümleri, registry SHA, AF pipeline kilidi | 200 |
| `GET /models` | yalnız `app_visible` modeller ({len(ms['models'])}): hedef, popülasyon, gerekli alanlar, kanıt katmanları, sınırlılıklar, `module_label`, `schema_v2_changes` | 200 |
| `GET /schema` | şema v2 alanları ({len(sc['fields'])}), birim dönüşümleri, form bölümleri, koşul kuralları, `changes_from_v1`, `known_limitations_v2` | 200 |
| `POST /eligibility` | canlı panel: model başına `READY` / `MISSING` / `OUT_OF_SCOPE` / `ABSTAIN`; **model çalıştırmaz** | 200, 422 (gövde biçimi) |
| `POST /predict` | hastalık başına sonuç: `OK` / `ABSTAIN` / `NOT_APPLICABLE` | 200, 422 |
| `POST /ecg/af` | multipart EKG (`header_file`, `signal_file`, `age_years`, `sex`) → ilk 10 sn → kilitli AF-ECGDELI-OCTAVE-v1 → `af_S4_DEVICE` | 200, 413 (> 2 MB), 422, 429 (pipeline meşgul) |

OpenAPI'deki yollar: {', '.join(f'`{p}`' for p in paths)}.

## Akış (/predict)

1. **Birim dönüşümü** (`unit_conversions`; tanınmayan birim → 422).
2. **Doğrulama (422):** bilinmeyen alan, sayısal olmayan değer, makul aralık dışı (dönüşümden sonra), SBP ≤ DBP, FEV1 > FVC,
   EKG pipeline alanının formdan girilmesi. Şemada olmayan **kategori** 422 değildir → kullanan model ABSTAIN.
3. Model başına `Service.precheck`: popülasyon uygunluğu → dönüşümler → registry feature sırası → model girdi aralığı.
4. Tahmin → donmuş eşik → `ESIK_USTU`/`ESIK_ALTI`. B modelleri (dm_B, ckd_B) laboratuvar varsa önce denenir; değilse A'ya
   düşülür (`fallback_from`).
5. Hedefi tanımlayan girdi (HbA1c/açlık glukozu, ölçülen KB ≥ 140/90 veya KB ilacı, hemoglobin, kreatinin/UACR) →
   `warnings[].code = TARGET_DEFINING_INPUT`.

## Durumlar

| `/predict` status | ne zaman |
|---|---|
| `OK` | uygun popülasyon, zorunlu alanlar tam ve geçerli |
| `ABSTAIN` | zorunlu alan eksik, şema dışı kategori, uygunluk sorusu yanıtsız / "bilmiyorum", model devre dışı, EKG pipeline başarısız veya AF çalışma ortamı yok |
| `NOT_APPLICABLE` | popülasyon dışı (yaş, gebelik, tanı, diyaliz, FEV1/FVC ≥ 0,70) veya dönüştürülmüş değer model girdi aralığı dışında; AF için `/predict` |

| `/eligibility` state | arayüz | ne zaman |
|---|---|---|
| `READY` | Çalışabilir | `/predict` bu model için karar üretebilir |
| `MISSING` | Eksik: … | zorunlu alan veya uygunluk sorusu yanıtsız (`missing_fields`); AF'de ortam varken `ecg_record` |
| `OUT_OF_SCOPE` | Kapsam dışı: … | popülasyon dışı |
| `ABSTAIN` | Karar verilemez: … | şema dışı kategori, gebelik "bilmiyorum", model devre dışı; **AF çalışma ortamı yok (Phase XLVI)** |

Birden fazla neden aynı anda geçerliyse hepsi döner: `reasons` ana durumun (kişiye özel) gerekçeleri, `additional_reasons`
diğer nedenlerdir (arayüz: ana satırın altında **"Ayrıca: …"**). Ör. popülasyon dışı bir kişide yanıtsız/"bilmiyorum"
uygunluk soruları ve AF çalışma ortamı yokluğu `additional_reasons`'a yazılır; ana durum değişmez.

## /eligibility

İstek: `{{"fields": {{...}}}}` (`/predict` ile aynı). Alan hataları 422 yerine `field_errors` listesinde döner; hatalı alan
dışarıda bırakılıp kalan alanlar değerlendirilir. Model çalıştırılmaz (`tests/test_phase45_ui_support.py ::
test_eligibility_never_runs_models`).

Örnek: 55 yaş kadın, yalnız form (laboratuvarsız), AF ortamı **var**:

{tbl(el_rows, ['model', 'durum', 'eksik', 'gerekce'])}

Alan hatası örneği (birim verilmeden 5,4 açlık glukozu): `field_errors` =
`{json.dumps(el_err['field_errors'], ensure_ascii=False)}`.

### AF çalışma ortamı yokken (Phase XLVI)

Octave/ECGDeli veya kilitli pipeline dosyaları yoksa (ör. yalnız GitHub deposu klonlandıysa) ya da kilit/SHA256 doğrulaması
başarısızsa AF satırı:

```json
{short({k: af_row_noenv[k] for k in ('model_id', 'state', 'missing_fields', 'reasons', 'additional_reasons', 'af_pipeline_available', 'details')}, 900)}
```

Arayüz satırı: **"Karar verilemez: {af_row_noenv['reasons'][0]}"**; "EKG kaydı yükle" bağlantısı gösterilmez. Kişiye özel
neden de varsa (Phase XLVI kapanış düzeltmesi) ana durum o nedendir, ortam nedeni `additional_reasons`'tadır; ör. yaş 95:
`state = {af_row_noenv95['state']}`, `reasons[0] = "{af_row_noenv95['reasons'][0]}"`,
`additional_reasons = {json.dumps(af_row_noenv95['additional_reasons'], ensure_ascii=False)}` → arayüz
**"Kapsam dışı: {af_row_noenv95['reasons'][0]}"** ve altında **"Ayrıca: {'; '.join(af_row_noenv95['additional_reasons'])}"**.
Boş formda ana satır "Eksik: …" (yaş, cinsiyet; EKG kaydı eksik sayılmaz), altında yine "Ayrıca: …". Ortam varken AF
satırı: `state = {af_row['state']}`, `missing_fields` içinde `ecg_record`, `af_pipeline_available = true`. Kilit/SHA hatasında
gerekçe "AF pipeline devre dışı: kilit/SHA256 doğrulaması başarısız" olur. Diğer modeller etkilenmez
(`tests/test_phase46_af_panel.py`).

## /predict

Aynı kişi, yanıt özeti:

{tbl(pr_rows, ['model', 'status', 'karar', 'not_'])}

Tek sonucun biçimi (kanıt ve sınırlılık metinleri kısaltıldı):

```json
{short(pr_one, 2200)}
```

Laboratuvar + farklı birim (`total_chol_mgdl` 5,2 mmol/L) → `unit_conversion_notes`:
`{json.dumps(pr_lab['unit_conversion_notes'], ensure_ascii=False)}`.

422 örneği (`age_years = 150`): HTTP {r422.status_code},
`{json.dumps(r422.json()['detail'], ensure_ascii=False)}`.

## /ecg/af

`multipart/form-data`: `header_file` (`<kayıt>.hea`), `signal_file` (başlığın gösterdiği `.dat` veya `.mat`), `age_years`,
`sex`. Dosya başına 2 MB sınırı (413). Aynı anda tek kayıt (429). Zincir: başlık ön kontrolü (fs = 500 Hz, ≥ 5.000 örnek)
→ ilk 10 sn (`ecg_window.py`, Phase XXIX/XXXIII `read_first10s` birebir) → kilitli `run_ecgdeli` → `features_from_mat`
→ model. 60 sn zaman aşımı. Yanıt: `result.status`, `result.decision`, `result.pipeline` (sürüm, pencere, süreler,
`features_ms`: 10 EKG aralığı, ms), `result.display` (lead II + R tepeleri; yalnız gösterim). AF ortamı yoksa
`status = ABSTAIN`, gerekçe `EKG pipeline başarısız: …devre dışı…`. Öznitelikler olasılık değildir.

## /health (bu makine, belge üretimi sırasında)

`status = {h['status']}`, devre dışı modeller: {h['disabled_models'] or 'yok'}, AF pipeline etkin: {h['af_pipeline']['enabled']},
şema sürümü {h['schema_version']}. Temiz klonda (AF ortamı olmadan) beklenen: `status = degraded`, AF pipeline devre dışı,
11 modelin 11'i etkin (`phase_xlv/03b_clean_clone.md`).

## Sınırlılıklar

- Kimlik doğrulama yok; tek kullanıcılı, yalnız localhost araştırma kullanımı.
- `/ecg/af` aynı anda tek kayıt işler; süre makine yüküne bağlı (≈ 7–30 sn).
- Kararlar "araştırma sınıflaması"dır; negatif sonuç hastalığı dışlamaz.
"""
    (DOCS / 'api.md').write_text(md, encoding='utf8')
    print('openapi yolları', paths, 'api.md', len(md))


if __name__ == '__main__':
    main_()
