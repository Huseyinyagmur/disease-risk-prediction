# PHASE XLIV — FastAPI tahmin sunucusu (app/backend)

Durum: **FINAL (uygulama fazı).** Model eğitilmedi veya yeniden fit edilmedi; eşik, kalibrasyon, feature sırası, birimler,
registry ve önceki faz dosyaları değiştirilmedi. Test/mühürlü veri dosyası okunmadı. Model olasılığı hiçbir uç noktada
dönülmez (`clinical_probability_eligibility = false`). Sunucu yalnız `127.0.0.1`'de çalışır.

## Çıktılar

| konum | içerik |
|---|---|
| `app/backend/healthrisk_api/` | sunucu kodu (main, service, validation, eligibility, transforms, features, model_loader, ecg_af, paths) |
| `app/backend/config/app_config.json` | beklenen registry SHA'ları, paket sürümleri, çalışma modu, uygulama uygunluk soruları |
| `app/backend/run_server.py`, `README.md`, `requirements.in`, `requirements.lock` | çalıştırma ve ortam |
| `app/backend/tests/` | pytest paketi (7 dosya) + `parity_lib.py` |
| `01_env_equivalence.md` | Görev 1: app venv ve eşdeğerlik |
| `02_api.md` | Görev 2: uç noktalar, akış, örnek istek/yanıtlar |
| `03_tests.md` | Görev 3: test sonuçları, parity tablosu, AF uçtan uca |
| `scripts/` | `t1_env_equivalence.py`, `t2_api_examples.py`, `t3_parity.py`, `verify44.py`, `sha_full_scan.py` |
| `results/` | `env_equivalence.json` (+ sentetik girdiler), `api_examples.json`, `af_e2e.json`, `parity_summary.json`, `parity_features.csv`, `parity_mismatch_examples.csv`, `pytest_junit.xml`, `sha256_after.json`, `verification44.json` |

## Görev 1 — Ortam

Yalıtılmış `app/backend/.venv` (Python 3.13.3; sklearn 1.8.0, lightgbm 4.7.0, xgboost 3.4.1, catboost 1.2.10, numpy
2.2.6, pandas 2.3.1, scipy 1.16.3). 13 modelin her biri 200 sentetik girdide kayıtlı venv'inde ve app venv'inde ayrı
süreçte çalıştırıldı: **13/13 bit düzeyinde aynı (max |Δ| = 0)**; kök `.venv`'deki LightGBM 4.6.0 ile fit edilmiş KBH A/B
dahil. Ayrı süreç/venv gerekmedi. Sunucu, kurulu paket sürümleri beklenenden farklıysa tüm modelleri devre dışı bırakır.

## Görev 2 — Sunucu

`GET /health`, `GET /models` (yalnız app_visible 11 model), `GET /schema` (75 şema alanı + 3 uygunluk sorusu),
`POST /predict`, `POST /ecg/af`. Akış: birim dönüşümü → aralık doğrulaması (422) → model bazında popülasyon uygunluğu →
dönüşümler (tek kaynak, 46 kural) → registry feature sırası → tahmin → yalnız `ESIK_USTU`/`ESIK_ALTI`.
Durumlar `OK` / `ABSTAIN` / `NOT_APPLICABLE`, gerekçe, eksik alanlar, şema dışı kategoriler, katmanlı kanıt ve
sınırlılıklar döner. B modelleri laboratuvar varsa seçilir, yoksa A'ya düşülür (`fallback_from`). Hedefi tanımlayan girdi
(HbA1c/açlık glukozu, tansiyon ≥140/90 veya ilaç, hemoglobin, kreatinin/UACR) uyarısı verilir.
Model SHA256'sı **yüklemeden önce** registry ile doğrulanır; registry/şema SHA'sı, AF kilidi (pipeline, Octave exe,
ECGDeli ağacı, compat) başlangıçta doğrulanır; uyuşmazlık `/health`'te raporlanır ve ilgili model devre dışı kalır.
`/ecg/af` kilitli `af_pipeline_v1.py`'yi değiştirmeden ve kopyalamadan, SHA doğrulamasından sonra dosya yolundan çağırır;
60 sn zaman aşımı; başarısızlıkta ABSTAIN.

## Görev 3 — Testler

