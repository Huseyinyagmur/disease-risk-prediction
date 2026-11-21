# Phase XLVIII — 01 Ortam ve model seçimi (Görev 1)

## 1. Ortam (bu makine, 2026-11-21)

| öğe | değer |
|---|---|
| işlemci | Intel Core i5-14500HX (14 çekirdek / 20 iş parçacığı) |
| RAM | 15,7 GB (ölçüm anında boş ≈ 3,4 GB) |
| GPU | NVIDIA GeForce RTX 4050 Laptop, 6141 MiB VRAM, sürücü 592.82 (+ Intel UHD) |
| disk | C: ≈ 22 GB boş (indirme öncesi) |
| Ollama | 0.40.16, yalnız `127.0.0.1:11434` (istemci kodu loopback dışı adresi reddeder; `trust_env=False` ile sistem vekili yok sayılır) |
| başlangıçta yüklü model | yalnız `llama3:latest` (8.0B Q4_0, `365c0bd3…`) |

İndirilen modeller (kullanıcı onayıyla, boyutları onay sorusunda belirtildi): `qwen2.5:7b` (4,7 GB), `gemma3:4b` (3,4 GB),
`bge-m3` (1,2 GB). Resmi Ollama kayıt deposundan `ollama pull` ile; doğrulama Ollama'nın içerik adresli (SHA256) blob
digest'leriyle.

| model | Ollama digest | parametre / niceleme | lisans |
|---|---|---|---|
| llama3:latest | `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` | 8.0B Q4_0 | Meta Llama 3 Community License |
| qwen2.5:7b | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | 7.6B Q4_K_M | Apache 2.0 |
| **gemma3:4b** | `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7` | 3.9B Q4_K_M | Gemma Terms of Use |
| **bge-m3:latest** (gömme) | `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab` | 566.7M F16, 1024 boyut | MIT |

## 2. Karşılaştırma yöntemi

`phase_xlviii/scripts/compare_models.py`: 15 Türkçe kapsam içi soru (hastalık tanımları, testler, uygulama terimleri;
test setinden ayrı), üç model **aynı RAG hattında** (aynı indeks, aynı sistem istemi, k=5, sıcaklık 0, seed 42,
`num_ctx` 8192). Her modelden önce diğerleri bellekten boşaltıldı; 1 ısınma çağrısı ölçülmedi. Ham yanıtlar:
`results/model_selection/answers.json`; otomatik özet: `summary_auto.json`; elle puanlar: `manual_ratings.csv`.

* **Türkçe akıcılık** — elle 1–5 (5 = doğal, hatasız Türkçe) + otomatik: Latin dışı karakter (CJK vb.) içeren yanıt sayısı.
* **Kaynağa sadakat** — elle 0–2 (2 = kaynakla uyumlu; 1 = küçük hata/ekleme/bağlam karışıklığı; 0 = ciddi hata,
  uydurma, dil karışması veya sistem istemi sızıntısı) + otomatik: son kontrol (kaynakta olmayan sayı, yasak ifade).
* **Süre** — bu makinede soru başına uçtan uca (gömme + LLM).

Elle puanlayan: asistan (Claude); kullanıcı tarafından ayrıca doğrulanmadı. Not: karşılaştırma, son kontrolün ilk
sürümüyle koştu (yüzde işareti her durumda ihlal; laboratuvar birimi `mg/dL` doz sayılıyordu); otomatik "son kontrol"
sayıları bu sürüme aittir. Elle puanlar ham yanıt üzerindendir.

## 3. Sonuçlar (15 soru)

