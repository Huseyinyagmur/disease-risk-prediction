# Phase XLVIII — Yerel LLM açıklama asistanı (Ollama + RAG) ve küçük arayüz düzeltmeleri

Tarih: 2026-11-21. Kod: `app/backend/healthrisk_api/assistant/`, `app/backend/assistant/` (bilgi tabanı, kilit),
`app/frontend/src/components/AssistantPanel.tsx`. **Model, eşik, registry, şema ve uygunluk mantığı değişmedi**
(`results/verification48.json`). Asistan klinik karar aracı değildir; tanı koymaz, tedavi/ilaç/doz önermez, olasılık
vermez.

## 1. Özet

| görev | durum |
|---|---|
| 0 Arayüz düzeltmeleri | AF EKG'siz → "EKG kaydı gerekiyor" + "Ne gerekiyor?" (yaş kapsam dışında eski ifade kalır); osteo "yapısal boşluk … age_last_period" yalnız Teknik ayrıntıda; karar kutusu satırı "Araştırma sınıflamasıdır; klinik karar değildir. Olasılık gösterilmez." Metinler `app_config.json > ui.text_tr` |
| 1 Ortam ve model seçimi | 3 aday × 15 Türkçe soru → **gemma3:4b** (digest `68ceab7e…`), gömme **bge-m3** (`79076464…`); kilit `assistant_lock.json` → `01_model_selection.md` |
| 2 Bilgi tabanı | 47 belge (iç 18: 13 model kartı, sözlük, "Ne yapmalıyım?", kanıt, analizler, Hakkında; dış 29: MedlinePlus 17, CDC 6, NIDDK 6), 469 parça; NHLBI ve WHO yalnız bağlantı → `02_knowledge_base.md` |
| 3 `POST /assistant/ask` | ön filtre → sayı maskeleme → RAG (+ etiket sabitleri) → yerel LLM → son kontrol → yanıt + kaynaklar + uyarı; loglama/disk yok; yalnız loopback; Ollama yoksa 503 ve `/health > assistant.reason` |
| 4 Arayüz paneli | her sayfada "Açıklama asistanı"; örnek sorular, kaynak bağlantıları, yerel model notu, bekleme göstergesi; sohbet yalnız bellekte |
| 5 Değerlendirme | 67 soru / 6 grup, kilitli; **62/67 (0,925; GA 0,837–0,968)**; acil v2 ayrı doğrulama → `03_eval.md` |

## 2. Ana sonuçlar (03_eval.md)

Test seti, 1. çalıştırma. Wilson %95 GA. Bunlar ana sonuçlardır ve düzeltmeden sonra değiştirilmedi.

| grup | n | geçen | oran | GA |
|---|---|---|---|---|
| G1 kapsam içi bilgi | 16 | 14 | 0,875 | 0,640–0,965 |
| G2 sonuç açıklama | 10 | 10 | 1,000 | 0,722–1,000 |
| G3 tanı/tedavi/doz → ret | 10 | 9 | 0,900 | 0,596–0,982 |
| G4 acil → 112 | 10 | 8 | 0,800 | 0,490–0,943 |
| G5 kapsam dışı → ret | 10 | 10 | 1,000 | 0,722–1,000 |
| G6 enjeksiyon / uydurma | 11 | 11 | 1,000 | 0,741–1,000 |

Düzeltme sonrası ayrı doğrulama (acil filtresi v2, yeni kilitli set, bir kez çalıştırıldı):

| | n | sonuç |
|---|---|---|
| acil yakalama | 24 | 23 (0,958; GA 0,798–0,993) |
| yanlış alarm (acil olmayan benzer kelimeli bilgi sorusu) | 12 | 4 (0,333; GA 0,138–0,609) |
| ret (bilgi amaçlı, filtre değişmedi) | 10 | 8 (0,800) |

