# PHASE XLIII — Uygulama için model kaydı (registry) ve ortak girdi şeması

Durum: **FINAL (kayıt fazı).** Model eğitilmedi, test kümesi açılmadı, raporlanan yeni tahmin üretilmedi. Önceki faz dosyaları salt okunur kaldı. `clinical_probability_eligibility = false` (kayıt ve 13 modelin tamamı).

## Çıktılar

| dosya | içerik |
|---|---|
| `registry/models.json` | 13 model: dosya yolu + SHA256, venv ve paket sürümleri, feature listesi/sırası (ad, tip, birim, aralık veya kategoriler), eşikler, kalibrasyon, hedef tanımı, kanıt düzeyi, sınırlılıklar, eksik-girdi kuralı |
| `registry/input_schema.json` | 75 ortak girdi alanı (birim, aralık, kategori), 46 dönüşüm tanımı, birim dönüşümleri, model × alan × dönüşüm eşlemesi, model bazında "eksikse tahmin üretme" kuralı |
| `01_model_selection.md` | hastalık × model × gerekçe × kanıt düzeyi tablosu; 4 hastalık için uygulamaya alma ÖNERİSİ |
| `scripts/registry_check.py` | doğrulama betiği; sonucu `results/registry_check.json`, `logs/registry_check.log` |
| `scripts/build_registry.py`, `registry_spec.py`, `registry_lib.py`, `make_selection_doc.py`, `verify43.py`, `sha_full_scan.py` | kayıt üretimi, elle yazılan içerik, ortak yardımcılar, belge üretimi, faz sonu denetimi |
| `config/sha256_before.json`, `results/sha256_after.json`, `results/verification43.json` | faz başı / faz sonu SHA envanteri ve denetim |

## Görev 1 — Model seçimi

Ön seçimlerin tamamı onaylandı; hiçbiri önceki faz raporlarıyla çelişmedi, her model dosyası bulundu ve SHA256'sı kilit/manifest ile birebir eşleşti. Kayıt kimlikleri:

| hastalık | kayıt | dosya (özet) |
|---|---|---|
| AF | `af_S4_DEVICE` | Phase21 `af_S4_DEVICE.joblib` (pipeline AF-ECGDELI-OCTAVE-v1) |
| MI | `mi_model` | `phase_xxxviii/models/mi_model.joblib` |
| CAD | `cad_DEVICE` | kök `models/cad/DEVICE.joblib` |
| Diyabet | `dm_A` (birincil), `dm_B` (ikincil) | `phase_xlii/models/dm_{A,B}_final.joblib` |
| Anemi | `anemia_LR16` | Phase25 `anemia_CBC_MATCHED16.joblib` |
| KOAH | `copd_S4_DEVICE` | Phase21 `copd_S4_DEVICE.joblib` |
| Kalp yetmezliği | `hf_S2_BASIC_LAB` | Phase21 `heart_failure_S2_BASIC_LAB.joblib` (Phase XXVII/26 donmuş manifesti) |
| Hipertansiyon | `htn_M1` | `phase_xxxvii/models/htn3_M1.joblib` |
| Fibrozis | `fibrosis_final` | `phase_xxxi/models/fibrosis_final.joblib` |
| Osteoporoz | `osteo_final` | `phase_xxx/models/osteo_final.joblib` |
| Böbrek | `ckd_A` (birincil), `ckd_B` (ikincil) | `phase_xxxv/models/ckd_{A,B}_final.joblib` |

Kanıt satırları, her modelin **en yüksek kanıt düzeyindeki** sonucudur (dış > zamansal > iç); iç test / zamansal / dış doğrulama `01_model_selection.md` §2'de ayrı sütunlardır. CV sonuçları kayda kanıt olarak girmedi.

