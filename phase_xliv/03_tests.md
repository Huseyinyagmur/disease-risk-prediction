# Phase XLIV — Görev 3: testler ve parity

Test paketi: `app/backend/tests/` (pytest 8.4.1, app venv). Tam çalıştırma:
`.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests` → **205 geçti, 9 beklenen başarısızlık (xfail,
strict), 0 hata** (47,7 sn; log `logs/pytest_full.log`, JUnit `results/pytest_junit.xml`).

| dosya | geçti | xfail | kapsam |
|---|---|---|---|
| `test_transforms.py` | 112 | – | şemadaki 46 dönüşümün **tamamı** (test, şema ile uygulama kümesinin eşit ve her dönüşümün en az bir vakası olduğunu doğrular); eksik → Missing, şema dışı kategori → UnknownCategory, yaş ≥ 90 → NotApplicable; osteo yapısal boşluk; **CAD string-float** çıktılarının fitted kategorilerle birebir aynılığı (`'1.0'`, `'1'` değil); models.json ↔ model_usage dönüşüm adı tutarlılığı (13 model) |
| `test_validation_units.py` | 37 | – | 19 alan–birim dönüşümünün tamamı (şemadaki çiftlerle küme eşitliği), 422 vakaları (aralık dışı, sayısal olmayan, bool sayı yerine, bilinmeyen alan, desteklenmeyen birim, sistolik ≤ diyastolik, FEV1 > FVC, EKG alanı formdan), şema dışı kategori 422 değil, null = eksik, belirsiz birim (glukoz 5,4) → 422 |
| `test_api.py` | 30 | – | /health, /models (yalnız app_visible; MI ve KY yok), /schema; tam kişi OK ve yanıtta olasılık/skor anahtarı yok, karar yalnız 4 metin alanı; **negatif**: eksik alan → ABSTAIN; aralık dışı → 422; bilinmeyen kategori → ABSTAIN; CAD `'1'` → ABSTAIN; **ırk yanıtsız → tam olarak 5 model** (dm_A, dm_B, ckd_A, ckd_B, htn_M1) ABSTAIN; B → A düşüşü ve laboratuvarla B seçimi; 6 hedef-tanımlayıcı uyarı vakası ve uyarısız durum; 8 popülasyon uygunluğu vakası; KOAH oran ≥ 0,70 → NOT_APPLICABLE; AF /predict'te değil; loopback dışı istemci → 403; kararın donmuş eşikle tutarlılığı ve eşik değerinin yanıtta olmaması |
| `test_integrity.py` | 5 | – | model SHA uyuşmazlığı → model **yüklenmeden** devre dışı, /health `degraded`; registry SHA uyuşmazlığı → tüm modeller devre dışı; paket sürüm farkı → tüm modeller devre dışı; AF kilidi doğrulandı; pipeline SHA uyuşmazlığı → /ecg/af devre dışı |
| `test_parity.py` | 11 | 9 | aşağıda |
| `test_af_e2e.py` | 10 | – | 5 kayıt uçtan uca (yavaş), dosya adı uyuşmazlığı / bozuk başlık / 250 Hz başlık → ABSTAIN, yaş 150 → 422, 3 sn zaman aşımı → ABSTAIN |

## Parity (en önemli test)

Betikler: `app/backend/tests/parity_lib.py` (adaptörler ve karşılaştırma), `tests/test_parity.py` (pytest),
`phase_xliv/scripts/t3_parity.py` (sonuçları yazar: `results/parity_summary.json`, `results/parity_features.csv`,
`results/parity_mismatch_examples.csv`).

