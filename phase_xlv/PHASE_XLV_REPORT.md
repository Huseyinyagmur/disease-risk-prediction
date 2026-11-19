# PHASE XLV — React arayüzü (app/frontend)

Durum: **TAMAMLANDI (uygulama fazı; kullanıcı onayı bekleyen noktalar aşağıda).** Model eğitilmedi veya yeniden fit
edilmedi; eşik, kalibrasyon, feature sırası, birimler, registry, şema dosyaları ve önceki faz dosyaları değiştirilmedi.
Test/mühürlü veri okunmadı. Model olasılığı arayüzde gösterilmez. Sunucular yalnız `127.0.0.1`.

## Çıktılar

| konum | içerik |
|---|---|
| `app/frontend/` | Vite + React + TS + Tailwind + Recharts arayüzü (`src/`), testler (`src/**/*.test.ts(x)`, `e2e/`), `README.md` (kurulum, çalıştırma, örnek EKG lisans/atıf), `package-lock.json` |
| `app/frontend/public/samples/` | PTB-XL `00691_hr` (AF) ve `00165_hr` (SR) — phase_xxviii parity kümesinden bayt kopya |
| `app/backend/` (ek) | `POST /eligibility`, `/schema` sunum alanları, `/ecg/af` `display`; `tests/test_phase45_ui_support.py`; `test_privacy.py` güncellemesi; README |
| `01_ui_overview.md` | ekranlar, ilkelerin uygulanışı, backend ekleri, demo verisi, talimattan ayrılan noktalar |
| `02_tests.md` | Vitest, Playwright (dört senaryo grubu + gizlilik), backend pytest |
| `screenshots/` | 10 ekran görüntüsü (giriş, form + panel durumları, birim hatası, sonuçlar, EKG AF/SR, model kartları, hakkında) |
| `scripts/` | `sha_full_scan.py` (XLIV kopyası + `node_modules` hariç), `summarize_tests.py`, `verify45.py` |
| `results/`, `logs/`, `config/` | test raporları, `test_summary.json`, `sha256_after.json`, `verification45.json`; faz başı envanteri `config/sha256_before.json` |

## Ne yapıldı

- **Şema:** `/schema` v2 şemayı sunuyor (`schema_version 2.0`); form tamamen buradan üretiliyor.
- **Ekranlar (7):** Giriş; bölümlü veri girişi (birim seçici, sunucu doğrulama hatası alan altında, koşullu sorular,
  isteğe bağlı ve açıklamalı ırk sorusu, 4 sentetik örnek profil); canlı yönlendirme paneli (11 model; Çalışabilir /
  Eksik / Kapsam dışı / Karar verilemez + modül etiketi); sonuçlar (karar, ABSTAIN nedeni, kanıt rozetleri, P/R/FPR/AUC
  ve %95 GA, hedef tanımı, sınırlılıklar, hedef-tanımlayan girdi uyarısı; ana modüller üstte, deneyseller ayrı/gri); EKG
  ile AF (sürükle-bırak, ilerleme, sonuç kartı, 10 öznitelik, lead II + R tepeleri ve RR takogramı, ilk 10 sn bilgisi);
  model kartları; hakkında.
- **Backend ekleri** (model çalıştırmayan `/eligibility`; tahmin öncesi mantık `Service.precheck` olarak `/predict` ile
  ortak; şema koşullarının sunucuda yapılandırılmış hâle getirilmesi; EKG görüntüleme verisi kilitli `load_fpt`
  çıktısından).

## Ne doğrulandı

| kontrol | sonuç |
|---|---|
| Vitest | 29/29 |
| Playwright | 20/20 (iki ardışık koşu): @normal 4/4, @eksik 5/5, @birim 4/4, @kapsam 5/5 (her grupta fibrozis ve AF), @gizlilik 2/2 |
| Gizlilik (tarayıcı) | depolama boş, `setItem`/`indexedDB.open` çağrısı yok, çerez/Cache Storage yok, yenilemede veri silinir, istekler yalnız localhost |
| Backend pytest | 310 geçti, 5 strict-xfail (onaylı XLIV BMI sınırlılığı), 0 hata |
| `/eligibility` model çalıştırmıyor; panel ↔ `/predict` tutarlılığı | 8 girdi varyantında uyumlu |
| EKG ekinin feature/karara etkisi | 2 örnekte 10 feature phase_xxviii ile birebir; `median(RR)` = `RR_Mean_Global` |
| Örnek EKG kopyaları | SHA256 = phase_xxviii = PhysioNet SHA256SUMS |
| Statik tarama | `src/` içinde storage/analytics/harici URL yok (yalnız açıklama satırı) |

## Bütünlük (`results/verification45.json`)

- Faz başı envanteri (158.326 dosya) kod yazılmadan önce alındı ve bitmesi beklendi. XLIV sonu envanterine göre fark:
  yalnız XLIV'ün kendi son log/doğrulama dosyaları (`sha_after.log`, `verify44.log`, `verification44.json`) ve
  `sha256_after.json` — başka fark yok.
- Tarama kapsamı XLIV ile aynı, ek olarak `node_modules` hariç (faz başında yoktu).
- **V1:** `phase_xlv/` ve `app/` dışında **değişen 0, silinen 0, yeni 0**.
- **V2:** 13 model dosyasının SHA256'sı registry = faz başı = faz sonu. **V3:** `models.json`, v1 ve v2 şema, AF kilidi
  ve `af_pipeline_v1.py` değişmedi. **V5:** faz başından sonra yazılmış `.pyc` yok.
