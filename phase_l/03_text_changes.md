# Phase L — değişen arayüz metinleri (app_config.json)

Kaynak: `scripts/text_changes.py` (HEAD ile çalışma kopyası karşılaştırması; elle yazılmadı). Model, eşik, registry, şema ve uygunluk mantığı bu dosyada değil; yalnız sunum metinleri.

Değişen: 4 · eklenen: 75 · kaldırılan: 3

## Değişen metinler

| anahtar | önce | sonra |
|---|---|---|
| `form.sections[olcumler].description_tr` | Boy, kilo, bel çevresi ve oturarak, ≥ 5 dk dinlenme sonrası ardışık 3 tansiyon okuması. | Boy, kilo, bel çevresi ve tansiyon analizlerin çoğunda kullanılır. Tansiyonu oturarak, en az 5 dakika dinlendikten sonra art arda 3 kez ölçün. |
| `form.virtual_field_labels_tr.ecg_record` | EKG kaydı (.hea + .dat/.mat) | EKG kaydı |
| `ui.analysis_groups_tr[deneysel].title` | Deneysel modüller | Deneysel modüller (isteğe bağlı) |
| `ui.next_steps_tr.af.ESIK_USTU` | EKG'nizin bir hekim tarafından değerlendirilmesi için hekiminize danışın. | EKG'nizin bir hekim tarafından değerlendirilmesi için hekiminize danışın. AF dışındaki bazı ritim bozuklukları (ör. ekstrasistol, flutter, hızlı kalp atımı) da bu sonucu verebilir. |

## Kaldırılan anahtarlar

| anahtar | önceki değer |
|---|---|
| `ui.glossary_tr[Eşik üstü / Eşik altı].code` | ESIK_USTU / ESIK_ALTI |
| `ui.glossary_tr[Eşik üstü / Eşik altı].term` | Eşik üstü / Eşik altı |
| `ui.glossary_tr[Eşik üstü / Eşik altı].text` | Modelin araştırmada sabitlenmiş eşiğine göre sınıflaması. Tanı değildir; olasılık gösterilmez. |

## Eklenen metinler ve kurallar

