# Deney tabloları — tüm hastalıklar

Üretim: `phase_xlvi/scripts/build_experiment_tables.py` (Phase XLVI). **Elle değer yazılmadı.** Registry'deki modeller için
değerler kayıtlı test sonuç dosyalarından (`phase_xlvi/results/card_metrics.json`; registry ile 3 ondalıkta çapraz kontrol:
236 kontrol, 0 uyuşmazlık, 2 yuvarlama farkı); registry dışı adaylar için ilgili faz sonuç dosyalarından okundu.

Tabloda **15 hastalık** vardır: registry'de 11 hastalık (13 model) ve registry'ye alınmayan 4 aday
(karaciğer yağlanması, lipid, astım, safra taşı). Görev tanımında "14 hastalık" yazıyordu; proje kayıtlarında 15 hastalık
bulunduğu için tümü gösterildi.

**Okuma kuralları**
- İç test, zamansal doğrulama, dış doğrulama ve teknik tekrar ayrı satırlardır; aynı model birden çok satırda görünebilir.
- CV sonuçları yalnız test edilmemiş adaylarda ve "CV — ADAY" etiketiyle yer alır.
- Oranlar Wilson %95 GA, AUC bootstrap %95 GA. AF dış doğrulamasında Precision prevalansa bağlı olduğu için raporlanmaz.
- "Üç hedef": P ≥ 0,70, R ≥ 0,75, FPR ≤ 0,15 aynı eşikte (nokta tahmini). Araştırma hedefidir, klinik onay kriteri değildir.
- \* Teknik tekrar (CAD Hungarian/VA): düzeltilmiş yeniden skorlama, seçilmiş eksiksiz vaka; bağımsız dış doğrulama değildir.
- Uygulamadaki durum: ana / araştırma / deneysel modül (`app_config.json > module_labels`) veya uygulamada değil.

