# Phase XLV — Görev 2: Testler

Tüm girdiler sentetiktir; EKG testleri yalnız iki açık PTB-XL örneğini (ve bunlardan türetilmiş bozuk başlığı) kullanır.
Test/mühürlü veri dosyası okunmadı. Model metriği hesaplanmadı veya raporlanmadı. Özet: `results/test_summary.json`
(`scripts/summarize_tests.py`).

## Özet

| paket | sonuç | rapor |
|---|---|---|
| Vitest + React Testing Library (jsdom) | **29/29 geçti** (4 dosya) | `results/vitest_junit.xml`, `logs/vitest.log` |
| Playwright uçtan uca (Chromium, üretim derlemesi `vite preview` + canlı backend) | **20/20 geçti**; tekrar koşusu 20/20 | `results/playwright_results.json`, `results/playwright_junit.xml`, `logs/playwright_e2e.log`, `logs/playwright_e2e_repeat.log` |
| Backend pytest (XLIV paketi + yeni `test_phase45_ui_support.py`) | **310 geçti, 5 strict-xfail, 0 hata** | `results/pytest_backend_full.xml`, `logs/pytest_backend_full.log` |
| TypeScript `tsc --noEmit` (strict) | hata yok | — |

5 strict-xfail, XLIV kapanışında onaylanan BMI dönem hassasiyeti sınırlılığıdır (dm_A, dm_B, ckd_A, ckd_B,
osteo_final); bu fazda değişmedi. XLIV sonundaki 292 geçen teste 18 yeni test eklendi (292 + 18 = 310).

## Vitest (bileşen / birim)

