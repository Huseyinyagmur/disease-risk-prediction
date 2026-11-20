"""Phase XLVI — model kartlarının ELLE yazılan (metin) içeriği. Her alan kaynak dosyayı belirtir.

Sayısal performans, TP/FP/TN/FN, ΔAUC: results/card_metrics.json (extract_metrics.py, kayıtlı dosyalardan).
Feature listesi, eşik değeri, hedef/popülasyon metni, sınırlılıklar, eksik-girdi kuralı, uygulama modu: registry.
Bu dosyadaki sayılar önceki faz raporlarından aynen alınmıştır; kaynak her alanda yazılıdır. Bulunamayan: BULUNAMADI.
"""

NHANES = ('NHANES (CDC/NCHS), kamuya açık anket + muayene verisi; https://wwwn.cdc.gov/nchs/nhanes/ '
          '(döngü dosyaları SHA256 ile ilgili fazın download_manifest dosyasında)')
PTBXL = 'PTB-XL 1.0.3 (PhysioNet), doi:10.13026/kfzx-aw45; Wagner ve ark., Sci Data 2020, doi:10.1038/s41597-020-0495-6'
PTBXLP = 'PTB-XL+ ECGDeli öznitelikleri (PhysioNet PTB-XL+, `ecgdeli_features.csv`; sürüm numarası proje dosyalarında BULUNAMADI)'
CH21 = 'PhysioNet/CinC Challenge 2021 1.0.3, doi:10.13026/34va-7q14 (kaynaklar: cpsc_2018, cpsc_2018_extra, chapman_shaoxing, georgia)'
UCI = 'UCI Heart Disease, doi:10.24432/C52P4X (Cleveland; teknik tekrar: Hungarian, VA Long Beach)'
MEND = 'Mendeley Data 7v4w66wxj8.1, doi:10.17632/7v4w66wxj8.1 (RIP3 kalp yetmezliği; birincil yayın PMID 32598878)'

P21_SEL = ('Phase21 eğitim protokolü (`All_Disease_Improvement_Phase21/training_protocol.json`, seed 20261111): 8 aile '
           '(Dummy, LR, RF, ExtraTrees, HistGB, XGBoost, LightGBM, CatBoost); yalnız fit kümesinde 3-fold '
           'StratifiedGroupKFold (kişi grubu); en iyi 2 aile-panel için Optuna (görev başına ≤ 6 deneme); seçim CV AP ile; '
           'test ve dış veri seçimde kullanılmadı.')
P21_THR = ('Phase21 eşik kuralı (`training_protocol.json > threshold`): validation kümesinde önce P ≥ 0,70, R ≥ 0,75, '
           'FPR ≤ 0,15 birlikte; yoksa R ≥ 0,60, FPR ≤ 0,25; içinde F2 − 0,5·FPR + 0,25·P en büyük ("BALANCED" senaryosu). '
           '**Bu fazda bulundu:** registry eşiği `All_Disease_Improvement_Phase21/selected_model_registry.json` içindeki '
           'BALANCED senaryo eşiğiyle bit düzeyinde aynıdır (XLIII registry\'de "kural BULUNAMADI" yazıyordu). '
           'Hangi dalın (birincil/yedek) uygulandığı: senaryo kaydında `constraints_met = true`.')
P21_CAL = ('Phase21: ham skor ile fit kümesi OOF üzerinde sigmoid kalibrasyon karşılaştırıldı; validation\'da seçildi '
           '(isotonic yalnız ≥ 1000 fit ve sınıf başına ≥ 100 ise).')
P21_IMB = ('Phase21: azınlık/çoğunluk < 0,8 ise LR class_weight, ROS, RUS, SMOTENC adayları yalnız eğitim fold\'unda; '
           'seçilen strateji modelin meta verisinde.')
CV2 = ('`phase_xxxi/config/cv_protocol_v2.md`: konfigürasyon (Optuna, iç 3-fold, amaç PR-AUC) tüm geliştirme verisinde '
       'bir kez seçilir; sabit konfigürasyonla dış 5-fold CV; eşik havuzlu OOF\'tan; fold–havuz AUC farkı > 0,02 ise uyarı.')