- **V4 (app/, CLAUDE.md istisnası):** değişen 6 dosya — `app/backend/README.md`, `config/app_config.json` (`form`
  bloğu), `healthrisk_api/{service,main,ecg_af}.py`, `tests/test_privacy.py`; yeni 57 dosya (frontend kaynakları,
  testler, fixture'lar, örnek EKG, `dist/` derlemesi, yeni backend testi); silinen 0.

## Açık kalanlar — onayınızı gerektirenler

1. **Panelde 4. durum "Karar verilemez"** (gebelik "bilmiyorum", şema dışı kategori, devre dışı model). Talimatta üç
   durum vardı. Uygun mu?
2. **Türkçe kategori etiketleri ve bölüm ataması** backend `app_config.json > form` içinde benim tanımımdır (ör. ırk
   sınıfları, CAD kategorileri). Gözden geçirilmeli.
3. **XLIV test dosyası değişikliği:** `test_privacy.py` izinli yol kümesine `/eligibility` eklendi ve gizlilik
   isteklerine `/eligibility` çağrıları eklendi.
4. **Uyarı metni farkı:** arayüz talimattaki metni ("…sınıflandırması yapar…"), backend yanıtı XLIV metnini
   ("…sınıflandırmasıdır…") taşır. Birleştirilsin mi?

## Sınırlılıklar

- Aralık denetimi yalnız sunucudadır; alan altı hata ≈ 300 ms gecikmeyle görünür ve hatalı alan panelde "Eksik" olarak
  da sayılır.
- AF analizi arayüzden 14–23 sn sürdü (XLIV API ölçümü 6–7 sn); nedeni incelenmedi. `.mat` yükleme arayüzden uçtan uca
  denenmedi. Yalnız Chromium; erişilebilirlik denetimi ve mobil görünüm sınanmadı.
- Örnek EKG kayıtları modelin geliştirme verisindendir; bunlardaki kararlar ve demo profillerindeki sonuçlar (ör.
  fibrozis profilinde "ileri değerlendirme önerilir") performans kanıtı değildir.
- Recharts 2.15.3 (npm "v2 artık aktif değil" uyarısı veriyor) kilitli; JS paketi tek parça ~605 kB (Vite boyut
  uyarısı). Kimlik doğrulama yok; yalnız localhost, tek kullanıcı.
- Kararlar "araştırma sınıflaması"dır; model olasılığı klinik olasılık değildir ve gösterilmez. Klinik onay yoktur.


---

## Güncelleme — kullanıcı kararları (2026-11-19)

**Kararlar:** (1) "Karar verilemez" durumu kalıyor. (3) `test_privacy.py` değişikliği onaylandı. (4) Uyarı metninin tek
kaynağı backend. Metin: "Araştırma prototipidir; mevcut durum sınıflandırması yapar, gelecek risk tahmini değildir;
negatif sonuç hastalığı dışlamaz; tanı ve tedavi için hekime başvurun." (2) Kategori etiketleri ve bölümler gözden
geçirme için `app_config_review.json` olarak bu klasöre kopyalandı (SHA256 `1f048a1a…c5a04d`, kaynakla aynı).

### Uyarı metni — tek kaynak backend

- `app/backend/config/app_config.json > disclaimer_tr` yeni metne güncellendi. Tüm JSON yanıtlarının `disclaimer`
  alanı bu metindir.
- Frontend metni tutmaz. Uyarı bandı ile Giriş ve Hakkında sayfalarındaki kutular metni `/schema` yanıtının
  `disclaimer` alanından alır. Metin gelmeden önce "yükleniyor…", sunucuya ulaşılamazsa "araştırma uyarısı
  yüklenemedi" yazılır; uyarının yerine geçen bir metin uydurulmaz.
- Testler: backend `test_disclaimer_single_source` (config = onaylı metin; 5 uç noktada aynı metin),
  `test_scenarios.py` beklenen metni güncellendi. Vitest `src/components/disclaimer.test.tsx` (4 test): arayüz backend
  ne gönderirse onu her ekranda gösteriyor; sunucu yoksa metin uydurulmuyor; `src/` kaynaklarında metin yok. Fixture'lar
  backend'den yeniden üretildi. Playwright gizlilik testi canlı backend metnini 6 ekranda birebir doğruluyor.
- XLIV belgelerindeki eski metin ("…sınıflandırmasıdır…") salt okunur olduğu için değiştirilmedi.

### AF süre farkı (`03_af_timing.md`)

Fark arayüzden kaynaklanmıyor. Tarayıcıda sunucu dışındaki süre medyan 0,14 sn (yükleme + kuyruk 0,04 sn, indirme
1 ms, 19 KB yanıt, çizim 0,06 sn). Sürenin tamamı kilitli Octave/ECGDeli pipeline'ında geçiyor. Bu süre sunucu ve
tarayıcı olmadan da 18–21 sn ölçüldü; Octave hesaplaması XLIV'e göre 3–4 kat yavaş. Ölçüm sırasında makinede bir oyun
ve üretici arka plan servisleri CPU kullanıyordu; işlemci azami frekansın %77'sindeydi. BLAS = 1 iş parçacığı ve
P-çekirdek benzeşimi denendi; tutarlı bir iyileşme görülmedi (feature'lar her durumda birebir). Uygulama kodu
değiştirilmedi. Yalnız arayüzdeki süre metni ölçüme göre "≈ 7–30 sn, makine yüküne bağlı; üst sınır 60 sn" yapıldı.

### Yeniden doğrulama

| kontrol | sonuç |
|---|---|
| Vitest | 33/33 |
| Playwright (canlı backend, üretim derlemesi) | 20/20 (son metin değişikliğinden sonra), önceki iki koşu da 20/20 |
| Backend pytest | 311 geçti, 5 strict-xfail (onaylı), 0 hata |
| Ekran görüntüleri | yeniden üretildi (`screenshots/`) |