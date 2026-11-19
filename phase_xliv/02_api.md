# Phase XLIV — Görev 2: API (app/backend)

Kod: `app/backend/healthrisk_api/` (`main.py` uç noktalar, `service.py` akış, `validation.py` birim/aralık,
`eligibility.py` popülasyon uygunluğu, `transforms.py` 46 dönüşüm, `features.py` vektör, `model_loader.py`, `ecg_af.py`).
Başlatma: `app/backend/run_server.py` (yalnız `127.0.0.1`). Örnekler canlı sunucudan alındı
(`scripts/t2_api_examples.py` → `results/api_examples.json`, `results/af_e2e.json`); tüm kişiler **sentetiktir**.

## Genel ilkeler

- Modeller yalnız `phase_xliii/registry/models.json` üzerinden yüklenir. Sunucu önceki faz dosyalarına yazmaz.
- Başlangıç doğrulamaları: registry ve şema SHA256 (Phase XLIII sonu değerleri), paket sürümleri, şemadaki 46 dönüşümün
  tamamının uygulanmış olması, her model için `models.json` ↔ `input_schema.model_usage` tutarlılığı (feature kümesi,
  dönüşüm adı, input_field), **model dosyası SHA256'sı (yüklemeden önce)**. Uyuşmazlıkta model devre dışı ve `/health`'te
  nedeniyle listelenir.
- **Olasılık hiçbir yanıtta yoktur.** Karar yalnız `research_class: ESIK_USTU | ESIK_ALTI` (birincil donmuş eşik, `>=`).
  Eşiğin sayısal değeri de yanıta konmaz. Her sonuçta `clinical_probability_eligibility: false`.
- Kanıt: registry'deki iç test / zamansal / dış doğrulama blokları ayrı katmanlar halinde aynen döner (yeniden
  hesaplanmaz; CV sonuçları yer almaz).
- Loopback dışı istemci → 403 (ara katman); `run_server.py` `bind_host` localhost değilse başlamaz. Canlı denemede
  makinenin yerel ağ adresinden (192.168.1.199:8765) bağlantı kurulamadı (zaman aşımı).

## Uç noktalar

| uç nokta | yanıt |
|---|---|
| `GET /health` | `status` (`ok`/`degraded`), `disabled_models` + nedenleri, paket sürümleri (beklenen/kurulu), registry SHA, AF pipeline kilidi durumu |
| `GET /models` | yalnız `app_visible=true` 11 model: `model_id`, `disease`, `role`, `app_mode`, `endpoint`, `fields.required` / `fields.conditional`, `target_definition`, `population`, `missing_input_rule`, `evidence` (katmanlı), `limitations` |
| `GET /schema` | 75 şema alanı + 3 uygulama uygunluk sorusu (`form_input` bayrağıyla; EKG pipeline alanları `form_input=false`), birim dönüşümleri, istek biçimi, model başına alanlar |
| `POST /predict` | `{"fields": {...}}` → hastalık başına bir sonuç |
| `POST /ecg/af` | multipart `header_file`, `signal_file`, `age_years`, `sex` |

HTTP kodları: 422 (doğrulama), 413 (dosya > 2 MB), 429 (AF pipeline meşgul; aynı anda tek kayıt), 403 (loopback dışı).

## /predict akışı

1. **Birim dönüşümü**: `{"value": x, "unit": u}` biçiminde `u` kayıtlı birimden farklıysa `input_schema.unit_conversions`
   op metniyle çevrilir (14 kural, 19 alan–birim çifti; tanınmayan op başlangıçta hata verir).
2. **Doğrulama (422)**: bilinmeyen alan; sayısal olmayan değer; desteklenmeyen birim; `plausible_range` dışı (dönüşümden
   sonra); okuma i için sistolik ≤ diyastolik; FEV1 > FVC; EKG pipeline alanı / cihaz grubu formdan girilmesi.
   Şemada olmayan **kategori** 422 değildir → kullanan model ABSTAIN.
