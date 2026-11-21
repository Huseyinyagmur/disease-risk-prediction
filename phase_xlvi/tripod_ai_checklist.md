# Phase XLVI — TRIPOD+AI kontrol listesi × model

Kaynak: Collins GS ve ark. TRIPOD+AI statement. *BMJ* 2024;385:e078378. doi:10.1136/bmj-2023-078378 (PMID 38626948).
Madde metinleri makalenin Tablo 2'sinden (CC BY; makale DOI ile atıflanır, tam metin depoda tutulmaz;
`data/refs/tripod_ai_table2.json`) otomatik alınmıştır; tabloda kısaltıldı. D = geliştirme, E = değerlendirme.

Değerlendirme birimi: model kartı (`model_cards/<model_id>.md`) + kartın gösterdiği kaynak faz dosyaları. Kartlar bir dergi
makalesi değildir; "başlık", "özet" ve "tartışma" maddeleri kart biçimine göre kısmen karşılanır. Durumlar
`scripts/build_cards.py :: status()` içinde kural olarak tanımlıdır.

Simgeler: ✔ karşılandı · ◐ kısmen · ✘ yok · — uygulanamaz.

## Özet

| model | karşılandı | kısmen | yok | uygulanamaz |
|---|---|---|---|---|
| `af_S4_DEVICE` | 25 | 20 | 5 | 2 |
| `fibrosis_final` | 24 | 17 | 8 | 3 |
| `osteo_final` | 25 | 16 | 8 | 3 |
| `cad_DEVICE` | 23 | 20 | 8 | 1 |
| `dm_A` | 24 | 19 | 6 | 3 |
| `dm_B` | 24 | 19 | 6 | 3 |
| `anemia_LR16` | 25 | 18 | 6 | 3 |
| `copd_S4_DEVICE` | 25 | 18 | 6 | 3 |
| `htn_M1` | 25 | 17 | 7 | 3 |
| `ckd_A` | 24 | 17 | 8 | 3 |
| `ckd_B` | 24 | 17 | 8 | 3 |
| `mi_model` | 22 | 20 | 8 | 2 |
| `hf_S2_BASIC_LAB` | 21 | 20 | 9 | 2 |

## Madde × model

