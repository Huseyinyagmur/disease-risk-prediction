# Model kartları

Phase XLVI, TRIPOD+AI eşlemeli. Üretim: `phase_xlvi/scripts/build_cards.py`.

| model | hastalık | uygulamadaki durum | en yüksek kanıt |
|---|---|---|---|
| [`af_S4_DEVICE`](af_S4_DEVICE.md) | Atriyal fibrilasyon (AF) | ana modül | dış doğrulama (bağımsız, farklı kaynaklar; donmuş model + kilitli pipeline bileşimi) |
| [`fibrosis_final`](fibrosis_final.md) | Karaciğer fibrozisi (LSM ≥ 8 kPa) | ana modül | iç test (NHANES L 2021–23; PREVIOUSLY_EXPOSED: kişiler CAP hedefi için görülmüş) |
| [`osteo_final`](osteo_final.md) | Osteoporoz (DXA femur T-skoru ≤ −2,5) | araştırma modülü | zamansal test (NHANES J 2017–18; DXA etiketi ilk kez) — bağımsız kurum doğrulaması DEĞİL |
| [`cad_DEVICE`](cad_DEVICE.md) | Koroner arter hastalığı (CAD) | deneysel | iç test + düzeltilmiş teknik tekrar (bağımsız dış doğrulama DEĞİL) |
| [`dm_A`](dm_A.md) | Diyabet (teşhis edilmemiş) | deneysel | iç test (NHANES içi; zamansal değil; PREVIOUSLY_EXPOSED_PERSONS başka hedef; diyabet hedefinde yeni kişiler) |
| [`dm_B`](dm_B.md) | Diyabet (teşhis edilmemiş) — laboratuvarlı | deneysel | iç test (NHANES içi; zamansal değil) |
| [`anemia_LR16`](anemia_LR16.md) | Anemi | deneysel | dış doğrulama (NHANES farklı döngüler; aynı anket programı, PREVIOUSLY_EXPOSED başka hedef) — bağımsız kurum doğrulaması DEĞİL |
| [`copd_S4_DEVICE`](copd_S4_DEVICE.md) | KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) | deneysel | zamansal tekrar (aynı anket, farklı döngü; PREVIOUSLY_EXPOSED) — bağımsız klinik kohort DEĞİL |
| [`htn_M1`](htn_M1.md) | Hipertansiyon | deneysel | zamansal test (C 2003–04; ölçüm yöntemi kaymalı: auskültatuvar vs oskilometrik) — bağımsız kurum doğrulaması DEĞİL |
| [`ckd_A`](ckd_A.md) | Böbrek (farkında olunmayan tek ziyaret renal anormalliği) | deneysel | iç test (NHANES I 2015–16; PREVIOUSLY_EXPOSED başka hedef; zamansal değil) |
| [`ckd_B`](ckd_B.md) | Böbrek — laboratuvarlı | deneysel | iç test (NHANES I; PREVIOUSLY_EXPOSED) |
| [`mi_model`](mi_model.md) | Miyokard enfarktüsü (EKG bulgusu) | uygulamada değil (registry_only) | iç test |
| [`hf_S2_BASIC_LAB`](hf_S2_BASIC_LAB.md) | Kalp yetmezliği | uygulamada değil (registry_only) | iç test (n=37) |

TRIPOD+AI kontrol listesi: `phase_xlvi/tripod_ai_checklist.md`.
