# Phase L2: tasarım yönü belgesi

Kaynak skill: `frontend-design`. Sırası: plan, brife göre gözden geçirme, uygulama, ekran görüntüsüyle öz eleştiri.
Kontrol aracı: `anti-ui-slop`. Kullanılan adımları sayım ve ayrı bağlamda eleştiri.

## Konu, kitle, birincil iş

- **Konu.** Yerel çalışan bir sağlık araştırma prototipi. Kişinin mevcut durumunu, araştırmada sabitlenmiş eşiğe göre
  sınıflar.
- **Kitle.** Tıp bilgisi olmayan bir kişi ve demoyu izleyen jüri.
- **Birincil iş.** Kullanıcı gerekli bilgiyi girer, her analizin sonucunu ve "ne yapmalıyım" önerisini okur, aklına
  takılanı asistana sorar.
- **Ton.** Sakin ve güven veren. Klinik, ama soğuk değil.
  - Alarm rengi yalnız gerçek uyarıda kullanılır.
  - Kullanıcı daha hiçbir şey girmeden olumsuz durum gösterilmez.

## Önce görüntülerindeki sorunlar (`screenshots/before/`)

1. **Sütun sayısı.** 1.440 px'te form, durum paneli ve asistan üç sütun oluyor; form 500 px'e iniyor
   (`d1440_05_asistan_sohbet`).
2. **Durum paneli.** Boş formda her analiz sarı "Eksik bilgi" rozetiyle açılıyor. Uzun eksik listeleri görünüyor ve
   "Yaş girilmediği için…" cümlesi her analizde tekrar ediyor (`d1440_01_bos_form_secim`).
3. **Genişletilmiş asistan.** Ekranın %92'sini kaplıyor. Örnek soru düğmeleri 1.700 px genişliğe uzuyor, ortası boş
   kalıyor (`d1920_04_asistan_genis`).
4. **Uyarı tekrarı.** Aynı uzun uyarı üç kez görünüyor: üst bant, her asistan yanıtının sonu, panelin altı.
5. **Zayıf hiyerarşi.** Örnek profil kutusu sayfanın en üstünde ve formla yarışıyor. Kartlarda gölge ile kenarlık
   karışık kullanılmış.

## Yerleşim kararı: asistan için çekmece

```
masaüstü ≥ 1024, asistan kapalı           masaüstü, asistan açık (çekmece)
┌───────────────────────────────┬───────┐  ┌──────────────────────┬─────────────┐
│ form (fluid, en çok ~760 px)   │ durum │  │ (karartılmış içerik) │  asistan    │
│                               │ 320px │  │                      │  ~460 px    │
└───────────────────────────────┴───────┘  └──────────────────────┴─────────────┘
genişletilmiş: ortada, en çok 860 px, %88 yükseklik, iki yanda karartılmış boşluk
tablet / mobil: tam ekran
```