APP_ELIG = {   # phase_xliv/02_api.md "Popülasyon uygunluğu" tablosu + şema v2 güncellemesi
    'af_S4_DEVICE': 'Yalnız `POST /ecg/af`: WFDB `.hea` + `.dat`/`.mat`, 500 Hz, 12 lead, ≥ 10 sn (uzunsa ilk 10 sn). '
                    'NOT_APPLICABLE: yaş 18–89 dışı (≥ 90). ABSTAIN: yaş/cinsiyet yok, fs ≠ 500 Hz, < 5.000 örnek, pipeline '
                    'başarısız (zero_beats, ECGDeli hatası, NaN öznitelik), 60 sn zaman aşımı, AF çalışma ortamı (Octave/ECGDeli/'
                    'kilit) yok veya SHA uyuşmazlığı. `/predict` için her zaman NOT_APPLICABLE.',
    'mi_model': 'Uygulamada YOK (`app_visible = false`, `registry_only`): 168 lead bazlı ECGDeli özniteliğini üretecek kilitli '
                'pipeline yok.',
    'cad_DEVICE': 'Klinik mod (`clinical_mode`). NOT_APPLICABLE: yaş 20–100 dışı. ABSTAIN: 11 zorunlu alandan (göğüs ağrısı tipi, '
                  'istirahat KB, kolesterol, açlık glukozu > 120, istirahat EKG, maks. kalp hızı, efor anjinası, ST depresyonu, '
                  'ST eğimi, yaş, cinsiyet) biri eksik veya şema dışı kategori.',
    'dm_A': 'NOT_APPLICABLE: yaş < 20, gebe, diyabet tanısı, tanısız ama insülin/hap kullanan. ABSTAIN: yaş, cinsiyet, ırk, '
            'gebelik (kadın; "bilmiyorum" dahil), diyabet tanısı sorusu yanıtsız veya zorunlu alan eksik (3 tansiyon okuması '
            'dahil). HbA1c/açlık glukozu girilirse TARGET_DEFINING_INPUT uyarısı. `dm_B` laboratuvar varsa önce denenir.',
    'dm_B': '`dm_A` ile aynı uygunluk; ek olarak TK, HDL, TG, ALT, ürik asit zorunlu. Eksikse sonuç `dm_A`\'ya düşer '
            '(`fallback_from`).',
    'anemia_LR16': 'NOT_APPLICABLE: erkek 20–65 dışı, kadın 20–44 dışı, gebe. ABSTAIN: yaş, cinsiyet, gebelik (kadın 20–44) '
                   'yanıtsız veya 16 alandan biri eksik. Hemoglobin girilirse TARGET_DEFINING_INPUT uyarısı.',
    'copd_S4_DEVICE': 'Klinik mod. NOT_APPLICABLE: yaş 40–79 dışı veya pre-BD FEV1/FVC ≥ 0,70 (hedef popülasyon yalnız '
                      'obstrüksiyonlu ve BD testine alınmış kişiler). ABSTAIN: yaş, FEV1, FVC, BMI, sigara eksik.',
    'hf_S2_BASIC_LAB': 'Uygulamada YOK (`app_visible = false`, `registry_only`): RIP3 özel ELISA ölçümü gerekir; test n = 37.',
    'htn_M1': 'NOT_APPLICABLE: yaş < 18, gebe. ABSTAIN: yaş, cinsiyet, ırk, gebelik (kadın) yanıtsız veya 13 alandan biri eksik '
              '(HbA1c, TK, HDL, kreatinin → eGFR, idrar albümin/kreatinin → UACR dahil). Ölçülen tansiyon ≥ 140/90 veya ilaç '
              '→ TARGET_DEFINING_INPUT uyarısı.',
    'fibrosis_final': 'NOT_APPLICABLE: yaş < 20, gebe. ABSTAIN: yaş, cinsiyet, gebelik (kadın) yanıtsız veya 17 alandan biri '
                      'eksik (ALT, AST, GGT, ALP, albümin, trombosit, glukoz, HbA1c, TG, HDL, alkol dahil).',
    'osteo_final': 'NOT_APPLICABLE: yaş < 50. ABSTAIN: yaş veya 16 alandan biri eksik. Erkekte menopoz soruları yapısal boşluktur '
                   '(eğitimdeki `na_male` kuralı; eksik sayılmaz).',
    'ckd_A': 'NOT_APPLICABLE: yaş < 20, gebe, "doktor zayıf/başarısız böbrek dedi", diyaliz. ABSTAIN: yaş, cinsiyet, ırk, gebelik, '
             'böbrek tanısı sorusu yanıtsız veya zorunlu alan eksik (2. ve 3. tansiyon okuması dahil). Kreatinin veya idrar '
             'albümin+kreatinin girilirse TARGET_DEFINING_INPUT uyarısı. `ckd_B` laboratuvar varsa önce denenir.',
    'ckd_B': '`ckd_A` ile aynı uygunluk; ek olarak glukoz, HbA1c, TK, HDL, hemoglobin zorunlu. Eksikse `ckd_A`\'ya düşer.',
}