| anahtar | değer |
|---|---|
| `form.sections[oyku].description_tr` | Aldığınız tanılar ve kullandığınız ilaçlar, bazı analizlerin size uygun olup olmadığını belirler; bir kısmı analizde de kullanılır. |
| `form.sections[temel].description_tr` | Yaş, cinsiyet ve gebelik durumu, her analizin kimler için geliştirildiğini kontrol etmek için sorulur. |
| `ui.asst_examples_by_disease_tr.af` | Atriyal fibrilasyon nedir? |
| `ui.asst_examples_by_disease_tr.anemia` | Anemi nedir? |
| `ui.asst_examples_by_disease_tr.cad` | Koroner arter hastalığı nedir? |
| `ui.asst_examples_by_disease_tr.copd` | KOAH nedir? |
| `ui.asst_examples_by_disease_tr.diabetes` | HbA1c testi nedir? |
| `ui.asst_examples_by_disease_tr.hypertension` | Yüksek tansiyon nedir? |
| `ui.asst_examples_by_disease_tr.kidney` | İdrarda albümin testi nedir? |
| `ui.asst_examples_by_disease_tr.liver_fibrosis` | FibroScan nedir? |
| `ui.asst_examples_by_disease_tr.osteoporosis` | Kemik yoğunluğu ölçümü (DXA) nedir? |
| `ui.asst_examples_by_outcome_tr.ABSTAIN` | Neden sonuç üretilmedi? |
| `ui.asst_examples_by_outcome_tr.ECG_REQUIRED` | AF analizi için EKG kaydını nasıl yüklerim? |
| `ui.asst_examples_by_outcome_tr.ESIK_ALTI` | Eşik altı sonuç hastalığı dışlar mı? |
| `ui.asst_examples_by_outcome_tr.ESIK_USTU` | Eşik üstü sonuç ne anlama geliyor? |
| `ui.asst_examples_by_outcome_tr.NOT_APPLICABLE` | Bu analiz neden bana uygun değil? |
| `ui.asst_examples_source` | Phase L: öneriler yalnız sonuç ETİKETİNDEN (hastalık anahtarı + durum) seçilir; ölçüm değeri kullanılmaz. |
| `ui.default_selected_module_labels` | ["ana modül", "araştırma modülü"] |
| `ui.default_selected_source` | Phase L: ilk açılışta yalnız ana modüller + araştırma modülü (osteoporoz) seçili; deneyseller kapalı. |
| `ui.disease_needs_tr.af` | [{"text": "EKG kaydı gerekir"}] |
| `ui.disease_needs_tr.anemia` | [{"text": "Kan tahlili gerekir"}] |
| `ui.disease_needs_tr.cad` | [{"text": "Hekim muayenesi ve efor testi gerekir"}] |
| `ui.disease_needs_tr.copd` | [{"text": "Solunum testi gerekir"}] |
| `ui.disease_needs_tr.diabetes` | [{"text": "Tahlil gerekmez", "none": true}, {"text": "Tahlil varsa kullanılır"}] |
| `ui.disease_needs_tr.hypertension` | [{"text": "Kan ve idrar tahlili gerekir"}] |
| `ui.disease_needs_tr.kidney` | [{"text": "Tahlil gerekmez", "none": true}, {"text": "Tahlil varsa kullanılır"}] |
| `ui.disease_needs_tr.liver_fibrosis` | [{"text": "Kan tahlili gerekir"}] |
| `ui.disease_needs_tr.osteoporosis` | [{"text": "Tahlil gerekmez", "none": true}] |
| `ui.feature_labels_tr.age` | Yaş |
| `ui.feature_labels_tr.bmi` | Vücut kitle indeksi (boy ve kilodan hesaplanır) |
| `ui.feature_labels_tr.egfr` | Böbrek süzme hızı (kreatininden hesaplanır) |
| `ui.field_error_rules_tr` | [{"re": "^(\\w+)=(\\S+) .*makul aralık dışında \\[(.+), (.+)\\]$", "text": "{label} $3–$4 {unit} arasında olmalı."}, {"re": "^(\\w+) sayısal olmalı", "text": "{label} bir sayı olmalı."}, {"re": "^(\\w+): desteklenmeyen birim", "text": "{label} için bu birim kullanılamaz."}, {"re": "^tutarsız okuma (\\d): sistolik \\((\\S+)\\) ≤ diyastolik \\((\\S+)\\)", "text": "$1. ölçümde büyük tansiyon ($2), küçük tansiyondan ($3) büyük olmalı."}, {"re": "^tutarsız spirometri", "text": "FEV1 değeri FVC değerinden büyük olamaz."}] |
| `ui.glossary_tr[Eşik altı].code` | ESIK_ALTI |
| `ui.glossary_tr[Eşik altı].term` | Eşik altı |
| `ui.glossary_tr[Eşik altı].text` | Model sonucu, araştırmada sabitlenmiş eşiğin altında kaldı. Tanı değildir; olasılık gösterilmez. Eşik altı (negatif) sonuç hastalığı dışlamaz. |
| `ui.glossary_tr[Eşik üstü].code` | ESIK_USTU |
| `ui.glossary_tr[Eşik üstü].term` | Eşik üstü |
| `ui.glossary_tr[Eşik üstü].text` | Model sonucu, araştırmada sabitlenmiş eşiğin üstünde kaldı. Tanı değildir ve hastalık olduğu anlamına gelmez; olasılık gösterilmez. Sonucun bir hekimle değerlendirilmesi önerilir. |
| `ui.limitations_extra_source` | Phase L: registry sınırlılıklarına (salt okunur) EK, arayüzde aynı listede gösterilir. Sayılar phase_xxxiii/results/b_rhythm_fpr.csv ve afl_results.csv 'Havuz (4 kaynak, ikincil)' satırlarından birebir alınmıştır (FP/n, Wilson %95 GA). Flutter (AFL) satırı yanlış pozitif değil 'AF olarak sınıflandırılma oranı'dır; birincil metriklere katılmamıştır. |
| `ui.limitations_extra_tr.af_S4_DEVICE` | ["Başka ritimlerde \"eşik üstü\" çıkma oranı (yanlış pozitif; Challenge 2021'in 4 kaynağı birlikte, Phase XXXIII; parantez içinde %95 güven aralığı): ventrikül kaynaklı ekstrasistol (PVC) 19/62 = 0,306 (0,206–0,430); kalp pili ritmi 3/10 = 0,300 (0,108–0,603); sinüs taşikardisi (hızlı kalp atımı) 43/237 = 0,181 (0,138–0,235); kulakçık kaynaklı ekstrasistol (PAC/SVPB) 20/131 = 0,153 (0,101–0,224); diğer ritimler 72/1142 = 0,063 (0,050–0,079).", "Atriyal flutter kayıtlarının 420/651'i = 0,645 (0,608–0,681) AF olarak sınıflandı (aynı 4 kaynak, Phase XXXIII). Flutter bu modelin ayırdığı bir sınıf değildir; bu oran birincil metriklere katılmamıştır."] |
| `ui.reason_rules_source` | Phase L: phase_l/scripts/scan_reasons.py ile toplanan tüm sunucu metinleri (phase_l/results/reason_scan.json) için yazıldı; Vitest her metnin sade karşılığını denetler. |
| `ui.reason_rules_tr` | [{"re": "^eksik zorunlu alan", "hide": true}, {"re": "^yapısal boşluk", "hide": true}, {"re": "^(\\w+)=(\\S+) (\\S*) ?model girdi aralığı dışında \\[(.+), (.+)\\]$", "hide_if_other": true, "text": "{feature}: bu analiz yalnız $4–$5 {unit3} arasındaki değerlerle geliştirildi (sizin değeriniz: $2)."}, {"re": "^age: yaş ≥ 90", "text": "90 yaş ve üstünde bu analiz sonuç üretmez (eğitim verisinde 89 yaş üstü gizlilik nedeniyle tek değerle kodlanmıştı)."}, {"re": "^yaş (\\S+) model popülasyonu dışında \\(≥ (\\d+)\\)$", "text": "Bu analiz yalnız $2 yaş ve üstündeki kişiler için geliştirildi (girdiğiniz yaş: $1)."}, {"re": "^yaş (\\S+) model popülasyonu dışında \\((\\d+)–(\\d+)(?: \\(model girdi aralığı\\))?\\)$", "text": "Bu analiz yalnız $2–$3 yaş arasındaki kişiler için geliştirildi (girdiğiniz yaş: $1)."}, {"re": "^yaş (\\S+): erkekte model popülasyonu (\\d+)–(\\d+)$", "text": "Bu analiz erkeklerde yalnız $2–$3 yaş arası için geliştirildi (girdiğiniz yaş: $1)."}, {"re": "^yaş (\\S+): kadında model popülasyonu (\\d+)–(\\d+) \\(gebe olmayan\\)$", "text": "Bu analiz kadınlarda yalnız $2–$3 yaş arası ve gebe olmayanlar için geliştirildi (girdiğiniz yaş: $1)."}, {"re": "^yaş yanıtsız", "text": "Yaş girilmediği için bu analizin size uygun olup olmadığı belirlenemiyor."}, {"re": "^cinsiyet yanıtsız", "text": "Cinsiyet seçilmediği için bu analizin size uygun olup olmadığı belirlenemiyor."}, {"re": "^gebelik durumu \"bilmiyorum\"", "text": "Gebelik durumu bilinmediği için bu analiz yapılamadı; model gebe olmayan kişilerde geliştirildi."}, {"re": "^gebelik durumu yanıtsız", "text": "Gebelik sorusu yanıtlanmadığı için bu analiz yapılamadı; model gebe olmayan kişilerde geliştirildi."}, {"re": "^gebe:", "text": "Bu analiz gebe olmayan kişilerde geliştirildi; gebelikte kullanılamaz."}, {"re": "^diyabet tanısı sorusu yanıtsız", "text": "Diyabet tanısı sorusu yanıtlanmadı; bu analiz yalnız diyabet tanısı almamış kişiler için geliştirildi."}, {"re": "^diyabet tanısı var", "text": "Diyabet tanınız olduğu için bu analiz size uygun değil; yalnız tanı almamış kişiler için geliştirildi."}, {"re": "^diyabet ilacı/insülin", "text": "Diyabet ilacı veya insülin kullananlar bu analizin geliştirildiği grupta yoktu."}, {"re": "^\"doktor zayıf/başarısız böbrek dedi mi\" yanıtsız", "text": "Böbrek hastalığı sorusu yanıtlanmadı; bu analiz yalnız böbrek hastalığı tanısı olmayan kişiler için geliştirildi."}, {"re": "^tanılı böbrek hastalığı", "text": "Böbrek hastalığı tanınız olduğu için bu analiz size uygun değil."}, {"re": "^diyaliz:", "text": "Diyalize girenler bu analizin geliştirildiği grupta yoktu."}, {"re": "^pre-BD FEV1/FVC", "text": "Solunum testinizde FEV1/FVC oranı 0,70 veya üstü (hava yolu daralması görünmüyor). Bu analiz yalnız hava yolu daralması olan kişiler için geliştirildi."}, {"re": "^(\\w+): şemada olmayan değer", "text": "Bir sorunun yanıtı geçersiz ({label}); bu analiz sonuç üretmez."}, {"re": "^şemada olmayan kategori: (\\w+)=", "text": "Bir sorunun yanıtı geçersiz ({label}); bu analiz sonuç üretmez."}, {"re": "^ırk/etnik köken yanıtsız", "text": "Irk / etnik köken yanıtlanmadığı için bu analiz sonuç üretmez; bu bilgi tahminle doldurulmaz."}, {"re": "^AF modeli yalnız EKG kaydı", "text": "AF analizi yalnız EKG kaydı yüklenerek yapılır (\"EKG ile AF\" sayfası)."}, {"re": "^EKG pipeline başarısız: örnekleme frekansı", "text": "Kayıt 500 Hz değil; bu analiz yalnız 500 Hz kayıtlarla çalışır."}, {"re": "^EKG pipeline başarısız: kayıt 10 sn'den kısa", "text": "Kayıt 10 saniyeden kısa; bu analiz en az 10 saniyelik kayıt gerektirir."}, {"re": "^EKG pipeline başarısız: AF pipeline meşgul", "text": "EKG analizi şu an başka bir kaydı işliyor; birkaç saniye sonra tekrar deneyin."}, {"re": "^EKG pipeline başarısız", "text": "EKG kaydı işlenemedi; bu kayıt için sonuç üretilmedi."}, {"re": "^pipeline şu feature", "text": "EKG kaydından bazı ölçümler çıkarılamadı."}, {"re": "AF çalışma ortamı yok", "text": "EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz."}, {"re": "^(model devre dışı\|bu model için uygunluk kuralı\|AF pipeline devre dışı)", "text": "Bu analiz şu anda bu bilgisayarda çalıştırılamıyor (teknik sorun)."}] |
| `ui.text_tr.asst_expand` | Paneli genişlet |
| `ui.text_tr.asst_resize` | Panel genişliğini değiştir (sol/sağ ok tuşları) |
| `ui.text_tr.asst_shrink` | Paneli daralt |
| `ui.text_tr.asst_sources_n` | Kaynaklar ({n}) |
| `ui.text_tr.asst_suggest_title` | Gördüğünüz sonuçlara göre örnek sorular |
| `ui.text_tr.ecg_sample_af_desc` | Kayıt etiketi atriyal fibrilasyon olan örnek (PTB-XL 00691). |
| `ui.text_tr.ecg_sample_af_title` | AF kaydı |
| `ui.text_tr.ecg_sample_sr_desc` | Kayıt etiketi normal sinüs ritmi olan örnek (PTB-XL 00165). |
| `ui.text_tr.ecg_sample_sr_title` | Sinüs ritmi kaydı |
| `ui.text_tr.ecg_samples_note` | Açık PhysioNet kayıtları (PTB-XL geliştirme kümesi, test kaydı değil). Yaş ve cinsiyet sentetiktir (60, erkek). |
| `ui.text_tr.ecg_samples_title` | Örnek kayıtla dene |
| `ui.text_tr.ecg_wait` | Analiz yaklaşık 10–30 sn sürebilir; bu sayfadan ayrılmayın. |
| `ui.text_tr.evidence_done` | yapıldı |
| `ui.text_tr.evidence_missing` | yok |
| `ui.text_tr.evidence_missing_note` | Üstü çizili: bu tür test bu model için yapılmadı veya kayıtlı sonucu yok. |
| `ui.text_tr.field_error_fallback` | Bu değer kabul edilmedi; ayrıntısı "Teknik ayrıntı" bölümünde. |
| `ui.text_tr.needs_label` | Gerekenler |
| `ui.text_tr.reason_fallback` | Bu analiz için bir koşul sağlanmadı; ayrıntısı "Teknik ayrıntı" bölümünde. |
| `ui.text_tr.step_of_named` | Adım {i} / {n}: {name} |
| `ui.text_tr.step_skipped` | Seçtiğiniz analizler için gerekmeyen adımlar atlandı: {x}. |
| `ui.text_tr.step_why` | Neden soruluyor? |
| `ui.text_tr.summary_ABSTAIN` | {n} sonuç üretilmedi |
| `ui.text_tr.summary_ECG_REQUIRED` | {n} EKG kaydı bekliyor |
| `ui.text_tr.summary_ESIK_ALTI` | {n} eşik altı |
| `ui.text_tr.summary_ESIK_USTU` | {n} eşik üstü |
| `ui.text_tr.summary_NOT_APPLICABLE` | {n} uygun değil |
| `ui.text_tr.summary_label` | Sonuç özeti |
| `ui.text_tr.summary_line` | {n} analiz |
| `ui.text_tr.summary_note` | Her kartın ayrıntısı aşağıda. Eşik üstü tanı değildir; eşik altı hastalığı dışlamaz. |
| `ui.unit_display_tr.10^3/µL` | bin/µL |
| `ui.unit_display_tr.10^6/µL` | milyon/µL |
| `ui.unit_display_tr.kg/m2` | kg/m² |
| `ui.unit_display_tr.mL/dk/1.73m2` | mL/dk/1,73 m² |
