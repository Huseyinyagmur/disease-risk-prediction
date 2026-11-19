| model | modül | kanıt düzeyi | kaynak | n (pozitif) | Precision | Recall | FPR | AUC | üç hedef (nokta) |
|---|---|---|---|---|---|---|---|---|---|
| Atriyal fibrilasyon (EKG) (`af_S4_DEVICE`) | ana modül | iç test | Phase XXVII (PTB-XL, hasta düzeyinde ayrık) | 1572 (114) | 0,873 [0,801–0,921] | 0,904 [0,835–0,945] | 0,010 [0,006–0,017] | 0,980 [0,959–0,995] | evet |
| Atriyal fibrilasyon (EKG) (`af_S4_DEVICE`) | ana modül | dış doğrulama | Phase XXXIII A2 (Challenge 2021: CPSC2018, CPSC-Extra, Chapman-Shaoxing, Georgia; AF vs SR, tam örneklem, havuz) | 7817 (3497) | — | 0,929 [0,919–0,937] | 0,003 [0,001–0,005] | 0,990 [0,987–0,992] | değerlendirilemez |
| Atriyal fibrilasyon (EKG) (`af_S4_DEVICE`) | ana modül | diğer ritimler dahil (Phase XXXIII B)** | Phase XXXIII B (Challenge 2021, 4 kaynak havuz, ikincil analiz; AF vs SR + diğer ritimler) | 5477 (3497) | — | 0,929 [0,919–0,937] | 0,072 [0,062–0,084] | 0,965 [0,960–0,970] | değerlendirilemez |
| Karaciğer fibrozisi (`fibrosis_final`) | ana modül | iç test | Phase XXXI (NHANES L, kilitli tek sefer) | 4714 (—) | 0,240 [0,221–0,260] | 0,768 [0,733–0,801] | 0,346 [0,332–0,361] | 0,794 [0,773–0,813] | hayır |
| Osteoporoz (`osteo_final`) | araştırma modülü | zamansal | Phase XXX (NHANES J, kilitli tek sefer) | 2275 (164) | 0,208 [0,178–0,242] | 0,780 [0,711–0,837] | 0,230 [0,213–0,249] | 0,849 [0,818–0,880] | hayır |
| Koroner arter hastalığı (`cad_DEVICE`) | deneysel | iç test | Cleveland UCI test (phase_xxvii; önceden görülmüş) | 61 (28) | 0,885 [0,710–0,960] | 0,821 [0,644–0,921] | 0,091 [0,031–0,236] | 0,948 [0,888–0,990] | evet |
| Koroner arter hastalığı (`cad_DEVICE`) | deneysel | teknik tekrar* Hungarian | Phase XLI düzeltilmiş teknik tekrar (UCI Hungarian n=95, VA n=64; eksiksiz-vaka, seçilmiş, PREVIOUSLY_EXPOSED; bağımsız dış doğrulama DEĞİL) | 95 (68) | 0,857 [0,757–0,921] | 0,882 [0,785–0,939] | 0,370 [0,215–0,558] | 0,852 [0,766–0,928] | hayır |
| Koroner arter hastalığı (`cad_DEVICE`) | deneysel | teknik tekrar* VA | Phase XLI düzeltilmiş teknik tekrar (UCI Hungarian n=95, VA n=64; eksiksiz-vaka, seçilmiş, PREVIOUSLY_EXPOSED; bağımsız dış doğrulama DEĞİL) | 64 (54) | 0,885 [0,782–0,943] | 1,000 [0,934–1,000] | 0,700 [0,397–0,892] | 0,667 [0,437–0,859] | hayır |
| Diyabet A (form) (`dm_A`) | deneysel | iç test | Phase XLII (NHANES G 2011–12 + H 2013–14, kilitli tek sefer) | 8895 (389) | 0,103 [0,092–0,115] | 0,733 [0,687–0,774] | 0,292 [0,282–0,302] | 0,800 [0,781–0,819] | hayır |
| Diyabet B (+lab) (`dm_B`) | deneysel | iç test | Phase XLII (G+H, kilitli tek sefer) | 8895 (389) | 0,122 [0,109–0,136] | 0,715 [0,668–0,757] | 0,236 [0,227–0,245] | 0,826 [0,808–0,843] | hayır |
| Anemi (`anemia_LR16`) | deneysel | iç test | Phase XXVII (NHANES 1999–2000 A, önceden görülmüş) | 410 (21) | 0,810 [0,600–0,923] | 0,810 [0,600–0,923] | 0,010 [0,004–0,026] | 0,991 [0,980–0,999] | evet |
| Anemi (`anemia_LR16`) | deneysel | farklı döngüler (aynı program; bağımsız kurum değil) | Phase XL (NHANES C, E, F, I birleşik) | 11171 (669) | 0,709 [0,678–0,739] | 0,883 [0,857–0,906] | 0,023 [0,020–0,026] | 0,991 [0,989–0,993] | evet |
| KOAH (`copd_S4_DEVICE`) | deneysel | iç test | Phase XXVII (NHANES G 2011–12) | 37 (20) | 1,000 [0,772–1,000] | 0,650 [0,433–0,819] | 0,000 [0,000–0,184] | 0,921 [0,824–0,988] | hayır |
| KOAH (`copd_S4_DEVICE`) | deneysel | zamansal | Phase XXVII (NHANES F 2009–10) | 250 (156) | 0,929 [0,871–0,962] | 0,756 [0,683–0,817] | 0,096 [0,051–0,172] | 0,898 [0,857–0,934] | evet |
| Hipertansiyon (`htn_M1`) | deneysel | zamansal | Phase XXXVII (NHANES C 2003–04, kilitli tek sefer; hiçbir hedefte önceden kullanılmamış kişiler) | 2798 (1001) | 0,702 [0,675–0,729] | 0,766 [0,739–0,791] | 0,181 [0,164–0,199] | 0,875 [0,862–0,887] | hayır |
| Böbrek A (form) (`ckd_A`) | deneysel | iç test | Phase XXXV (NHANES I, kilitli tek sefer) | 4812 (716) | 0,293 [0,273–0,314] | 0,767 [0,734–0,796] | 0,323 [0,309–0,337] | 0,791 [0,773–0,809] | hayır |
| Böbrek B (+lab) (`ckd_B`) | deneysel | iç test | Phase XXXV (NHANES I, kilitli tek sefer) | 4812 (716) | 0,313 [0,291–0,335] | 0,754 [0,721–0,784] | 0,290 [0,276–0,304] | 0,805 [0,788–0,823] | hayır |

\* CAD Hungarian/VA satırları düzeltilmiş teknik tekrardır; kişiler önceden görülmüştür ve bu satırlar bağımsız dış doğrulama **değildir** (registry notu).

\*\* AF Phase XXXIII B: negatif sınıfta sinüs ritminin yanında diğer ritimler de vardır (havuz, ikincil analiz; kaynak `phase_xxxiii/results/b_results.csv`). Ritim bazında FPR: sinüs taşikardisi 0,181 [0,138–0,235] (n = 237), PVC 0,306 [0,206–0,430] (n = 62) (`b_rhythm_fpr.csv`). Precision örneklem bileşimine bağlı olduğu için, registry'nin A2 satırındaki kuralla aynı şekilde raporlanmaz.

AF dış doğrulama (A2) havuzunda CPSC-Extra kaynağında yalnız 4 negatif (SR) kayıt vardır; bu kaynak tek başına yorumlanamaz (`a2_results.csv`: "YORUMLANAMAZ (SR n=4)").
