# Phase XLVII — Arayüz kullanılabilirlik iyileştirmesi

Tarih: 2026-11-21. Kapsam: yalnız sunum katmanı (`app/frontend/`). Backend'de yalnız metin alanları eklendi
(`app_config.json` ve `/schema` yanıtına iki anahtar). Model, eşik, registry, şema dönüşümleri ve uygunluk mantığı
**değişmedi** (bkz. §7 doğrulama).

## 1. Özet

| İstek | Yapılan | Kanıt |
|---|---|---|
| Sade dil, kodlar teknik ayrıntıda | 67 form alanının hepsine sade etiket (+ gerekirse yardım metni). NHANES/UCI kodları yalnız her alanın yanındaki "?" ile açılan teknik ayrıntıda | `test_phase47_ui_text.py`, `ui.test.tsx` |
| Tutarlı terimler, tek sözlük | `ui.terms_tr`: ABSTAIN → "Sonuç üretilmedi", NOT_APPLICABLE / OUT_OF_SCOPE → "Bu analiz size uygun değil", READY → "Hesaplanabilir", MISSING → "Eksik bilgi" | Vitest: sözlük değişince arayüz değişiyor; kaynak kodda terim metni yok |
| Metinler app_config'te | Yeni ve değişen tüm etiket/terim/yönlendirme metinleri `app_config.json > ui` ve `> form.field_ui_tr` içinde; arayüz bunları `/schema` yanıtından alıyor | §2 |
| Analiz seçimiyle başlayan akış | 1. adım "Hangi analizleri yapmak istiyorsunuz?": ana modüller, araştırma modülü, açılır deneysel bölüm ve "Tümü". Alanlar backend'in model başına gerekli alan listesinden (`/schema > models`) filtreleniyor | Vitest: 5 filtreleme testi; Playwright: yalnız fibrozis senaryosu |
| Sihirbaz | Adımlar: seçim → (seçime göre boş olmayan) bölümler → kontrol ve hesaplama. Geri/ileri düğmeleri, ilerleme çubuğu, tıklanabilir adım listesi. Veri bellekte kalıyor; adım değişince odak başlığa geçiyor | Vitest: gezinme testi; Playwright: klavye testi |
| Sonuç ekranı | Her kartta "Ne yapmalıyım?" yönlendirmesi, sade kanıt açıklaması. Metrik tabloları "Ayrıntılı test sonuçları" altında ve varsayılan kapalı. Model kimliği ve ham gerekçe teknik ayrıntıda | Vitest: 7 sonuç testi |
| Hesapla düğmesi içeriğe binmesin | Düğme yapışkan (sticky) çubuk yerine form sonundaki statik çubukta | Playwright @mobil: 375/768/1440 px, iki kaydırma konumunda kesişme 0 |
| Mobil ve erişilebilirlik | 375 ve 768 px'te yatay taşma 0. axe (WCAG 2.0/2.1 A+AA) ile 12 ekran × 2 genişlik taranıyor; son durumda tüm düzeylerde ihlal 0 | `results/axe_results.json` |

## 2. app_config.json değişiklikleri (yalnız sunum)

| Anahtar | İçerik |
|---|---|
| `form.sections[laboratuvar, klinik]` | Başlık ve açıklama sade dile çevrildi: "Tahlil ve solunum testi", "Hekim değerlendirmesi ve efor testi". `id` değerleri değişmedi |
| `form.field_ui_tr` (yeni) | 67 alan için `label` (sade etiket), isteğe bağlı `help` (sade yardım metni) ve `source` (kaynak değişken). `source` içindeki NHANES kodları yalnız şema metninde zaten geçen kodlardır; bunu bir test denetliyor. UCI adları (cp, restecg, thalach, exang, oldpeak, slope) UCI Heart Disease değişken adlarıdır |
| `ui.terms_tr` (yeni) | Durum, karar ve kanıt düzeyi terimleri |
| `ui.glossary_tr` (yeni) | Hakkında sayfasındaki "Terimler" bölümü: terim, kod, açıklama |
| `ui.disease_names_tr`, `ui.disease_hints_tr`, `ui.model_names_tr` (yeni) | Analiz seçimi ve kart başlıkları |
| `ui.evidence_plain_tr` (yeni) | Model başına sade kanıt açıklaması. Registry'deki kanıt kaynaklarından yazıldı: AF için Almanya (PTB-XL) ile Çin ve ABD (Challenge 2021). Diğer modeller için ABD NHANES veya UCI. Bağımsız olmayan doğrulamalar açıkça "bağımsız değildir" diye yazıldı |
| `ui.next_steps_tr` (yeni) | Her sonuç türü için varsayılan "Ne yapmalıyım?" metni ve hastalığa özgü eşik üstü metni. Örnek: fibrozis için "Karaciğer elastografisi (FibroScan) için hekiminize danışın". Eşik altı varsayılanı: "Bu sonuç hastalığı dışlamaz…". Tanı ve tedavi önerisi içermez; bir test yasak ifadeleri tarıyor |
| `ui.analysis_groups_tr` (yeni) | Seçim ekranındaki modül grupları; deneysel grup `collapsed` (açılır) |
| `ui.reason_replacements_tr` (yeni) | Sunucu gerekçelerindeki teknik ifadelerin sade karşılığı (yalnız gösterim). Örnekler: "model popülasyonu" → "analizin geliştirildiği grup", "policy.optional_race gereği…" → "bu bilgi tahminle doldurulmaz", ": POST /ecg/af" → ' ("EKG ile AF" sayfası)'. Ham metin teknik ayrıntıda kalıyor |
| `ui.text_tr` (yeni) | Sihirbaz, panel ve sonuç ekranı metinleri (74 anahtar) |