**Uygulamaya taşırken önemli bulgular** (ayrıntı: `01_model_selection.md` §3):
- **MI ve kalp yetmezliği uygulamaya alınamaz.** MI: 168 lead bazlı ECGDeli feature'ını üretecek kilitli pipeline yok, yalnız iç test. KY: RIP3 özel ELISA değeri gerekir, test n=37, dış doğrulama yapılamadı. İkisi de kayıtta `app_feasibility` ile işaretli.
- **Formla doldurulabilen** modeller yalnız `dm_A`, `ckd_A`, `osteo_final`. AF (EKG + Octave pipeline), CAD (efor testi + EKG), KOAH (kaliteli pre-BD spirometri; yalnız obstrüksiyonlu 40–79 yaş) cihaz/özel veri ister. HTN M1, fibrozis, anemi, `dm_B`, `ckd_B` laboratuvar ister.
- **Anemi LR16**: ML katkısı Hct kuralına eşdeğer (ΔAUC +0,004). **HTN M1**: yaş+cinsiyet+BMI'ye katkı +0,012. **KOAH**: pre-BD FEV1/FVC<0,70 kuralına eşdeğer (+0,009). **KY**: tek değişken RIP3'e eşdeğer.
- **Üç araştırma hedefi** (P≥0,70, R≥0,75, FPR≤0,15) GA sınırlarıyla birlikte yalnız AF'nin iç testinde sağlandı (AF dış doğrulamada P prevalansa bağlı olduğundan değerlendirilemedi). Diyabet, KBH, fibrozis, osteoporoz, HTN'de hiçbir eşikte sağlanmadı; MI, CAD, anemi, KOAH, KY'de yalnız nokta tahminiyle.

**Uygulamaya alma önerisi (karar sizindir)** — dört hastalık için de **ALMA** öneriyorum; gerekçeler `01_model_selection.md` §4:
- Karaciğer yağlanması: test etiketi CONTAMINATED, FLI'ye katkı yok (+0,005, GA 0'ı içeriyor), dış CAP verisi BULUNAMADI.
- Lipid: hedefi tanımlayan lipidler girdi olamıyor; kilitli/test edilmiş yeni model yok, CV AUC ≈ 0,70.
- Astım: n=253, yaş+cinsiyete katkı ≈ 0, spirometri/semptom yok.
- Safra taşı: AUC 0,751, P 0,174, FPR 0,365; yaş+cinsiyet+BMI'ye katkı +0,012; NHANES III (1988–94).

Bu dördü için `models.json`'da model kaydı açılmadı (`candidates_not_registered`).

## Görev 2 ve 3 — Kayıt ve ortak girdi şeması

- **Üretim yöntemi.** Model SHA'sı, eşikler ve feature sırası kilit dosyalarından (veya Phase26 donmuş manifestinden); kategoriler fitted encoder'lardan okundu. Elle yazılan kısım yalnız birim, aralık, dönüşüm, kanıt sayıları ve sınırlılıklardır (`registry_spec.py`). Kanıt sayıları önceki faz raporlarından aynen alındı; **bu fazda yeniden hesaplanmadı**.
- **Kategoriler birebir.** CAD kategorileri `'0.0'/'1.0'`, `cp` `'1.0'…'4.0'`; MI `HA__Global` `'1.0'…'6.0'`; DM/KBH ikili sütunlar sayısal 0/1. Osteoporoz encoder'ında `None` kategorisi vardır: `learned_categories` içinde `null` olarak tutuldu, `allowed_values` dışında bırakıldı (eksik girdi zaten tahmin üretmez). `input_schema.policy` sessiz tür dönüşümünü yasaklar; dönüşüm tablosu tek kaynaktır (V2 CAD hatası: `phase_xlii/ERRATA_CAD_V2.md`).
- **Eksik girdi politikası.** Her modelde zorunlu alan eksikse model tahmin üretmez; dondurulmuş imputer uygulama tarafında kullanılmaz. Yapısal atlama kuralları (erkekte GDM=0, hipertansiyon yoksa `htn_med`=0, osteoporozda erkekte `na_male`) eğitimdeki tanımın aynısıdır ve eksik sayılmaz. Phase26 manifesti Phase21/25 modelleri için kısmi eksikte dondurulmuş imputer'ı serbest bırakıyordu; CLAUDE.md'ye uygun olarak daha katı kural seçildi (**karar gerektirir**, aşağıda).
- **Dönüşümler.** boy+kilo→BMI; mg/dL↔mmol/L ve diğer birimler (`unit_conversions`); `ln(max(x,1))` (DM `tg_log`, `alt_log`); CKD-EPI 2021 → `egfr`; `ln(1+UACR)` → `uacr_log`; tansiyon için DM'de 3 okumanın ortalaması, KBH'de 2. ve 3. okumanın ortalaması; yaş NHANES için 80'de kırpma.
- **Çalışma ortamı.** Kök `.venv` (sklearn 1.8.0, lightgbm 4.6.0): CAD, DM A/B, anemi, osteo, KBH A/B. `Focused_Current_Disease_Improvement_2026/.venv` (lightgbm 4.7.0, xgboost 3.4.1, catboost 1.2.10): AF, MI, KOAH, HTN, KY, fibrozis. Kök `.venv`'de catboost/xgboost yok. Fit ortamı kaydı AF (lightgbm 4.7.0, Phase21 `environment.json`) ve KBH (lightgbm 4.6.0) için bulundu; DM A/B, CAD, anemi ve osteo (hepsi LR) için fit venv kaydı BULUNAMADI; KOAH/KY Phase21 `environment.json`'a, MI/HTN/fibrozis ilgili faz raporlarına dayanır.