| bölüm | madde | D/E | TRIPOD+AI maddesi (kısaltılmış) | kartta | `af_S4_DEVICE` | `fibrosis_final` | `osteo_final` | `cad_DEVICE` | `dm_A` | `dm_B` | `anemia_LR16` | `copd_S4_DEVICE` | `htn_M1` | `ckd_A` | `ckd_B` | `mi_model` | `hf_S2_BASIC_LAB` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Title | 1 | D;E | Identify the study as developing or evaluating the performance of a multivariable prediction model, the tar… | başlık | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Abstract | 2 | D;E | See TRIPOD+AI for Abstracts checklist | §0 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Background | 3a | D;E | Explain the healthcare context (including whether diagnostic or prognostic) and rationale for developing or… | §1 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Background | 3b | D;E | Describe the target population and the intended purpose of the prediction model in the context of the care … | §1 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Background | 3c | D;E | Describe any known health inequalities between sociodemographic groups | §1 | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Objectives | 4 | D;E | Specify the study objectives, including whether the study describes the development or validation of a pred… | §1 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Data | 5a | D;E | Describe the sources of data separately for the development and evaluation datasets (eg, randomised trial, … | §2 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Data | 5b | D;E | Specify the dates of the collected participant data, including start and end of participant accrual; and, i… | §2 | ✔ | ✔ | ✔ | ◐ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ◐ |
| Participants | 6a | D;E | Specify key elements of the study setting (eg, primary care, secondary care, general population) including … | §3 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Participants | 6b | D;E | Describe the eligibility criteria for study participants | §3 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Participants | 6c | D;E | Give details of any treatments received, and how they were handled during model development or evaluation, … | §3 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Data preparation | 7 | D;E | Describe any data pre-processing and quality checking, including whether this was similar across relevant s… | §7 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Outcome | 8a | D;E | Clearly define the outcome that is being predicted and the time horizon, including how and when assessed, t… | §4 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Outcome | 8b | D;E | If outcome assessment requires subjective interpretation, describe the qualifications and demographic chara… | §4 | ◐ | — | — | ✘ | — | — | — | — | — | — | — | ◐ | ✘ |
| Outcome | 8c | D;E | Report any actions to blind assessment of the outcome to be predicted | §4 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Predictors | 9a | D | Describe the choice of initial predictors (eg, literature, previous models, all available predictors) and a… | §5 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Predictors | 9b | D;E | Clearly define all predictors, including how and when they were measured (and any actions to blind assessme… | §5 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Predictors | 9c | D;E | If predictor measurement requires subjective interpretation, describe the qualifications and demographic ch… | §5 | — | — | — | ✘ | — | — | — | — | — | — | — | — | — |
| Sample size | 10 | D;E | Explain how the study size was arrived at (separately for development and evaluation), and justify that the… | §6 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Missing data | 11 | D;E | Describe how missing data were handled. Provide reasons for omitting any data | §7 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Analytical methods | 12a | D | Describe how the data were used (eg, for development and evaluation of model performance) in the analysis, … | §8 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Analytical methods | 12b | D | Depending on the type of model, describe how predictors were handled in the analyses (functional form, resc… | §5 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Analytical methods | 12c | D | Specify the type of model, rationale†, all model building steps, including any hyperparameter tuning, and m… | §9 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Analytical methods | 12d | D;E | Describe if and how any heterogeneity in estimates of model parameter values and model performance was hand… | §12/§14 | ◐ | ✘ | ✘ | ◐ | ◐ | ◐ | ◐ | ◐ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Analytical methods | 12e | D;E | Specify all measures and plots used (and their rationale) to evaluate model performance (eg, discrimination… | §11–13 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Analytical methods | 12f | E | Describe any model updating (eg, recalibration) arising from the model evaluation, either overall or for pa… | §11 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Analytical methods | 12g | E | For model evaluation, describe how the model predictions were calculated (eg, formula, code, object, applic… | §16 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Class imbalance | 13 | D;E | If class imbalance methods were used, state why and how this was done, and any subsequent methods to recali… | §9 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Fairness | 14 | D;E | Describe any approaches that were used to address model fairness and their rationale | §14 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Model output | 15 | D | Specify the output of the prediction model (eg, probabilities, classification). Provide details and rationa… | §10 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Training versus evaluation | 16 | D;E | Identify any differences between the development and evaluation data in healthcare setting, eligibility cri… | §8 | ✔ | ◐ | ✔ | ✔ | ◐ | ◐ | ✔ | ✔ | ✔ | ◐ | ◐ | ◐ | ◐ |
| Ethical approval | 17 | D;E | Name the institutional research board or ethics committee that approved the study and describe the particip… | §17 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Funding | 18a | D;E | Give the source of funding and the role of the funders for the present study | §17 | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Conflicts of interest | 18b | D;E | Declare any conflicts of interest and financial disclosures for all authors | §17 | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Protocol | 18c | D;E | Indicate where the study protocol can be accessed or state that a protocol was not prepared | §17–18 | ✔ | ✔ | ✔ | ◐ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Registration | 18d | D;E | Provide registration information for the study, including register name and registration number, or state t… | §17 | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Data sharing | 18e | D;E | Provide details of the availability of the study data | §17 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Code sharing | 18f | D;E | Provide details of the availability of the analytical code§ | §17 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Patient and public involvement | 19 | D;E | Provide details of any patient and public involvement during the design, conduct, reporting, interpretation… | §17 | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Participants | 20a | D;E | Describe the flow of participants through the study, including the number of participants with and without … | §6 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Participants | 20b | D;E | Report the characteristics overall and, where applicable, for each data source or setting, including the ke… | §3/§18 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Participants | 20c | E | For model evaluation, show a comparison with the development data of the distribution of important predicto… | §2 | ◐ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ◐ | ✘ | ✘ | ✘ | ✘ |
| Model development | 21 | D;E | Specify the number of participants and outcome events in each analysis (eg, for model development, hyperpar… | §6 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Model specification | 22 | D | Provide details of the full prediction model (eg, formula, code, object, application programming interface)… | §0/§5 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Model performance | 23a | D;E | Report model performance estimates with confidence intervals, including for any key subgroups (eg, sociodem… | §12–14 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Model performance | 23b | D;E | If examined, report results of any heterogeneity in model performance across clusters. See TRIPOD-Cluster f… | §12/§14 | ◐ | ✘ | ✘ | ◐ | ◐ | ◐ | ◐ | ◐ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Model updating | 24 | E | Report the results from any model updating, including the updated model and subsequent performance | §11 | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Interpretation | 25 | D;E | Give an overall interpretation of the main results, including issues of fairness in the context of the obje… | §12/§15 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Limitations | 26 | D;E | Discuss any limitations of the study (such as a non-representative sample, sample size, overfitting, missin… | §15 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Usability of the model in the context of current care | 27a | D | Describe how poor quality or unavailable input data (eg, predictor values) should be assessed and handled w… | §16 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ◐ | ◐ |
| Usability of the model in the context of current care | 27b | D | Specify whether users will be required to interact in the handling of the input data or use of the model, a… | §16 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ◐ | ◐ |
| Usability of the model in the context of current care | 27c | D;E | Discuss any next steps for future research, with a specific view to applicability and generalisability of t… | §15 | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |

## Tam/olmayan maddelerin gerekçeleri

- **1** — kısmen: kart başlığı model ve hedefi adlandırır; çalışma raporu değildir (tüm modeller)
- **2** — kısmen: özet tablo; TRIPOD+AI for Abstracts uygulanmadı (tüm modeller)
- **3c** — yok: eşitsizlik analizi yok (tüm modeller)
- **5b** — kısmen: veri toplama tarihleri BULUNAMADI (cad_DEVICE, hf_S2_BASIC_LAB)
- **6c** — kısmen: yalnız uygunluk/hedef içinde (tüm modeller)
- **7** — kısmen: ön işleme pipeline'da; sosyodemografik gruplar arası karşılaştırma yok (tüm modeller)
- **8b** — kısmen: insan doğrulamalı okuma; değerlendirici demografisi BULUNAMADI (af_S4_DEVICE, mi_model); uygulanamaz: objektif ölçüm (lab/cihaz) (fibrosis_final, osteo_final, dm_A, dm_B, anemia_LR16, copd_S4_DEVICE, htn_M1, ckd_A, ckd_B); yok: BULUNAMADI (cad_DEVICE, hf_S2_BASIC_LAB)
- **8c** — kısmen: körleme raporlanmadı; ikincil veri (tüm modeller)
- **9a** — kısmen: panel tanımı protokolde; ön seçim gerekçesi kısmen (tüm modeller)
- **9c** — uygulanamaz: otomatik/objektif ya da öz bildirim (af_S4_DEVICE, fibrosis_final, osteo_final, dm_A, dm_B, anemia_LR16, copd_S4_DEVICE, htn_M1, ckd_A, ckd_B, mi_model, hf_S2_BASIC_LAB); yok: klinik değerlendirici bilgisi yok (cad_DEVICE)
- **10** — kısmen: sayılar var; örneklem büyüklüğü hesabı yok (tüm modeller)
- **12b** — kısmen: dönüşümler listelendi; ölçekleme pipeline içinde (tüm modeller)
- **12d** — kısmen: kaynak/döngü başına sonuç (af_S4_DEVICE, cad_DEVICE, dm_A, dm_B, anemia_LR16, copd_S4_DEVICE); yok: tek kaynak (fibrosis_final, osteo_final, htn_M1, ckd_A, ckd_B, mi_model, hf_S2_BASIC_LAB)
- **14** — kısmen: yalnız alt grup raporu (tüm modeller)
- **16** — kısmen: yalnız iç test (fibrosis_final, dm_A, dm_B, ckd_A, ckd_B, mi_model, hf_S2_BASIC_LAB)
- **17** — kısmen: proje etik onayı BULUNAMADI (tüm modeller)
- **18a** — yok: BULUNAMADI (tüm modeller)
- **18b** — yok: BULUNAMADI (tüm modeller)
- **18c** — kısmen: kök V2: seçim kilidi, protokol dosyası yok (cad_DEVICE)
- **18d** — yok: kayıt yok (tüm modeller)
- **18f** — kısmen: uygulama kodu açık; faz betiklerinin tamamı depoda değil (tüm modeller)
- **20a** — kısmen: sayılar; akış tablosu kaynak fazda (tüm modeller)
- **20b** — kısmen: karakteristikler kaynak faz raporunda (tüm modeller)
- **20c** — kısmen: yalnız seçilmiş karşılaştırmalar (af_S4_DEVICE, htn_M1)
- **22** — kısmen: donmuş nesne + SHA; açık formül yok (tüm modeller)
- **23b** — kısmen: kaynak/döngü başına (af_S4_DEVICE, cad_DEVICE, dm_A, dm_B, anemia_LR16, copd_S4_DEVICE); yok: tek kaynak (fibrosis_final, osteo_final, htn_M1, ckd_A, ckd_B, mi_model, hf_S2_BASIC_LAB)
- **24** — uygulanamaz: güncelleme yok (tüm modeller)
- **25** — kısmen: kart; tartışma bölümü değil (tüm modeller)
- **27a** — kısmen: uygulamada değil (mi_model, hf_S2_BASIC_LAB)
- **27b** — kısmen: uygulamada değil (mi_model, hf_S2_BASIC_LAB)
- **27c** — kısmen: açık noktalar sınırlılıklarda (tüm modeller)

## Başlıca eksikler (tüm modeller)

- **3c, 14:** sağlık eşitsizlikleri ve adalet için yöntem yok; yalnız alt grup performansı.
- **10:** örneklem büyüklüğü hesabı yapılmadı; KOAH, KY ve CAD'de test kümeleri çok küçük.
- **17, 18a, 18b, 18d, 19:** proje düzeyinde etik onay, fon, çıkar beyanı, çalışma kaydı ve hasta/halk katılımı BULUNAMADI.
- **22:** model açık formül olarak değil, donmuş nesne (joblib + SHA256) olarak paylaşılır.
