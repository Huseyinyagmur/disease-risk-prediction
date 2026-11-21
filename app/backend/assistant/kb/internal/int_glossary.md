---
id: int_glossary
title: Terim sözlüğü
source_ref: app_config.json > ui.glossary_tr / terms_tr
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Terim sözlüğü

## Eşik üstü / Eşik altı (ESIK_USTU / ESIK_ALTI)

Eşik üstü / Eşik altı: Modelin araştırmada sabitlenmiş eşiğine göre sınıflaması. Tanı değildir; olasılık gösterilmez.

## Sonuç üretilmedi (ABSTAIN)

Sonuç üretilmedi: Gerekli bir bilgi eksik veya belirsiz olduğu için analiz bilerek sonuç vermedi. Eksik bilgi tahminle doldurulmaz.

## Bu analiz size uygun değil (NOT_APPLICABLE / OUT_OF_SCOPE)

Bu analiz size uygun değil: Analiz sizin grubunuz (ör. yaş aralığı, gebelik, mevcut tanı) için geliştirilmedi.

## Hesaplanabilir (READY)

Hesaplanabilir: Girdiğiniz bilgiler bu analiz için yeterli.

## Eksik bilgi (MISSING)

Eksik bilgi: Analizin çalışması için listelenen bilgilerin girilmesi gerekiyor.

## İç test (internal_test)

İç test: Model, geliştirildiği veri kaynağında, eğitimde kullanılmayan kişilerde bir kez test edildi.

## Zamansal doğrulama (temporal)

Zamansal doğrulama: Model aynı kaynağın başka bir dönemine ait verisinde test edildi.

## Dış doğrulama (external)

Dış doğrulama: Model farklı bir veri kaynağında test edildi. Kartta bağımsız olup olmadığı ayrıca yazar.

## Ana modül / araştırma modülü / deneysel (module_label)

Ana modül / araştırma modülü / deneysel: Danışman tanımlı modül etiketi. Deneysel sonuçlar ana modüllerle aynı ağırlıkta yorumlanmamalıdır.

## Sonuç kartındaki durum adları

- Sonuç durumu OK: "Sonuç üretildi"
- Sonuç durumu ABSTAIN: "Sonuç üretilmedi"
- Sonuç durumu NOT_APPLICABLE: "Bu analiz size uygun değil"
- Araştırma sınıflaması ESIK_USTU: "Eşik üstü — ileri değerlendirme önerilir"
- Araştırma sınıflaması ESIK_ALTI: "Eşik altı"
- Canlı panel durumu READY: "Hesaplanabilir"
- Canlı panel durumu MISSING: "Eksik bilgi"
- Canlı panel durumu OUT_OF_SCOPE: "Bu analiz size uygun değil"
- Canlı panel durumu ABSTAIN: "Sonuç üretilemez"

## Karar kutusu notu

Araştırma sınıflamasıdır; klinik karar değildir. Olasılık gösterilmez.
Her kart, araştırmada sabitlenmiş eşiğe göre bir "araştırma sınıflaması"dır; tanı değildir ve olasılık gösterilmez.