3. Model başına: **popülasyon uygunluğu** → **dönüşümler** (tek kaynak `transforms.py`, adlar registry'den) →
   **feature sırası registry'den** → model `allowed_range` kontrolü → tahmin → eşik üstü/altı.

### Durumlar

| status | ne zaman |
|---|---|
| `OK` | uygun popülasyon, tüm zorunlu alanlar mevcut ve geçerli |
| `ABSTAIN` | zorunlu alan eksik (`missing_fields`), şemada olmayan kategori (`unknown_categories`), uygunluk sorusu yanıtsız, model devre dışı, EKG pipeline başarısız |
| `NOT_APPLICABLE` | popülasyon dışı (yaş, gebelik, tanı, diyaliz, FEV1/FVC ≥ 0,70) veya dönüştürülmüş değer model girdi aralığı dışında |

### Popülasyon uygunluğu (models.json `population` / `missing_input_rule` metinlerinden)

| model | NOT_APPLICABLE | ABSTAIN (doğrulanamıyor) |
|---|---|---|
| dm_A / dm_B | yaş < 20; gebe; diyabet tanısı; tanısız ama insülin/hap | yaş, cinsiyet, (kadında) gebelik veya diyabet tanısı sorusu yanıtsız |
| ckd_A / ckd_B | yaş < 20; gebe; "zayıf/başarısız böbrek" tanısı; diyaliz | yaş, cinsiyet, gebelik (kadın), böbrek tanısı sorusu yanıtsız |
| htn_M1 | yaş < 18; gebe | yaş, cinsiyet, gebelik (kadın) |
| fibrosis_final | yaş < 20; gebe | aynı |
| osteo_final | yaş < 50 | yaş |
| anemia_LR16 | erkek 20–65 dışı; kadın 20–44 dışı; gebe | yaş, cinsiyet, gebelik (kadın 20–44) |
| copd_S4_DEVICE | yaş 40–79 dışı; pre-BD FEV1/FVC ≥ 0,70 | yaş |
| cad_DEVICE | yaş 20–100 dışı (model girdi aralığı) | yaş |
| af_S4_DEVICE | yaş 18–89 dışı (≥ 90: age_cap89_ptbxl) | yaş |

Gebelik (`pregnant`), "doktor zayıf/başarısız böbrek dedi mi" (`told_weak_failing_kidneys`, NHANES KIQ022) ve diyaliz
(`on_dialysis`, KIQ025) Phase XLIII şemasında **yoktur**; `app/backend/config/app_config.json > extra_eligibility_fields`
içinde uygulama düzeyinde tanımlandı. Model feature'ı değildir, yalnız uygunluk içindir (karar gerektirir, rapor §Açık).

### B modelleri

`dm_B` ve `ckd_B` önce denenir; `OK` ise hastalık sonucu B'dir (`selected_over: dm_A`). Değilse (laboratuvar eksik vb.)
A çalışır ve sonuçta `fallback_from: {model_id: dm_B, status, missing_fields, reasons}` bulunur.

### Hedefi tanımlayan girdi uyarısı (`warnings[].code = TARGET_DEFINING_INPUT`)

| hastalık | tetikleyen |
|---|---|
| diyabet | `hba1c_pct` veya `glucose_fasting_mgdl` girilmiş |
| hipertansiyon | girilen okumaların ortalaması SBP ≥ 140 veya DBP ≥ 90; ya da `on_bp_medication = true` |
| anemi | `hemoglobin_gdl` girilmiş |
| böbrek | `creatinine_mgdl`, ya da idrar albümin + idrar kreatinin girilmiş |

Mesaj: "… Bu durumda model yerine doğrudan klinik eşik kullanın." Model yine çalışır (uyarı, engel değil).

## Örnek: yalnız form (laboratuvarsız), 55 yaş kadın

İstek (kısaltılmış):
```json
{"fields": {"age_years": 55, "sex": "female", "pregnant": false, "race_ethnicity": "nh_white",
  "height_cm": 165, "weight_kg": 72, "waist_cm": 90,
  "sbp_1_mmhg": 128, "dbp_1_mmhg": 80, "sbp_2_mmhg": 126, "dbp_2_mmhg": 78, "sbp_3_mmhg": 124, "dbp_3_mmhg": 79,
  "smoking_status": "never", "alcohol_drinks_per_day": 0.2, "told_hypertension": false, "told_diabetes": false,
  "family_hx_diabetes": true, "gestational_diabetes_hx": false, "recreational_activity": true,
  "hx_coronary_disease": false, "hx_heart_failure": false, "hx_stroke": false, "told_weak_failing_kidneys": false,
  "glucocorticoid_ge1month": false, "fracture_hip": false, "fracture_wrist": false, "fracture_spine": false,
  "fracture_after_age20": false, "parent_hip_fracture": false, "menses_absent_12m": true,
  "age_last_period_years": 50, "hrt_ever": false}}
```
Yanıt özeti (HTTP 200):

| model | status | karar / gerekçe |
|---|---|---|
| af_S4_DEVICE | NOT_APPLICABLE | yalnız `POST /ecg/af` |
| cad_DEVICE | ABSTAIN | eksik: göğüs ağrısı tipi, kolesterol, açlık glukozu, istirahat EKG, efor bulguları |
| dm_A (fallback_from dm_B) | OK | ESIK_ALTI |
| anemia_LR16 | NOT_APPLICABLE | yaş 55: kadında popülasyon 20–44 |
| copd_S4_DEVICE | ABSTAIN | eksik: fev1_pre_ml, fvc_pre_ml |
| htn_M1 | ABSTAIN | eksik: hba1c, kolesterol, HDL, kreatinin, idrar albümin/kreatinin |
| fibrosis_final | ABSTAIN | eksik: karaciğer enzimleri, albümin, trombosit, glukoz, HbA1c, TG, HDL |
| osteo_final | OK | ESIK_ALTI |
| ckd_A (fallback_from ckd_B) | OK | ESIK_ALTI |

Tek sonucun tam biçimi (`dm_A`, kanıt ve sınırlılık metinleri kısaltıldı):
```json
{"model_id": "dm_A", "disease": "Diyabet (teşhis edilmemiş)", "disease_key": "diabetes", "role": "primary",
 "app_mode": "standard", "status": "OK", "reasons": [], "missing_fields": [], "unknown_categories": [],
 "decision": {"research_class": "ESIK_ALTI",
              "label_tr": "Eşik altı — araştırma sınıflaması (klinik karar değildir)",
              "threshold": "birincil donmuş eşik (registry; değiştirilmez)",
              "threshold_rule": "havuzlu OOF Recall>=0.75 sağlayan en yüksek eşik"},
 "evidence": {"highest_tier": "iç test (NHANES içi; zamansal değil; …)",
              "tiers": {"internal_test": {"source": "Phase XLII (NHANES G 2011–12 + H 2013–14, kilitli tek sefer)",
                         "n": 8895, "n_pos": 389, "precision": {"value": 0.103, "ci95": [0.092, 0.115]},
                         "recall": {"value": 0.733, "ci95": [0.687, 0.774]}, "fpr": {"value": 0.292, "ci95": [0.282, 0.302]},
                         "auc": {"value": 0.8, "ci95": [0.781, 0.819]}, "npv": 0.983,
                         "delta_auc_vs_ADA": {"value": 0.042, "ci95": [0.028, 0.055]}, "tier_label": "iç test"}},
              "research_target_note": "Hiçbir eşikte sağlanmadı …"},
 "limitations": ["Tarama sıralayıcısı; P ≈ 0,10 …", "…"],
 "clinical_probability_eligibility": false,
 "fallback_from": {"model_id": "dm_B", "status": "ABSTAIN",
                   "missing_fields": ["total_chol_mgdl", "hdl_mgdl", "tg_mgdl", "alt_ul", "uric_acid_mgdl"],
                   "note": "B modeli (laboratuvarlı) çalışmadı; birincil A modeline düşüldü"},
 "warnings": []}
```

## Örnek: laboratuvar + farklı birimler

Ek alanlar: `"total_chol_mgdl": {"value": 5.2, "unit": "mmol/L"}`, `"creatinine_mgdl": {"value": 70, "unit": "µmol/L"}`,
HbA1c 5,3, hemoglobin 13,5 ve diğer laboratuvarlar. Yanıtta `unit_conversion_notes`:
`total_chol_mgdl: 5.2 mmol/L -> 201.084 mg/dL (x * 38.67)`, `creatinine_mgdl: 70 µmol/L -> 0.791855 mg/dL (x / 88.4)`.
Sonuç: `dm_B` OK (B seçildi), `htn_M1` OK, `fibrosis_final` OK, `osteo_final` OK, `ckd_B` OK; uyarılar: diyabet (HbA1c),
anemi (hemoglobin; model popülasyon dışı olduğu için NOT_APPLICABLE), böbrek (kreatinin, idrar albümin/kreatinin).

## Örnek: ırk yanıtsız

`race_ethnicity` çıkarıldığında `dm_A`/`dm_B`, `ckd_A`/`ckd_B` ve `htn_M1` ABSTAIN:
`"eksik zorunlu alan(lar): race_ethnicity"`, `"ırk/etnik köken yanıtsız: policy.optional_race gereği varsayılan sınıf
atanmaz"`. `osteo_final` OK kalır.

## Örnek: bilinmeyen kategori

`"smoking_status": "sometimes"` → HTTP 200; sigara durumunu kullanan modeller (dm, ckd, osteo, copd, htn) ABSTAIN,
`unknown_categories: [{"field": "smoking_status", "value": "'sometimes'"}]`.

## Örnek: 422

```json
{"fields": {"age_years": 150, "...": "..."}}
→ 422 {"detail": [{"loc": ["fields", "age_years"], "msg": "age_years=150 yıl makul aralık dışında [18, 120]"}]}

{"fields": {"glucose_fasting_mgdl": 5.4, "...": "..."}}      (birim verilmemiş; mmol/L olasılığı)
→ 422 {"detail": [{"loc": ["fields", "glucose_fasting_mgdl"], "msg": "glucose_fasting_mgdl=5.4 mg/dL makul aralık dışında [30, 800]"}]}
```

## Örnek: hedefi tanımlayan girdi

HbA1c 6,9 ve okumalar 152/150/149 mmHg: `dm_A` sonucu `warnings: [{"code": "TARGET_DEFINING_INPUT", "fields":
["hba1c_pct"], "message_tr": "Diyabet hedefini tanımlayan ölçüm girildi (HbA1c / açlık plazma glukozu). Bu durumda model
yerine doğrudan klinik eşik kullanın."}]`; hipertansiyon sonucunda da ölçülen tansiyon uyarısı.

## Örnek: klinik mod (CAD)

```json
{"fields": {"age_years": 58, "sex": "male", "cad_chest_pain_type": "asymptomatic", "sbp_1_mmhg": 140,
  "total_chol_mgdl": 230, "glucose_fasting_mgdl": 100, "cad_resting_ecg": "normal", "cad_max_hr_bpm": 150,
  "cad_exercise_angina": false, "cad_st_depression_mm": 1.0, "cad_st_slope": "flat"}}
```
`cad_DEVICE` OK (`decision.research_class` döner). CAD string kategorileri (`'4.0'` vb.) dönüşüm tablosuyla üretilir;
`"cad_chest_pain_type": "1"` gibi şema dışı değer ABSTAIN'a gider (V2 CAD hatası biçimi; sessiz dönüşüm yok).

## /ecg/af

İstek: `header_file=00165_hr.hea`, `signal_file=00165_hr.dat`, `age_years=60`, `sex=male` (yaş/cinsiyet sentetik).

İşleyiş: başlık ayrıştırılır, kayıt adı ve sinyal dosya adı uyuşmalı (tek `.dat` veya `.mat`); dosyalar geçici klasöre
yazılır; kilitli `af_pipeline_v1.py`'nin kendi işlevleri sırayla çağrılır: `read_wfdb_500` (500 Hz, 12 lead, 5000
örnek, mV, lead sırası; aksi ABSTAIN) → `run_ecgdeli(timeout=kalan süre)` → `features_from_mat`. Toplam 60 sn aşılırsa
ABSTAIN. Pipeline herhangi bir feature'ı üretemezse (NaN) ABSTAIN. Pipeline dosyası, Octave exe, ECGDeli kaynak ağacı ve
compat dosyalarının SHA256'ları başlangıçta kilitle doğrulanır; pipeline kodu kopyalanmaz/değiştirilmez.

