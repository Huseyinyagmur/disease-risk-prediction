# Phase XLVIII — 02 Bilgi tabanı (kaynak listesi ve lisanslar)

Kod ve veri: `app/backend/assistant/` (README: atıf ve yeniden üretim). Erişim tarihi: **2026-11-21**.

## 1. Özet

| öğe | değer |
|---|---|
| belge | 47 (iç 18 + dış 29) |
| parça | 495 (iç 254, dış 241); parça uzunluğu 42–1199 karakter (medyan 511); `## ` bölüm sınırı, en çok 1200 karakter |
| gömme modeli | `bge-m3:latest` (Ollama digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`; 566,7 M parametre, F16, 1024 boyut, MIT) |
| indeks | `kb/index/chunks.jsonl` `62d6ebc2…`, `embeddings.f32` `0a9d4124…`, `manifest.json` **`c3ecb13738bd4ee5cfe68a3887ecb8a9391536ccfc2e130db98f95fc6b76491f`** (assistant_lock.json'da kilitli) |
| kaynak listesi | `kb/sources.json` `ddb5f61c91741c9c330ff471729514569cf9c3a36bcc9d8fbaf299675007875b` |
| tekrarlanabilirlik | `build_index.py` aynı makinede iki kez çalıştırıldı: üç indeks dosyasının SHA256'sı **bit düzeyinde aynı** (ilk sürümde denendi; son sürüm aynı betikle üretildi) |

Sunucu, açılışta manifest SHA256'sını kilitle, manifestteki her belge/indeks dosyasının SHA256'sını diskle karşılaştırır;
uyuşmazlıkta asistan devre dışıdır (`/health > assistant.reason`).

## 2. Proje içi belgeler (18)

Metin yazılmadı; yalnız mevcut dosyalardan kopyalandı (`build_index.py > build_internal`).

| belge | kaynak |
|---|---|
| `int_glossary` Terim sözlüğü (terim başına bölüm) | `app_config.json > ui.glossary_tr`, `terms_tr`, `text_tr.decision_note` |
| `int_next_steps` "Ne yapmalıyım?" yönlendirmeleri | `app_config.json > ui.next_steps_tr` |
| `int_evidence` Kanıt düzeyi açıklamaları | `ui.glossary_tr` (kanıt terimleri), `analysis_groups_tr`, `evidence_plain_tr`, `module_labels` |
| `int_analyses` Analizler ve gerekli bilgiler | `ui.disease_hints_tr`, `text_tr.af_form_note` |
| `int_about` Hakkında | `frontend/src/pages/About.tsx` (sabit metin), `disclaimer_tr`, `privacy.policy` |
| `mc_<model>` ×13 Model kartları | `app/docs/model_cards/*.md`; bölümler 0–5, 7, 10–13, 15, 16 (dosya yolları, alt grup tabloları, etik ve TRIPOD özeti alınmadı); kart SHA256'sı belge başlığında |

## 3. Dış kaynaklar — metin olarak alınanlar (29)

Lisans doğrulaması kaynakların kendi resmi sayfalarından yapıldı (aşağıda). Metin, sayfanın ana içerik alanından
**değiştirilmeden** alındı; başlığı tedavi/ilaç/doz/terapi/cerrahi/yönetim/klinik çalışma/kaynakça içeren bölümler asistan
kuralları gereği **alınmadı** (alıntı seçimi; `sources.json > sections_excluded`). Dipnot üst simgeleri (`<sup>`) atlandı.

| kaynak | lisans dayanağı (resmi sayfa) | koşul |
|---|---|---|
| MedlinePlus (NLM) — sağlık konusu özetleri, tıbbi test sayfaları | [Linking to and Using Content](https://medlineplus.gov/about/using/usingcontent/): "Summaries on health topic pages", "Medical test information" kamu malı | atıf "Source: MedlinePlus, National Library of Medicine."; A.D.A.M. ansiklopedisi ve ASHP ilaç monografları telifli → alınmadı |
| CDC | [Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html): çoğu içerik kamu malı | atıf, onay anlamına gelmediği notu (README + belge başlığı), içerik değiştirilmez, ücretsiz erişim notu |
| NIDDK | [Copyright](https://www.niddk.nih.gov/copyright): "copyright free" | değiştirilmeden yeniden üretimde NIDDK kaynak gösterilir; onay/kişisel tıbbi tavsiye ima edilmez |

Bu nedenle dış metinler repoya konuldu (`kb/external/*.md`, her birinde URL, erişim tarihi, lisans ve atıf başlığı).

| id | yayıncı | başlık | URL | metin SHA256 |
|---|---|---|---|---|
| mp_af | MedlinePlus | Atrial Fibrillation | https://medlineplus.gov/atrialfibrillation.html | 7e532264f9adfbf5… |
| mp_cirrhosis | MedlinePlus | Cirrhosis | https://medlineplus.gov/cirrhosis.html | d2990631cffcf8d5… |
| mp_steatotic_liver | MedlinePlus | Steatotic Liver Disease | https://medlineplus.gov/steatoticliverdisease.html | b7be272f1fcac0e2… |
| mp_osteoporosis | MedlinePlus | Osteoporosis | https://medlineplus.gov/osteoporosis.html | 9168037af50dcb7f… |
| mp_diabetes | MedlinePlus | Diabetes | https://medlineplus.gov/diabetes.html | ecee1ce3f6b73e2e… |
| mp_ckd | MedlinePlus | Chronic Kidney Disease | https://medlineplus.gov/chronickidneydisease.html | c01a21207c7fddc4… |
| mp_hbp | MedlinePlus | High Blood Pressure | https://medlineplus.gov/highbloodpressure.html | fa4a45eca43ccb0a… |
| mp_anemia | MedlinePlus | Anemia | https://medlineplus.gov/anemia.html | 6934d38cde283c43… |
| mp_copd | MedlinePlus | COPD | https://medlineplus.gov/copd.html | 1ec0064ec6e6eca9… |
| mp_cad | MedlinePlus | Coronary Artery Disease | https://medlineplus.gov/coronaryarterydisease.html | c173c987f1383b0a… |
| mp_test_a1c | MedlinePlus | Hemoglobin A1C (HbA1c) Test | https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/ | cd4bd4f291a3826d… |
| mp_test_cbc | MedlinePlus | Complete Blood Count (CBC) | https://medlineplus.gov/lab-tests/complete-blood-count-cbc/ | 1f785ca798577e9f… |
| mp_test_lft | MedlinePlus | Liver Function Tests | https://medlineplus.gov/lab-tests/liver-function-tests/ | 6be89ea0223e720a… |
| mp_test_ecg | MedlinePlus | Electrocardiogram | https://medlineplus.gov/lab-tests/electrocardiogram/ | 5e03030bd067fa0c… |
| mp_test_lung | MedlinePlus | Lung Function Tests | https://medlineplus.gov/lab-tests/lung-function-tests/ | 7701cabab536da85… |
| mp_test_egfr | MedlinePlus | Estimated Glomerular Filtration Rate (eGFR) and GFR Tests | https://medlineplus.gov/lab-tests/estimated-glomerular-filtration-rate-egfr-and-gfr-tests/ | 549c166133481ea9… |
| mp_test_uacr | MedlinePlus | Microalbumin Creatinine Ratio | https://medlineplus.gov/lab-tests/microalbumin-creatinine-ratio/ | 45670340aab8493f… |
| cdc_diabetes | CDC | Diabetes Basics | https://www.cdc.gov/diabetes/about/index.html | 26acc23fc1ee25a9… |
| cdc_ckd | CDC | Chronic Kidney Disease Basics | https://www.cdc.gov/kidney-disease/about/index.html | e20133341b42e697… |
| cdc_hbp | CDC | About High Blood Pressure | https://www.cdc.gov/high-blood-pressure/about/index.html | 004530e933f0c5a6… |
| cdc_cad | CDC | About Coronary Artery Disease (CAD) | https://www.cdc.gov/heart-disease/about/coronary-artery-disease.html | 39c168847937baa9… |
| cdc_copd | CDC | About COPD | https://www.cdc.gov/copd/about/index.html | 1813e0ec4468f21b… |
| cdc_af | CDC | About Atrial Fibrillation | https://www.cdc.gov/heart-disease/about/atrial-fibrillation.html | 57b460f26aad1c05… |
| niddk_diabetes | NIDDK | What Is Diabetes? | https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes | 6528c375a6606828… |
| niddk_ckd | NIDDK | What Is Chronic Kidney Disease in Adults? | https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/what-is-chronic-kidney-disease | 3b4dc83c8a1ec401… |
| niddk_nafld | NIDDK | Definition & Facts of NAFLD & NASH | https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash/definition-facts | cfb7c92a30e9f15c… |
| niddk_nafld_dx | NIDDK | Diagnosis of NAFLD & NASH | https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash/diagnosis | 2d56ef8a11f57aa4… |
| niddk_cirrhosis | NIDDK | Definition & Facts for Cirrhosis | https://www.niddk.nih.gov/health-information/liver-disease/cirrhosis/definition-facts | 0061cee6de6f1e2b… |
| niddk_a1c | NIDDK | The A1C Test & Diabetes | https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test | 1ce0b89e07a69697… |

Tam SHA256 (ham yanıt + metin) `kb/sources.json`'dadır. Kapsam: AF, karaciğer fibrozisi (siroz, steatotik karaciğer,
NAFLD tanısı / elastografi), osteoporoz (yalnız MedlinePlus), diyabet, KBH, hipertansiyon, anemi, KOAH, KAH.

## 4. Yalnız bağlantı (metin kopyalanmadı)

| id | URL | neden |
|---|---|---|
| nhlbi_af, nhlbi_copd, nhlbi_anemia, nhlbi_hbp, nhlbi_chd | https://www.nhlbi.nih.gov/health/… | NHLBI sitesinde yeniden kullanım/telif beyanı **BULUNAMADI** (denenen sayfalar 404; "Website, Privacy, and Accessibility" sayfasında telif maddesi yok). ABD federal eseri olması muhtemeldir, ancak doğrulanmadığı için metin alınmadı. |
| who_diabetes, who_hypertension, who_copd | https://www.who.int/news-room/fact-sheets/… | görev kuralı: WHO metinleri kopyalanmaz |

## 5. Sınırlılıklar

* Dış metinler İngilizcedir; Türkçe yanıt LLM çevirisidir — çeviri hatası olasıdır (bkz. 03_eval.md elle inceleme).
* Sayfalar güncellenebilir; kilitli sürüm erişim tarihindeki metindir. `fetch_external.py` yeniden çalıştırılırsa SHA
  değişebilir → indeks yeniden kurulur ve kilit elle güncellenir.
* Eski biçimli MedlinePlus özetlerinde (siroz, KBH, hipertansiyon, anemi) başlık yoktur; tek bölüm olarak alındı ve bu
  bölümlerde tedaviden söz eden cümleler (ör. siroz özetinde nakil) metinde kalır (bölüm düzeyinde ayıklama).
* Osteoporoz için CDC/NIDDK sayfası yoktur (NIAMS kapsam listesinde değildi).
* İç belgeler `app_config.json`, `About.tsx` ve model kartlarının **bu fazdaki** sürümünden üretildi. Bu kaynaklar
  sonradan değişirse iç belgeler eskir: `build_index.py` yeniden çalıştırılmalı ve kilit güncellenmelidir. Sunucu yalnız
  `kb/` altındaki dosyaları doğrular; kaynakların güncelliği backend testi `test_internal_kb_docs_up_to_date` ile denetlenir.