**205 geçti, 9 beklenen-xfail, 0 hata.** Tüm 46 dönüşüm ve 19 birim dönüşümü birim testli; negatif testler (eksik alan →
ABSTAIN, aralık dışı → 422, şema dışı kategori → ABSTAIN, ırk yanıtsız → tam olarak 5 model ABSTAIN) geçti.

**Parity** (10 standard/clinical model, geliştirme verisinden 200 kişi; KOAH 143):
- **CAD: 200/200 birebir.**
- Diğer 9 modelde BMI dışındaki tüm feature'lar karşılaştırılan her kişide eşit (BMI-dışı max |Δ| = 4,4e-16), şu iki
  istisna dışında. BMI farkı her kişide (1.675/1.675) NHANES `BMXBMI`'nin kaynak yuvarlamasıyla birebir açıklandı
  (|Δ| ≤ 0,05 kg/m²); yalnız BMI'si farklı 1.669 kişide 1 karar değişimi (KOAH).
- **Belgelenen registry/şema farkları** (dönüşümler değiştirilmedi):
  1. `osteo_final` `age` / `age_cap80`: NHANES D döngüsü yaşı 85'te kodlar, geliştirme feature'ı kırpılmamış (havuzda
     201/8.635 kişi; örnekte 5; 1 karar değişimi).
  2. `ckd_A/ckd_B` `dm_pills`/`dm_insulin` (`*_rule`): eğitimde "tanı yok/sınırda" + hap/insülin = 1 olan kişiler var
     (havuzda 145/20.059); şema kuralı bunları 0 yapar (örnekte 1; karar değişimi yok).
- Uygulama politikasından gelen ABSTAIN/422 (uyuşmazlık değil): DM 3 okuma, KBH 2.–3. okuma ister; eğitim mevcut okumaların
  ortalamasını almıştı. Diyastolik < 30 mmHg ve idrar albümini < 0,1 mg/L makul aralık dışı (422).

**AF uçtan uca:** phase_xxviii parity kümesinden 5 kayıt; 10 EKG feature'ı Phase XXVIII çıktısıyla **bit düzeyinde aynı**
(max |Δ| = 0), canlı sunucuda HTTP 200, kayıt başına ≈ 6–7 sn.

## Bütünlük (`results/verification44.json`)

- Faz başı envanteri (158.243 dosya) Görev 1'den önce alındı ve bitmesi beklendi. Faz başında Phase XLIII sonuna göre fark:
  `CLAUDE.md` (Uygulama bölümü eklenmiş) ve XLIII'ün kendi son log/denetim dosyaları; başka fark yok.
- `phase_xliv/` ve `app/` dışında 158.241 → 158.241 dosya: **değişen 0, silinen 0, yeni 0** (V1).
- 13 model dosyasının SHA256'sı registry, faz başı ve faz sonu envanterinde aynı (V2). Registry, şema, AF kilidi ve
  pipeline dosyası değişmedi (V3). Faz başından sonra yazılmış `.pyc` yok (V5; tüm süreçler `-B` / `dont_write_bytecode`).
- `app/` altında 23 yeni dosya (CLAUDE.md istisnası); `.venv` ve `__pycache__` önceki fazlardaki gibi taramaya dahil değil.

## Açık kalanlar — karar gerektirenler

1. **BMI yuvarlaması.** Şema dönüşümü yuvarlamasız; eğitim NHANES `BMXBMI` (0,1 / anemide 0,01) kullandı. Seçenekler:
   olduğu gibi bırakmak (önerim: etki |Δ| ≤ 0,05 ve 1.669 kişide 1 karar değişimi) veya şema v2'de 0,1'e yuvarlama.
2. **Osteo yaşı.** Eğitimde D döngüsü 81–85 yaşları kırpılmamış, diğer döngüler 80'de kodlu; hiçbir tek dönüşüm ikisini
   birden yeniden üretmez. Mevcut `age_cap80` korunsun mu?
3. **KBH ilaç sorusu.** `dm_pills/dm_insulin_rule` "tanı yok"ta 0 verir; eğitimde sınırda diyabetli + ilaç kullananlar 1'di.
   Hap/insülin sorusunu herkese sormak şema v2 değişikliği gerektirir.