Yanıt (HTTP 200):
```json
{"result": {"model_id": "af_S4_DEVICE", "status": "OK",
  "decision": {"research_class": "ESIK_ALTI", "label_tr": "Eşik altı — araştırma sınıflaması (klinik karar değildir)",
               "threshold": "birincil donmuş eşik (registry; değiştirilmez)",
               "threshold_rule": "BULUNAMADI (frozen_model_manifest kural metni taşımıyor; eşik değeri manifestte dondurulmuş)"},
  "pipeline": {"version": "AF-ECGDELI-OCTAVE-v1", "octave_seconds": 4.35, "wall_seconds": 7.07,
               "features_ms": {"RR_Mean_Global": 912.0, "RR_Mean_Global_iqr": 38.0, "QRS_Dur_Global": 175.0,
                               "QRS_Dur_Global_iqr": 15.5, "PR_Int_Global": 258.0, "PR_Int_Global_iqr": 54.0,
                               "P_Dur_Global": 198.0, "P_Dur_Global_iqr": 47.0, "QT_Int_Global": 455.0,
                               "QT_Int_Global_iqr": 22.5}},
  "evidence": {"…": "…"}, "limitations": ["…"], "clinical_probability_eligibility": false}, "...": "..."}
```
EKG feature'ları (ms) olasılık değildir; şeffaflık için döner. Örnekteki karar yalnız uç noktanın çalıştığını gösterir.