| hastalık | model | veri | test türü | n (pozitif) | Precision | Recall | FPR | AUC | baseline ΔAUC [%95 GA] | üç hedef | uygulamada |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Atriyal fibrilasyon (AF) | `af_S4_DEVICE` | PTB-XL fold 10 (hasta düzeyinde ayrık) | iç test | 1572 (114) | 0,873 [0,801–0,921] | 0,904 [0,835–0,945] | 0,010 [0,006–0,017] | 0,980 [0,959–0,995] | model − RR_iqr / RR_mean: 0,021 [0,006–0,037] | evet | ana |
| Atriyal fibrilasyon (AF) | `af_S4_DEVICE` | Challenge 2021, 4 kaynak havuzu, AF vs SR (A2) | dış | 7817 (3497) | raporlanmaz | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | 0,990 [0,987–0,992] | model − RR_iqr/RR_mean ≥ 0,138235: 0,021 [0,018–0,025] | değerlendirilemez | ana |
| Karaciğer fibrozisi (LSM ≥ 8 kPa) | `fibrosis_final` | NHANES L 2021–23 (PREVIOUSLY_EXPOSED) | iç test | 4714 (587) | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,794 [0,773–0,813] | model − FIB-4: 0,197 [0,169–0,225]; model − NFS: 0,096 [0,075–0,117] | hayır | ana |
| Osteoporoz (DXA femur T-skoru ≤ −2,5) | `osteo_final` | NHANES J 2017–18 | zamansal | 2275 (164) | 0,208 [0,178–0,242] | 0,780 [0,711–0,837] | 0,230 [0,213–0,249] | 0,849 [0,818–0,880] | model − (−OST): 0,025 [0,012–0,038] | hayır | araştırma |
| Koroner arter hastalığı (CAD) | `cad_DEVICE` | UCI Cleveland (önceden açılmış) | iç test | 61 (28) | 0,885 [0,710–0,960] | 0,821 [0,644–0,921] | 0,091 [0,031–0,236] | 0,948 [0,888–0,990] | model − LR(age, sex): 0,253 [0,147–0,382]; model − Tek değişken: thalach (− yön; fit AUC=0.282): 0,173 [0,072–0,290] | evet | deneysel |
| Koroner arter hastalığı (CAD) | `cad_DEVICE` | UCI Hungarian (eksiksiz vaka, seçilmiş) | teknik tekrar* | 95 (68) | 0,857 [0,757–0,921] | 0,882 [0,785–0,939] | 0,370 [0,215–0,558] | 0,852 [0,766–0,928] | model − LR(yaş, cinsiyet): 0,190 [0,072–0,315] | hayır | deneysel |
| Koroner arter hastalığı (CAD) | `cad_DEVICE` | UCI VA Long Beach (eksiksiz vaka, seçilmiş) | teknik tekrar* | 64 (54) | 0,885 [0,782–0,943] | 1,000 [0,934–1,000] | 0,700 [0,397–0,892] | 0,667 [0,437–0,859] | model − LR(yaş, cinsiyet): 0,055 [-0,164–0,288] | hayır | deneysel |
| Diyabet (teşhis edilmemiş) | `dm_A` | NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | iç test | 8895 (389) | 0,103 [0,092–0,115] | 0,733 [0,687–0,774] | 0,292 [0,282–0,302] | 0,800 [0,781–0,819] | A − ADA: 0,042 [0,028–0,055]; A − yaş+BMI: 0,054 [0,040–0,068] | hayır | deneysel |
| Diyabet (teşhis edilmemiş) — laboratuvarlı | `dm_B` | NHANES G 2011–12 + H 2013–14 (kilitli tek sefer) | iç test | 8895 (389) | 0,122 [0,109–0,136] | 0,715 [0,668–0,757] | 0,235 [0,227–0,245] | 0,825 [0,808–0,843] | B − ADA: 0,067 [0,050–0,083]; B − A: 0,025 [0,014–0,036] | hayır | deneysel |
| Anemi | `anemia_LR16` | NHANES A 1999–2000 (Phase25 holdout; önceden açılmış) | iç test | 410 (21) | 0,810 [0,600–0,923] | 0,810 [0,600–0,923] | 0,010 [0,004–0,026] | 0,991 [0,980–0,999] | model − Hct_proxy=RBC×MCV/10 sabit (E<39, K<36): 0,002 [-0,003–0,008] | evet | deneysel |
| Anemi | `anemia_LR16` | NHANES C, E, F, I birleşik | farklı döngüler (aynı program) | 11171 (669) | 0,709 [0,678–0,739] | 0,883 [0,857–0,906] | 0,023 [0,020–0,026] | 0,991 [0,989–0,993] | model − Hct_proxy kuralı: 0,004 [0,002–0,005] | evet | deneysel |
| KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) | `copd_S4_DEVICE` | NHANES G 2011–12 | iç test | 37 (20) | 1,000 [0,772–1,000] | 0,650 [0,433–0,819] | 0,000 [0,000–0,184] | 0,921 [0,824–0,988] | model − pre-BD FEV1/FVC < 0.70: 0,009 [-0,059–0,076] | hayır | deneysel |
| KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) | `copd_S4_DEVICE` | NHANES F 2009–10 | zamansal | 250 (156) | 0,929 [0,871–0,962] | 0,756 [0,683–0,817] | 0,096 [0,051–0,172] | 0,898 [0,857–0,934] | model − pre-BD FEV1/FVC < 0.70: 0,023 [-0,005–0,052] | evet | deneysel |
| Hipertansiyon | `htn_M1` | NHANES C 2003–04 (ölçüm yöntemi kaymalı) | zamansal | 2798 (1001) | 0,702 [0,675–0,729] | 0,766 [0,739–0,791] | 0,181 [0,164–0,199] | 0,875 [0,862–0,887] | M1 − LR(yaş, cinsiyet, BMI): 0,012 [0,007–0,018] | hayır | deneysel |
| Böbrek (farkında olunmayan tek ziyaret renal anormalliği) | `ckd_A` | NHANES I 2015–16 (kilitli tek sefer) | iç test | 4812 (716) | 0,293 [0,273–0,314] | 0,767 [0,734–0,796] | 0,323 [0,309–0,337] | 0,791 [0,773–0,809] | A − SCORED: 0,032 [0,020–0,043] | hayır | deneysel |
| Böbrek — laboratuvarlı | `ckd_B` | NHANES I 2015–16 (kilitli tek sefer) | iç test | 4812 (716) | 0,313 [0,291–0,335] | 0,754 [0,721–0,784] | 0,290 [0,276–0,304] | 0,805 [0,788–0,823] | B − SCORED: 0,047 [0,035–0,058]; B − A: 0,015 [0,009–0,021] | hayır | deneysel |
| Miyokard enfarktüsü (EKG bulgusu) | `mi_model` | tümü (fold 9 + fold 10 AF-test dışı) | iç test | 1474 (521) | 0,781 [0,747–0,811] | 0,942 [0,919–0,959] | 0,145 [0,124–0,169] | 0,973 [0,965–0,980] | model − B1 yaş+cinsiyet LR: 0,155 [0,134–0,175]; model − B2 Q kuralı (ters yönde çalışıyor; yorumlanmaz): 0,667 [0,638–0,695] | evet | uygulamada değil (registry_only) |
| Kalp yetmezliği | `hf_S2_BASIC_LAB` | Mendeley 7v4w66wxj8.1 (n=37) | iç test | 37 (18) | 0,824 [0,590–0,938] | 0,778 [0,548–0,910] | 0,158 [0,055–0,376] | 0,950 [0,877–0,997] | model − LR(age, sex, bmi): 0,371 [0,158–0,588]; model − Tek değişken: rip3 (+ yön; fit AUC=0.927): -0,006 [-0,044–0,023] | hayır | uygulamada değil (registry_only) |
| Karaciğer yağlanması | liver_final (XGBoost) | NHANES L (CONTAMINATED test etiketi) | iç test (CONTAMINATED) | 2429 (966) | 0,720 [0,690–0,749] | 0,648 [0,617–0,678] | 0,166 [0,148–0,186] | 0,845 [0,829–0,860] | model − FLI: 0,005 [-0,003–0,013] | hayır | uygulamada değil (ALMA) |
| Safra taşı | gallstone_final (CatBoost) | NHANES III Faz 2 | zamansal | 6528 (614) | 0,174 [0,160–0,189] | 0,741 [0,705–0,774] | 0,365 [0,353–0,377] | 0,751 [0,732–0,769] | model − LR(yaş, cinsiyet, BMI): 0,012 [0,004–0,019] | hayır | uygulamada değil (ALMA) |
| Lipid bozukluğu (dislipidemi) | LR varsayılan / ros [FULL] | Phase XXIX-B geliştirme | **CV — ADAY** (test yok) | 1533 (prevalans 0,487) | 0,67 | 0,17 | 0,08 | 0,703 | LR(age,sex,bmi): 0,658 → +0,045 (+0,025…+0,066) (CV) | hayır | uygulamada değil (ALMA) |
| Astım | LR varsayılan / none [FULL] | Phase XXIX-B geliştirme | **CV — ADAY** (test yok) | 253 (prevalans 0,249) | 0,74 | 0,49 | 0,06 | 0,758 | LR(age,sex): 0,756 → +0,001 (-0,013…+0,017) (CV) | hayır | uygulamada değil (ALMA) |

