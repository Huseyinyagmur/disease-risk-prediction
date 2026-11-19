"""Model bazında popülasyon uygunluğu (models.json: population, missing_input_rule metinlerinin kodlanmış hali).

Sonuç: (not_applicable_reasons, abstain_reasons, missing_fields).
  * Belirlenebilir ve uygunsuz -> NOT_APPLICABLE (eksik alanlardan bağımsız).
  * Uygunluk sorusu yanıtsız -> ABSTAIN (varsayım yapılmaz).
Yaş sınırları ham yaşla (age_years) kontrol edilir; model girdi aralıkları (allowed_range) ayrıca feature düzeyinde
kontrol edilir (features.py). Gebelik/böbrek tanısı/diyaliz soruları şema v2 fields içindedir (model feature'ı değildir).
Gebelik sorusu yalnız kadının yaşı ilgili modelin yaş aralığındaysa değerlendirilir (aralık dışı zaten NOT_APPLICABLE)."""
from .transforms import Invalid


class _Ctx:
    def __init__(self, F):
        self.F, self.na, self.ab, self.miss = F, [], [], []

    def get(self, name):
        v = self.F.get(name)
        if isinstance(v, Invalid):
            self.ab.append(f'{name}: şemada olmayan değer {v.raw!r}')
            return None
        if v is None:
            self.miss.append(name)
        return v

    def age_between(self, lo, hi, label):
        a = self.get('age_years')
        if a is None:
            self.ab.append('yaş yanıtsız: popülasyon uygunluğu doğrulanamıyor')
            return
        if (lo is not None and a < lo) or (hi is not None and a > hi):
            self.na.append(f'yaş {a:g} model popülasyonu dışında ({label})')

    def sex(self):
        s = self.get('sex')
        if s is None:
            self.ab.append('cinsiyet yanıtsız: popülasyon uygunluğu doğrulanamıyor')
        return s

    def not_pregnant(self):
        s = self.sex()
        if s == 'female':
            p = self.get('pregnant')
            if p is None:
                self.ab.append('gebelik durumu yanıtsız (kadın; zorunlu soru): popülasyon "gebe değil" doğrulanamıyor')
            elif p == 'unknown':
                self.ab.append('gebelik durumu "bilmiyorum": popülasyon "gebe değil" doğrulanamıyor (katı yorum)')
            elif p is True:
                self.na.append('gebe: model popülasyonu gebe olmayan kişilerdir')


def _dm(c):
    c.age_between(20, None, '≥ 20')
    c.not_pregnant()
    told = c.get('told_diabetes')
    if told is None:
        c.ab.append('diyabet tanısı sorusu yanıtsız: model yalnız tanısız kişide geçerli')
    elif told is True:
        c.na.append('diyabet tanısı var: model yalnız diyabet tanısı almamış kişide geçerli (doğrudan klinik izlem)')
    else:
        # on_insulin/on_diabetes_pills yalnız told_diabetes=true iken sorulur (ask_when); yanıtsızlık eksik sayılmaz
        if c.F.get('on_insulin') is True or c.F.get('on_diabetes_pills') is True:
            c.na.append('diyabet ilacı/insülin kullanımı: eğitimde tanısız ama ilaç kullananlar dışlandı')


def _ckd(c):
    c.age_between(20, None, '≥ 20')
    c.not_pregnant()
    k = c.get('told_weak_failing_kidneys')
    if k is None:
        c.ab.append('"doktor zayıf/başarısız böbrek dedi mi" yanıtsız: model yalnız farkında olmayan kişide geçerli')
    elif k is True:
        c.na.append('tanılı böbrek hastalığı: model yalnız böbrek hastalığı tanısı olmayan kişide geçerli')
    d = c.F.get('on_dialysis')
    if d is True:
        c.na.append('diyaliz: model popülasyonu dışında')
    elif isinstance(d, Invalid):
        c.ab.append(f'on_dialysis: şemada olmayan değer {d.raw!r}')


def _htn(c):
    c.age_between(18, None, '≥ 18')
    c.not_pregnant()


def _fib(c):
    c.age_between(20, None, '≥ 20')
    c.not_pregnant()


def _osteo(c):
    c.age_between(50, None, '≥ 50')


def _anemia(c):
    s = c.sex()
    a = c.get('age_years')
    if a is None:
        c.ab.append('yaş yanıtsız: popülasyon uygunluğu doğrulanamıyor')
    elif s == 'male' and not (20 <= a <= 65):
        c.na.append(f'yaş {a:g}: erkekte model popülasyonu 20–65')
    elif s == 'female':
        if not (20 <= a <= 44):
            c.na.append(f'yaş {a:g}: kadında model popülasyonu 20–44 (gebe olmayan)')
        else:
            c.not_pregnant()


def _copd(c):
    c.age_between(40, 79, '40–79')
    fev1, fvc = c.F.get('fev1_pre_ml'), c.F.get('fvc_pre_ml')
    if fev1 is not None and fvc is not None and fev1 / fvc >= 0.70:
        c.na.append(f'pre-BD FEV1/FVC = {fev1 / fvc:.3f} ≥ 0,70: model yalnız obstrüksiyonlu (bronkodilatör testi yapılmış) alt grupta geçerli')


def _cad(c):
    c.age_between(20, 100, '20–100 (model girdi aralığı)')


def _af(c):
    c.age_between(18, 89, '18–89')


RULES = {'dm_A': _dm, 'dm_B': _dm, 'ckd_A': _ckd, 'ckd_B': _ckd, 'htn_M1': _htn, 'fibrosis_final': _fib,
         'osteo_final': _osteo, 'anemia_LR16': _anemia, 'copd_S4_DEVICE': _copd, 'cad_DEVICE': _cad,
         'af_S4_DEVICE': _af}

ELIGIBILITY_FIELDS = {
    'dm_A': ['age_years', 'sex', 'pregnant?', 'told_diabetes', 'on_insulin?', 'on_diabetes_pills?'],
    'dm_B': ['age_years', 'sex', 'pregnant?', 'told_diabetes', 'on_insulin?', 'on_diabetes_pills?'],
    'ckd_A': ['age_years', 'sex', 'pregnant?', 'told_weak_failing_kidneys', 'on_dialysis?'],
    'ckd_B': ['age_years', 'sex', 'pregnant?', 'told_weak_failing_kidneys', 'on_dialysis?'],
    'htn_M1': ['age_years', 'sex', 'pregnant?'], 'fibrosis_final': ['age_years', 'sex', 'pregnant?'],
    'osteo_final': ['age_years'], 'anemia_LR16': ['age_years', 'sex', 'pregnant?'],
    'copd_S4_DEVICE': ['age_years', 'fev1_pre_ml', 'fvc_pre_ml'], 'cad_DEVICE': ['age_years'], 'af_S4_DEVICE': ['age_years'],
}


def check(model_id, F):
    c = _Ctx(F)
    rule = RULES.get(model_id)
    if rule is None:
        return ['bu model için uygunluk kuralı tanımlı değil (uygulamaya bağlı değil)'], [], []
    rule(c)
    # yalnız uygunluk sorusu olan yanıtsız alanlar raporlanır; ana feature eksikleri features.py'de
    miss = [m for m in dict.fromkeys(c.miss) if m in ('pregnant', 'told_diabetes', 'told_weak_failing_kidneys')]
    return c.na, c.ab, miss