| model | ort. süre (sn) | en uzun (sn) | elle akıcılık (ort. 1–5) | elle sadakat (toplam /30) | sadakat = 0 olan yanıt | Latin dışı karakterli yanıt | atıf ([n]) içeren | son kontrolde düşen |
|---|---|---|---|---|---|---|---|---|
| llama3:latest | 28,3 | 36,3 | 2,47 | 12 | 7 | 0 | 9 | 6 (hepsi kaynakta olmayan sayı; 6'sında sistem istemi sızıntısı) |
| qwen2.5:7b | 25,7 | 38,0 | 2,80 | 18 | 2 | **1 (yanıtın çoğu Çince)** | 9 | 0 |
| **gemma3:4b** | **6,5** | **11,8** | **4,27** | **23** | 1 | 0 | **15** | 3 (2 yüzde, 1 "olasılığınız") |

GPU yerleşimi (`ollama ps`): qwen2.5:7b 5,4 GB — %24 CPU / %76 GPU (6 GB VRAM'e sığmıyor, kısmi CPU); gemma3:4b
gömme modeliyle birlikte tamamen GPU'da. Süre farkının ana nedeni budur.

Gözlenen tipik hatalar: llama3 — sistem isteminin ilk cümlesini yanıta kopyalama, "kidney filtration rateı" gibi İngilizce
karışması; qwen2.5 — Çince'ye geçiş, "kirpikler" (böbrek), "soft clip nösteniz" gibi anlamsız çeviriler; gemma3 — seyrek
çeviri hatası ("idrarla (öksürük)", "anemi nervoza"), bağlam karıştırma (spirometriyi eşik üstü/altı ile ilişkilendirme),
bir yanıtta model kartındaki sayısal eşik değerinin aktarılması.

## 4. Seçim (kilitli)

**Sohbet modeli: `gemma3:4b`** (digest `68ceab7e…38df7`). Gerekçe: en yüksek Türkçe akıcılık ve kaynağa sadakat, her
yanıtta atıf, ~4× daha hızlı (tamamen GPU; bu makinede 6,5 sn ort.), Latin dışı karaktere geçiş yok. Zayıflıkları (seyrek
çeviri/bağlam hatası) son kontrol ve elle inceleme ile raporlanır (03_eval.md); klinik doğruluk garantisi verilmez.

**Gömme modeli: `bge-m3:latest`** (digest `79076464…46bab`) — çok dilli (Türkçe sorgu ↔ İngilizce kaynak), 8K bağlam,
MIT. Tek aday; kullanıcı onay sorusunda önerilen seçenek olarak seçildi.

Kilit: `app/backend/assistant/assistant_lock.json` (model adı, etiket, digest, Ollama sürümü, seçenekler
`temperature=0, seed=42, top_k=1, top_p=1.0, num_ctx=8192, num_predict=512`, indeks manifest SHA256). Sunucu her durum
sorgusunda Ollama `/api/tags` digest'lerini kilitle karşılaştırır; uyuşmazlıkta asistan devre dışı.

Seçim sonrası, test seti açılmadan yapılan geliştirme ayarları (yalnız bu 15 soru ve `eval/dev_questions.json` ile):
1. model kartlarının sayısal eşik (§10) ve kalibrasyon (§11) bölümleri bilgi tabanından çıkarıldı (eşik sızıntısı);
2. atıf ayrıştırıcı `[1, 4]` / `[2-3]` biçimlerini destekler;
3. istemde "yüzde işareti kullanma" ve "kaynakta olmayan ayrıntı (kısaltma açılımı vb.) ekleme" kuralları;
4. son kontrolde yüzde yalnız kaynakta aynı değerle geçiyorsa serbest (ör. "%95 GA"); `mg/dL` gibi laboratuvar birimleri doz
   sayılmaz; "kesin tanı" yasak listesinden çıkarıldı (hep olumsuz bağlamda kullanılıyordu; "kesinlikle"/"kesin olarak" kaldı);
5. oturum etiketi varsa durum tanımı ve hastalık yönlendirmesi parçaları bağlama sabitlenir (`label_pins`).
Bu ayarların ardından geliştirme seti 17/17 geçti; ardından test seti ve politika SHA256 ile kilitlendi
(`eval/questions.sha256`).

## 5. Sınırlılıklar

* 15 soru küçük bir örneklemdir; elle puanlar tek değerlendiricinindir (kör değil: model adı biliniyordu).
* Süreler bu dizüstü makineye özgüdür; RAM baskısında Ollama'nın llama-server süreci bir kez CUDA başlatma hatasıyla çöktü
  (`server.log`: "CUDA error: shared object initialization failed"); betik 10 sn bekleyip yeniden dener ve deneme sayısını
  kaydeder.
* Gemma lisansı OSI onaylı açık kaynak değildir (Gemma Terms of Use; kullanım kısıtlamaları politikası). Araştırma
  prototipinde yerel kullanım için uygun görüldü; dağıtım öncesi lisans ayrıca değerlendirilmelidir.