| dosya | kapsam | test |
|---|---|---|
| `src/lib/form.test.ts` | form tanımı şemadan (yalnız `form_input`, EKG alanı yok, her alanın bölümü var); koşullu sorular (gebelik yalnız kadın; gebelik zorunluluğu kadın ve ≥ 18; son adet yaşı kadın + adet yok; tansiyon ilacı tanı varsa; GDM yalnız kadın; diyabet ilaçları herkese); istek gövdesi (şema biriminde düz sayı, başka birimde `{value, unit}`; gizli alan gönderilmez; sayı olmayan girdi biçim hatası; aralık dışı değer frontend'de elenmez — sunucu yetkili); birim seçici seçenekleri | 12 |
| `src/demo/profiles.test.ts` | 4 profil; her profil alanı şemada form alanı, birimler seçeneklerde, kategoriler geçerli | 5 |
| `src/pages/DataEntry.test.tsx` | form doğrulama (sunucu `field_errors` alan altında, `aria-invalid`, hata sayacı; biçim hatası hesaplamayı engeller ve `/predict` çağrılmaz); koşullu sorular (kadın ↔ erkek geçişinde gebelik/GDM açılır-kapanır, "Bilmiyorum" seçeneği); ırk sorusu isteğe bağlı ve açıklamalı; birim seçici (mmol/L → `/eligibility` gövdesinde `{value: 5.4, unit: "mmol/L"}`, mg/dL → düz sayı); panel durumları (Çalışabilir / Eksik: alan etiketleri / Kapsam dışı: gerekçe / Karar verilemez; modül etiketi; ana modüller üstte; hedef-tanımlayan uyarı); sunucuya ulaşılamazsa panel hatası | 9 |
| `src/pages/Results.test.tsx` | ana/deneysel bölüm ayrımı, olasılık metni yok; eşik üstü → "İleri değerlendirme önerilir", ABSTAIN nedeni, kanıt rozetleri, metrik tablosu, hedef tanımı; HbA1c uyarısı kartta | 3 |

Fixture'lar (`src/test/fixtures/`) backend'in sentetik girdilere verdiği gerçek yanıtlardır (`/schema`, `/models`,
`/eligibility`, `/predict`).

## Playwright — dört senaryo grubu (ayrı raporlanır)

| grup | fibrozis | AF | toplam |
|---|---|---|---|
| **@normal** normal girdi | 1/1 | 3/3 | **4/4** |
| **@eksik** eksik girdi | 2/2 | 3/3 | **5/5** |
| **@birim** birim hatası | 1/1 (+1 genel: birim hatalı profil) | 2/2 | **4/4** |
| **@kapsam** kapsam dışı veri | 3/3 | 2/2 | **5/5** |
| **@gizlilik** depolama / yenileme / uyarı | — | — | **2/2** |

| grup | test | beklenen ve gözlenen |
|---|---|---|
| normal | fibrozis: çalışabilir profil | panel READY → sonuç `OK`, karar metni, metrik tablosu, hedef tanımı; diyabet kartında HbA1c uyarısı |
| normal | AF: PTB-XL 00691 (AF) örneği | ilerleme göstergesi → `OK`, 10 öznitelik satırı, lead II grafiği, RR takogramı, "ilk 10 sn" pencere bilgisi |
| normal | AF: PTB-XL 00165 (SR) örneği | `OK` |
| normal | AF: dosya seçiciyle yükleme (+ yaş 45, kadın) | `OK` |
| eksik | fibrozis: eksik alanlı profil | panel "Eksik: … ALT … AST" → sonuç `ABSTAIN`, "eksik zorunlu alan" |
| eksik | fibrozis: trombosit silinir/geri yazılır | READY → MISSING ("Trombosit") → READY |
| eksik | AF: formda | panel "Eksik: EKG kaydı" |
| eksik | AF: yalnız .hea | ".dat veya .mat sinyal dosyası yok", "Analiz et" devre dışı |
| eksik | AF: yaş/cinsiyet yanıtsız | `ABSTAIN` ("yaş yanıtsız") |
| birim | fibrozis: albümin 42 g/dL biriminde | alan altında "makul aralık dışında", panel MISSING; g/L seçilince hata kalkar, READY; sonuç ekranında sunucu notu `albumin_gdl: 42 g/L -> 4.2 g/dL`, fibrozis `OK` |
| birim | birim hatalı profil | glukoz `[30, 800]` ve kreatinin `[0.2, 15]` alan altı hataları; "Sonuçları hesapla" engellenir; mmol/L ve µmol/L seçilince hatalar kalkar |
| birim | AF: başlıkta 250 Hz | `ABSTAIN` ("500 Hz değil") |
| birim | AF: yaş ay cinsinden (720) | sunucu 422 mesajı gösterilir |
| kapsam | fibrozis: gebe kadın profili | panel OUT_OF_SCOPE ("gebe"), osteo OUT_OF_SCOPE ("yaş 30") → sonuç `NOT_APPLICABLE` |
| kapsam | fibrozis: 19 yaş | OUT_OF_SCOPE ("yaş 19") |
| kapsam | fibrozis: gebelik "bilmiyorum" | panelde "bilmiyorum" gerekçesi (eksik laboratuvar nedeniyle durum "Eksik") |
| kapsam | AF: formda yaş 95 | panel OUT_OF_SCOPE ("18–89") |
| kapsam | AF: EKG ile yaş 95 | `NOT_APPLICABLE` ("18–89") |
| gizlilik | form + sonuç + EKG + yenileme | localStorage = 0, sessionStorage = 0, IndexedDB veritabanı yok, çerez yok, Cache Storage boş; `Storage.setItem` ve `indexedDB.open` çağrısı hiç yapılmadı (sayfaya enjekte izleyiciyle); yenileme sonrası yaş alanı boş, profil etiketi yok, "Henüz sonuç yok", EKG sonucu yok; tüm ağ istekleri yalnız `127.0.0.1:4173` (vekil üzerinden backend) |
| gizlilik | sabit uyarı | 6 ekranın hepsinde metin birebir |

AF testi süreleri (tarayıcı + Octave dahil, tek test) 14,5–22,8 sn; ekran görüntüsündeki sunucu `wall_seconds` 19,3 sn.
XLIV'de doğrudan API ile ölçülen 6–7 sn'den uzundur; neden bu fazda incelenmedi (aynı makinede tarayıcı + Vite
önizleme + Octave birlikte çalışıyordu). 60 sn zaman aşımının altında.

İlk Playwright koşusunda 3 test hatası test kodundan kaynaklandı ve düzeltildi (diyabet kartının `dm_A`'ya geri düşmesi,
gezinme düğmesi ile "Sonuçları hesapla" ad çakışması, örnek yükleme bitmeden yaş alanını doldurma). İkinci koşuda 250 Hz
testi yarış koşuluyla düştü (anında ABSTAIN'da ilerleme göstergesi doğrulanamadan kayboluyordu); yardımcı sonucu
bekleyecek şekilde düzeltildi, ilerleme göstergesi Octave çalışan AF testinde ayrıca doğrulanıyor. Sonraki iki koşu
20/20.

## Backend — yeni testler (`app/backend/tests/test_phase45_ui_support.py`, 18)

| test | doğrulanan |
|---|---|
| `test_eligibility_never_runs_models` | tüm modellerde `predict_proba` patlatıldı; `/eligibility` çalıştı; yanıtta olasılık/eşik/karar yok; disclaimer var |
| `test_eligibility_lists_all_app_visible_models` | 11 model; boş girdide hepsi MISSING; AF `ecg_record` |
| `test_eligibility_consistent_with_predict` ×8 | 8 girdi varyantında (laboratuvarsız, laboratuvarlı, hedef-tanımlayan, ırk yok, gebelik bilmiyorum, 19 yaş, şema dışı kategori, gebe) panel durumu `/predict` durumuyla uyumlu (OK↔READY, NOT_APPLICABLE↔OUT_OF_SCOPE, ABSTAIN↔MISSING/ABSTAIN; B modelleri dahil) |
| `test_eligibility_field_errors_instead_of_422` | aralık dışı, tutarsız tansiyon, desteklenmeyen birim → `field_errors`; geçerli dönüşüm notu; hatalı değer modele gitmez; `/predict` aynı girdide hâlâ 422 |
| `test_eligibility_states_examples`, `test_eligibility_target_warnings` | örnek durumlar ve uyarılar |
| `test_schema_form_presentation`, `test_parse_condition_rejects_unknown` | `ask_when_rule` / `required_when_rule`, her form alanının bölümü, her kategorinin Türkçe etiketi; tanınmayan koşul → hata |
| `test_frontend_samples_are_byte_copies` | 4 örnek dosya phase_xxviii kopyasıyla SHA256 aynı |
| `test_ecg_display_payload` ×2 (slow) | 10 feature phase_xxviii parity çıktısıyla birebir (ek feature'ı etkilemedi); 2500 örnek, 250 Hz; R tepeleri 0–10 sn; RR = ardışık R farkı; `median(rr_ms)` = `RR_Mean_Global` |

## Çalıştırılmayan / kapsam dışı kalan kontroller

- `.hea + .mat` (Challenge) biçimi arayüzden uçtan uca **denenmedi** (backend XLIV'de 3 kayıtla denenmişti; arayüz
  dosya uzantısını kabul ediyor).
- Yalnız Chromium; Firefox/WebKit ve mobil görünüm denenmedi. Erişilebilirlik için otomatik denetim (axe vb.) yapılmadı.
- Gerçek sürükle-bırak olayı Playwright'ta simüle edilmedi; aynı işleyici yolu dosya seçiciyle sınandı (`addFiles`).


---

## Güncelleme (2026-11-19)

- Vitest **33/33**: yeni `src/components/disclaimer.test.tsx` (4 test; uyarı metni tek kaynak backend). Fixture'lar
  yeniden üretildi.
- Backend **311 geçti, 5 strict-xfail**: yeni `test_disclaimer_single_source`; `test_scenarios.py` beklenen uyarı metni
  güncellendi.
- Playwright **20/20** (iki koşu, ardından metin değişikliğinden sonra bir koşu daha). Gizlilik testi uyarı metnini
  canlı backend'den doğruluyor.
- `@timing` teşhis spec'i (`e2e/timing.spec.ts`) normal koşuya dahil değil; sonuçlar `03_af_timing.md`. Normal komut:
  `npx playwright test --grep-invert "@screenshots|@timing"`.