## Başarısız veya sınırlı modeller — kısa gerekçe

Metinler registry'den (`research_target_note`, `app_feasibility`, `candidates_not_registered.rationale`) aynen alınmıştır.

- **Atriyal fibrilasyon (AF) (`af_S4_DEVICE`; ana)** — Üç hedef AF vs SR iç testte GA ile birlikte sağlandı; dış doğrulamada P prevalansa bağlı olduğu için değerlendirilemez. Diğer ritimlerde FPR 0,072 (sinüs taşikardisinde 0,181; PVC 0,306).
- **Karaciğer fibrozisi (LSM ≥ 8 kPa) (`fibrosis_final`; ana)** — Üçlü hedef sağlanmadı; eşik Recall ≥ 0,85 hedefiyle seçilmişti, testte 0,768 (tarama hedefi 0,85 altında). Yönlendirme oranı 0,399.
- **Osteoporoz (DXA femur T-skoru ≤ −2,5) (`osteo_final`; araştırma)** — Üçlü hedef (ve tarama hedefi Recall ≥ 0,85) sağlanmadı; eşik Recall ≥ 0,85 için seçilmişti, testte 0,780.
- **Koroner arter hastalığı (CAD) (`cad_DEVICE`; deneysel)** — İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil; n=61). Düzeltilmiş dış tekrarlarda FPR 0,37–0,70 (hedef yok).
- **Diyabet (teşhis edilmemiş) (`dm_A`; deneysel)** — Hiçbir eşikte sağlanmadı (P 0,09–0,12; %4,4 prevalansta yapısal olarak zor). Birincil eşikte Recall ≥ 0,75 testte korunmadı (0,733).
- **Diyabet (teşhis edilmemiş) — laboratuvarlı (`dm_B`; deneysel)** — Hiçbir eşikte sağlanmadı (P 0,10–0,12).
- **Anemi (`anemia_LR16`; deneysel)** — İç testte 3 hedef nokta tahminiyle sağlandı (GA ile değil). Dış: P hedefte C/I'da (0,77/0,87), E/F'de altında (0,64/0,62); Recall ≥ 0,75 ve FPR ≤ 0,15 tüm döngülerde sağlandı.
- **KOAH (post-bronkodilatör hava akımı obstrüksiyonunun sürmesi) (`copd_S4_DEVICE`; deneysel)** — F 2009–10'da 3 hedef nokta tahminiyle sağlandı (GA ile değil; E 2007–08'de Recall 0,718 < 0,75). Seçilmiş popülasyonda P/FPR genel popülasyona taşınamaz.
- **Hipertansiyon (`htn_M1`; deneysel)** — Hiçbir eşikte üçlü hedef sağlanmadı (birincil: FPR 0,181; ikincil: Recall 0,665).
- **Böbrek (farkında olunmayan tek ziyaret renal anormalliği) (`ckd_A`; deneysel)** — Hiçbir model ve eşikte sağlanmadı (P 0,29–0,31, FPR 0,29–0,32; %15 prevalansta P ≥ 0,70 yapısal olarak zor).
- **Böbrek — laboratuvarlı (`ckd_B`; deneysel)** — Hiçbir eşikte sağlanmadı.
- **Miyokard enfarktüsü (EKG bulgusu) (`mi_model`; uygulamada değil (registry_only))** — Tüm testte 3 hedef nokta tahminiyle sağlandı (FPR GA üst sınırı 0,169 > 0,15); temiz alt kümede FPR 0,173 (hedef yok). MI dışı anormallikler negatife katılınca FPR 0,396. Uygulama: UYGULAMAYA ALINAMAZ (şimdilik): 168 lead bazlı ECGDeli feature'ını üretecek kilitli pipeline mevcut değil.
- **Kalp yetmezliği (`hf_S2_BASIC_LAB`; uygulamada değil (registry_only))** — İç testte P ve Recall hedefte, FPR 0,158 > 0,15 (GA geniş). Dış doğrulama YAPILAMADI (Phase XXXIX: uyumlu RIP3 assay'li başka veri BULUNAMADI). Uygulama: UYGULAMAYA ALINAMAZ (şimdilik): RIP3 özel assay değeri ve sağlıklı-kontrol tasarımı; kullanıcı girdisiyle üretilemez.
- **Karaciğer yağlanması (uygulamada değil; karar: ALMA (kullanıcı onayladı, Phase XLIII sonrası))** — ['Test etiketi CONTAMINATED (L CAP etiketleri V2 başlangıcı ve Focused fazında model/eşik seçiminde kullanılmış); bağımsız test sayılamaz.', "FLI baseline'ına testte ΔAUC +0,005 (−0,003…+0,013): anlamlı katkı yok; HSI'ya göre var. TG ile FLI zaten formülle hesaplanabilir.", 'Açık dış CAP verisi BULUNAMADI (KNHANES/CHARLS/CHNS dahil); dış doğrulama yolu şimdilik yok.', 'Üçlü hedef sağlanmadı (P 0,720, R 0,648, FPR 0,166).']
- **Lipid bozukluğu (dislipidemi) (uygulamada değil; karar: ALMA (kullanıcı onayladı, Phase XLIII sonrası))** — ['Lipidler hedefi tanımladığı için girdi olamıyor; kalan rutin girdilerle AUC ≈ 0,70 (CV) ve P ≥ 0,70 eşiğinde Recall ≈ 0,17.', "Doğrudan lipid ölçümü varken ML'in klinik katkısı yok; tarama değeri kanıtlanmadı. Phase XXIX-B sonrası kilitli/test edilmiş yeni model YOK.", "Eski modeller Phase25'te daha önce kullanılmamış A döngüsü holdout'unda değerlendirildi: üçlü hedef karşılanmadı; sonraki iyileştirme yalnız CV aday (Phase XXIX-B)."]
- **Astım (uygulamada değil; karar: ALMA (kullanıcı onayladı, Phase XLIII sonrası))** — ["Veri çok küçük (n=253; Exasens vaka-kontrol, saliva/klinik gruplar); yaş+cinsiyet LR'ye göre ΔAUC +0,001 (GA 0'ı içeriyor).", 'Spirometri/semptom/geri dönüşlülük verisi yok; hedef kaynak-grubu (astım vs HC/enfeksiyon) genel popülasyona taşınmaz.', 'Dış doğrulama yok.']
- **Safra taşı (uygulamada değil; karar: ALMA (kullanıcı onayladı, Phase XLIII sonrası))** — ["Test AUC 0,751; P 0,174 (prevalans %9,4), FPR 0,365; yaş+cinsiyet+BMI LR'ye göre ΔAUC yalnız +0,012 (+0,004…+0,019).", "Veri 1988–94 (NHANES III); 20 feature'ın çoğu laboratuvar (CRP, GFR, kreatinin, LDL…); zamansal test aynı kaynak içinde; kişiler karaciğer hedefi için görülmüş.", 'Üçlü hedef sağlanmadı; klinik karar değeri düşük (çok yüksek yanlış pozitif).']

Model başına ayrıntı: [model kartları](model_cards/README.md).
