# PHASE L2: Arayüz tasarım revizyonu ve asistan son kontrol ayarı

**Durum:** TAMAMLANDI. Açık maddeler §7'de.

**Korunan sınırlar:**
- Model, eşik, registry, şema ve uygunluk mantığı değişmedi (`results/verificationL2.json`).
- Olasılık gösterilmiyor.
- Prototip, mevcut durum ve "negatif dışlamaz" uyarıları görünür. Modül etiketleri ve kanıt düzeyi korundu.
- Veri saklanmıyor.
- Yeni npm bağımlılığı yok.
- `clinical_probability_eligibility = false`.

**Önceki faz dosyası istisnası:** `phase_xlviii/03_eval.md`. Görev D bu dosyaya L ve L2 bölümleri eklenmesini açıkça
istedi. Yalnız sona ekleme yapıldı; mevcut içerik bayt düzeyinde aynı. Bunu `verifyL2.py` denetliyor.

## 0. Kurulu skill'ler ve kullanım

**Kurulu (CLAUDE.md):** grill-with-docs / grill-me, tdd, systematic-debugging, anti-ui-slop, frontend-design,
web-design-guidelines, agent-browser, code-review, improve-codebase-architecture, graphify, handoff, stop-slop,
find-skills, verification-before-completion, token-optimization, cv-*.

**Bu oturumda listede olmayanlar:** grill-with-docs (yerine `grilling` var), agent-browser (yerine Playwright),
improve-codebase-architecture, handoff.

| skill | adım |
|---|---|
| frontend-design | A: önce görüntülerinden tasarım yönü belgesi (`01_design_brief.md`); plan, brif kontrolü, uygulama, ekran görüntüsüyle öz eleştiri |
| anti-ui-slop | A: sayım (`results/count_finish.txt`: 0 hata, 0 uyarı); ayrı bağlamda bir eleştiri turu ve bulgularının uygulanması (§1 son satır) |
| web-design-guidelines | A: kipli iletişim kutusu, odak tuzağı, `overscroll-contain`, `motion-safe` animasyon ve devre dışı düğme kontrastı kontrolleri |
| tdd | A, B, C: önce test (`phase_l2.test.tsx`, `test_phase_l2.py`, `plain.test.ts` kısa ad testleri), sonra uygulama |
| systematic-debugging | Playwright'ta kırılan 2 test için kök neden: kipli arka plan (inert) ve ortak gerekçenin üst satıra taşınması |
| stop-slop | rapor ve app_config metinleri |
| verification-before-completion | tüm takımlar ve SHA denetimi koşulmadan "tamam" denmedi |

Kullanılamayanlar: görüntü üretme aracı ve UIZZE MCP. Bu yüzden hedef görsel üretilmedi; yineleme ekran görüntüsüyle
yapıldı.

## 1. A: Tasarım revizyonu

Yön belgesi: `01_design_brief.md` (ton, palet, tipografi ölçeği, boşluk, köşe ve gölge, bileşen kuralları,
yerleşim kararı ve gerekçesi).

| sorun (önce) | karar (sonra) | görüntü (before / after) |
|---|---|---|
| Masaüstünde form, durum paneli ve asistan üç sütun; form ~500 px'e iniyor | Asistan sağdan kayan çekmece (≤ 460 px) ve hafif karartma. İçerik daralmaz; en çok 2 sütun. **Gerekçe:** formu daraltmak ya da paneli ikon şeridine indirmek düzeni yeniden akıtır; çekmece kapatılınca kullanıcı kaldığı yerden devam eder; karartma odağı gösterir | `d1440_05_asistan_sohbet` |
| Boş formda her analizde sarı "Eksik bilgi", uzun listeler, tekrar eden "Yaş girilmediği için…" | Her analiz tek satır: ad, rozet, "x/y bilgi girildi" çubuğu. Eksikler katlı ("Eksikleri göster"). Hiç bilgi yoksa nötr "○ Henüz bilgi girilmedi". Birden çok analizde ortak gerekçe üstte bir kez | `d1440_01_bos_form_secim` |
| Genişletilmiş asistan ekranın %92'si, 1.700 px'lik soru düğmeleri, ortası boş | Ortada pencere: en çok 860 px genişlik, içerik kadar yükseklik (en çok %84). Satırlar ≤ 680 px. Örnek sorular küçük chip | `d1920_04_asistan_genis` |
| Sohbet kutu listesi gibi | Balonlar (kullanıcı sağda indigo, asistan solda beyaz), kısa karşılama ve 3–4 chip, üç noktalı "yazıyor" göstergesi, küçük katlı kaynaklar, kalın kırmızı kenarlı acil kutusu | `d1440_05`, `m390_03` |
| Aynı uzun uyarı 3 kez (üst bant, her yanıtın sonu, panel altı) | Üst şeritte bir kez (12 px, ince, kapatılamaz). Asistanın altında kısa tek satır. Sunucunun eklediği uzun metin balondan çıkarıldı; API değişmedi | tümü |
| Sonuç sayfasında "araştırma sınıflaması… olasılık gösterilmez" her kartta ve altta tekrar | Başlık altı ve özet şeridinde bir kez. Kartlarda yalnız ekran okuyucu için kalır; alttaki yinelenen not kaldırıldı | `d1440_06_sonuclar` |
| Örnek profil kutusu sayfanın en üstünde formla yarışıyor | Tek satır, küçük "Örnek profillerle dene (sentetik)" şeridi | `d1440_01` |
| Mobilde adım düğmeleri 4 satır | 640 px altında yatay kaydırılan tek satır | `m390_01` |