Diğer ölçümler:
- Tekrarlanabilirlik: karar 66/67 aynı; metin 50/67 aynı (LLM yanıtlarında 19/36).
- Süre (LLM'e giden): ortalama 4,41 sn, medyan 4,25 sn, en uzun 7,59 sn.
- Elle inceleme (18 yanıt, tek değerlendirici, kör değil): doğruluk ortalaması 1,61/2, sadakat 1,83/2, Türkçe 4,44/5;
  1 kritik güvenlik sorunu (G4-04, inme belirtisi; v2 ile filtrelenir) ve 1 sorun (G6-04).

## 3. Testler (bu makine)

| paket | sonuç |
|---|---|
| Backend pytest, tam (AF uçtan uca + gerçek Ollama dahil) | **402 geçti, 5 xfail** (belgelenmiş BMI/osteo sınırlılığı), 0 başarısız (`results/pytest_backend_full.xml`). Asistan: 75 test (`test_phase48_assistant.py`; 74 sahte Ollama + 1 gerçek Ollama) |
| Vitest | **62/62** (8 yeni: panel + Görev 0) (`results/vitest_junit.xml`) |
| Tip denetimi + üretim derlemesi | geçti |
| Playwright (zamanlama hariç) | **33/33**, SKIP 0. Asistan uçtan uca 3 test (gerçek Ollama), axe a11y 1440/375 px, gizlilik, senaryolar, ekran görüntüleri (`results/playwright/`) |
| Sunucu logu | sohbet içeriği yok (soru metinleri aratıldı, 0 eşleşme) |

Ekran görüntüleri: `screenshots/` (asistan `desktop_assistant_01–04`, `mobile375_assistant_kapsam_disi`; Görev 0
`desktop_gorev0_af_ekg_gerekiyor`, `desktop_gorev0_karar_kutusu`; güncel sihirbaz akışı masaüstü, tablet ve mobil).

## 4. SHA256 bütünlüğü

Faz başı `results/sha256_before.json` (158 603 dosya); faz sonu `sha256_after.json` (158 745).
- Önceki dosyalarda değişen: yalnız `app/` (uygulama istisnası) ve kök `.gitignore` (kullanıcı onayıyla
  `phase_xlviii/logs/` ve Playwright artefakt satırları eklendi). Silinen 0. Faz dışı yeni dosya 0 (`app/` hariç).
- Kök `.gitattributes`: commit sırasında yalnız **ekleme** yapıldı (`app/backend/assistant/kb/** -text`, `*.f32 binary`,
  kilit/politika JSON'ları ve `phase_xlviii/eval/*.json|*.sha256` için `-text`). Gerekçe: `core.autocrlf=true` iken temiz
  Windows klonu bu dosyaları CRLF ile açar; indeks manifest SHA256 kilidi tutmaz ve asistan devre dışı kalırdı. Commit
  edilen blob'lar diskle bayt düzeyinde aynı (73 dosya denetlendi). Bu değişiklik ayrıca onaylanmadı; kullanıcıya bildirildi.
- Model mantığı dosyaları (service, transforms, eligibility, features, model_loader, validation, ecg_*, paths) son
  commit'e göre değişmedi.
- `app_config.json`'da yalnız `ui.text_tr`'ye anahtar eklendi; mevcut metin değişmedi. Registry/şema SHA'ları kilitle aynı.
- `main.py` yalnız ekleme içerir (asistan uç noktası, `/health > assistant`, KNOWN_PATHS).

## 5. Disk ve indirmeler

Kullanıcı onayıyla indirildi: qwen2.5:7b (4,68 GB; elendi, silinmedi), gemma3:4b (3,35 GB), bge-m3 (1,16 GB). Disk
dolunca kullanıcı onayıyla silindi: pip önbelleği (20,4 GB) ve Ollama'nın kendi güncelleme yükleyicisi `updates_v2`
(1,86 GB). `%TEMP%\hr_af_*` yoktu. Ollama modellerine ve proje klasörüne dokunulmadı.

## 6. Açık kalanlar ve sınırlılıklar

- Elle puanlar tek değerlendiricinindir (Claude) ve kör değildir. Kör doğrulama dosyası
  `eval/manual_review_blind.csv` kullanıcıda.
- gemma3:4b seyrek ama anlamı değiştiren çeviri ve bağlam hataları yapıyor; son kontrol anlam hatalarını yakalamaz.
- Model kartlarının eşik (§10) ve kalibrasyon (§11) bölümleri, gemma'nın bir yanıtta eşik değerini aktarması üzerine
  test öncesi bilgi tabanından çıkarıldı.
- Ön filtrelerde açıklar ve takaslar:
  - ret filtresinde çekim açığı (G3-05);
  - acil v2'de "soluğum" açığı (E-06);
  - yanlış alarm 1/3 (bilgi sorularında "göğüs ağrısı", "bayıldım" gibi ifadeler);
  - enjeksiyon kalıbı araya kelime girince kaçıyor (G6-01; sonuç güvenliydi).
  
  Bunlar için v3 ve yeni kilitli bir doğrulama seti önerilir.
- LLM metinleri sıcaklık 0'da bile çalıştırmalar arasında tam belirlenimci değil.
- Dış kaynaklar İngilizce ve erişim tarihindeki sürüm. NHLBI'de yeniden kullanım beyanı bulunamadığı için metin alınmadı.
- gemma lisansı (Gemma Terms of Use) OSI açık kaynak değildir.
- AF ve temiz klon: Phase XLVI notları geçerli. Asistan, temiz klonda Ollama ve modeller kurulursa çalışır
  (`app/docs/INSTALL.md §4b`); bu fazda temiz klonda ayrıca denenmedi.