4. **Uygunluk soruları şema dışı.** Gebelik, "zayıf/başarısız böbrek" tanısı ve diyaliz soruları Phase XLIII şemasında
   yok; `app_config.json`'da tanımlandı. Kadında gebelik yanıtsızsa ilgili 5 model ABSTAIN eder (katı yorum). Onay veya
   şemaya resmi ekleme kararı sizin.
5. **HTN eGFR yaşı.** Şema metni "ham yaş (age_cap80 DEĞİL)" der; Phase XXXVII kodu kırpılmış yaşı geçirir. NHANES P/L
   zaten 80'de kodlu olduğundan geliştirme verisinde fark 0'dır (parity doğruladı), ancak 80 yaş üstü kullanıcıda iki
   tanım ayrışır. Uygulama şemayı (ham yaş) izler.

## Sınırlılıklar

- Parity model başına 200 kişilik örnektir; adaptör (ham kod → form yanıtı) bu fazda yazıldı ve gerçek kullanıcı
  yanıtlarına denkliği bir varsayımdır.
- `.hea + .mat` (PhysioNet Challenge) biçimi kabul edilir ancak gerçek bir `.mat` kaydıyla **denenmedi**; uçtan uca test
  yalnız PTB-XL `.hea + .dat` ile yapıldı. EKG feature aralıkları (registry) geçicidir.
- Eşdeğerlik ve AF süreleri yalnız bu makinede ölçüldü. Sunucuda kimlik doğrulama yok; yalnız localhost, tek kullanıcı.
- Kanıt metrikleri registry'den aynen verilir, bu fazda yeniden hesaplanmadı. Hiçbir karar klinik karar değildir.


---

## Güncelleme — kullanıcı kararları ve danışman istekleri (2026-11-19)

İlke (kullanıcı): **şema metni ile eğitim kodu ayrışırsa eğitim kodu kazanır.** Phase XLIII şeması salt okunur kaldı.
Değişiklikler yeni bir **şema v2** dosyasında yapıldı: `phase_xliv/registry/input_schema_v2.json`
(SHA256 `01f0241a…`, `.sha256` dosyası; üretici `scripts/build_schema_v2.py`). `changes_from_v1` her değişikliği
model, feature, eski/yeni dönüşüm, gerekçe ve kanıtla listeler (15 satır). models.json (model, eşik, feature sırası)
değişmedi. Sunucu, models.json ile v2 arasındaki her dönüşüm farkının bu listede bulunmasını zorunlu tutar; listede
olmayan bir fark modeli devre dışı bırakır.

### Kararların uygulanması

