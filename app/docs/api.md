# API belgesi (app/backend)

Sürüm: 0.1.0 · OpenAPI 3.1.0 · makine tarafından okunur şema: [`openapi.json`](openapi.json)
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
- Alan değeri doğrudan (`"age_years": 55`) veya birimle (`{"value": 5.2, "unit": "mmol/L"}`) verilir.

## Uç noktalar

| yöntem ve yol | özet | HTTP kodları |
|---|---|---|
| `GET /health` | durum (`ok`/`degraded`), devre dışı modeller ve nedenleri, paket sürümleri, registry SHA, AF pipeline kilidi | 200 |
| `GET /models` | yalnız `app_visible` modeller (11): hedef, popülasyon, gerekli alanlar, kanıt katmanları, sınırlılıklar, `module_label`, `schema_v2_changes` | 200 |
| `GET /schema` | şema v2 alanları (78), birim dönüşümleri, form bölümleri, koşul kuralları, `changes_from_v1`, `known_limitations_v2` | 200 |
| `POST /eligibility` | canlı panel: model başına `READY` / `MISSING` / `OUT_OF_SCOPE` / `ABSTAIN`; **model çalıştırmaz** | 200, 422 (gövde biçimi) |
| `POST /predict` | hastalık başına sonuç: `OK` / `ABSTAIN` / `NOT_APPLICABLE` | 200, 422 |
| `POST /ecg/af` | multipart EKG (`header_file`, `signal_file`, `age_years`, `sex`) → ilk 10 sn → kilitli AF-ECGDELI-OCTAVE-v1 → `af_S4_DEVICE` | 200, 413 (> 2 MB), 422, 429 (pipeline meşgul) |

OpenAPI'deki yollar: `/ecg/af`, `/eligibility`, `/health`, `/models`, `/predict`, `/schema`.

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

İstek: `{"fields": {...}}` (`/predict` ile aynı). Alan hataları 422 yerine `field_errors` listesinde döner; hatalı alan
dışarıda bırakılıp kalan alanlar değerlendirilir. Model çalıştırılmaz (`tests/test_phase45_ui_support.py ::
test_eligibility_never_runs_models`).

Örnek: 55 yaş kadın, yalnız form (laboratuvarsız), AF ortamı **var**:

| model | durum | eksik | gerekce |
|---|---|---|---|
| af_S4_DEVICE | MISSING | ecg_record | AF modeli yalnız EKG kaydı (.hea + .dat/.mat) yüklenerek çalışır: POST /ecg/af |
| cad_DEVICE | MISSING | cad_chest_pain_type, total_chol_mgdl, glucose_fasting_mgdl, cad_resting_ecg, cad_max_hr_bpm, cad_exercise_angina, cad_st_depression_mm, cad_st_slope | eksik zorunlu alan(lar): cad_chest_pain_type, total_chol_mgdl, glucose_fasting_mgdl, cad_resting_ecg, cad_max_hr_bpm, ca |
| dm_A | READY |  |  |
| dm_B | MISSING | total_chol_mgdl, hdl_mgdl, tg_mgdl, alt_ul, uric_acid_mgdl | eksik zorunlu alan(lar): total_chol_mgdl, hdl_mgdl, tg_mgdl, alt_ul, uric_acid_mgdl |
| anemia_LR16 | OUT_OF_SCOPE |  | yaş 55: kadında model popülasyonu 20–44 (gebe olmayan) |
| copd_S4_DEVICE | MISSING | fev1_pre_ml, fvc_pre_ml | eksik zorunlu alan(lar): fev1_pre_ml, fvc_pre_ml |
| htn_M1 | MISSING | hba1c_pct, total_chol_mgdl, hdl_mgdl, creatinine_mgdl, urine_albumin_mgl, urine_creatinine_mgdl | eksik zorunlu alan(lar): hba1c_pct, total_chol_mgdl, hdl_mgdl, creatinine_mgdl, urine_albumin_mgl, urine_creatinine_mgdl |
| fibrosis_final | MISSING | alt_ul, ast_ul, ggt_ul, alp_ul, albumin_gdl, platelets_k_ul, glucose_serum_mgdl, hba1c_pct, tg_mgdl, hdl_mgdl | eksik zorunlu alan(lar): alt_ul, ast_ul, ggt_ul, alp_ul, albumin_gdl, platelets_k_ul, glucose_serum_mgdl, hba1c_pct, tg_ |
| osteo_final | READY |  |  |
| ckd_A | READY |  |  |
| ckd_B | MISSING | glucose_serum_mgdl, hba1c_pct, total_chol_mgdl, hdl_mgdl, hemoglobin_gdl | eksik zorunlu alan(lar): glucose_serum_mgdl, hba1c_pct, total_chol_mgdl, hdl_mgdl, hemoglobin_gdl |