SPEC = {
    'af_S4_DEVICE': dict(
        sources=['All_Disease_Improvement_Phase21/training_protocol.json', 'All_Disease_Improvement_Phase21/selected_model_registry.json',
                 'phase_xxvii/PHASE_XXVII_REPORT.md', 'phase_xxviii/PHASE_XXVIII_REPORT.md', 'phase_xxix/PHASE_XXIX_REPORT.md',
                 'phase_xxxiii/PHASE_XXXIII_REPORT.md', 'phase_xlvi/af_validation_dossier.md'],
        purpose='12 derivasyonlu 10 sn EKG kaydında ritmin AF mi sinüs ritmi mi olduğunu sınıflar (kayıttaki mevcut ritim). '
                'Paroksismal AF öyküsünü dışlamaz; gelecekte AF riskini tahmin etmez. Araştırma ve eğitim amaçlı EKG yükleme '
                'demosu.',
        data=[('geliştirme + iç test', f'{PTBXL}; öznitelikler: {PTBXLP}', 'tek kurum arşivi (PTB, Almanya); kayıt tarihleri: bkz. §2 not'),
              ('dış doğrulama', CH21, 'dört hastane kaynağı; tarih aralığı BULUNAMADI')],
        dates_note='PTB-XL `recording_date` aralığı build_cards.py tarafından metadata\'dan okunur (yalnız tarih sütunu).',
        setting='Hastane EKG arşivi (PTB-XL: tek kurum). Genel nüfus taraması değildir.',
        eligibility='PTB-XL\'de hasta başına ilk EKG (etiket süzgecinden önce seçilir); `validated_by_human = True`; SCP kodlarında '
                    'AFIB xor SR; yaş ≥ 18 (> 89 yaşlar HIPAA gereği 300 kodludur → eksik). Diğer ritimler (AFL, taşikardi, '
                    'bradikardi, PAC, PVC) eğitimde yoktu. Kaynak: `prepare.py :: af()`.',
        target_method='PTB-XL SCP ritim kodu (AFIB veya SR); kardiyolog/insan doğrulamalı kayıtlar (`validated_by_human`). '
                      'Likelihood alanı kullanılmadı. Değerlendiricilerin demografisi BULUNAMADI. Etiketleme modelden bağımsızdır '
                      '(veri seti yayın öncesi).',
        samples=[('fit (fold 1–8)', 8839, 560, 'phase_xlvi/results/af_split_check.json'),
                 ('validation (fold 9; eşik seçimi)', 1614, 117, 'aynı'),
                 ('iç test (fold 10)', 1572, 114, 'aynı; Phase XXVII ci_metrics'),
                 ('dış A2 havuz (AF vs SR)', 7817, 3497, 'phase_xxxiii/results/a2_results.csv'),
                 ('dış B havuz (AF vs SR + diğer ritim)', 5477, 3497, 'phase_xxxiii/results/b_results.csv')],
        sample_size_note='Örneklem büyüklüğü hesaplanmadı; veri setinin uygun tüm kişileri kullanıldı (BULUNAMADI: önceden güç/kesinlik hesabı).',
        missing='Eğitim: yaş %1,7 eksik (HIPAA > 89 kodu), EKG öznitelikleri %0 (`training_protocol.json > missing_fraction`); '
                'eğitim fold\'u içi imputasyon (model pipeline\'ı). Dış: pipeline başarısızı birincil analizde dışlandı, '
                'duyarlılık analizinde FN/TN sayıldı.',
        split='Kişi düzeyi, PTB-XL resmî `strat_fold`: 1–8 fit, 9 validation, 10 test; kişi kesişimi 0 (bu fazda doğrulandı). '
              'Zamansal değil. Dış: Challenge 2021, farklı kaynaklar.',
        family=P21_SEL + ' Seçilen: LightGBM, HPO uygulandı; parametreler `selected_model_registry.json`.',
        imbalance=P21_IMB + ' Seçilen strateji: baseline (yeniden örnekleme yok).',
        threshold=P21_THR,
        calibration=P21_CAL + ' Seçilen: raw. Olasılık klinik olasılık değildir; pipeline sapması AF kayıtlarında olasılığı kaydırabilir.',
        subgroups_text='Dış doğrulamada kaynak başına sonuçlar performans tablosundadır (Georgia Recall 0,764). Diğer ritimlerde FPR: '
                       'sinüs taşikardisi 0,181, PVC 0,306, PAC 0,153 (`phase_xxxiii/results/b_rhythm_fpr.csv`). Yaş/cinsiyet '
                       'alt grup analizi bu karta alınmadı (BULUNAMADI: kilitli alt grup tablosu).',
        extra_limits=['Eğitim/iç test öznitelikleri PTB-XL+ golden, dış/uygulama öznitelikleri kilitli Octave pipeline; karar uyumu '
                      '0,99 (GA alt sınırı 0,946) — bkz. AF doğrulama belgesi.',
                      'PTB-XL ↔ Challenge kayıt düzeyi hash karşılaştırması yapılmadı; Challenge\'da hasta kimliği yok.'],
    ),
    'mi_model': dict(
        sources=['phase_xxxviii/PHASE_XXXVIII_REPORT.md', 'phase_xxxviii/01_cohort.md', 'phase_xxxviii/02_dev_cv.md',
                 'phase_xxxviii/03_test_results.md', 'phase_xxxviii/config/model_lock.json'],
        purpose='PTB-XL kaydında kardiyoloğun MI (eski/akut, EKG bulgusu) kodlamasının NORM kayıtlardan ayrımı. Troponin veya '
                'görüntülemeye dayalı MI tanısı değildir. Yalnız registry\'de (uygulamada yok).',
        data=[('geliştirme + iç test', f'{PTBXL}; öznitelikler: {PTBXLP} (168 lead bazlı + global)', 'tek kurum arşivi')],
        setting='Hastane EKG arşivi (tek kurum).',
        eligibility='İnsan doğrulamalı kayıtlar; hasta başına ilk doğrulanmış EKG; yaş ≥ 18 (300 → 90); MI süper sınıfı (14 kod, '
                    'INJ* dahil) vs yalnız NORM; tutarsız hastalar (herhangi bir kaydı MI, seçilen kaydı değil) negatiften dışlandı. '
                    'AF test kişileri ve parity kişileri testten dışlandı. Kaynak: `phase_xxxviii/01_cohort.md`.',
        target_method='PTB-XL SCP tanısal süper sınıfı (resmî `example_physionet.py` toplama kuralı; likelihood eşiği yok). '
                      'Kardiyolog EKG okuması; değerlendirici demografisi BULUNAMADI.',
        samples=[('geliştirme (fold 1–8)', 7230, 2037, 'phase_xxxviii/02_dev_cv.md'),
                 ('iç test (fold 9 + fold 10 AF-test dışı)', 1474, 521, 'phase_xxxviii/03_test_results.md'),
                 ('iç test temiz alt küme', 368, 160, 'aynı')],
        sample_size_note='Örneklem büyüklüğü hesaplanmadı; uygun tüm kayıtlar.',
        missing='Eksiklik `phase_xxxviii/results/t0_feature_missingness.csv`; `ST_Elev_missing` göstergesi modele girdi olarak eklendi. '
                'Eğitimde imblearn pipeline içi imputasyon.',
        split='Kişi düzeyi PTB-XL fold\'ları: 1–8 geliştirme, 9 + 10 test. Zamansal değil. Test kişilerinin 1.106\'sı AF eşik '
              'seçiminde kullanıldı (PREVIOUSLY_EXPOSED, başka hedef).',
        family=CV2 + ' Adaylar LR ve LightGBM; LightGBM − LR = +0,026 (≥ 0,01) → LightGBM (class_weight).',
        imbalance='class_weight (LightGBM).',
        threshold='Birincil: havuzlu OOF\'ta P ≥ 0,70 ve FPR ≤ 0,15 içinde en yüksek Recall (kilitli 0,0443). Bu kural eşiği FPR '
                  'sınırına dayatır (OOF FPR 0,149). İkincil (yalnız rapor): Recall ≥ 0,75 sağlayan en yüksek eşik 0,8634.',
        calibration='Uygulanmadı (ham skor; class_weight nedeniyle olasılık ölçeği kaymış).',
        subgroups_src='mi',
        extra_limits=['B2 operasyonel Q kuralı ters yönde çalıştı (AUC 0,31); geçerli kural baseline\'ı kurulamadı.'],
    ),
    'cad_DEVICE': dict(
        sources=['models/cad/DEVICE.json', 'results/cad_results.json', 'src/evaluation/metrics.py', 'phase_xxvii/02_baselines.md',
                 'phase_xli/01_cad_rescore.md', 'phase_xlii/ERRATA_CAD_V2.md'],
        purpose='Anjiyografiye yönlendirilmiş semptomatik hastada >%50 koroner daralma (UCI `num > 0`) olup olmadığını efor testi '
                've EKG bulgularıyla sınıflar. Genel nüfus taraması değildir.',
        data=[('geliştirme + iç test', f'{UCI}', 'Cleveland Clinic hastane kohortu; toplama tarihleri BULUNAMADI'),
              ('teknik tekrar', 'UCI Hungarian (n = 95) ve VA Long Beach (n = 64), eksiksiz vaka alt kümesi', 'önceden hatalı skorlanmış; PREVIOUSLY_EXPOSED')],
        setting='Hastane, anjiyografiye yönlendirilmiş hastalar (seçilmiş, eski kohort).',
        eligibility='UCI Cleveland 303 satır; kopya/çelişki 0; `ca`, `thal`, `num` girdi değil (`models/cad/DEVICE.json`).',
        target_method='Anjiyografik çap daralması > %50 (UCI `num > 0`); değerlendirici ve körleme bilgisi BULUNAMADI.',
        samples=[('fit', 181, 83, 'models/cad/DEVICE.json (n 303, pozitif 139; validation ve test 28\'er pozitif)'),
                 ('validation (eşik seçimi)', 61, 28, 'models/cad/DEVICE.json > validation'),
                 ('iç test', 61, 28, 'phase_xxvii/results/ci_metrics.csv'),
                 ('teknik tekrar Hungarian', 95, 68, 'phase_xli/results/cad_v2_rescore.json'),
                 ('teknik tekrar VA', 64, 54, 'aynı')],
        sample_size_note='Küçük örneklem (test n = 61); GA geniş. Örneklem büyüklüğü hesabı BULUNAMADI.',
        missing='Cleveland\'da eksik 0. Eğitim fold\'u içi imputasyon tanımlı; çıkarımda zorunlu girdi eksikse ABSTAIN. Teknik '
                'tekrar eksiksiz-vaka alt kümesidir (pozitif olmayan yaş/KB/kolesterol/kalp hızı eksik sayıldı).',
        split='Satır (kişi) düzeyi tabakalı rastgele bölme: önce %20 test, kalanın %25\'i validation (181/61/61); '
              '`src/training/train.py`, `random_state = SEED` (model meta verisinde seed 42). Zamansal değil.',
        family='Kök V2 eğitim kodu (`src/training/train.py`): aileler × stratejiler için fit kümesinde 3-fold GridSearchCV '
               '(amaç AP); her aday ham ve sigmoid-OOF olarak validation\'da değerlendirildi. Sıralama: P ≥ 0,70, R ≥ 0,75, '
               'FPR ≤ 0,15 sağlanıyorsa en yüksek validation AP, sağlanmıyorsa en yüksek F1; eşitlikte düşük Brier. Seçilen: LR '
               '(C = 0,1), strateji baseline, sigmoid-OOF (`models/cad/DEVICE.json`).',
        imbalance='Yok (baseline).',
        threshold='**Bu fazda bulundu:** kök V2 `src/evaluation/metrics.py :: choose_threshold` — validation\'da P ≥ 0,70, '
                  'R ≥ 0,75, FPR ≤ 0,15 sağlayan noktalar arasında en yüksek F1; yoksa tüm noktalarda en yüksek F1. Registry eşiği '
                  '0,5402 `results/cad_DEVICE_validation_thresholds.csv`\'de bu kuralın seçtiği satırla aynıdır (feasible = true).',
        calibration='Sigmoid (Platt), eğitim OOF; klinik olasılık değildir.',
        subgroups_text='İç testte alt grup analizi yok (n = 61; BULUNAMADI). Merkez bazında teknik tekrar sonuçları performans '
                       'tablosundadır.',
        extra_limits=['V2 dış sonuçları kategori kodlama hatası nedeniyle geçersizdi; yalnız Phase XLI düzeltilmiş teknik tekrar '
                      'geçerlidir (ERRATA_CAD_V2).'],
    ),
    'dm_A': dict(
        sources=['phase_xlii/PHASE_XLII_REPORT.md', 'phase_xlii/01_cohort.md', 'phase_xlii/02_dev_cv.md', 'phase_xlii/03_test_results.md'],
        purpose='Diyabet tanısı olmayan erişkinde tek ziyaret ölçümüyle teşhis edilmemiş diyabet (HbA1c ≥ %6,5 veya açlıkta FPG ≥ 126) '
                'olup olmadığını laboratuvarsız girdilerle sıralar. Tarama sıralayıcısıdır; ADA tanısı (doğrulama testi) değildir.',
        data=[('geliştirme', f'{NHANES}: E 2007–08, F 2009–10, I 2015–16, J 2017–18', 'ABD genel nüfus örneklemi'),
              ('iç test', f'{NHANES}: G 2011–12, H 2013–14', 'aynı program; kişi düzeyinde ayrık döngüler')],
        setting='ABD sivil, kurum dışı nüfusunun olasılık örneklemi (NHANES MEC muayenesi). Tasarım ağırlıkları kullanılmadı.',
        eligibility='Yaş ≥ 20, MEC muayenesi, gebe değil, HbA1c ölçülmüş; hariç: diyabet tanısı (DIQ010 = 1), DIQ010 7/9/eksik, '
                    'tanısız ama insülin/hap kullanan (`phase_xlii/01_cohort.md`).',
        target_method='HbA1c (laboratuvar) ≥ %6,5 veya geçerli açlık alt örnekleminde (8–24 sa) FPG ≥ 126 mg/dL; I/J\'de CDC C311→C501 '
                      'geri denklemi. Objektif laboratuvar ölçümü; tek ziyaret.',
        samples=[('geliştirme (E, F, I, J)', 17950, 829, 'phase_xlii/01_cohort.md'), ('iç test (G + H)', 8895, 389, 'aynı')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI; uygun tüm kişiler.',
        missing='Geliştirmede BMI %1,1, bel %4,4, KB %3,9, GDM %5,7 eksik; fold içinde medyan imputasyon. Uygulamada imputasyon '
                'yok: zorunlu alan eksikse ABSTAIN.',
        split='Kişi düzeyi, döngü bazlı (G+H test; diğerleri geliştirme). Zamansal değil. Test kişileri diyabet hedefinde yeni, '
              'başka hedeflerde görülmüş (PREVIOUSLY_EXPOSED_PERSONS).',
        family=CV2 + ' Adaylar LR ve LightGBM; seçim kuralı havuzlu OOF AUC (fark < 0,01 ise LR) → LR (class_weight, C = 0,0422).',
        imbalance='class_weight = balanced (skorlar yukarı kaymış; olasılık değildir).',
        threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,4959). İkincil: ADA ≥ 5 geliştirme yönlendirme '
                  'oranına eşlenen eşik (0,4704).',
        calibration='Uygulanmadı. Testte ort. skor gözlenen oranın çok üstünde (en üst %10: 0,806 → 0,158); sıralama monoton.',
        subgroups_src='dm_A',
        extra_limits=[],
    ),
    'htn_M1': dict(
        sources=['phase_xxxvii/PHASE_XXXVII_REPORT.md', 'phase_xxxvii/00_harmonization.md', 'phase_xxxvii/01_cohort.md',
                 'phase_xxxvii/02_dev_cv.md', 'phase_xxxvii/03_test_results.md'],
        purpose='Tek ziyarette ölçülen KB ≥ 140/90 veya antihipertansif ilaç kullanımı (mevcut durum) olup olmadığını, ölçülen '
                'tansiyonu girdi almadan sınıflar.',
        data=[('geliştirme', f'{NHANES}: P 2017–Mar 2020, L Ağu 2021–Ağu 2023', 'genel nüfus; oskilometrik KB'),
              ('zamansal test', f'{NHANES}: C 2003–04', 'auskültatuvar (cıvalı) KB; ölçüm yöntemi kaymalı')],
        setting='ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.',
        eligibility='Yaş ≥ 18, gebe değil, ≥ 2 geçerli KB okuması (> 0), BMI var; testte Phase21 işitme dış testindekiler hariç.',
        target_method='Ortalama SBP ≥ 140 veya DBP ≥ 90 (geçerli okumalar) veya ilaç kullanımı (öz bildirim). Test döngüsünde hekim, '
                      'geliştirmede cihaz ölçümü.',
        samples=[('geliştirme (P + L)', 13877, 5461, 'phase_xxxvii/01_cohort.md'), ('zamansal test (C)', 2798, 1001, 'aynı')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI.',
        missing='Testte sigara %16,3, alkol %23,1 eksik; geliştirmede öğrenilen medyan/mod ile dolduruldu. Uygulamada imputasyon yok.',
        split='Zamansal: geliştirme 2017–2023, test 2003–04; kişiler daha önce hiçbir hedefte kullanılmadı.',
        family=CV2 + ' LR (ROS) vs LightGBM; fark 0,0048 < 0,01 → LR (C = 0,027).',
        imbalance='RandomOverSampler (fold içi). Olasılıklar sistematik yüksek (gözlenen/tahmin 0,88).',
        threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,5397). İkincil: FPR ≤ 0,15 en düşük eşik (0,6459).',
        calibration='Uygulanmadı; testte eğim 1,02, kesişim −0,35, O/E 0,88.',
        subgroups_src='htn',
        extra_limits=[],
    ),
    'fibrosis_final': dict(
        sources=['phase_xxxi/PHASE_XXXI_REPORT.md', 'phase_xxxi/03_fibrosis_dev.md', 'phase_xxxi/04_fibrosis_test.md',
                 'phase_xxxi/config/protocol_fibrosis.md', 'phase_xlvi/01_reference_score_analysis.md'],
        purpose='FibroScan karaciğer sertliği (LSM) ≥ 8,0 kPa olup olmadığını rutin laboratuvar ve antropometriyle sınıflar '
                '(ileri değerlendirmeye yönlendirme sıralayıcısı). Histolojik fibrozis evresi değildir.',
        data=[('geliştirme', f'{NHANES}: P 2017–Mar 2020 (LUX FibroScan)', 'genel nüfus'),
              ('iç test', f'{NHANES}: L Ağu 2021–Ağu 2023', 'aynı program; L kişileri CAP hedefi için görülmüş (PREVIOUSLY_EXPOSED)')],
        setting='ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.',
        eligibility='Yaş ≥ 20, gebe değil, FibroScan tam (LUAXSTAT = 1), LSM var, FIB-4/NFS girdileri tam (ALT, AST, trombosit, '
                    'albümin, BMI). Açlık şartı yok (`phase_xxxi/results/fibrosis_eligibility_counts.json`).',
        target_method='VCTE (FibroScan) medyan LSM ≥ 8,0 kPa (AASLD 2023 bandı). Cihaz ölçümü; operatör bilgisi BULUNAMADI.',
        samples=[('geliştirme (P)', 6826, 697, 'phase_xxxi/results/fib_dev_summary.json (prevalans 0,1021)'),
                 ('iç test (L)', 4714, 587, 'phase_xxxi/results/fibrosis_test_results.csv')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI.',
        missing='Uygunluk ölçütü gereği FIB-4/NFS girdileri tam; diğer girdiler pipeline içi imputasyon. Uygulamada imputasyon yok.',
        split='Döngü bazlı (P geliştirme, L test); kişi düzeyi ayrık (SEQN kesişimi 0). Zamansal sıralı ama test önceden başka hedefte '
              'kullanılmış.',
        family=CV2 + ' Adaylar LR, LightGBM, XGBoost, CatBoost → CatBoost (strateji none).',
        imbalance='Seçilen ailede yok (none).',
        threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,85 sağlayan en yüksek eşik (0,0615); testte Recall 0,768 (hedef korunmadı). '
                  'İkincil (kilitli, raporlama): cinsiyete özgü eşikler; geliştirmede FIB-4 ≥ 1,3 Recall\'una eşlenmiş eşik.',
        calibration='Uygulanmadı (ham skor).',
        subgroups_src='fibrosis',
        extra_limits=['FIB-4 ve NFS biyopside ilerlemiş fibrozis için geliştirildi; buradaki hedef farklıdır (bkz. 01_reference_score_analysis.md).'],
    ),
    'osteo_final': dict(
        sources=['phase_xxx/PHASE_XXX_REPORT.md', 'phase_xxx/02_dev_results.md', 'phase_xxx/03_test_results.md',
                 'phase_xxx/config/protocol_osteo.md', 'phase_xxxi/01_osteo_clinical_utility.md',
                 'phase_xlvi/01_reference_score_analysis.md'],
        purpose='≥ 50 yaşta DXA femur T-skoru ≤ −2,5 (osteoporoz) olup olmadığını DXA\'sız girdilerle sıralar; DXA\'ya yönlendirme '
                'araştırması.',
        data=[('geliştirme', f'{NHANES}: D 2005–06, E 2007–08, F 2009–10, H 2013–14 (DXXFEM)', 'genel nüfus'),
              ('zamansal test', f'{NHANES}: J 2017–18', 'DXA etiketi projede ilk kez')],
        setting='ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.',
        eligibility='Yaş ≥ 50, DXA taranmış, geçerli femur boynu ve total femur ölçümü, kilo/boy tam (`phase_xxx/00_data_inventory.md` §3).',
        target_method='min(femur boynu, total femur) T ≤ −2,5; T = (BMD − μ)/σ, NHANES III 20–29 yaş Hispanik olmayan beyaz kadın '
                      'referansı (erkekte de). DXA cihaz ölçümü.',
        samples=[('geliştirme (D, E, F, H)', 8635, 566, 'phase_xxx/results/osteo_dev_summary.json (kadın 4174/455, erkek 4461/111)'),
                 ('zamansal test (J)', 2275, 164, 'phase_xxx/results/osteo_test_results.csv')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI. Erkekte test pozitif sayısı 31.',
        missing='Yapısal boşluklar (erkekte menopoz soruları) eğitimdeki imputasyon kuralıyla; kullanıcı yanıtsızsa ABSTAIN.',
        split='Zamansal: geliştirme 2005–2014, test 2017–18; kişi düzeyi ayrık.',
        family='Phase XXX protokolü: dış 5-fold kişi düzeyi CV, fold içi Optuna; aile seçimi ortalama dış PR-AUC (fark < 0,005 → daha '
               'basit) → LR (strateji none). Not: fold başına ayrı HPO nedeniyle havuzlu OOF ölçekleri karşılaştırılabilir değildi '
               '(`02_dev_results.md` yöntemsel not); cv_protocol_v2 bundan sonra yazıldı.',
        imbalance='Yok (none).',
        threshold='Havuzlu OOF\'ta Recall ≥ 0,85 sağlayan en yüksek eşik (0,0603); testte Recall 0,780.',
        calibration='Uygulanmadı; testte eğim 0,976, O/E 1,169 (Phase XXXI 01).',
        subgroups_src='osteo',
        extra_limits=['OST karşılaştırması ve OST\'nin özgün popülasyonu (postmenopozal Asyalı kadınlar): 01_reference_score_analysis.md.'],
    ),
    'ckd_A': dict(
        sources=['phase_xxxv/PHASE_XXXV_REPORT.md', 'phase_xxxv/01_cohort.md', 'phase_xxxv/02_dev_cv.md', 'phase_xxxv/03_test_results.md'],
        purpose='Böbrek hastalığı tanısı olmayan erişkinde tek ziyarette eGFR < 60 veya UACR ≥ 30 mg/g olup olmadığını laboratuvarsız '
                'girdilerle sıralar. KDIGO KBH tanısı (3 ay) değildir.',
        data=[('geliştirme', f'{NHANES}: E 2007–08, F 2009–10, G 2011–12, H 2013–14', 'genel nüfus'),
              ('iç test', f'{NHANES}: I 2015–16', 'aynı program; PREVIOUSLY_EXPOSED (başka hedef)')],
        setting='ABD genel nüfus örneklemi (NHANES). Tasarım ağırlıkları kullanılmadı.',
        eligibility='Yaş ≥ 20, MEC, kreatinin ve UACR var, gebe değil, diyaliz değil, KIQ022 = Hayır (`phase_xxxv/01_cohort.md`).',
        target_method='CKD-EPI 2021 (ırksız) eGFR < 60 veya UACR ≥ 30 mg/g; E-2007 kreatinin CDC Deming düzeltmeli dosya.',
        samples=[('geliştirme (E–H)', 20059, 3190, 'phase_xxxv/01_cohort.md'), ('iç test (I)', 4812, 716, 'aynı')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI.',
        missing='Fold içi medyan imputasyon (`dev_feature_missingness.csv`). Uygulamada imputasyon yok.',
        split='Döngü bazlı kişi düzeyi (I test); zamansal sıralı, ancak I kişileri başka hedeflerde dış test olarak görülmüş.',
        family=CV2 + ' LR vs LightGBM; fark 0,0184 ≥ 0,01 → LightGBM (strateji none).',
        imbalance='Yok (none).',
        threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,1266). İkincil: modifiye SCORED ≥ 4 '
                  'yönlendirme oranına eşlenmiş (0,1302).',
        calibration='Uygulanmadı (betimsel tablo `test_calibration.csv`).',
        subgroups_src='ckd_A',
        extra_limits=[],
    ),
    'copd_S4_DEVICE': dict(
        sources=['All_Disease_Improvement_Phase21/training_protocol.json', 'All_Disease_Improvement_Phase21/selected_model_registry.json',
                 'phase_xxvii/04_copd_temporal_validation.md', 'phase_xxvii/02_baselines.md'],
        purpose='Bronkodilatör testine alınmış (pre-BD obstrüksiyonlu) 40–79 yaş kişide post-BD FEV1/FVC < 0,70\'in sürüp sürmediğini '
                'sınıflar. Genel nüfusta KOAH taraması değildir.',
        data=[('geliştirme + iç test', f'{NHANES}: G 2011–12 (SPX)', 'BD testine seçilmiş alt grup'),
              ('zamansal tekrar', f'{NHANES}: F 2009–10, E 2007–08', 'aynı program, önceden raporlanmış (PREVIOUSLY_EXPOSED)')],
        setting='NHANES spirometri alt örneklemi; BD testine seçilmiş kişiler.',
        eligibility='40–79 yaş, pre-BD FEV1/FVC < LLN ve/veya < 0,70 nedeniyle BD testi yapılmış, ATS A/B kalitesinde.',
        target_method='Post-BD FEV1/FVC < 0,70 (sabit oran; ATS kaliteli spirometri). Klinik KOAH adjudikasyonu yok.',
        samples=[('fit', 108, 'BULUNAMADI', 'All_Disease_Improvement_Phase21/config/copd_splits.json (toplam 182, pozitif 97)'),
                 ('validation', 37, 20, 'selected_model_registry.json (BALANCED)'), ('iç test', 37, 20, 'phase_xxvii/results/ci_metrics.csv'),
                 ('zamansal F', 250, 156, 'aynı'), ('zamansal E', 274, 163, 'aynı')],
        sample_size_note='Çok küçük geliştirme (fit 108) ve iç test (37). Örneklem büyüklüğü hesabı BULUNAMADI.',
        missing='BMI %1,1 eksik (fit içi imputasyon); spirometri eksiksiz.',
        split='Kişi düzeyi rastgele fit/validation/test (G içinde); zamansal tekrar F ve E döngüleri.',
        family=P21_SEL + ' Seçilen: LR (L1, C = 4,98), HPO uygulandı.',
        imbalance=P21_IMB + ' Seçilen: baseline.',
        threshold=P21_THR,
        calibration=P21_CAL + ' Seçilen: raw.',
        subgroups_text='Alt grup analizi yok (küçük örneklem). Döngü bazlı sonuçlar (G, F, E) performans tablosundadır.',
        extra_limits=[],
    ),
    'hf_S2_BASIC_LAB': dict(
        sources=['All_Disease_Improvement_Phase21/training_protocol.json', 'All_Disease_Improvement_Phase21/selected_model_registry.json',
                 'phase_xxvii/02_baselines.md', 'phase_xxxix/PHASE_XXXIX_REPORT.md'],
        purpose='Kaynak veri setinde klinik kalp yetmezliği ile sağlıklı kontrolü RIP3 ELISA ve temel bilgilerle ayırır '
                '(vaka-kontrol). Yalnız registry\'de.',
        data=[('geliştirme + iç test', MEND, 'tek merkez vaka-kontrol; tarih aralığı BULUNAMADI')],
        setting='Hastane vaka-kontrol çalışması (HF hastaları vs sağlıklı gönüllüler).',
        eligibility='Kaynaktaki 184 uygun kişi (89 HF, 95 kontrol); yaş ≥ 18; LVEF/BNP/NYHA girdi değil.',
        target_method='Kaynak çalışmanın klinik HF grubu; adjudikasyon ayrıntıları kısmen yayımlanmış (BULUNAMADI).',
        samples=[('fit', 110, 'BULUNAMADI', 'heart_failure_splits.json (toplam 184, pozitif 89)'), ('validation', 37, 18, 'selected_model_registry.json'),
                 ('iç test', 37, 18, 'phase_xxvii/results/ci_metrics.csv')],
        sample_size_note='Çok küçük (test n = 37); GA çok geniş.',
        missing='BMI %5,4, sigara %1,6 eksik (fit içi imputasyon).',
        split='Kişi düzeyi rastgele (fit/validation/test 110/37/37).',
        family=P21_SEL + ' Seçilen: XGBoost, HPO yok.',
        imbalance=P21_IMB + ' Seçilen: baseline.',
        threshold=P21_THR,
        calibration=P21_CAL + ' Seçilen: sigmoid (Platt).',
        subgroups_text='Alt grup analizi yok (n = 37).',
        extra_limits=['Dış doğrulama yapılamadı: uyumlu RIP3 ölçümlü başka veri BULUNAMADI (Phase XXXIX).'],
    ),
    'anemia_LR16': dict(
        sources=['Clinical_Optimization_Phase25/00_MASTER_RESULTS.md', 'Clinical_Optimization_Phase25/development_protocol.json',
                 'Clinical_Optimization_Phase25/models/anemia_CBC_MATCHED16.json', 'phase_xl/02_anemia_external.md', 'phase_xxvii/02_baselines.md'],
        purpose='Uygun erişkinde düşük hemoglobini (erkek 20–65 Hb < 13; gebe olmayan kadın 20–44 Hb < 12 g/dL) Hb/Hct/MCH/MCHC '
                'kullanmadan hemogram ve biyokimyayla sınıflar. Demir eksikliği anemisi tanısı değildir.',
        data=[('geliştirme', f'{NHANES}: D 2005–06 (1.962 kişi, önceki geliştirme) + A 1999–2000', 'genel nüfus'),
              ('iç test', f'{NHANES}: A 1999–2000 holdout', 'önceden açılmış'),
              ('dış (aynı program)', f'{NHANES}: C 2003–04, E 2007–08, F 2009–10, I 2015–16', 'bağımsız kurum değil; PREVIOUSLY_EXPOSED (başka hedef)')],
        setting='ABD genel nüfus örneklemi (NHANES).',
        eligibility='Erkek 20–65, kadın 20–44 ve RIDEXPRG = 2 (gebe olmadığı doğrulanmış); gebeliği bilinmeyenler dışlandı.',
        target_method='Laboratuvar Hb eşiği; yükseklik/sigara düzeltmesi yok.',
        samples=[('fit (D + A)', 3298, 143, 'Clinical_Optimization_Phase25/00_MASTER_RESULTS.md §5'),
                 ('validation (A)', 444, 27, 'aynı'), ('iç test (A)', 410, 21, 'aynı'),
                 ('dış birleşik (C, E, F, I)', 11171, 669, 'phase_xl/results/anemia_external.json')],
        sample_size_note='Örneklem büyüklüğü hesabı BULUNAMADI; iç test pozitif sayısı 21.',
        missing='Fit içi imputasyon (Phase26 manifestinde kısmi eksikte dondurulmuş imputer); uygulamada katı kural: eksikse ABSTAIN.',
        split='Kişi düzeyi; A döngüsü içinde fit/validation/test; dış: farklı döngüler.',
        family='Phase25 protokolü (`development_protocol.json`): 3-fold StratifiedGroupKFold; fold içi ön işleme. LR16 "eş şemalı" '
               'karşılaştırma modeli testten önce ayrıca kaydedildi (önceden tanımlı ikincil; Phase26\'da dış birincil).',
        imbalance='Yok (baseline).',
        threshold='**Bu fazda bulundu:** Phase25 kuralı (`development_protocol.json > threshold`): validation\'da P ≥ 0,70, FPR ≤ 0,15, '
                  'TP ≥ 5 içinde en yüksek Recall; yoksa F2 − 0,5·FPR + 0,25·P. Registry eşiği (0,2703) '
                  '`anemia_CBC_MATCHED16.json` BALANCED senaryo eşiğiyle aynıdır.',
        calibration='Sigmoid (fit 3-fold OOF); klinik olasılık değildir.',
        subgroups_src='anemia',
        extra_limits=[],
    ),
}
SPEC['dm_B'] = dict(SPEC['dm_A'], purpose=SPEC['dm_A']['purpose'].replace('laboratuvarsız girdilerle', 'rutin laboratuvar eklenmiş girdilerle (TK, HDL, TG, ALT, ürik asit; HbA1c/glukoz girdi değil)'),
                    family=CV2 + ' Adaylar LR ve LightGBM → LR (class_weight, C = 0,0696).',
                    threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,5315). İkincil: ADA-eşleşmeli (0,4549).',
                    subgroups_src='dm_B')
SPEC['ckd_B'] = dict(SPEC['ckd_A'], purpose=SPEC['ckd_A']['purpose'].replace('laboratuvarsız girdilerle', 'rutin laboratuvar eklenmiş girdilerle (glukoz, HbA1c, TK, HDL, hemoglobin; kreatinin/UACR girdi değil)'),
                     family=CV2 + ' LR vs LightGBM; fark 0,0200 → LightGBM (strateji none).',
                     threshold='Birincil: havuzlu OOF\'ta Recall ≥ 0,75 sağlayan en yüksek eşik (0,1383). İkincil: SCORED-eşleşmeli (0,1295).',
                     subgroups_src='ckd_B')