| # | karar | uygulama | sonuç |
|---|---|---|---|
| 1 | BMI 0,1'e yuvarla | `bmi_kgm2_r1` (ondalık yarım-yukarı) — dm_A/B, ckd_A/B, osteo, htn, fibrozis, KOAH (+ kayıtlı KY). **Anemide `bmi_kgm2_r2` (0,01)** — aşağıda | Katı parity: CAD, anemi, KOAH, HTN, fibrozis **birebir**, xfail kaldırıldı. dm_A/B, ckd_A/B, osteo **xfail kaldı** (aşağıda) |
| 2 | Osteo yaşı `age_cap80` kalsın | dönüşüm değişmedi; `known_limitations_v2` ve parity testinde belgelendi | 5/198 kişide fark (D döngüsü 81–85 yaş) |
| 3 | Hap/insülin herkese; eğitim tanımı | alanlardan `ask_when` kaldırıldı; KBH `dm_insulin_train` / `dm_pills_train` (yanıt varsa tanıdan bağımsız kullanılır; yanıtsız + tanı yok → 0; yanıtsız + tanı var → ABSTAIN); dm_A/B dışlaması aynı alanlardan (tanısız + insülin/hap → NOT_APPLICABLE; eğitim kodu `on_med` ile aynı) | KBH dm_pills farkı 1 → 0 |
| 4 | Gebelik: katı yorum; arayüzde zorunlu, "bilmiyorum" → ABSTAIN | şema v2 alanı `pregnant: true/false/"unknown"`, `required_when: sex = female ve age_years ≥ 18`; gebelik yalnız kadının yaşı ilgili modelin yaş aralığındaysa değerlendirilir | "unknown" ve yanıtsız → dm, ckd, htn, fibrozis (ve 20–44 yaşta anemi) ABSTAIN |
| 5 | HTN eGFR: eğitimdeki (kırpılmış) yaş | `egfr_ckdepi2021_cap80`; v1 metnindeki "ham yaş" ifadesi v2'de düzeltildi | geliştirme verisinde fark 0 (önceden de 0); 80 üstü kullanıcıda artık eğitimle aynı |
| 6 | AF `.mat` biçim testi | phase_xxxiii'ten 3 Challenge kaydı (chapman_shaoxing, cpsc_2018, georgia; 10 sn), canlı sunucu + pytest | 3/3 HTTP 200, 10 feature phase_xxxiii çıktısıyla **birebir** (max \|Δ\| = 0); model metriği raporlanmadı |
| 7a | Sağlık verisi log'a/diske yok | erişim logu kapalı; genel hata işleyicisi yalnız hata türünü loglar; 422 ayrıntısı girdiyi yansıtmaz; `/health > request_stats` yalnız uç nokta sayacı/süre; AF geçici dosyaları yanıt öncesi silinir | `test_privacy.py` 5/5: süreç içi (DEBUG) ve gerçek sunucu stdout/stderr'inde işaret yok; app/backend altında yeni dosya yok; geçici AF klasörü kalmadı |
| 7b | Modül etiketi | `module_label`: AF ve fibrozis "ana modül", osteoporoz "araştırma modülü", diğerleri "deneysel" (`app_config.json > module_labels`) | her sonuçta ve `/models`'te |
| 7c | Sabit uyarı | her JSON yanıtında `disclaimer` (200/403/404/413/422/429/500) | testlerle doğrulandı |
| 7d | Dört senaryo grubu | pytest işaretleri `scenario_normal`, `scenario_missing`, `scenario_unit`, `scenario_out_of_scope` | normal 8/8, eksik 10/10, birim hatası 10/10, kapsam dışı 17/17 |

### Talimattan ayrılan / karar gerektiren noktalar

1. **Anemide BMI 0,01'e yuvarlandı (talimat 0,1 idi).** Anemi eğitim verisi (NHANES D 2005–06 + A 1999–2000)
   `BMXBMI` değerlerinin tamamı 2 ondalıklıdır; "eğitim kodu kazanır" ilkesi 0,01'i gerektirir. Sonuç: 200/200
   birebir. 0,1 isterseniz tek satırlık bir şema değişikliği yeter; o durumda anemi |Δ| ≤ 0,05 ile xfail'e döner.
   **Onayınızı rica ederim.**
2. **5 xfail kaldı ve ilkesel olarak kapanamaz.** NHANES `BMXBMI` 2009–10 ve öncesinde 2 ondalık, 2011'den sonra 1
   ondalıktır (ham XPT analizi: her döngüde %99,98–100). dm/ckd (E–F + sonraki döngüler) ve osteo (D–F + H) iki
   hassasiyeti birlikte içerir; tek bir yuvarlama ikisini birden üretemez. Kalan farkların tamamı 2 ondalıklı
   döngülerdendir ve |Δ| ≤ 0,05. Karar değişimi: dm/ckd'de 0/369. Osteo'daki 1/134 değişim, yaşı ve BMI'si birlikte
   farklı olan kişide. Katı testler bu 5 modelde strict-xfail olarak duruyor: düzelirse kırmızıya döner.