Alan hatası örneği (birim verilmeden 5,4 açlık glukozu): `field_errors` =
`[{"field": "glucose_fasting_mgdl", "msg": "glucose_fasting_mgdl=5.4 mg/dL makul aralık dışında [30, 800]"}]`.

### AF çalışma ortamı yokken (Phase XLVI)

Octave/ECGDeli veya kilitli pipeline dosyaları yoksa (ör. yalnız GitHub deposu klonlandıysa) ya da kilit/SHA256 doğrulaması
başarısızsa AF satırı:

```json
{
 "model_id": "af_S4_DEVICE",
 "state": "ABSTAIN",
 "missing_fields": [],
 "reasons": [
  "Octave/ECGDeli AF çalışma ortamı yok"
 ],
 "additional_reasons": [],
 "af_pipeline_available": false,
 "details": [
  "Octave/ECGDeli AF çalışma ortamı yok: kilitli AF pipeline dosyaları bulunamadı (yok/af_pipeline_lock.json). AF için Octave 10.3.0 + ECGDeli v1.1 + kilitli pipeline ayrıca kurulmalıdır."
 ]
}
```

Arayüz satırı: **"Karar verilemez: Octave/ECGDeli AF çalışma ortamı yok"**; "EKG kaydı yükle" bağlantısı gösterilmez. Kişiye özel
neden de varsa (Phase XLVI kapanış düzeltmesi) ana durum o nedendir, ortam nedeni `additional_reasons`'tadır; ör. yaş 95:
`state = OUT_OF_SCOPE`, `reasons[0] = "yaş 95 model popülasyonu dışında (18–89)"`,
`additional_reasons = ["Octave/ECGDeli AF çalışma ortamı yok"]` → arayüz
**"Kapsam dışı: yaş 95 model popülasyonu dışında (18–89)"** ve altında **"Ayrıca: Octave/ECGDeli AF çalışma ortamı yok"**.
Boş formda ana satır "Eksik: …" (yaş, cinsiyet; EKG kaydı eksik sayılmaz), altında yine "Ayrıca: …". Ortam varken AF
satırı: `state = MISSING`, `missing_fields` içinde `ecg_record`, `af_pipeline_available = true`. Kilit/SHA hatasında
gerekçe "AF pipeline devre dışı: kilit/SHA256 doğrulaması başarısız" olur. Diğer modeller etkilenmez
(`tests/test_phase46_af_panel.py`).

## /predict

Aynı kişi, yanıt özeti:

| model | status | karar | not_ |
|---|---|---|---|
| af_S4_DEVICE | NOT_APPLICABLE |  |  |
| cad_DEVICE | ABSTAIN |  |  |
| dm_A | OK | ESIK_ALTI | fallback_from dm_B |
| anemia_LR16 | NOT_APPLICABLE |  |  |
| copd_S4_DEVICE | ABSTAIN |  |  |
| htn_M1 | ABSTAIN |  |  |
| fibrosis_final | ABSTAIN |  |  |
| osteo_final | OK | ESIK_ALTI |  |
| ckd_A | OK | ESIK_ALTI | fallback_from ckd_B |