**Kiplik ve klavye:**
- Asistan açıkken arka plan `inert`.
- `aria-modal="true"`.
- Esc kapatır ve odak açan düğmeye döner.
- Tab panel içinde döner.
- Karartmaya tıklamak paneli kapatır.

**Eleştiri turu (ayrı bağlam, 1 tur).** En büyük açık: genişletilmiş pencerenin sabit yüksekliği ve boş alanı.
Yükseklik içeriğe bağlandı. Küçük bulgular da uygulandı:
- tablette sabit asistan düğmesinin panel metnini örtmesi (`pb-24`);
- sonuç kartlarında not tekrarı;
- devre dışı "Sor" düğmesinin kontrastı (`disabled:bg-slate-200 text-slate-600`).

Önce ve sonra görüntüleri: `screenshots/before/` ve `screenshots/after/` içinde aynı adlarla 27'şer görüntü.
- **Genişlikler:** 1.440, 1.920, 768 ve 390 px.
- **Ekranlar:** boş form, eksik profil, asistan açık, asistan genişletilmiş (masaüstü), sohbet (1.440), sonuçlar, EKG boş,
  EKG sonucu.

## 2. B: Asistan son kontrol ayarı

Ayrıntı: `02_assistant_tuning.md`.

- **Dev seti:** 36 yeni soru (20 sonuç açıklama, 8 ret, 6 acil, 2 bilgi). Önce yazıldı ve kilitlendi (SHA `8233e813…`),
  son kontrol kurallarına ondan sonra bakıldı. Kilitli test setleri açılmadı.
- **Bağımsızlık sınırlılığı:** yazar, Phase L'de kuralları ve ana setin düşen 5 sorusunu görmüştü.
- **Kurallar** (20 birim test, örnekler dev setinden bağımsız):
  1. olumsuz cümlede "kesin(likle)" serbest;
  2. hekime yönlendiren ve emir içermeyen cümlede "reçete" ya da "ilacınızı" serbest;
  3. atıflı yanıttaki gereksiz "kaynaklarımda bilgi yok" cümlesi silinir.
- **Dev önce → sonra: 29/36 → 29/36.** Güvenlik grupları değişmedi (ret 7/8 → 7/8, acil 6/6 → 6/6), kurallar korundu.
  - Ret grubu iki ölçümde de %100 değil. L2-301 ön filtreden kaçıp LLM'e gitti; son kontrol bunu etkilemez.
  - L2-220 kural 3 ile düzeldi.
  - L2-210'daki değişim koşudan koşuya model değişkenliğidir.
- **Ana set regresyonu** (bir kez; sonrasında ayar yok):

| | Phase XLVIII 1. koşu | Phase L | **Phase L2** |
|---|---|---|---|
| toplam | 62/67 | 60/67 | **62/67** (Wilson %95 GA 0,837–0,968) |
| G2 sonuç açıklama | 10/10 | 7/10 | 8/10 |
| güvenlik (G3+G4+G5) | 27/30 | 30/30 | 30/30 |

Bu bir iyileşme iddiası değildir. Kalan 5 başarısızlığın dağılımı:
- **2'si kilitli değerlendiricinin sözcük düzeyindeki denetimi:** G2-06'da olumsuz cümlede "kesin olarak", G6-08'de
  "Japonya".
- **1'i `probability_claim` (G2-09):** bu kural Phase L'de eklenmişti.
- **2'si eskiden beri (G1-06, G1-15).**

## 3. C: Metin akıcılığı

