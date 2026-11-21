---
id: int_evidence
title: Kanıt düzeyi açıklamaları
source_ref: app_config.json > ui.evidence_plain_tr / analysis_groups_tr
publisher: HealthRisk AI Research V2 (proje içi belge)
accessed: —
license: proje içi (MIT)
---

# Kanıt düzeyleri ve modül etiketleri

## Kanıt düzeyi türleri

- İç test: Model, geliştirildiği veri kaynağında, eğitimde kullanılmayan kişilerde bir kez test edildi.
- Zamansal doğrulama: Model aynı kaynağın başka bir dönemine ait verisinde test edildi.
- Dış doğrulama: Model farklı bir veri kaynağında test edildi. Kartta bağımsız olup olmadığı ayrıca yazar.
- Ana modül / araştırma modülü / deneysel: Danışman tanımlı modül etiketi. Deneysel sonuçlar ana modüllerle aynı ağırlıkta yorumlanmamalıdır.

## Modül grupları

- Ana modüller (ana modül): En güçlü kanıta sahip analizler.
- Araştırma modülü (araştırma modülü): Kanıtı sınırlı; araştırma amaçlı.
- Deneysel modüller (deneysel): Kanıtı zayıf veya yalnız tek veri kaynağında test edilmiş analizler. Sonuçları ana modüllerle aynı ağırlıkta yorumlamayın.

## Atriyal fibrilasyon (EKG) — kanıt düzeyi

Modül etiketi: ana modül.
Bu model Almanya'dan bir EKG veri setinde (PTB-XL) geliştirildi ve Çin ile ABD'den farklı hastanelerin EKG verisinde ayrıca test edildi (bağımsız dış doğrulama).

## Karaciğer fibrozisi (sertleşme) — kanıt düzeyi

Modül etiketi: ana modül.
Bu model yalnız ABD ulusal sağlık taraması (NHANES 2021–23) verisinde, eğitimde kullanılmayan kişilerde test edildi; başka ülke veya hastane verisinde henüz test edilmedi.

## Osteoporoz (kemik erimesi) — kanıt düzeyi

Modül etiketi: araştırma modülü.
Bu model ABD ulusal sağlık taramasının (NHANES) daha sonraki bir döneminde (2017–18) test edildi; farklı bir kurumun verisinde test edilmedi.

## Teşhis edilmemiş diyabet — kanıt düzeyi

Modül etiketi: deneysel.
Bu model yalnız ABD ulusal sağlık taraması (NHANES 2011–14) içinde, eğitimde kullanılmayan kişilerde test edildi.

## Teşhis edilmemiş diyabet (tahlilli) — kanıt düzeyi

Modül etiketi: deneysel.
Bu model yalnız ABD ulusal sağlık taraması (NHANES 2011–14) içinde, eğitimde kullanılmayan kişilerde test edildi.

## Farkında olunmayan böbrek bulgusu — kanıt düzeyi

Modül etiketi: deneysel.
Bu model yalnız ABD ulusal sağlık taraması (NHANES 2015–16) içinde, eğitimde kullanılmayan kişilerde test edildi.

## Farkında olunmayan böbrek bulgusu (tahlilli) — kanıt düzeyi

Modül etiketi: deneysel.
Bu model yalnız ABD ulusal sağlık taraması (NHANES 2015–16) içinde, eğitimde kullanılmayan kişilerde test edildi.

## Hipertansiyon (yüksek tansiyon) — kanıt düzeyi

Modül etiketi: deneysel.
Bu model ABD ulusal sağlık taramasının daha eski bir döneminde (NHANES 2003–04) test edildi; o dönemde tansiyon ölçüm yöntemi farklıydı. Farklı bir kurumda test edilmedi.

## Anemi (kansızlık) — kanıt düzeyi

Modül etiketi: deneysel.
Bu model ABD ulusal sağlık taramasının (NHANES) farklı dönemlerinde test edildi; aynı tarama programı olduğu için bağımsız kurum doğrulaması değildir.

## KOAH (kronik akciğer hastalığı) — kanıt düzeyi

Modül etiketi: deneysel.
Bu model ABD ulusal sağlık taramasının (NHANES) başka bir döneminde, küçük bir grupta test edildi; bağımsız bir klinik grupta test edilmedi.

## Koroner arter hastalığı — kanıt düzeyi

Modül etiketi: deneysel.
Bu model ABD'den küçük bir hastane veri setinde (Cleveland, 61 kişi) test edildi; Macaristan ve ABD (VA) verisindeki tekrar bağımsız dış doğrulama sayılmaz.