3. **AF: 10 sn'den uzun kayıtlar ABSTAIN alıyor.** Kilitli `read_wfdb_500` tam 5000 örnek ister. Phase XXIX/XXXIII
   uzun kayıtlarda kilit dışında bir "ilk 10 sn" sarmalayıcısı (`sampto=5000`) kullanmıştı (Challenge kayıtlarının
   önemli bir kısmı > 10 sn: cpsc_2018 kaydının ~%70'i). Uygulamaya eklenmesi kilidin kapsamını genişletmek demektir;
   karar sizin.
4. Gebelik sorusunda katı yorum, eğitim kodundan daha muhafazakârdır: eğitimde yalnız anemi "gebe olmadığı doğrulanmış"
   şartı koymuştu; diğer modeller yalnız RIDEXPRG = 1'i dışlamıştı (≥ 60 yaşta gebelik yanıtı yoktu). Bu, onayladığınız
   yorumdur; ilke 1'den bilinçli bir istisna olarak şema `policy.pregnancy`'de yazılıdır.

### Yeniden çalıştırılanlar

- **registry_check** (`scripts/registry_check44.py`; XLIII betiği salt okunur, XLIII sonuç dosyalarına yazılmadı):
  XLIII eşdeğeri **269/269** + şema v2 kontrolleri **6/6** (S3: models.json ↔ v2 farkları == changes_from_v1, 15 satır).
- **Ortam eşdeğerliği:** 13/13 model bit düzeyinde aynı.
- **Tüm testler:** **284 geçti, 5 strict-xfail, 0 hata** (`results/pytest_full.xml`, `results/test_scenarios.json`).
- **Canlı sunucu:** `/health` ok (schema 2.0); PTB-XL 5/5 ve Challenge `.mat` 3/3 feature birebir; yerel ağ adresinden
  erişim yok.
- **Parity:** `results/parity_summary.json` (v2), ayrıntılar `03_tests.md` güncelleme bölümünde.

### Bütünlük (`results/verification44.json`, faz sonu yeniden)

`phase_xliv/` ve `app/` dışında 158.241 → 158.241: **değişen 0, silinen 0, yeni 0**. 13 model SHA'sı, registry, v1 şema
ve AF kilidi değişmedi. Faz başından sonra yazılmış `.pyc` yok. `app/` altında 26 dosya.

### Sınırlılıklar (güncel)

- Osteo yaş kodlaması (karar 2) ve karışık BMI hassasiyeti (5 model) yukarıdaki gibi belgelendi.
- Gizlilik testi sunucunun kendi log ve disk davranışını sınar. İşletim sistemi düzeyindeki kayıtlar (ör. Windows
  olay günlüğü, ağ izleme) kapsam dışıdır. AF yüklemeleri işlem süresince geçici klasörde durur; bu, kilitli Octave
  pipeline'ının dosya girişi istemesinden kaynaklanır.
- Modül etiketleri danışman tanımıdır; kanıt düzeyini değiştirmez (kanıt katmanları ayrı alanda aynen döner).


---

## Kapanış — son kararlar (2026-11-19)

**Durum: FAZ KAPANDI.**

### Kararlar

1. **Anemi BMI 0,01** (`bmi_kgm2_r2`) onaylandı; şema v2'de olduğu gibi kaldı. Parity 200/200 birebir.
2. **5 strict-xfail kaldı** (dm_A, dm_B, ckd_A, ckd_B, osteo_final). Bunlar onaylı sınırlılıktır: NHANES `BMXBMI`
   2009–10 ve öncesinde 0,01, 2011 ve sonrasında 0,1 hassasiyetle yayımlanır. Bu modellerin eğitim verisi iki dönemi
   birlikte içerdiğinden tek bir yuvarlama ikisini birden üretemez. Kalan farklar |Δ| ≤ 0,05, yalnız 0,01'lik dönem
   kişilerinde. Karar değişimi dm/ckd'de 0/369, osteo'da 1/134 (aynı kişide yaş da farklı). Osteo'daki yaş farkı
   (`age_cap80`, karar 2) ayrı bir sınırlılıktır. İkisi de şema v2 `known_limitations_v2`'de yazılıdır.
3. **EKG "ilk 10 saniye" ön adımı** kilitli pipeline'ın ÖNÜNE ayrı bir modül olarak eklendi:
   `app/backend/healthrisk_api/ecg_window.py`.
   - **Kaynak:** `phase_xxxiii/scripts/t3_extract.py :: read_first10s` (satır 61–68; dosya SHA256
     `2abc9e677a6ac6760e03bdb25a272d3b4a898676c08e5bfe117e58932a293dca`; fonksiyon kaynak parçası SHA256
     `4818ea0622a496813d388143c41725582685c396ed4a70a40f3bb3f01dfd8471`). Aynı mantık
     `phase_xxix/scripts/t3_extract.py :: read_first10s` (satır 38–45; dosya SHA256 `58687dba…c19a99`; fonksiyon
     SHA256 `4054f472…db1ce1`); iki gövde yalnız kayıt yolu satırında farklıdır.
   - **Birebirlik:** gövde karakter karakter aynıdır. Tek fark, fazın `record_base(rel)` yardımcısının yerini doğrudan
     `record_path` argümanının almasıdır. Kilitli modül (`pl`) argüman olarak verilir. wfdb, o fazlarda olduğu gibi
     kilitli pipeline'ın vendored wfdb 4.3.1'idir.
   - **Başlangıç doğrulaması** (`verify_source`): iki kaynak dosyanın ve fonksiyon parçalarının SHA256'ları, satır
     aralığı ve ast ile okunan kaynak gövdesinin uygulamadaki kopyayla eşitliği kontrol edilir. Uyuşmazlıkta /ecg/af
     devre dışı kalır ve /health'te raporlanır.
   - **Zincir:** başlık ön kontrolü (fs ≠ 500 Hz → ABSTAIN; örnek sayısı < 5000, yani 10 sn'den kısa → ABSTAIN) →
     `read_first10s` → kilitli `run_ecgdeli` → kilitli `features_from_mat`. Bu, Phase XXIX/XXXIII zinciriyle aynıdır.
   - **Kilit değişmedi:** `phase_xxviii/config/af_pipeline_lock.json` ve `af_pipeline_v1.py` SHA'ları aynı (V3).
   - Yanıtta `pipeline.record_samples` ve `pipeline.window` (ör. "ilk 10 sn (5000 örnek) — kayıt daha uzun, kırpıldı")
     döner.

### Doğrulama

| test | sonuç |
|---|---|
| cpsc_2018, 10 sn'den uzun ilk 3 kayıt (A0005 12.500, A0036 15.687, A0048 5.807 örnek) — pytest + canlı sunucu | 3/3 HTTP 200, status OK, **10 feature phase_xxxiii kayıtlı çıktısıyla birebir** (max \|Δ\| = 0); 6,6–7,1 sn (`results/af_long_e2e.json`) |
| 10 sn kayıtlar (PTB-XL 5 + Challenge 3) ön adımla yeniden | 8/8 feature birebir (ön adım 5000 örneklik kayıtta önceki okumayla aynı) |
| 250 Hz, 1000 Hz, 4999 örnek, 3000 örnek başlıkları | 4/4 ABSTAIN (gerekçe: "500 Hz değil" / "10 sn'den kısa") |
| ön adım kaynak doğrulaması + kurcalama tespiti (değiştirilmiş gövde, yanlış SHA) | geçti |
| **Tam pytest paketi** | **292 geçti, 5 strict-xfail (onaylı), 0 hata** (`results/pytest_full.xml`) |
| Dört senaryo grubu | normal 8/8, eksik 10/10, birim hatası 10/10, kapsam dışı 17/17 |
| registry_check (XLIII eşdeğeri + şema v2) | 269/269 + 6/6 |
| Ortam eşdeğerliği | 13/13 bit düzeyinde aynı |

Model metriği raporlanmadı. phase_xxxiii'ten yalnız kimlik ve 10 feature sütunu okundu. Test/mühürlü dosya okunmadı.

### Faz sonu bütünlük

`results/verification44.json` (son tarama, kapanıştan hemen önce): `phase_xliv/` ve `app/` dışında **değişen 0, silinen
0, yeni 0**. 13 model, registry, v1 şema, AF kilidi ve pipeline dosyası değişmedi. Faz başından sonra yazılmış `.pyc` yok.

### Kalan sınırlılıklar (kapanışta)

- 5 modelde BMI dönem hassasiyeti farkı ve osteo yaş kodlaması (yukarıda; onaylı).
- Gebelik için katı yorum (onaylı). Eğitim kodundan daha muhafazakârdır (şema `policy.pregnancy`).
- "İlk 10 sn" penceresi uzun kayıtta yalnız ilk 10 saniyeyi değerlendirir; kaydın geri kalanındaki ritim görülmez
  (Phase XXIX/XXXIII ile aynı sınırlılık).
- Eşdeğerlik ve süreler yalnız bu makinede ölçüldü. Sunucu kimlik doğrulamasızdır; yalnız localhost, tek kullanıcı.
- Kararlar "araştırma sınıflaması"dır; model olasılığı klinik olasılık değildir ve dönülmez.