- **Seçilen.** Çekmece içeriğin üstüne kayar; arka plan hafif kararır (slate-900 %30).
- **Neden çekmece, ikon şeridi değil.**
  - Asistan açıkken kullanıcı sohbete odaklanır. Formu daraltmak (Phase L'deki yan panel) ya da durum panelini ikon
    şeridine indirmek düzenin yeniden akmasına yol açar.
  - Çekmecede form ve panel yerinde kalır. Kapatınca kullanıcı kaldığı yerden devam eder.
  - Ekranda hiçbir zaman ikiden fazla sütun okunmaz.
  - Karartma, odağın nerede olduğunu gösterir. Çekmece kipliktir: `aria-modal="true"`, arka plan `inert`, Esc kapatır,
    odak açan düğmeye döner.

## Renk (Tailwind ölçeği; durum renkleri tek kaynak `lib/status.ts`)

| ad | değer | rol |
|---|---|---|
| zemin | `#F4F6F8` (slate-100'e yakın, özel) | sayfa arka planı |
| yüzey | `#FFFFFF` | kart, panel, çekmece |
| mürekkep | slate-900 `#0F172A` | başlık ve gövde |
| ikincil metin | slate-600 `#475569` | yardımcı metin (beyaz üstünde AA) |
| vurgu | indigo-700 `#4338CA` | birincil düğme, seçili öğe, odak halkası, kullanıcı balonu |
| uyarı bandı | amber-50 + amber-900 | yalnız üst şerit |

**Durum renkleri (değişmedi; Phase L sözleşmesi):**
- eşik üstü turuncu ▲
- eşik altı mavi ▼
- sonuç üretilmedi kesikli gri ?
- uygun değil taş grisi –
- panelde: hazır yeşil ✓, eksik amber !, **henüz başlanmadı nötr gri ○ (yeni)**

## Tipografi

- **Yazı tipi.** Sistem yazı tipi korunur: Windows'ta Segoe UI. Yeni bağımlılık ve ağdan yazı tipi yok; uygulama yalnız
  localhost'ta çalışır.
- **Ölçek (px):** 12 yardımcı, 14 küçük gövde, 16 gövde, 18 kart başlığı, 22 bölüm başlığı, 28 sayfa başlığı.
- **Yasak:** ana içerikte 12 px'ten küçük metin. Büyük harf etiket kullanılmaz.
- **Satır uzunluğu:**
  - sohbet balonu en çok 680 px (~70 karakter);
  - açıklama paragrafları `max-w-prose`.

## Boşluk, köşe, gölge

- **Boşluk.** 4 px ızgara: 4, 8, 12, 16, 24, 32. Kart iç boşluğu 16 px (mobilde 12 px). Bölümler arası 24 px.
- **Köşe.** Gerçekleşen ölçek (`results/count_finish.txt`) katman derinliğine göre artar:
  - 4–6 px: form denetimleri ve küçük düğmeler; eski denetimler 4 px'te kaldı;
  - 8 px: kart ve panel;
  - 12 px: çekmece, ortalanmış asistan ve giriş alanı;
  - 16 px: sohbet balonu;
  - tam yuvarlak: hap, chip ve durum rozeti.
- **Gölge.** Kartlarda gölge yok, yalnız 1 px kenarlık. Gölge yalnız üstte duran katmanlarda: çekmece, genişletilmiş
  asistan, açma düğmesi.

## Bileşen kuralları

1. **Durum paneli.** Her analiz tek satır: ad, durum rozeti ve "x/y bilgi girildi" ilerleme çubuğu.
   - Eksikler katlı gelir ("Eksikleri göster").
   - Analiz için hiç bilgi girilmemişse nötr "Henüz bilgi girilmedi" görünür, sarı "Eksik bilgi" görünmez.
   - Birden çok analizde tekrar eden gerekçe, panelin üstünde bir kez yazılır ("Seçili tüm analizler için: …").
2. **Asistan:**
   - kullanıcı balonu sağda, indigo zemin, beyaz metin;
   - asistan balonu solda, beyaz zemin, kenarlıklı;
   - boş durumda iki cümlelik karşılama ve 3–4 küçük chip;
   - yanıt beklenirken üç noktalı "yazıyor" göstergesi;
   - kaynaklar balonun altında küçük, katlı;
   - acil uyarı kutusu kalın kırmızı kenarlıyla balonun üstünde.
3. **Uyarı.**
   - Uzun metin üst şeritte bir kez görünür: ince, 12 px, kapatılamaz.
   - Asistanda giriş alanının altında kısa tek satır bulunur.
   - Sunucunun her yanıta eklediği uzun uyarı balondan çıkarılır. API değişmez; uyarı yine yanıtta gelir ve kısa satır
     her zaman görünür.
4. **Örnek profil kutusu.** Formdan sonra, katlı bir "Örnek profillerle dene (sentetik)" bölümüne iner. Böylece formla
   yarışmaz.

## Brif karşısında gözden geçirme

- **İlk taslak.** Gradyanlı başlık, her kartta gölge ve büyük istatistik kutuları vardı. Bunlar her sağlık uygulamasında
  görülen varsayılanlar ve ton brifiyle ("sakin") çelişiyor. Çıkarıldı.
- **Cesaretin harcandığı yer.** Tek bir yerde: sonuç kutusu ve durum simgeleri. Geri kalan her şey sessiz.
- **Renk ve yazı tipi.** Yeni bir vurgu rengi denenmedi. İndigo, Phase L'den beri birincil eylem rengi; değiştirmek
  durum renkleriyle (mavi eşik altı) karışma riski taşıyordu.