Tek sonucun biçimi (kanıt ve sınırlılık metinleri kısaltıldı):

```json
{
 "model_id": "dm_A",
 "disease": "Diyabet (teşhis edilmemiş)",
 "disease_key": "diabetes",
 "role": "primary",
 "app_mode": "standard",
 "module_label": "deneysel",
 "status": "OK",
 "reasons": [],
 "missing_fields": [],
 "unknown_categories": [],
 "decision": {
  "research_class": "ESIK_ALTI",
  "label_tr": "Eşik altı — araştırma sınıflaması (klinik karar değildir)",
  "threshold": "birincil donmuş eşik (registry; değiştirilmez)",
  "threshold_rule": "havuzlu OOF Recall>=0.75 sağlayan en yüksek eşik"
 },
 "evidence": {
  "highest_tier": "iç test (NHANES içi; zamansal değil; PREVIOUSLY_EXPOSED_PERSONS başka hedef; diyabet hedefinde yeni kişiler)",
  "tiers": "… (registry kanıt katmanları)"
 },
 "limitations": [
  "… (registry sınırlılıkları)"
 ],
 "clinical_probability_eligibility": false,
 "fallback_from": {
  "model_id": "dm_B",
  "status": "ABSTAIN",
  "reasons": [
   "eksik zorunlu alan(lar): total_chol_mgdl, hdl_mgdl, tg_mgdl, alt_ul, uric_acid_mgdl"
  ],
  "missing_fields": [
   "total_chol_mgdl",
   "hdl_mgdl",
   "tg_mgdl",
   "alt_ul",
   "uric_acid_mgdl"
  ],
  "note": "B modeli (laboratuvarlı) çalışmadı; birincil A modeline düşüldü"
 },
 "warnings": []
}
```

Laboratuvar + farklı birim (`total_chol_mgdl` 5,2 mmol/L) → `unit_conversion_notes`:
`["total_chol_mgdl: 5.2 mmol/L -> 201.084 mg/dL (x * 38.67)"]`.

422 örneği (`age_years = 150`): HTTP 422,
`[{"loc": ["fields", "age_years"], "msg": "age_years=150 yıl makul aralık dışında [18, 120]"}]`.

## /ecg/af

`multipart/form-data`: `header_file` (`<kayıt>.hea`), `signal_file` (başlığın gösterdiği `.dat` veya `.mat`), `age_years`,
`sex`. Dosya başına 2 MB sınırı (413). Aynı anda tek kayıt (429). Zincir: başlık ön kontrolü (fs = 500 Hz, ≥ 5.000 örnek)
→ ilk 10 sn (`ecg_window.py`, Phase XXIX/XXXIII `read_first10s` birebir) → kilitli `run_ecgdeli` → `features_from_mat`
→ model. 60 sn zaman aşımı. Yanıt: `result.status`, `result.decision`, `result.pipeline` (sürüm, pencere, süreler,
`features_ms`: 10 EKG aralığı, ms), `result.display` (lead II + R tepeleri; yalnız gösterim). AF ortamı yoksa
`status = ABSTAIN`, gerekçe `EKG pipeline başarısız: …devre dışı…`. Öznitelikler olasılık değildir.

## /health (bu makine, belge üretimi sırasında)

`status = ok`, devre dışı modeller: yok, AF pipeline etkin: True,
şema sürümü 2.0. Temiz klonda (AF ortamı olmadan) beklenen: `status = degraded`, AF pipeline devre dışı,
11 modelin 11'i etkin (`phase_xlv/03b_clean_clone.md`).

## Sınırlılıklar

- Kimlik doğrulama yok; tek kullanıcılı, yalnız localhost araştırma kullanımı.
- `/ecg/af` aynı anda tek kayıt işler; süre makine yüküne bağlı (≈ 7–30 sn).
- Kararlar "araştırma sınıflaması"dır; negatif sonuç hastalığı dışlamaz.
