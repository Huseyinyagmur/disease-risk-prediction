# Phase XLV — Görev 3: AF süre farkının ölçümü (arayüz 14–23 sn ↔ XLIV API 6–7 sn)

Özet: `results/af_timing_summary.json` (`scripts/summarize_af_timing.py`). Ham ölçümler: `af_timing_api.json`,
`af_timing_browser.json`, `af_timing_octave.json`, `af_timing_octave_pcores.json`. Betikler:
`scripts/t_af_timing_api.py`, `scripts/t_af_timing_octave.py`, `app/frontend/e2e/timing.spec.ts` (`@timing`; normal test
koşusuna dahil değil). Kayıtlar: iki açık PTB-XL örneği (`00691_hr`, `00165_hr`); yaş/cinsiyet sentetik.
Tüm ölçümler 2026-11-19'da aynı makinede (i5-14500HX, 6P + 8E çekirdek, AC, "Dengeli" güç planı) yapıldı.

## Sonuç

**Fark arayüzden gelmiyor.** Tarayıcıda sunucu dışındaki toplam süre (tıklama → istek, yükleme + kuyruk, indirme,
grafik çizimi) medyan **0,14 sn** (en çok 0,36 sn). Sürenin tamamı sunucudaki kilitli pipeline'da (Octave/ECGDeli)
geçiyor. Bu süre ölçüm anındaki makine yüküne göre 15–30 sn arasında değişti; XLIV'deki 6–7 sn başka bir yük
koşulunda ölçülmüştü. Uygulama tarafında güvenilir ve kolay bir düzeltme bulunmadı; kod değiştirilmedi.

## Ayrıştırma

| aşama | ölçüm | medyan [min–max] |
|---|---|---|
| Tarayıcı: tıklama → XHR başlangıcı | Resource Timing, 6 istek | 0,037 sn [0,028–0,049] |
| Tarayıcı: yükleme (120 KB) + sunucu kuyruğu, sunucu süresi hariç | TTFB − `wall_seconds` | 0,041 sn [0,037–0,043] |
| Tarayıcı: yanıt indirme | `responseEnd − responseStart` | 0,001 sn |
| Yanıt boyutu | toplam / `display` bloğu | ≈ 19,4 KB / ≈ 18,6 KB |
| Tarayıcı: yanıttan lead II çiziminin DOM'a gelmesine | MutationObserver | 0,06 sn [0,04–0,26] |
| **Tarayıcı: sunucu dışı toplam** | tıklama → grafik − `wall_seconds` | **0,14 sn [0,11–0,36]** |
| Tarayıcı koşusu: sunucu `wall_seconds` | 6 istek | 29,2 sn [28,6–30,4] |
| Doğrudan API (tarayıcısız): gidiş-dönüş | httpx, 6 istek | 17,7 sn [15,4–25,4] |
| Doğrudan API: istemci ek yükü | gidiş-dönüş − `wall_seconds` | 0,03 sn; JSON ayrıştırma 1 ms |
| Sunucusuz kilitli pipeline: `run_ecgdeli` duvar süresi | 4 çağrı | 19,6 sn [18,1–20,6] |
| Sunucusuz: Octave içi ECGDeli hesaplaması (`toc`) | 4 çağrı | 13,3 sn [12,0–13,9] |
| Sunucusuz: Octave çıplak başlatma / `pkg load` (signal, statistics, image) | | 0,66 sn / 4,6 sn [3,4–5,8] |
| XLIV referansı (`phase_xliv/results/af_e2e.json`) | Octave `toc` / `wall_seconds` | ≈ 4,3–4,5 sn / ≈ 6,9–7,1 sn |

Gözlem: aynı kayıtlar ve aynı kilitli kod, sunucu ve tarayıcı olmadan da 18–21 sn sürdü. Octave'ın yalnız hesaplama
kısmı (`toc`) XLIV'e göre ≈ 3–4 kat yavaş; paket yüklemesi bile 3,4–8,4 sn arasında oynuyor.

## Neden: makine yükü

Ölçüm sırasında (CIM performans verisi): toplam CPU %18–31; çekirdek başına en yüksek tüketenler `WmiPrvSE` (%97),
bir oyun süreci (`VALORANT-Win64-Shipping`, %80), `AppHelperCap` (%76), `LightStudio-background`,
`OmenCommandCenterBackground`. İşlemci azami frekansının %77'sindeydi (2,2 GHz). Octave ve sunucu süreçleri normal
öncelikteydi; pil değil AC gücü.

## Denenen düzeltmeler (yalnız teşhis; uygulamaya alınmadı)

| deney | sonuç | feature'lar |
|---|---|---|
| BLAS/OpenMP iş parçacığı = 1 (`OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`) | hızlandırmadı: `run_ecgdeli` 22,7 sn [20,2–24,1] (varsayılan 19,6) | 10 feature birebir |
| Süreç benzeşimi yalnız P-çekirdekler (mantıksal 0–11; Octave alt sürece miras) | tutarsız: aynı koşuda varsayılan ortamda 29,6 / 28,8 sn, BLAS=1 ile 11,6 / 15,8 sn; varyansı arka plan yükü belirliyor | 10 feature birebir |

Kalıcı bir uygulama düzeltmesi (benzeşim veya iş parçacığı zorlama, güç planı) yapılmadı. Gerekçeler: (1) ölçülen etki
tutarlı değil; (2) bunlar kilitli AF pipeline'ının çalışma ortamını değiştirir; (3) güç planı ve arka plan uygulamaları
kullanıcının sistem ayarlarıdır.

## Öneriler (karar sizin)

- Ölçümler ve demolar sırasında oyun ve üretici arka plan araçlarını kapatın; gerekirse "Yüksek performans" güç planını
  kullanın. Bu koşulda XLIV'deki 6–7 sn'nin yeniden elde edilip edilmediği ayrıca ölçülmelidir (bu fazda ölçülmedi).
- Arayüzdeki işlem süresi metni bu ölçüme göre güncellendi: "bu makinede ölçülen ≈ 7–30 sn, makine yüküne bağlı; üst
  sınır 60 sn". 60 sn sınırı hiçbir ölçümde aşılmadı; aşılırsa sonuç ABSTAIN olur.
