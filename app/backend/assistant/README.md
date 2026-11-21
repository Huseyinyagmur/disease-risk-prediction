# Açıklama asistanı — bilgi tabanı ve kilitler (Phase XLVIII)

Yerel (Ollama, yalnız `127.0.0.1:11434`) RAG asistanının veri dosyaları. Kod: `app/backend/healthrisk_api/assistant/`.
Ayrıntılı kullanım: `app/docs/assistant.md`. Faz raporu: `phase_xlviii/`.

| dosya | içerik |
|---|---|
| `assistant_lock.json` | sohbet ve gömme modeli adı + Ollama digest'i, üretim seçenekleri (sıcaklık 0, seed 42), indeks manifest SHA256'sı. Sunucu açılışta/durum sorgusunda digest'leri ve indeksi doğrular; uyuşmazlıkta asistan devre dışı. |
| `assistant_config.json` | sabit yanıt metinleri (acil, ret, olasılık, kaynak yok), ön filtre anahtar kelimeleri, erişim parametreleri (k, min_score), sorgu genişletme sözlüğü |
| `kb/sources.json` | dış kaynak listesi: URL, erişim tarihi, yayıncı, lisans notu, atıf metni, ham yanıt ve metin SHA256, alınan / dışarıda bırakılan bölümler; yalnız bağlantı verilen kaynaklar |
| `kb/external/*.md` | dış metin parçaları (29 sayfa; değiştirilmeden, tedavi/ilaç/doz bölümleri hariç) |
| `kb/internal/*.md` | proje içi belgeler (13 model kartı, terim sözlüğü, "Ne yapmalıyım?", kanıt düzeyleri, analiz gereksinimleri, Hakkında) — `app_config.json`, `About.tsx` ve `app/docs/model_cards/` dosyalarından **kopyalanır**, metin yazılmaz |
| `kb/index/` | `chunks.jsonl`, `embeddings.f32` (float32, L2-normalize), `manifest.json` (tüm belge ve indeks SHA256'ları) |
| `scripts/fetch_external.py` | dış sayfaları resmi kaynaklardan indirir (yalnız bu betik dış ağa çıkar) |
| `scripts/build_index.py` | iç belgeleri üretir, parçalar, yerel gömme modeliyle gömer; aynı makinede bit düzeyinde tekrarlanabilir |

Yeniden üretim (kök dizinden):

```powershell
app\backend\.venv\Scripts\python.exe -B -I app\backend\assistant\scripts\fetch_external.py   # ağ; sayfalar güncellenmiş olabilir
app\backend\.venv\Scripts\python.exe -B app\backend\assistant\scripts\build_index.py          # Ollama + bge-m3 gerekli
```

`build_index.py`, `sources.json`'daki metin SHA256'ları tutmazsa durur. Yeni indeks üretildiğinde
`kb/index/manifest.json` SHA256'sı `assistant_lock.json > kb_index.manifest_sha256` alanına elle yazılmalıdır (kilit
bilinçli olarak otomatik güncellenmez).

## Kaynaklar ve atıf

Metinler İngilizce ve kaynak sayfadan değiştirilmeden alınmıştır (dipnot üst simgeleri hariç); asistan yanıtlarında
Türkçe özetlenir ve her yanıtta kaynak bağlantısı gösterilir. Erişim tarihi: **2026-11-21**.

* **MedlinePlus (U.S. National Library of Medicine)** — sağlık konusu özetleri (web servisi
  `wsearch.nlm.nih.gov`, FullSummary) ve tıbbi test sayfaları. NLM'nin
  [Linking to and Using Content from MedlinePlus](https://medlineplus.gov/about/using/usingcontent/) sayfasına göre bu
  içerik kamu malıdır (telifsiz). A.D.A.M. Medical Encyclopedia ve ASHP ilaç monografları **teliflidir ve alınmamıştır**.
  Atıf: *Source: MedlinePlus, National Library of Medicine.*
* **CDC** — kamu malı; [Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html) koşulları: atıf
  (*Source: CDC. Materials developed by CDC.*), içerik değiştirilmez, materyal ajans sitesinde ücretsiz olarak
  mevcuttur. **Bu kullanım ve CDC/ATSDR/HHS sitelerine verilen bağlantılar CDC, ATSDR, HHS veya ABD Hükümeti
  tarafından bu projenin onaylandığı anlamına gelmez.** CDC sayfaları güncellenebilir; güncel sürüm için bağlantıyı açın.
* **NIDDK (NIH)** — [Copyright](https://www.niddk.nih.gov/copyright) sayfasına göre içeriğin çoğu telifsizdir;
  değiştirilmeden yeniden üretilen içerikte NIDDK kaynak olarak belirtilir. NIDDK içeriği bir şirketin/ürünün onayı veya
  kişisel tıbbi tavsiye olarak kullanılmaz. Atıf: *Source: National Institute of Diabetes and Digestive and Kidney
  Diseases (NIDDK), NIH.*
* **Yalnız bağlantı (metin kopyalanmadı):** NHLBI sağlık konusu sayfaları (sitede yeniden kullanım/telif beyanı
  BULUNAMADI) ve WHO bilgi notları (görev kuralı: WHO metni kopyalanmaz). Liste: `kb/sources.json > link_only`.

Sayfa başına URL, başlık ve SHA256: `kb/sources.json` ve `phase_xlviii/02_knowledge_base.md`.

Gömme modeli `bge-m3` (BAAI, MIT lisansı; Ollama `bge-m3:latest`).