**Yöntem.** Her model için fazın **geliştirme** feature tablosundan, modelin feature'ları eksiksiz olan kişiler arasından
seed 20261119 ile 200 kişi örneklendi. Bu kişilerin ham NHANES/UCI kayıtlarından input_schema alanları kuruldu (adaptör:
kullanıcının forma gireceği değer; model feature'ı adaptörde hesaplanmaz). Alanlar sunucunun kendi doğrulama
(`validate_fields`) ve feature (`features.build`) kodundan geçirildi; çıkan vektör geliştirme tablosuyla feature bazında
karşılaştırıldı (sayısal |Δ| ≤ 1e-6, kategorik birebir string).

**Veri erişimi.** Yalnız geliştirme tabloları okundu (`dm_dev.pkl`, `ckd_dev.pkl`, `osteo_dev.pkl`, `fib_dev.pkl`,
`htn3_dev.pkl`, Phase25 `anemia_development.pkl`, Phase21 `copd_development.pkl`, CAD için `cad.pkl` yalnız
`experiments/cad_split.json` train+validation kimlikleri). Yol koruması `_sealed` içeren dosyayı reddeder. Ham XPT/UCI
dosyaları bazı fazlarda (anemi D/A, KOAH G, CAD Cleveland) test kişilerini de içerir; okunduktan hemen sonra yalnız
örneklenen geliştirme kişilerine indirgendi. Hedef/etiket sütunlarına bakılmadı.

**Adaptörde uygulanan faz uyumlaştırmaları** (dönüşüm değil; geliştirme verisinin kendi tanımı): DM J döngüsü BIOPRO
CDC geri denklemleri (TG/ALT/ürik asit); HTN L döngüsü idrar albümini CDC geri denklemi; anemi kreatinin düzeltmeleri
(D: −0,016+0,978×Scr; A: 1,013×Scr+0,147); osteo/fibrozis/HTN alkol/gün fazların kendi ham tanımlarıyla. CAD: UCI `fbs`
yalnız ikili olduğundan adaptör temsili açlık glukozu verir (1 → 126, 0 → 100 mg/dL); bu, dönüşümün eşik mantığını sınar.

### Parity tablosu

"Karşılaştırılan" = sunucunun vektör üretebildiği kişiler. Karar etkisi: farklı çıkan kişilerde geliştirme vektörü ile
sunucu vektörünün birincil eşikte aynı sınıfı verip vermediği (olasılık saklanmadı).

| model | geliştirme havuzu (eksiksiz) | örnek | karşılaştırılan | birebir | yalnız BMI kaynak yuvarlaması | başka fark | ABSTAIN | 422 | BMI max \|Δ\| | karar değişimi |
|---|---|---|---|---|---|---|---|---|---|---|
| cad_DEVICE | 242 | 200 | 200 | **200** | – | 0 | 0 | 0 | – | 0/0 |
| dm_A | 15.666 | 200 | 180 | 0 | 180 | 0 | 16 | 4 | 0,045 | 0/180 |
| dm_B | 15.471 | 200 | 186 | 0 | 186 | 0 | 12 | 2 | 0,050 | 0/186 |
| anemia_LR16 | 3.554 | 200 | 200 | 0 | 200 | 0 | 0 | 0 | 0,005 | 0/200 |
| copd_S4_DEVICE | 143 | 143 | 143 | 0 | 143 | 0 | 0 | 0 | 0,050 | **1/143** |
| htn_M1 | 11.533 | 200 | 193 | 1 | 192 | 0 | 0 | 7 | 0,050 | 0/192 |
| fibrosis_final | 6.384 | 200 | 200 | 0 | 200 | 0 | 0 | 0 | 0,050 | 0/200 |
| osteo_final | 7.688 | 200 | 198 | 0 | 193 | **5 (age)** | 2 | 0 | 0,047 | **1/198** |
| ckd_A | 18.411 | 200 | 187 | 0 | 187 | 0 | 11 | 2 | 0,049 | 0/187 |
| ckd_B | 18.343 | 200 | 190 | 1 | 188 | **1 (dm_pills)** | 5 | 5 | 0,049 | 0/189 |

KOAH geliştirme kümesi 145 kişidir (2'sinde BMI eksik) → 143 kişinin tamamı kullanıldı (< 200).

BMI dışındaki tüm feature'lar, aşağıdaki iki fark dışında, karşılaştırılan her kişide eşit çıktı: sayısal farkların
maksimumu 0 (yalnız htn `uacr_log` 4,4e-16); kategorik/ikili değerler birebir. HTN `egfr` (CKD-EPI 2021) ve DM B
`tg_log`/`alt_log` dahil türetilmiş feature'larda fark 0.

### Uyuşmazlıklar: hangi feature, hangi dönüşüm

1. **`bmi` — dönüşüm `bmi_kgm2`** (9 model). Geliştirme tablolarındaki BMI, NHANES'in hazır `BMXBMI` değişkenidir ve
   kaynakta yuvarlanmıştır (2007 sonrası döngülerde 0,1; anemi D/A döngülerinde 0,01). Şema dönüşümü
   `weight_kg / (height_cm/100)^2` yuvarlamasızdır. Fark **her kişide** tam olarak kaynak yuvarlamasıyla açıklandı:
   sunucu değeri kaynağın ondalık hassasiyetine yuvarlanınca geliştirme değerine birebir eşit (1.675/1.675 kişi);
   |Δ| ≤ 0,05 kg/m². Karar etkisi: yalnız BMI'si farklı 1.669 kişide 1 karar değişimi (KOAH, eşik sınırında).
   **Dönüşüm değiştirilmedi** (şema tek kaynak, salt okunur). Karar gerektirir (rapor §Açık).
2. **`age` — dönüşüm `age_cap80`** (osteo_final). NHANES D (2005–06) yaşı 85'te kodlar; Phase XXX geliştirme feature'ı
   ham `RIDAGEYR`'dir (kırpılmamış). Registry dönüşümü 80'de kırpar → 81–85 yaşındaki D kişilerinde fark (örnekte 5;
   geliştirme havuzunda 201/8.635, hepsi D döngüsü; E/F/H zaten 80'de kodlu). Karar etkisi: 1 değişim (kişide yaş ve BMI
   birlikte farklı). Eğitimdeki yaş kodlaması döngüye göre karışık olduğundan hiçbir tek dönüşüm ikisini birden
   yeniden üretemez. Karar gerektirir.
3. **`dm_pills` — dönüşüm `dm_pills_rule`** (ckd_B; aynı kural ckd_A ve `dm_insulin_rule` için de geçerli). Geliştirme
   verisinde "diyabet tanısı yok" (DIQ010 = 2 veya 3 = sınırda) olup hap/insülin = 1 olan kişiler var (havuzda
   145/20.059). Şema kuralı `told_diabetes = false → 0` (yapısal atlama) bunları 0 yapar; ayrıca form bu soruyu yalnız
   tanı varsa sorar (`ask_when`). Örnekte 1 kişi; karar değişimi yok. Karar gerektirir.

### Parity'de sunucunun vektör üretmediği kişiler (uygulama politikası, uyuşmazlık değil)

- **ABSTAIN — tansiyon okuması eksik:** DM şeması 3 okumanın tamamını ister (`sbp_mean_all`); DM eğitimi mevcut 1–4
  okumanın ortalamasını kullanmıştı. KBH şeması 2. ve 3. okumayı ister; eğitim mevcut olanın ortalamasını almıştı.
  (dm_A 16, dm_B 12, ckd_A 11, ckd_B 5 kişi.)
- **ABSTAIN — osteo `age_last_period_years`:** adeti kesilmiş kadında son adet yaşı yanıtsız (2 kişi); eğitimde
  pipeline imputer'ı doldurmuştu, uygulamada katı kural (Phase XLIII kararı).
- **422 — makul aralık dışı:** diyastolik < 30 mmHg okumalar (DM 6, KBH 7 kişi; NHANES'te kayıtlı düşük DBP değerleri);
  HTN'de idrar albümini < 0,1 mg/L (7 kişi; L döngüsü geri denklemi 0'a kırpılan değerler dahil).

### Katı parity testi (xfail)

`test_parity_strict` her model için birebir eşitlik ister. BMI'yi `BMXBMI` olarak taşıyan 9 modelde **beklenen
başarısızlık** olarak işaretlidir (strict xfail: düzelirse test kırmızıya döner). CAD'de geçer (200/200 birebir).
`test_parity_explained` ise her farkın yalnız (a) BMI kaynak yuvarlaması veya (b) yukarıdaki belgelenmiş 3 registry farkı
olmasını şart koşar; 10 modelde geçer.

## AF uçtan uca

Kaynak: phase_xxviii tolerans (pipeline parity) kümesi, en küçük 5 `ecg_id` (165, 254, 480, 691, 1039);
`data/ptbxl500/*.hea/.dat`. Yaş/cinsiyet sentetik (60, erkek). Sonuç `results/af_e2e.json` (canlı sunucu, HTTP):

| ecg_id | HTTP | status | 10 feature \|Δ\| ≤ 1e-6 (phase_xxviii çıktısına göre) | max \|Δ\| | Octave sn | toplam sn |
|---|---|---|---|---|---|---|
| 165 | 200 | OK | evet | 0 | 4,2 | 6,9 |
| 254 | 200 | OK | evet | 0 | 4,4 | 6,9 |
| 480 | 200 | OK | evet | 0 | 4,3 | 6,8 |
| 691 | 200 | OK | evet | 0 | 4,4 | 6,9 |
| 1039 | 200 | OK | evet | 0 | 3,5 | 6,0 |

Pipeline çıktısı Phase XXVIII'in kayıtlı feature'larıyla bit düzeyinde aynı. Kararlar yalnız uç noktanın çalıştığını
gösterir; metrik olarak raporlanmaz (5 kayıt, sentetik yaş/cinsiyet).

## Doğrulanmayanlar / sınırlılıklar

- Parity örneklemi model başına 200 kişidir (KOAH 143); geliştirme havuzunun tamamı dönüştürülmedi.
- Adaptör (ham kod → şema alanı) bu faz tarafından yazıldı; kullanıcıların gerçek formda aynı yanıtı vereceği
  varsayımdır (ör. "sınırda diyabet" = hayır, "ilaç önerilmemiş" = ilaç kullanmıyor).
- AF uçtan uca yalnız PTB-XL `.hea + .dat` (format 16) ile denendi. PhysioNet Challenge `.hea + .mat` biçimi kabul
  edilir (başlığın gösterdiği dosya), ancak bu fazda gerçek bir `.mat` kaydıyla **denenmedi**.
- Gebelik/böbrek tanısı/diyaliz uygunluk soruları geliştirme verisinde doğrudan sınanamaz (popülasyon zaten uygun
  kişilerden oluşur); yalnız sentetik API testleriyle sınandı.


---

# Güncelleme — kullanıcı kararları sonrası (şema v2)

Yukarıdaki bölümler **v1 şema** sonuçlarıdır (tarihçe olarak korunur). Güncel sonuçlar aşağıdadır.
Betik: `scripts/t5_run_tests.py` → `results/pytest_full.xml`, `results/pytest_scenario_*.xml`,
`results/test_scenarios.json`, `logs/pytest_*.log`. (İlk çalıştırmanın `results/pytest_junit.xml` dosyası
`pytest_full.xml` ile değiştirildi.)

## Tam paket

**284 geçti, 5 beklenen başarısızlık (strict xfail), 0 hata** (183,8 sn; yavaş AF testleri dahil).

| dosya | geçti | xfail |
|---|---|---|
| `test_transforms.py` | 131 | – |
| `test_validation_units.py` | 37 | – |
| `test_api.py` | 30 | – |
| `test_scenarios.py` (dört senaryo grubu) | 45 | – |
| `test_privacy.py` (gizlilik + sabit uyarı) | 5 | – |
| `test_integrity.py` | 5 | – |
| `test_parity.py` | 16 | 5 |
| `test_af_e2e.py` (PTB-XL .hea + .dat) | 10 | – |
| `test_af_mat.py` (Challenge .hea + .mat) | 5 | – |

## Dört senaryo grubu (danışman isteği 7d; `pytest -m <grup>`)

| grup | test | geçti | kapsam |
|---|---|---|---|
| **Normal girdi** (`scenario_normal`) | 8 | 8 | yalnız form dolduran kadın; laboratuvarla B modelleri; erkek + laboratuvar; genç kadında anemi; CAD klinik; obstrüksiyonlu KOAH; ilaçlar "hayır" yanıtlı; tanısız + hap → KBH `dm_pills=1` (eğitim tanımı) ve dm_A NOT_APPLICABLE |
| **Eksik girdi** (`scenario_missing`) | 10 | 10 | bel eksik; ırk yanıtsız → tam olarak 5 model; gebelik yanıtsız ve "bilmiyorum" → 4 model ABSTAIN (osteo OK); erkekte gebelik gerekmez; kısmi laboratuvar → A'ya düşüş; tanılı + hap yanıtsız → KBH ABSTAIN; böbrek sorusu yanıtsız; son adet yaşı yanıtsız; boş form |
| **Birim hatası** (`scenario_unit`) | 10 | 10 | 8 hatalı birim vakası → 422 (birimsiz mmol/L glukoz, birimsiz µmol/L kreatinin, boy metre, spirometri litre, desteklenmeyen birim ×2, kategoriye birim, IFCC dönüşüm sonrası aralık dışı); lb/inç/mmol/L/IFCC ile girilen kişi mg/dL girişiyle aynı kararı alır; dönüşüm notu döner |
| **Kapsam dışı veri** (`scenario_out_of_scope`) | 17 | 17 | 9 popülasyon dışı vaka (yaş, gebe, tanılı diyabet, tanısız insülin, böbrek tanısı, diyaliz); KOAH oran ≥ 0,70 ve yaş 85; model girdi aralığı dışı UACR → NOT_APPLICABLE; AF yaş 92; makul aralık dışı 4 vaka → 422; şema dışı kategori → ABSTAIN |

Her senaryo testi yanıttaki sabit uyarıyı ve her sonuçtaki modül etiketini de doğrular.

## Gizlilik (danışman isteği 7a) ve sabit uyarı (7c)

`test_privacy.py`: işaretli sağlık verisi (bel 87,654321; kategori `ZZQX_PRIVACY_MARKER`; işaretli dosya adı) normal,
422, ABSTAIN, bilinmeyen alan, bozuk gövde ve hatalı AF yüklemesiyle gönderildi.
- Süreç içi: tüm logger'lar DEBUG, caplog + stdout/stderr → işaret **yok**.
- Gerçek sunucu süreci (`run_server.py`, stdout/stderr dosyaya): işaret ve `"fields"` **yok**; `app/backend` altında yeni
  dosya **yok**; geçici `hr_af_*` klasörü **kalmadı**.
- 422 yanıtı ham girdiyi yansıtmaz (FastAPI varsayılanındaki `input` alanı kaldırıldı).
- `/health > request_stats` yalnız bilinen uç nokta yolları, durum kodu sayıları ve ortalama süre içerir.
- 200, 403, 404 ve 422 yanıtlarının hepsi `disclaimer` taşır.

## Parity (şema v2)

| model | etkin BMI dönüşümü | birebir | yalnız BMI (2 ondalıklı kaynak döngüsü) | başka fark | ABSTAIN | 422 | katı test |
|---|---|---|---|---|---|---|---|
| cad_DEVICE | – | **200/200** | 0 | 0 | 0 | 0 | geçer |
| anemia_LR16 | `bmi_kgm2_r2` | **200/200** | 0 | 0 | 0 | 0 | geçer (xfail kaldırıldı) |
| copd_S4_DEVICE | `bmi_kgm2_r1` | **143/143** | 0 | 0 | 0 | 0 | geçer (xfail kaldırıldı) |
| htn_M1 | `bmi_kgm2_r1` | **193/193** | 0 | 0 | 0 | 7 | geçer (xfail kaldırıldı) |
| fibrosis_final | `bmi_kgm2_r1` | **200/200** | 0 | 0 | 0 | 0 | geçer (xfail kaldırıldı) |
| dm_A | `bmi_kgm2_r1` | 91 | 89 | 0 | 16 | 4 | xfail |
| dm_B | `bmi_kgm2_r1` | 84 | 102 | 0 | 12 | 2 | xfail |
| ckd_A | `bmi_kgm2_r1` | 106 | 81 | 0 | 11 | 2 | xfail |
| ckd_B | `bmi_kgm2_r1` | 93 | 97 | 0 (dm_pills düzeldi) | 5 | 5 | xfail |
| osteo_final | `bmi_kgm2_r1` | 64 | 129 | 5 (age) | 2 | 0 | xfail |

- **5 model neden hâlâ xfail:** eğitim BMI'si NHANES döngüsüne göre karışık hassasiyetlidir: 2009–10 ve öncesi
  (D, E, F, A) `BMXBMI` 0,01, sonrası 0,1 (ham XPT analizi: döngü başına %99,98–100 eşleşme). dm/ckd (E, F + sonraki
  döngüler) ve osteo (D, E, F + H) iki hassasiyeti birlikte içerir; tek bir yuvarlama ikisini birden üretemez. Kalan
  BMI farklarının tamamı 2 ondalıklı döngülerden gelir ve |Δ| ≤ 0,05. Karar değişimi: dm/ckd'de 0/369; osteo'da 1/134
  (yaşı ve BMI'si farklı aynı kişi). NHANES verisinde ondalık yarım-yukarı yuvarlama ile Python `round` arasında fark yok.
- **ckd dm_pills/dm_insulin:** `dm_*_train` ile örnekte fark 0 (v1'de 1).
- **HTN eGFR:** `egfr_ckdepi2021_cap80`; geliştirme verisinde fark 0 (P/L döngüleri yaşı zaten 80'de kodluyor).
- **Osteo yaş:** `age_cap80` korundu (karar 2); 5 fark belgelenmiş sınırlılık olarak kalıyor.
- v1'deki KOAH karar değişimi (BMI yuvarlaması) v2 ile ortadan kalktı.

## AF — Challenge `.hea + .mat` (karar 6)

phase_xxxiii'te işlenmiş kayıtlar. `records33.csv` dosyasından yalnız `rel/source/origin/completed` ve 10 feature sütunu
okundu (olasılık, etiket ve tanı sütunları okunmadı). Seçim: kilitli girdi koşulunu (5000 örnek = 10 sn) sağlayan ve
feature'ları eksiksiz kayıtlar arasından kaynak başına `rel` sırasına göre ilk kayıt. Yaş/cinsiyet sentetik.
Canlı sunucu sonucu (`results/af_mat_e2e.json`):

| kayıt | kaynak | HTTP | status | 10 feature \|Δ\| (phase_xxxiii'e göre) | toplam sn |
|---|---|---|---|---|---|
| JS00005 | chapman_shaoxing | 200 | OK | 0 | 17,8 |
| A0034 | cpsc_2018 | 200 | OK | 0 | 16,6 |
| E00011 | georgia | 200 | OK | 0 | 18,4 |

Model metriği raporlanmadı. 10 sn'den uzun Challenge kaydı (A0005, 12.500 örnek), kilitli `read_wfdb_500` koşulu
nedeniyle **ABSTAIN** alır. Phase XXIX/XXXIII bu tür kayıtlar için kilit dışında bir "ilk 10 sn" sarmalayıcısı
(`sampto=5000`) kullanmıştı; uygulamada bu sarmalayıcı yok (açık karar).

## registry_check

`scripts/registry_check44.py`: XLIII betiği salt okunur kullanıldı. Kayıt kontrolleri içe aktarıldı; model kontrolleri
orijinal `--worker` modunda, kayıtlı venv'lerde çalıştı. XLIII sonuç dosyalarına yazılmadı, zaman damgaları değişmedi.
**XLIII eşdeğeri 269/269** + **şema v2 kontrolleri S1–S6 6/6** = 275/275 (`results/registry_check44.json`).
S3: models.json ile v2 arasındaki dönüşüm farkları, `changes_from_v1` listesindeki 15 satırla birebir aynı.

Ortam eşdeğerliği yeniden çalıştırıldı: 13/13 model hâlâ bit düzeyinde aynı (`results/env_equivalence.json`).


---

## Kapanış güncellemesi — EKG "ilk 10 sn" ön adımı

Kilitli pipeline'ın önüne `app/backend/healthrisk_api/ecg_window.py` eklendi. Bu, `phase_xxxiii/scripts/t3_extract.py ::
read_first10s` fonksiyonunun birebir kopyasıdır (dosya SHA256 `2abc9e67…a293dca`, fonksiyon SHA256 `4818ea06…dfd8471`;
Phase XXIX'te aynı mantık). Kilit dosyası değişmedi. Başlıkta fs ≠ 500 Hz veya örnek sayısı < 5000 ise ABSTAIN.
cpsc_2018'den 10 sn'den uzun 3 kayıtta (A0005, A0036, A0048) 10 feature phase_xxxiii kayıtlı çıktısıyla birebir
(`results/af_long_e2e.json`). Tam paket: **292 geçti, 5 strict-xfail (onaylı BMI dönem sınırlılığı), 0 hata**.
Ayrıntı: `PHASE_XLIV_REPORT.md` kapanış bölümü.