## Sınırlılıklar

- Uygunluk soruları (gebelik, böbrek tanısı, diyaliz) şema dışıdır; bkz. rapor.
- `/ecg/af` aynı anda tek kayıt işler (Octave); eşzamanlı ikinci istek 429 alır.
- Sunucu kimlik doğrulama içermez; yalnız localhost'ta, tek kullanıcılı araştırma kullanımı içindir.


---

## Güncelleme — şema v2 ve danışman istekleri

- **Şema v2** (`phase_xliv/registry/input_schema_v2.json`): `/schema` yanıtı `schema_version: "2.0"`,
  `changes_from_v1` (15 satır: model, feature, eski/yeni dönüşüm, gerekçe, kanıt) ve `known_limitations_v2` döndürür.
  `/models` her model için `schema_v2_changes` içerir. Gebelik, böbrek tanısı ve diyaliz soruları artık şema alanı
  (`app_config.extra_eligibility_fields` kaldırıldı).
- **Gebelik:** `"pregnant": true | false | "unknown"`; kadında ≥ 18 yaşta zorunlu (`required_when`). `"unknown"` →
  gerekçe `gebelik durumu "bilmiyorum": popülasyon "gebe değil" doğrulanamıyor (katı yorum)` ile ABSTAIN.
- **İlaç soruları** herkese sorulur (`ask_when` kaldırıldı). Tanısız kişide `on_diabetes_pills: true` → KBH `dm_pills = 1`
  (eğitim tanımı) ve dm_A/dm_B NOT_APPLICABLE (eğitimde tanısız ama ilaç kullananlar dışlanmıştı).
