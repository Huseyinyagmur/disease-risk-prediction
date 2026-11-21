# Açıklama asistanı (Phase XLVIII)

Uygulamadaki terimleri, sonuç kartlarını ve kapsamdaki hastalıkları **yerel** bir dil modeliyle, yalnız bilgi tabanındaki
kaynaklara dayanarak açıklar. **Tanı koymaz; tedavi, ilaç veya doz önermez; model olasılığı vermez.** Araştırma
prototipinin parçasıdır; klinik karar aracı değildir.

## 1. Kurulum

1. [Ollama](https://ollama.com) kurun (bu fazda 0.40.16 ile denendi). Ollama yalnız `127.0.0.1:11434`'te dinlemelidir
   (varsayılan). `OLLAMA_HOST`'u `0.0.0.0` yapmayın.
2. Kilitli modelleri indirin (≈ 4,6 GB):
   ```powershell
   ollama pull gemma3:4b
   ollama pull bge-m3
   ```
3. Digest'leri doğrulayın: `ollama list` çıktısındaki kimlikler `gemma3:4b → 68ceab7e468a`, `bge-m3:latest →
   790764642607` ile başlamalıdır (tam değerler `app/backend/assistant/assistant_lock.json`). Farklıysa asistan
   devre dışı kalır (`/health > assistant.reason`).
4. Backend'i her zamanki gibi başlatın (`app/backend/run_server.py`). Ek Python paketi gerekmez (`httpx`, `numpy` mevcut).

Ollama çalışmıyorsa veya modeller eksikse yalnız asistan devre dışıdır; tahmin, uygunluk ve EKG uç noktaları etkilenmez.

## 2. Akış

```
soru ──► ön filtre (kod) ──► sayı maskeleme ──► RAG: bge-m3 gömme, k=5, min_score 0,45 (+ etiket sabitleri)
            │                                             │
            ├─ kendine zarar     → yalnız "112 Acil" (LLM'e gitmez; başka numara yok)
            ├─ acil (kişisel/belirsiz) → "Acil durumda 112'yi arayın." (LLM'e gitmez)
            ├─ acil (genel bilgi sorusu) → 112 uyarı kutusu + normal akış
            ├─ komut enjeksiyonu → sabit ret
            ├─ olasılık sorusu   → sabit açıklama + iç kaynak (Hakkında, sözlük)
            ├─ tanı/tedavi/doz   → sabit ret
            └─ kapsam dışı       → kibar ret
                                                          ▼
                       sistem istemi + numaralı kaynak parçaları + oturum etiketleri + soru (ayraçlı veri)
                                                          ▼
                       gemma3:4b (sıcaklık 0, seed 42, top_k 1) ──► son kontrol (kod) ──► yanıt + kaynaklar + uyarı
```

* **Acil filtresi (v3)**: kurallar doğal Türkçe yazılır ve girdiyle aynı `guard.key()` normalizasyonundan geçer (küçük
  harf, Türkçe → ASCII, g/ğ→k, d→t, b→p; "soluk/soluğum" aynı kök). Kural dili: boşluk = bitişik kelime, "…" = araya en
  çok 4 sözcük, parçalar kelime başı kökü (`assistant_config.json > emergency_rules`, `self_harm_rules`, `medical_rules`).
  İki kademe: **kişisel/şimdiki durum veya belirsiz** → LLM yok, sabit 112; **genel bilgi sorusu** → yanıtın en üstünde
  sabit 112 uyarı kutusu (`emergency_notice`) + normal yanıt; LLM yoksa sabit 112. Kendine zarar her zaman yalnız sabit
  yanıt (yalnız 112). Doğrulama ve kalan açıklar: `phase_xlviii/03_eval.md` §5–6.
* **Son kontrol**: doz birimi (`500 mg` vb.; `mg/dL` gibi laboratuvar birimi değil), yasak ifadeler ("tanınız",
  "kesinlikle", "kesin olarak", "hastasınız", "almalısınız" …), kaynakta olmayan sayı veya yüzde, bilgi tabanında olmayan
  URL → yanıt atılır, yerine sabit güvenli metin gelir. Model "kaynaklarımda bilgi yok" derse sabit metin döner.
* **Kaynaklar**: yalnız modelin atıf yaptığı ([n]) parçaların belgeleri listelenir (atıf yoksa ilk iki parça). Dış
  kaynaklar URL ile, iç belgeler ad ile gösterilir.
* **Sabit uyarı** (`app_config.json > disclaimer_tr`) her yanıtın sonuna eklenir ve `disclaimer` alanında da döner.

## 3. API

`POST /assistant/ask`

```json
{"question": "Neden sonuç üretilmedi?",
 "results": [{"disease_key": "osteoporosis", "outcome": "ABSTAIN", "missing_fields": ["fracture_hip"]}]}
```

* `question`: 1–2000 karakter (ilk 500 karakter kullanılır).
* `results` (isteğe bağlı): oturumdaki sonuç **etiketleri**. `outcome` ∈ `ESIK_USTU | ESIK_ALTI | ABSTAIN |
  NOT_APPLICABLE | ECG_REQUIRED`; `disease_key` uygulamanın hastalık anahtarı; `missing_fields` şema alan adları. Bilinmeyen
  hastalık/durum düşer, şemada olmayan alan adı düşer, fazladan anahtarlar (ör. `fields`, ölçüm değerleri) **yok sayılır**.
  Etiketler sunucuda sade Türkçe satıra çevrilir ("Osteoporoz (kemik erimesi): sonuç üretilmedi — eksik: …").
* Yanıt: `route` (`llm`, `no_source`, `postcheck_fail`, `emergency`, `emergency_self_harm`, `refused_medical`, `refused_scope`,
  `refused_injection`, `probability`), `answer`, `sources[]` (`doc_id`, `title`, `section`, `kind`, `url` | `ref`,
  `publisher`, `attribution`), `emergency_notice` (yalnız genel bilgi sorusunda acil kalıbı varsa), `llm_used`, `local_model`, `disclaimer`, `clinical_probability_eligibility=false`.
* Hatalar: 503 (asistan devre dışı; gerekçe), 429 (aynı anda tek LLM isteği), 422 (geçersiz gövde; girdi yansıtılmaz).

`GET /health > assistant`: `enabled`, `reason`, model adları/digest'leri, seçenekler, indeks durumu, anonim rota sayaçları.

## 4. Gizlilik

* Soru, etiketler ve yanıt **hiçbir log'a yazılmaz, diske kaydedilmez**. Yalnız anonim sayaçlar (rota başına sayı ve
  ortalama süre) bellekte tutulur.
* Sorudaki sayısal değerler (ör. "ALT 85") LLM'e ve gömme sorgusuna gitmeden `[sayı]` ile maskelenir ("tip 2" ve "112"
  korunur). Arayüz yalnız etiketleri gönderir; form değerleri gönderilmez.
* Ollama istemcisi yalnız loopback adresine bağlanır (kodda doğrulanır); sistem HTTP vekil değişkenleri yok sayılır. Dış
  ağa çıkan tek bileşen bilgi tabanı indirme betiğidir (`fetch_external.py`, elle çalıştırılır).
* Arayüzde sohbet yalnız React belleğindedir; tarayıcı depolaması kullanılmaz; sayfa yenilenince silinir.

## 5. Arayüz

Her sayfada sağ altta **"Açıklama asistanı"** düğmesi. Panel: "Yerel model — veriler bilgisayarınızdan çıkmaz" notu,
örnek sorular ("Eşik üstü ne demek?", "FibroScan nedir?", "Neden sonuç üretilmedi?"), yanıt beklenirken gösterge, yanıt
altında kaynak bağlantıları (yeni sekmede), sonuç varsa "Bu oturumdaki sonuç etiketlerini ekle" kutusu (varsayılan açık).
Ollama yoksa panel gerekçeyi gösterir ve giriş kapalıdır. Metinlerin tek kaynağı `app_config.json > ui.text_tr`
(`asst_*`).

## 6. Bilgi tabanı ve kilitler

`app/backend/assistant/README.md` (dosyalar, atıf, yeniden üretim) ve `phase_xlviii/02_knowledge_base.md` (kaynak listesi,
lisanslar). Değerlendirme: `phase_xlviii/03_eval.md`.

## 7. Testler

```powershell
cd app\backend
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests\test_phase48_assistant.py -m "not ollama"   # sahte Ollama
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests\test_phase48_assistant.py -m ollama          # gerçek Ollama
cd ..\frontend
npx vitest run src/components/AssistantPanel.test.tsx
npx playwright test e2e/assistant.spec.ts        # backend + Ollama çalışırken; Ollama yoksa SKIP
```

## 8. Sınırlılıklar

* Küçük (3.9B) yerel model; Türkçe çeviri ve bağlam hataları olabilir (bkz. 03_eval.md elle inceleme). Yanıtlar tıbbi
  doğrulamadan geçmemiştir.
* Ön filtre anahtar kelimeye dayalıdır: alışılmadık ifadeler kaçabilir (bu durumda istem kuralları ve son kontrol devreye
  girer) ve acil anahtar kelime içeren bilgi soruları da 112 yanıtı alır (bilinçli olarak temkinli).
* Dış kaynaklar İngilizcedir ve erişim tarihindeki sürümdür; güncel bilgi için bağlantıyı açın.
* Bu makinede yanıt süresi birkaç saniyedir; GPU'suz bir makinede çok daha uzun olabilir.
