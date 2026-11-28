# Phase L — Tasarım sözleşmesi ve sorun listesi

Kaynak skill'ler: `frontend-design` (plan → brif kontrolü → yapım → öz eleştiri), `anti-ui-slop` (sözleşme, durum kapsamı,
sayım kontrolü, ayrı bağlamda eleştiri). Mevcut görsel sistem (Tailwind, slate + indigo, sistem yazı tipi) korunur; bu bir
yeniden markalama değil, anlaşılırlık iyileştirmesidir (anti-ui-slop: "preserve an established visual system for polish").

## 1. Önce görüntülerinden sorun listesi (`screenshots/before/`)

| # | ekran | sorun | tür |
|---|---|---|---|
| S1 | analiz seçimi | Varsayılan seçim yok; "Tümü" deneysel 6 analizi de seçip 7 adımlı form üretiyor | kalabalık |
| S2 | analiz seçimi | Gereksinim bilgisi uzun cümle ("Ölçümler ve öykü yeterli; tahlil girilirse…"); bir bakışta "ne gerekir" okunmuyor | belirsiz ad |
| S3 | sihirbaz | Adım düğmeleri 12 px, iki satıra taşıyor; "Adım 1 / 7" adım adını söylemiyor | hiyerarşi |
| S4 | sihirbaz | Temel bilgiler ve Öykü adımlarında "neden soruluyor" açıklaması yok | anlaşılırlık |
| S5 | sonuçlar | Özet yok; kaç analizden kaçının eşik üstü olduğu kartlar taranarak bulunuyor | hiyerarşi |
| S6 | sonuç kartı | Sonuç kutusu "Ne yapmalıyım?" kutusuyla aynı ağırlıkta; eşik altı ve "uygun değil" aynı gri; "sonuç üretilmedi" alarm kırmızısı | renk tutarlılığı |
| S7 | sonuç kartı | Kanıt rozetleri: üst doğrulama varken üstü çizili "İç test" yanlış okunuyor; açıklama yalnız `title`/ekran okuyucuda | yanlış anlama |
| S8 | sağ panel | Teknik ham satırlar ("age=30 yıl model girdi aralığı dışında [50, 80]") ana listede | teknik dil |
| S9 | asistan | 26 rem kayan kutu içeriğin üstüne biniyor; örnek sorular 12 px hap düğme; kaynaklar her zaman açık | okunabilirlik |
| S10 | genel | Ana içerikte çok sayıda 11 px metin | okunabilirlik |
| S11 | EKG | Örnek kayıt düğmeleri 12 px, "PTB-XL 00691 — kayıt etiketi: AF" gibi teknik ad | belirsiz ad |

## 2. Sözleşme

- **Hedef kitle:** tıp bilgisi olmayan kişi; demo izleyen jüri.
- **Birincil görev:** analiz seç → yalnız gereken bilgileri gir → her analizin sonucunu ve "ne yapmalıyım"ı oku.
- **Kategorinin varsayılanı:** yoğun klinik form + eşit ağırlıklı kart ızgarası. **Öngörülebilir karşıtı:** büyük skor/gösterge
  kadranlı "sağlık uygulaması". Karşıtı burada yasak: olasılık/skor gösterilmez.
- **Bu ürünün kendi fikri — "önce durum":** her sonuç dört durumdan biridir (eşik üstü / eşik altı / sonuç üretilmedi /
  uygun değil). Her durumun **tek** rengi ve **tek** simgesi vardır ve her ekranda aynıdır (seçim paneli, özet şeridi, kart,
  asistan önerileri). Ne gerektiği (tahlil / EKG / solunum testi / hekim değerlendirmesi) seçimden ÖNCE görünür.

### Durum → görünüm (tek kaynak: `frontend/src/lib/status.ts`)

| durum | renk ailesi | simge | not |
|---|---|---|---|
| Eşik üstü | turuncu (orange-700 kenar, orange-50 zemin) | ▲ | tek "dikkat" rengi |
| Eşik altı | mavi (sky-700 / sky-50) | ▼ | yeşil KULLANILMAZ: "sağlıklı" izlenimi verir, negatif sonuç dışlamaz |
| Sonuç üretilmedi | gri, kesikli kenar (slate-500) | ? | alarm kırmızısı kaldırıldı |
| Uygun değil | taş grisi, düz kenar (stone-500 / stone-100) | – | |
| Panel: Hesaplanabilir | yeşil (emerald) | ✓ | yalnız "hazır" anlamında |
| Panel: Eksik bilgi | amber | ! | |

Renk tek taşıyıcı değildir: her durumda metin etiketi + simge vardır.

- **Vurgu rengi:** 1 (indigo: birincil düğme, seçili öğe, odak halkası).
- **Köşe ölçeği:** `rounded` (4 px), `rounded-lg` (8 px), `rounded-full` (yalnız hap/rozet).
- **Yazı:** sistem yazı tipi korunur. Ana içerikte en küçük boyut 12 px (`text-xs`); 11 px yalnız teknik ayrıntı ve altbilgide.
- **Yasak süsler:** gradyan, gölge yığını, emoji, büyük harf etiket, her karta hover animasyonu.
- **Durum kapsamı:** şema yükleniyor / hata; panel boş / güncelleniyor / hata / güncel; asistan denetleniyor / devre dışı /
  bekliyor / hata / acil uyarı; EKG boşta / yükleniyor / işleniyor / hata / sonuç.

## 3. Bu oturumda kullanılamayanlar

- Görüntü üretme aracı yok → hedef görsel üretilmedi; mevcut sistem üzerinde ekran görüntüsüyle yinelendi.
- UIZZE MCP bağlı değil → dış referans ekran getirilmedi.