- **Modül etiketi:** her sonuçta `module_label` var: `af_S4_DEVICE` ve `fibrosis_final` → "ana modül", `osteo_final` →
  "araştırma modülü", diğerleri → "deneysel".
- **Sabit uyarı:** her JSON yanıtında (200, 403, 404, 413, 422, 429, 500)
  `"disclaimer": "Araştırma prototipidir; mevcut durum sınıflandırmasıdır, gelecek risk tahmini değildir; negatif sonuç
  hastalığı dışlamaz; tanı ve tedavi için hekime başvurun."`
- **Gizlilik:** istek gövdesi ve sağlık verisi loglanmaz, saklanmaz. 422 hata ayrıntısı FastAPI'nin varsayılan `input`
  yansıtmasını içermez. Beklenmeyen hata → 500, yalnız hata türü loglanır. `/health` içinde `request_stats` (ör.
  `{"/predict": {"count": 10, "status_counts": {"200": 8, "422": 2}, "mean_seconds": 0.02}}`) ve `privacy` döner.
- **/ecg/af:** `.hea + .mat` (Challenge) uçtan uca denendi (3 kayıt; feature'lar phase_xxxiii ile birebir). 10 sn'den uzun
  kayıt → ABSTAIN (kilitli 5000 örnek koşulu).

Örnek (gebelik "bilmiyorum", 55 yaş kadın, yalnız form; canlı sunucu, `results/api_examples.json > pregnancy_unknown`):
dm_A ve ckd_A gebelik gerekçesiyle ABSTAIN; osteo_final OK (`module_label: "araştırma modülü"`); yanıtta `disclaimer`.


---

## Kapanış güncellemesi — EKG "ilk 10 sn" ön adımı

Kilitli pipeline'ın önüne `app/backend/healthrisk_api/ecg_window.py` eklendi. Bu, `phase_xxxiii/scripts/t3_extract.py ::
read_first10s` fonksiyonunun birebir kopyasıdır (dosya SHA256 `2abc9e67…a293dca`, fonksiyon SHA256 `4818ea06…dfd8471`;
Phase XXIX'te aynı mantık). Kilit dosyası değişmedi. Başlıkta fs ≠ 500 Hz veya örnek sayısı < 5000 ise ABSTAIN.
cpsc_2018'den 10 sn'den uzun 3 kayıtta (A0005, A0036, A0048) 10 feature phase_xxxiii kayıtlı çıktısıyla birebir
(`results/af_long_e2e.json`). Tam paket: **292 geçti, 5 strict-xfail (onaylı BMI dönem sınırlılığı), 0 hata**.
Ayrıntı: `PHASE_XLIV_REPORT.md` kapanış bölümü.