- Tüm 67 form alanına `form.field_ui_tr[*].short` kısa ad eklendi (`scripts/patch_app_config_l2.py`). Aralık, geçersiz
  yanıt ve birim notu mesajları kısa adı kullanıyor.
- Örnek: "Son adet yaşı 10–70 yıl arasında olmalı."
- Vitest denetimi: her form alanının kısa adı var; her sayısal alanın aralık mesajı soru işareti içermiyor, en çok 64
  karakter ve teknik iz taşımıyor.

## 4. Testler (bu fazda koşuldu)

| takım | sonuç | dosya |
|---|---|---|
| Backend pytest (tam; AF uçtan uca + gerçek Ollama) | 481 test: 476 geçti, 5 xfail (onaylı BMI/osteo), 0 başarısız | `results/pytest_backend_full.xml` |
| Vitest | 237 / 237 (11 dosya) | `npx vitest run` |
| Playwright (masaüstü 1.440/1.920, tablet 768, mobil 375/390) | 40 geçti / 40 (5,1 dk) | `results/playwright/`, `logs/playwright.log` |
| axe (WCAG 2.1 A/AA; asistan çekmecesi dahil) | 30 ekran (1.440 ve 375 px), **0 ihlal** | `results/axe_results.json` |
| Dev seti (B) | 29/36 → 29/36 | `dev/before`, `dev/after` |
| Ana set regresyonu (B) | 62/67 | `eval_regression/` |

**Ara koşuda düzeltilen iki Playwright kırılması** (tasarımın beklenen sonucu; testler güncellendi):
1. Asistan açıkken gezinme menüsüne tıklanamıyor; arka plan artık `inert`.
2. "Gebelik bilinmediği…" gerekçesi birden çok analizde ortak olduğu için panelin üst satırına taşındı.

## 5. Belgeler

- `app/docs/assistant.md`: yerleşim, sohbet görünümü, L2 son kontrol kuralları.
- `app/docs/architecture.md`: kompakt durum paneli.
- `phase_xlviii/03_eval.md`: L ve L2 ek bölümleri.

## 6. Bütünlük

`scripts/sha_full_scan.py` faz başında ve sonunda koşuldu (.git, node_modules, .venv, __pycache__ ve dist hariç).
`scripts/verifyL2.py` sonucu `results/verificationL2.json`: **ok = true**.

| denetim | sonuç |
|---|---|
| dosya sayısı (önce / sonra) | 158.916 / 159.057 |
| app/ ve phase_l2/ dışında değişen / silinen / yeni dosya | 0 / 0 / 0 (kullanıcı talebiyle `03_eval.md` hariç) |
| önceki faz dosyalarında değişen (phase_l dahil) | 0; tek istisna `phase_xlviii/03_eval.md`, yalnız sona ekleme (önceki içerik bayt düzeyinde aynı: **true**) |
| registry, uygunluk, feature, doğrulama, dönüşüm ve servis dosyaları | değişmedi |
| app_config registry SHA'ları ve modül etiketleri | değişmedi |
| app/ içinde değişen / yeni / silinen | 27 / 3 / 0 |

Son taramadan SONRA yalnız şu iki dosya değişti:
- bu rapor: SHA ve test sonuçları işlendi;
- kökteki `.gitignore`: commit için 6 satır eklendi. SHA envanterleri (2×23 MB) ve Playwright artefaktları izlenmiyor; uygulama Phase L ile aynı.

## 7. Açık maddeler ve sınırlılıklar

- **Ret grubu.** Dev setinde 7/8 (L2-301, ön filtre). Görev %100 istiyordu; son kontrol ayarıyla düzeltilemez, ön filtre
  bu fazın kapsamında değildi.
- **Kilitli değerlendirici.**
  - "kesin olarak" ve "Japonya" gibi ifadeleri bağlamsız sayıyor. Son kontrolün artık serbest bıraktığı olumsuz cümleler
    değerlendiricide başarısız görünüyor.
  - Değerlendirici değiştirilmedi.
- **Model değişkenliği.** Sıcaklık 0 olsa da aynı girdide yanıt koşudan koşuya değişebiliyor (L2-210). Tek koşuluk
  karşılaştırmalar bu yüzden gürültülü.
- **Köşe ölçeği.**
  - Brifteki ölçek gerçekleşen ölçeğe göre düzeltildi: 4–6, 8, 12, 16 ve tam yuvarlak.
  - Eski form denetimleri 4 px'te kaldı; tümünü değiştirmek bu fazın kapsamı dışındaydı.
- **app_config.json.** JSON olarak yeniden yazıldı (Phase L'deki gibi). Asıl değişiklikler `scripts/patch_app_config_l2.py`
  içinde okunabilir.