## Görev 4 — Doğrulama sonucu (`scripts/registry_check.py`)

**266 geçti / 0 kaldı** (13 model × 19–20 kontrol + 10 kayıt kontrolü). Her model kayıtlı venv'inde ayrı süreçte denendi. Kontroller:
- dosya SHA256, registry ve kilit dosyasıyla aynı (C1); kilit dosyası yeniden okunup feature sırası ve eşikler karşılaştırıldı;
- paket ve python sürümleri registry ile aynı (C2);
- feature sırası modelin `feature_names_in_` değeriyle (varsa), adlandırılmış sütun kümesi ColumnTransformer ile aynı (C3);
- kategoriler fitted encoder'larla string, None ve sıra dahil birebir aynı (C4);
- sentetik, sınırlar içinde ve eksiksiz girdi: yalnız ön-işleme `transform`'u; bilinmeyen kategori yok, her one-hot dilimi dolu, NaN yok (C5);
- **negatif kontrol**: bilinmeyen kategori sokulduğunda dedektör yakalıyor (C6; CAD'de `'0.0'`→`'0'`, V2 hatasının biçimi);
- `predict_proba` yalnız sentetik girdiyle ve yalnız çalıştığını göstermek için çağrıldı; sonuç raporlanmadı ve saklanmadı (C7); model SHA'sı sonrasında da aynı (C8).

**Denetçinin kendisinin sınanması.** Betik, geçici bir kopya üzerinde bilerek bozulan kayıtla (CAD `cp` kategorileri `'1'`, feature sırası değişik, SHA yanlış) bir kez denendi: 7 beklenen kontrol kaldı (C1a, C1c, C3a, C4b, C5c, C5d, C8). Kopya faz klasörü dışında tutuldu ve saklanmadı.

## Ne doğrulandı (`verify43`)

`results/verification43.json`:
- `phase_xliii/` dışında 158.222 → 158.222 dosya; **değişen 0, silinen 0, yeni 0**.
- Registry'deki 13 model SHA'sı faz başı envanteriyle aynı.
- `registry_check` 266/266.
- Faz başı SHA envanteri faz başında alındı ve beklendi (158.224 dosya; `phase_xliii/scripts/sha_full_scan.py` kopyası ve boş log dosyası bu envanterde de vardır, karşılaştırmada `phase_xliii/` süzüldü). `.venv` ve `__pycache__` önceki fazlardaki gibi hariç. Python süreçleri `-B -I` ile çalıştı.
- Test kümeleri ve mühürlü veri dosyaları bu fazda açılmadı: betikler yalnız model, kilit ve manifest dosyalarına erişir.

## Açık kalanlar ve sınırlılıklar

**Karar gerektirenler**
1. Lipid, astım, safra taşı ve karaciğer yağlanması: öneri **ALMA**; son karar sizin.
2. **Eksik girdi politikası**: katı kural (tahmin üretme) uygulandı. Phase26 manifestindeki "kısmi eksikte dondurulmuş imputer" kuralını geri getirmek isterseniz bu açık onay gerektirir.
3. MI ve KY kayıtta duruyor ama uygulamaya bağlanamaz; uygulama listesinden çıkarılmaları veya yalnız "araştırma modu"nda tutulmaları sizin kararınızdır.
4. DM ve KBH modelleri NHANES ırk sınıflarını ister. Ürün olarak ırk sorulmayacaksa bu iki model (A/B) tahmin üretemez; alternatif model eğitmek bu fazın kapsamı değildir.

**Sınırlılıklar**
- `plausible_range` ve model `allowed_range` değerleri fiziksel olarak makul giriş sınırlarıdır; modelin eğitim kapsamı (dev dağılımı) değildir. Eğitim kapsamı dışı uyarısı için dev verisi gerekir; bu fazda okunmadı. CAD sınırları Phase26 manifestinden, AF EKG ve RIP3 sınırları geçicidir (RIP3 için eğitim ort. 394, SD 235 pg/mL).
- Birim dönüşüm faktörleri (mmol/L→mg/dL vb.) standart değerlerdir; bu fazda birincil kaynaktan yeniden doğrulanmadı. CAD kodlarının anlamları (UCI `cp`, `slope` vb.) UCI belgelerinden alındı, bu fazda yeniden doğrulanmadı. Phase26 `source_definition` alanları boştur.
- DM modeli eğitimde 1–4 tansiyon okumasının ortalamasını kullandı; uygulama 3 okuma ister.
- Kanıt sayıları önceki raporlardan kopyalandı. Registry'nin yapısal doğruluğu (SHA, sıra, kategori, sürüm) kodla doğrulandı; kanıt sayılarının yeniden hesabı yapılmadı.
- 5 modelde eşik kural metni kayıtta BULUNAMADI (AF, CAD, anemi, KOAH, KY: manifest kural metni taşımıyor); eşik değerleri dondurulmuş manifestten alındı.
- Hiçbir model olasılığı klinik olasılık olarak sunulamaz. Eşik üstü/altı yalnız "araştırma sınıflaması"dır.

## Güncelleme — kullanıcı kararları işlendi

- **ALMA** (karaciğer yağlanması, lipid, astım, safra taşı): onaylandı; `candidates_not_registered.*.user_decision`.
- **Katı eksik-girdi kuralı** korundu.
- **Uygulama modu** (`models.json > app_visible, app_mode`): `mi_model`, `hf_S2_BASIC_LAB` → `app_visible=false` (registry_only); `cad_DEVICE`, `copd_S4_DEVICE` → `clinical_mode`; `af_S4_DEVICE` → `ecg_upload_demo`; diğer 8 model `standard`.
- **Irk isteğe bağlı**: yanıt yoksa `race_ethnicity` kullanan modeller (`dm_A`, `dm_B`, `ckd_A`, `ckd_B`, `htn_M1`) ABSTAIN eder; varsayılan sınıf atanmaz (şema alan notu, `policy.optional_race` ve modellerin eksik-girdi kuralı).
- **`input_schema.policy.structural_blanks`**: yapısal boşluklarda (ör. osteo `age_last_period`) modelin kendi imputer'ı eğitimdeki gibi çalışır; kullanıcının yanıtlamadığı alanlar için çalışmaz.
- `registry_check` yeni kontrollerle (R11 app modu, R12 policy maddeleri, R13 ırk-ABSTAIN kuralı) yeniden çalıştırıldı: **269 geçti / 0 kaldı**. Faz sonu SHA taraması ve `verify43` yeniden çalıştırıldı (sonuç: `results/verification43.json`).