Backend kodundaki tek değişiklik `service.py > schema_public` içinde iki satır: `form.field_ui_tr` ve `ui` anahtarları
`/schema` yanıtına eklendi. Vitest şema fixture'ı gerçek `/schema` yanıtından yeniden üretildi
(`scripts/gen_schema_fixture.py`). Betik, sunum anahtarları dışındaki her şeyin son commit'tekiyle birebir aynı
olduğunu doğruluyor; fark çıkarsa fixture'ı yazmadan duruyor (`results/schema_fixture_regen.json`).

## 3. Davranış notları

- **Gönderilen alanlar:** `/eligibility` ve `/predict` isteklerine yalnız seçilen analizlerin alanları gider. Bu, gizli
  alanları göndermeme kuralının (önceden de vardı: `ask_when` sağlanmayan alanlar) seçime genişletilmesidir. Seçilmeyen
  analizler sunucuda yine çalışır ve eksik bilgi nedeniyle sonuç üretmez, ancak arayüzde gösterilmez. Sunucu
  tarafındaki uygunluk mantığı aynıdır.
- **`rip3_pgml`:** hiçbir uygulama modeli bu alanı kullanmıyor; bu nedenle hiçbir seçimde, "Tümü"nde bile gösterilmez.
  Önceden formda görünüyordu ama hiçbir modeli etkilemiyordu.
- **Örnek profil:** analiz seçilmemişken bir sentetik profil yüklenirse "Tümü" seçilir. Seçim varsa korunur.
- **Uyarı bandı:** 640 px'ten dar ekranlarda sabit (sticky) değil. 375 px'te bant 4 satır tutuyor ve kaydırırken
  içeriğin üstüne biniyordu. Bant hâlâ her sayfanın en üstünde.
- **Enter tuşu:** bir alandayken Enter, eskiden olduğu gibi "Sonuçları hesapla"yı tetikler.

## 4. Testler

| Paket | Sonuç | Dosya |
|---|---|---|
| Backend pytest (tam) | 327 geçti, 5 strict-xfail (önceden onaylı BMI sınırlılığı), 0 hata. Faz başında 320 geçmişti; fark yeni 7 test | `results/pytest_backend_full.xml` |
| Vitest + RTL | 54/54 geçti (önceki 36 test güncellendi, yeni testler eklendi) | `results/vitest_junit.xml` |
| Playwright (canlı backend, üretim derlemesi) | 27/27 geçti, 0 flaky | `results/playwright/` |
| Playwright @screenshots | 3/3 (26 görüntü) | `screenshots/` |

Playwright grupları:

- Dört senaryo grubu yeniden koşuldu: @normal (5), @eksik (5), @birim (4), @kapsam (5).
- @gizlilik (2): yenilemede analiz seçimi de siliniyor.
- @mobil (3): 375, 768 ve 1440 px.
- @a11y (3): axe 1440 px, axe 375 px ve klavye testi.

Yeni testler:

- Vitest:
  - Analiz seçimine göre alan filtreleme (fibrozis, osteoporoz, AF, Tümü). Beklenen alan kümesi testte
    `/schema > models` listesinden hesaplanıyor, elle yazılmıyor.
  - Panelin yalnız seçilen analizleri göstermesi.
  - Sihirbaz gezinme ve odak.
  - Hesapla çubuğunun sticky/fixed olmaması.
  - Sözlük terimleri: sözlük değişince arayüz değişiyor; terimler kaynak kodda geçmiyor.
  - Sade dil: etiketlerde kaynak kodu yok; DOM'da eksik metin anahtarı (`⟦…⟧`) yok.
  - Sonuç kartlarının görünür metninde ham alan adı, model kimliği ve durum kodu yok.
  - Metrik tabloları varsayılan kapalı; "Ne yapmalıyım?" metinleri doğru.
- Backend: `test_phase47_ui_text.py` (7 test).
- Playwright: yalnız fibrozis seçimiyle gerçek backend senaryosu, `@mobil`, `@a11y`, yeni ekran görüntüsü spec'i.

Güncellenen eski testler yalnız metin ve akış nedeniyle değişti. Örnekler: "Çalışabilir" → "Hesaplanabilir",
"Kapsam dışı" → "Bu analiz size uygun değil", "eksik zorunlu alan" → "Eksik bilgiler", form öncesi analiz seçimi,
laboratuvar alanları için adım geçişi. Durum kodu (`data-state`, `data-status`) ve sonuç sınıfı beklentilerinin
hiçbiri değişmedi.

