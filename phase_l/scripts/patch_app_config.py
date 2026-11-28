"""Phase L: app_config.json'a arayüz metinlerini ekler (yalnız sunum; model, eşik, uygunluk mantığı değişmez).
Tekrar çalıştırılabilir: anahtarlar varsa üzerine yazar. Dosya biçimi: mevcut girinti korunmaz, json.dumps(indent=1).
Kullanım (V2 kökünden): python -B phase_l/scripts/patch_app_config.py"""
import json
from pathlib import Path

V2 = Path(__file__).resolve().parents[2]
P = V2 / 'app/backend/config/app_config.json'
cfg = json.loads(P.read_text(encoding='utf8'))
ui, form = cfg['ui'], cfg['form']

form['virtual_field_labels_tr']['ecg_record'] = 'EKG kaydı'
desc = {
    'temel': 'Yaş, cinsiyet ve gebelik durumu, her analizin kimler için geliştirildiğini kontrol etmek için sorulur.',
    'olcumler': 'Boy, kilo, bel çevresi ve tansiyon analizlerin çoğunda kullanılır. Tansiyonu oturarak, en az 5 dakika '
                'dinlendikten sonra art arda 3 kez ölçün.',
    'oyku': 'Aldığınız tanılar ve kullandığınız ilaçlar, bazı analizlerin size uygun olup olmadığını belirler; bir kısmı '
            'analizde de kullanılır.',
}
for s in form['sections']:
    if s['id'] in desc:
        s['description_tr'] = desc[s['id']]

ui['default_selected_module_labels'] = ['ana modül', 'araştırma modülü']
ui['default_selected_source'] = 'Phase L: ilk açılışta yalnız ana modüller + araştırma modülü (osteoporoz) seçili; deneyseller kapalı.'
for g in ui['analysis_groups_tr']:
    if g['module_label'] == 'deneysel':
        g['title'] = 'Deneysel modüller (isteğe bağlı)'

ui['disease_needs_tr'] = {
    'af': [{'text': 'EKG kaydı gerekir'}],
    'liver_fibrosis': [{'text': 'Kan tahlili gerekir'}],
    'osteoporosis': [{'text': 'Tahlil gerekmez', 'none': True}],
    'diabetes': [{'text': 'Tahlil gerekmez', 'none': True}, {'text': 'Tahlil varsa kullanılır'}],
    'kidney': [{'text': 'Tahlil gerekmez', 'none': True}, {'text': 'Tahlil varsa kullanılır'}],
    'hypertension': [{'text': 'Kan ve idrar tahlili gerekir'}],
    'anemia': [{'text': 'Kan tahlili gerekir'}],
    'copd': [{'text': 'Solunum testi gerekir'}],
    'cad': [{'text': 'Hekim muayenesi ve efor testi gerekir'}],
}

ui['feature_labels_tr'] = {'age': 'Yaş', 'bmi': 'Vücut kitle indeksi (boy ve kilodan hesaplanır)',
                           'egfr': 'Böbrek süzme hızı (kreatininden hesaplanır)'}
ui['unit_display_tr'] = {'10^3/µL': 'bin/µL', '10^6/µL': 'milyon/µL', 'kg/m2': 'kg/m²', 'mL/dk/1.73m2': 'mL/dk/1,73 m²'}

# Sunucu gerekçe metni (ham) -> ana listede gösterilen sade metin. Ham metin yalnız "Teknik ayrıntı" içinde kalır.
# re: JS düzenli ifadesi (u bayrağı). text: $1..$9 grup; {feature} = 1. grubun feature etiketi; {label}/{unit} = 1. grup
# alanının etiketi/birimi. hide: ana listede hiç gösterilmez. hide_if_other: aynı listede başka sade satır varsa gizlenir.
ui['reason_rules_source'] = ('Phase L: phase_l/scripts/scan_reasons.py ile toplanan tüm sunucu metinleri '
                             '(phase_l/results/reason_scan.json) için yazıldı; Vitest her metnin sade karşılığını denetler.')
