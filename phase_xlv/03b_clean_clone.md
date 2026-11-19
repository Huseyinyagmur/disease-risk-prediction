# Phase XLV — Ek: GitHub deposu düzenlemesi ve temiz klon doğrulaması (2026-11-20)

Kullanıcı onayıyla yapıldı (force push dahil). Depo: https://github.com/Huseyinyagmur/disease-risk-prediction.

## Yapılanlar

| # | iş | sonuç |
|---|---|---|
| 1 | SHA256 envanterleri (`sha256_before.json`, `sha256_after.json`, `sha256_final_scan.json`) takipten çıkarıldı, `.gitignore`'a eklendi; geçmişten `git filter-branch --index-filter` ile silindi, ardından reflog temizliği ve `git gc --aggressive`, force push | Geçmişte SHA envanteri: 0. Yerel `.git` paket boyutu **47,3 MiB → 4,97 MiB**; temiz klonun `.git` klasörü **5,1 MB**. Dosyalar diskte duruyor (faz bütünlüğü için). |
| 2 | Registry'deki 13 model dosyası registry'deki göreli yollarla eklendi (`.gitignore`'da `*.joblib` hariç, yalnız bu 13 yol için istisna). Pickle yüklemesinin istediği 4 yardımcı modül de eklendi (`All_Disease_Improvement_Phase21/src/` ve `Clinical_Optimization_Phase25/src/` altında `common.py` ve `pipeline_components.py`; ayrı süreçte yükleme izlenerek belirlendi). `.gitattributes`: `.joblib/.dat/.mat/.png` ikili, `.hea` satır sonu dönüşümsüz. | Git indeksindeki blob SHA256 = registry: **13/13** |
| 3 | `LICENSE` (MIT, kod) eklendi. README "Veri kaynakları ve lisanslar" bölümü yeniden yazıldı. | NHANES, PTB-XL, Challenge 2021, UCI, Mendeley lisans ve atıfları resmi sayfalardan kontrol edildi. ECGDeli: GPL-3.0 (yerel `LICENSE.txt` ve GitHub deposu); repoya konmadı. |
| 4 | Tablo betiği (`scripts/build_readme_assets.py`) güncellendi. AF "diğer ritimler dahil (Phase XXXIII B)" satırı ve sinüs taşikardisi/PVC FPR'leri `phase_xxxiii/results/b_results.csv` ve `b_rhythm_fpr.csv`'den, CPSC-Extra negatif sayısı `a2_results.csv`'den okunur. Anemi dış satırının etiketi "farklı döngüler (aynı program; bağımsız kurum değil)" yapıldı. | Elle yazılmış değer yok; README tablosu = üretilen tablo |
| 5 | README kurulum bölümü: klonla → çalıştır; AF için Octave + ECGDeli + kilitli pipeline ayrıca | — |
| — | Backend: AF ortamı yoksa gerekçe artık açık ("Octave/ECGDeli AF çalışma ortamı yok …"). Önceden kilit dosyası eksikliği "beklenmeyen hata: FileNotFoundError" olarak görünürdü. Octave exe eksikse "Octave yok: …". | 2 yeni test; tam paket **313 geçti, 5 strict-xfail, 0 hata** |

## Temiz klon doğrulaması (`results/clean_clone_result.json`, `scripts/verify_clean_clone.py`)

GitHub `main` (`8bd52f7`) boş bir klasöre klonlandı. Python 3.13.3 ile yeni venv kuruldu ve `requirements.lock` yüklendi.

| kontrol | sonuç |
|---|---|
| 13 model dosyası mevcut / SHA256 = registry / klonun `model_loader`'ı ile yüklenebilir | 13 / 13 / 13 |
| `/health`: paket sürümleri, registry ve şema SHA | temiz |
| `/health`: uygulamada görünen modeller | 11'in 11'i etkin |
| `/health`: AF pipeline | **devre dışı**, gerekçe: "Octave/ECGDeli AF çalışma ortamı yok: kilitli AF pipeline dosyaları bulunamadı (phase_xxviii/config/af_pipeline_lock.json, …)"; `status = degraded` |
| `POST /ecg/af` (örnek PTB-XL kaydı) | HTTP 200, ABSTAIN, aynı gerekçe |
| `POST /predict` (fibrozis profili) | fibrozis OK |
| Örnek `.hea` dosyası klonda bayt düzeyinde aynı | evet |

**Beklentiden fark:** talimatta "/health'te 12 model yüklü, AF Octave yok gerekçesiyle devre dışı" deniyordu. Gerçekte:

- Sunucu yalnız uygulamada görünen 11 modeli yükler; MI ve kalp yetmezliği registry'dedir ama uygulamada yoktur.
- AF model dosyası da klonda olduğu için AF modeli `/health`'te etkin görünür; devre dışı olan AF **pipeline**'ıdır.
- 13 model dosyasının tamamının yüklenebildiği ayrıca doğrulandı.

Canlı panel (`/eligibility`) pipeline durumunu göstermez: AF satırında yine "Eksik: EKG kaydı" yazar. Yükleme
yapıldığında ABSTAIN gerekçesi sonuç kartında görünür.

## Faz kuralı notu

Repo düzenlemesi için faz klasörü dışında şu dosyalar oluşturuldu veya değiştirildi; hepsi kullanıcı onayıyla:
`.gitignore`, `.gitattributes`, `LICENSE`, `README.md`, `docs/assets/`. Önceki faz dosyaları ve model dosyaları yalnız
git'e eklendi; içerikleri değişmedi (blob SHA256 = registry). Sonraki fazların SHA taramaları `.git` klasörünü hariç
tutmalıdır.