## 5. Erişilebilirlik (axe-core 4.11.3, `@axe-core/playwright`)

Taranan ekranlar (1440 px ve 375 px):

- giriş ve analiz seçimi (deneysel grup açık);
- 6 form adımı: öykü adımında teknik ayrıntı açık, tahlil adımında hata durumu;
- sonuçlar (tüm metrik tabloları açık);
- EKG sonucu (Octave ile gerçek çalıştırma);
- model kartları ve Hakkında.

Geliştirme sırasında bulunan ve düzeltilen sorunlar:

- **`scrollable-region-focusable` (serious):** metrik tablosu kaydırma alanı klavyeyle odaklanamıyordu. Alan
  `tabIndex=0` + `role=region` + etiket aldı. Hakkında tablosu da aynı biçimde düzeltildi.
- **375 px'te Hakkında yatay taşması:** 409 px > 375 px. Tablo kaydırılabilir bölgeye alındı.
- **Kontrast:** önlem olarak `text-slate-400` / `slate-500` küçük metinler `slate-600/700`'e yükseltildi; rozetlerde
  kenarlık koyulaştırıldı.

Son durum: 24 taramada kritik, ciddi, orta ve küçük düzeyde ihlal yok (`results/axe_results.json`).

Klavye testi: Tab ile analiz kutusu seçilir (odak halkası görünür) → İleri düğmesi (Enter) → odak adım başlığına
geçer → "?" teknik ayrıntı Enter ile açılır → Tab ile alana geçilir → Geri ile önceki adıma dönülür. Veri adımlar
arasında korunur.

Etiket–alan ilişkisi: her alanın `label[for]` ve `aria-describedby` bağlantısı var (yardım metni ve hata). "?"
düğmesinde `aria-expanded` ve `aria-controls` kullanılıyor. İlerleme çubuğu `role=progressbar` ve
`aria-valuenow`/`aria-valuetext` taşıyor. Etkin adım `aria-current="step"` ile işaretli.

## 6. Ekran görüntüleri

`screenshots/` klasöründe 26 görüntü var: masaüstü 12, tablet (768 px) 7, mobil (375 px) 7. Tümü sentetik
profillerle ve açık PTB-XL örnek kayıtlarıyla alındı. README'deki görseller bu klasöre yönlendirildi.

## 7. Bütünlük doğrulaması (`scripts/verify47.py` → `results/verification47.json`)

Faz başında 158 545 dosya, faz sonunda 158 600 dosya tarandı. Taramada `.git`, `node_modules`, `.venv`,
`__pycache__` ve `dist` hariç tutuldu.

| Denetim | Sonuç |
|---|---|
| Önceki faz klasörleri, modeller, registry, ham veri: değişen / silinen | 0 / 0 |
| Faz dışında (app/ ve phase_xlvii/ dışında) yeni dosya | 0 |
| Değişen dosyalar | 29: README.md (görseller, test tablosu), app_config.json, service.py (2 satır), frontend kaynakları/testleri, fixture, package.json/lock (`@axe-core/playwright` 4.11.3) |
| app/ altında yeni dosya | 7: AnalysisSelect.tsx, lib/selection.ts, lib/ui.ts, lib/ui.test.tsx, e2e/a11y.spec.ts, e2e/mobile.spec.ts, tests/test_phase47_ui_text.py |
| Model mantığı dosyaları (transforms, eligibility, features, model_loader, validation, ecg_af, ecg_window, main, paths) | değişmedi (son commit'e göre `git diff` boş) |
| service.py farkı | yalnız 2 satır eklendi, silinen satır yok (`/schema` metin anahtarları) |
| Kilitli registry dosyaları (models.json, input_schema v1/v2) SHA256 | app_config'teki değerlerle aynı |
| Parity ve senaryo testleri (backend) | tam pytest içinde geçti (§4) |

## 8. Sınırlılıklar ve açık kalanlar

- Giriş, EKG ve Hakkında sayfalarındaki uzun açıklama paragrafları ile EKG öznitelik tablosu metinleri hâlâ frontend
  kodunda duruyor. Bu fazda etiketler, terimler, yönlendirmeler ve sihirbaz/sonuç metinleri app_config'e taşındı;
  sayfa düzyazısı taşınmadı.
- Sade etiketler (ör. "Büyük tansiyon (sistolik)") şemadaki araştırma tanımının yerine geçmez. Araştırma tanımı
  teknik ayrıntıda gösteriliyor.
- "Ne yapmalıyım?" metinleri genel yönlendirmedir. Klinik kılavuz değerlendirmesinden geçmedi ve klinik onay
  kriteri değildir.
- axe otomatik denetimi WCAG uyumunun yalnız bir bölümünü kapsar. Ekran okuyucuyla elle test yapılmadı.
- Mobilde canlı durum paneli formun altında ve "Tümü" seçiliyken uzun.
- Kullanıcı testi (gerçek kullanıcılarla kullanılabilirlik çalışması) yapılmadı.