ui['reason_rules_tr'] = [
    {'re': r'^eksik zorunlu alan', 'hide': True},
    {'re': r'^yapısal boşluk', 'hide': True},
    {'re': r'^(\w+)=(\S+) (\S*) ?model girdi aralığı dışında \[(.+), (.+)\]$', 'hide_if_other': True,
     'text': '{feature}: bu analiz yalnız $4–$5 {unit3} arasındaki değerlerle geliştirildi (sizin değeriniz: $2).'},
    {'re': r'^age: yaş ≥ 90', 'text': '90 yaş ve üstünde bu analiz sonuç üretmez (eğitim verisinde 89 yaş üstü gizlilik nedeniyle tek değerle kodlanmıştı).'},
    {'re': r'^yaş (\S+) model popülasyonu dışında \(≥ (\d+)\)$', 'text': 'Bu analiz yalnız $2 yaş ve üstündeki kişiler için geliştirildi (girdiğiniz yaş: $1).'},
    {'re': r'^yaş (\S+) model popülasyonu dışında \((\d+)–(\d+)(?: \(model girdi aralığı\))?\)$', 'text': 'Bu analiz yalnız $2–$3 yaş arasındaki kişiler için geliştirildi (girdiğiniz yaş: $1).'},
    {'re': r'^yaş (\S+): erkekte model popülasyonu (\d+)–(\d+)$', 'text': 'Bu analiz erkeklerde yalnız $2–$3 yaş arası için geliştirildi (girdiğiniz yaş: $1).'},
    {'re': r'^yaş (\S+): kadında model popülasyonu (\d+)–(\d+) \(gebe olmayan\)$', 'text': 'Bu analiz kadınlarda yalnız $2–$3 yaş arası ve gebe olmayanlar için geliştirildi (girdiğiniz yaş: $1).'},
    {'re': r'^yaş yanıtsız', 'text': 'Yaş girilmediği için bu analizin size uygun olup olmadığı belirlenemiyor.'},
    {'re': r'^cinsiyet yanıtsız', 'text': 'Cinsiyet seçilmediği için bu analizin size uygun olup olmadığı belirlenemiyor.'},
    {'re': r'^gebelik durumu "bilmiyorum"', 'text': 'Gebelik durumu bilinmediği için bu analiz yapılamadı; model gebe olmayan kişilerde geliştirildi.'},
    {'re': r'^gebelik durumu yanıtsız', 'text': 'Gebelik sorusu yanıtlanmadığı için bu analiz yapılamadı; model gebe olmayan kişilerde geliştirildi.'},
    {'re': r'^gebe:', 'text': 'Bu analiz gebe olmayan kişilerde geliştirildi; gebelikte kullanılamaz.'},
    {'re': r'^diyabet tanısı sorusu yanıtsız', 'text': 'Diyabet tanısı sorusu yanıtlanmadı; bu analiz yalnız diyabet tanısı almamış kişiler için geliştirildi.'},
    {'re': r'^diyabet tanısı var', 'text': 'Diyabet tanınız olduğu için bu analiz size uygun değil; yalnız tanı almamış kişiler için geliştirildi.'},
    {'re': r'^diyabet ilacı/insülin', 'text': 'Diyabet ilacı veya insülin kullananlar bu analizin geliştirildiği grupta yoktu.'},
    {'re': r'^"doktor zayıf/başarısız böbrek dedi mi" yanıtsız', 'text': 'Böbrek hastalığı sorusu yanıtlanmadı; bu analiz yalnız böbrek hastalığı tanısı olmayan kişiler için geliştirildi.'},
    {'re': r'^tanılı böbrek hastalığı', 'text': 'Böbrek hastalığı tanınız olduğu için bu analiz size uygun değil.'},
    {'re': r'^diyaliz:', 'text': 'Diyalize girenler bu analizin geliştirildiği grupta yoktu.'},
    {'re': r'^pre-BD FEV1/FVC', 'text': 'Solunum testinizde FEV1/FVC oranı 0,70 veya üstü (hava yolu daralması görünmüyor). Bu analiz yalnız hava yolu daralması olan kişiler için geliştirildi.'},
    {'re': r'^(\w+): şemada olmayan değer', 'text': 'Bir sorunun yanıtı geçersiz ({label}); bu analiz sonuç üretmez.'},
    {'re': r'^şemada olmayan kategori: (\w+)=', 'text': 'Bir sorunun yanıtı geçersiz ({label}); bu analiz sonuç üretmez.'},
    {'re': r'^ırk/etnik köken yanıtsız', 'text': 'Irk / etnik köken yanıtlanmadığı için bu analiz sonuç üretmez; bu bilgi tahminle doldurulmaz.'},
    {'re': r'^AF modeli yalnız EKG kaydı', 'text': 'AF analizi yalnız EKG kaydı yüklenerek yapılır ("EKG ile AF" sayfası).'},
    {'re': r'^EKG pipeline başarısız: örnekleme frekansı', 'text': 'Kayıt 500 Hz değil; bu analiz yalnız 500 Hz kayıtlarla çalışır.'},
    {'re': r"^EKG pipeline başarısız: kayıt 10 sn'den kısa", 'text': 'Kayıt 10 saniyeden kısa; bu analiz en az 10 saniyelik kayıt gerektirir.'},
    {'re': r'^EKG pipeline başarısız: AF pipeline meşgul', 'text': 'EKG analizi şu an başka bir kaydı işliyor; birkaç saniye sonra tekrar deneyin.'},
    {'re': r'^EKG pipeline başarısız', 'text': 'EKG kaydı işlenemedi; bu kayıt için sonuç üretilmedi.'},
    {'re': r'^pipeline şu feature', 'text': 'EKG kaydından bazı ölçümler çıkarılamadı.'},
    {'re': r'AF çalışma ortamı yok', 'text': 'EKG analiz ortamı bu bilgisayarda kurulu değil; AF analizi şu an yapılamaz.'},
    {'re': r'^(model devre dışı|bu model için uygunluk kuralı|AF pipeline devre dışı)', 'text': 'Bu analiz şu anda bu bilgisayarda çalıştırılamıyor (teknik sorun).'},
]
ui['unit_note_rules_tr'] = [
    {'re': r'^(\w+): (\S+) (\S+) -> (\S+) (\S+)', 'text': '{label}: $2 $3, $4 $5 olarak kullanıldı.'},
]
ui['field_error_rules_tr'] = [
    {'re': r'^(\w+)=(\S+) .*makul aralık dışında \[(.+), (.+)\]$', 'text': '{label} $3–$4 {unit} arasında olmalı.'},
    {'re': r'^(\w+) sayısal olmalı', 'text': '{label} bir sayı olmalı.'},
    {'re': r'^(\w+): desteklenmeyen birim', 'text': '{label} için bu birim kullanılamaz.'},
    {'re': r'^tutarsız okuma (\d): sistolik \((\S+)\) ≤ diyastolik \((\S+)\)', 'text': '$1. ölçümde büyük tansiyon ($2), küçük tansiyondan ($3) büyük olmalı.'},
    {'re': r'^tutarsız spirometri', 'text': 'FEV1 değeri FVC değerinden büyük olamaz.'},
]

tx = ui['text_tr']
tx.update({
    'reason_fallback': 'Bu analiz için bir koşul sağlanmadı; ayrıntısı "Teknik ayrıntı" bölümünde.',
    'field_error_fallback': 'Bu değer kabul edilmedi; ayrıntısı "Teknik ayrıntı" bölümünde.',
    'needs_label': 'Gerekenler',
    'step_of_named': 'Adım {i} / {n}: {name}',
    'step_skipped': 'Seçtiğiniz analizler için gerekmeyen adımlar atlandı: {x}.',
    'step_why': 'Neden soruluyor?',
    'summary_label': 'Sonuç özeti',
    'summary_line': '{n} analiz',
    'summary_ESIK_USTU': '{n} eşik üstü',
    'summary_ESIK_ALTI': '{n} eşik altı',
    'summary_ABSTAIN': '{n} sonuç üretilmedi',
    'summary_NOT_APPLICABLE': '{n} uygun değil',
    'summary_ECG_REQUIRED': '{n} EKG kaydı bekliyor',
    'summary_note': 'Her kartın ayrıntısı aşağıda. Eşik üstü tanı değildir; eşik altı hastalığı dışlamaz.',
    'evidence_done': 'yapıldı',
    'evidence_missing': 'yok',
    'evidence_missing_note': 'Üstü çizili: bu tür test bu model için yapılmadı veya kayıtlı sonucu yok.',
    'asst_expand': 'Paneli genişlet',
    'asst_shrink': 'Paneli daralt',
    'asst_resize': 'Panel genişliğini değiştir (sol/sağ ok tuşları)',
    'asst_suggest_title': 'Gördüğünüz sonuçlara göre örnek sorular',
    'asst_sources_n': 'Kaynaklar ({n})',
    'ecg_samples_title': 'Örnek kayıtla dene',
    'ecg_sample_af_title': 'AF kaydı',
    'ecg_sample_af_desc': 'Kayıt etiketi atriyal fibrilasyon olan örnek (PTB-XL 00691).',
    'ecg_sample_sr_title': 'Sinüs ritmi kaydı',
    'ecg_sample_sr_desc': 'Kayıt etiketi normal sinüs ritmi olan örnek (PTB-XL 00165).',
    'ecg_wait': 'Analiz yaklaşık 10–30 sn sürebilir; bu sayfadan ayrılmayın.',
    'ecg_uploading': 'Yükleniyor… %{p}',
    'ecg_processing': 'Sunucuda işleniyor… {s} sn (bu bilgisayarda ölçülen süre 7–30 sn; en çok 60 sn)',
    'ecg_err_busy': 'EKG analizi şu an başka bir kaydı işliyor (aynı anda tek kayıt); birkaç saniye sonra tekrar deneyin.',
    'ecg_err_size': 'Dosya boyutu sınırı (2 MB) aşıldı.',
    'evidence_missing_short': 'kayıt yok',
    'ecg_sample_loaded': '{title} yüklendi (PTB-XL {id}). Açık PhysioNet kaydı (geliştirme kümesinden; test kaydı değil). Yaş ve cinsiyet SENTETİK (60, erkek).',
    'footer': 'HealthRisk AI Research V2 · Phase L arayüzü · yalnız localhost · klinik karar aracı değildir',
})
tx.pop('ecg_samples_note', None)  # yerine ecg_sample_loaded (tek anahtar, yer tutuculu)
ui['asst_examples_by_outcome_tr'] = {
    'ESIK_USTU': 'Eşik üstü sonuç ne anlama geliyor?',
    'ESIK_ALTI': 'Eşik altı sonuç hastalığı dışlar mı?',
    'ABSTAIN': 'Neden sonuç üretilmedi?',
    'NOT_APPLICABLE': 'Bu analiz neden bana uygun değil?',
    'ECG_REQUIRED': 'AF analizi için EKG kaydını nasıl yüklerim?',
}
ui['asst_examples_by_disease_tr'] = {
    'liver_fibrosis': 'FibroScan nedir?',
    'osteoporosis': 'Kemik yoğunluğu ölçümü (DXA) nedir?',
    'af': 'Atriyal fibrilasyon nedir?',
    'diabetes': 'HbA1c testi nedir?',
    'kidney': 'İdrarda albümin testi nedir?',
    'hypertension': 'Yüksek tansiyon nedir?',
    'anemia': 'Anemi nedir?',
    'copd': 'KOAH nedir?',
    'cad': 'Koroner arter hastalığı nedir?',
}
ui['asst_examples_source'] = 'Phase L: öneriler yalnız sonuç ETİKETİNDEN (hastalık anahtarı + durum) seçilir; ölçüm değeri kullanılmaz.'

P.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
print('ok', len(ui['reason_rules_tr']), 'gerekçe kuralı')
