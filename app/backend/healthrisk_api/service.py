"""Sunucu durumu: registry/şema doğrulama, model yükleme (SHA256 önce), tahmin akışı.

Akış (/predict): alanlar -> birim dönüşümü -> aralık doğrulaması (422) -> model bazında: popülasyon uygunluğu ->
dönüşümler -> registry feature sırası -> tahmin -> yalnız eşik üstü/altı (olasılık DÖNÜLMEZ)."""
import importlib
import json
import re
import sys
import time

from . import eligibility as EL
from . import features as FT
from . import transforms as T
from .model_loader import load_model, sha256_file
from .paths import APP_CONFIG, MODELS_JSON, SCHEMA_JSON, V2
from .validation import ValidationError422, parse_unit_conversions, validate_fields

STATUS_OK, STATUS_ABSTAIN, STATUS_NA = 'OK', 'ABSTAIN', 'NOT_APPLICABLE'
TIER_LABEL = {'internal_test': 'iç test', 'temporal': 'zamansal doğrulama', 'external': 'dış doğrulama'}
_METRIC_KEYS = ('source', 'n', 'n_pos', 'precision', 'recall', 'fpr', 'auc', 'npv')


def evidence_summary(e):
    ev = e['evidence']
    out = dict(highest_tier=ev.get('highest_tier'), research_target_note=ev.get('research_target_note'), tiers={})
    for k, label in TIER_LABEL.items():
        t = ev.get(k)
        if not t:
            continue
        s = {m: t[m] for m in _METRIC_KEYS if m in t}
        s.update({m: v for m, v in t.items() if m.startswith('delta_auc')})
        s['tier_label'] = label
        out['tiers'][k] = s
    out['note'] = ('Kanıt düzeyleri ayrı tutulur (iç test / zamansal / dış doğrulama); metrikler registry\'den aynen '
                   'alınmıştır, uygulamada yeniden hesaplanmamıştır. CV sonuçları kanıt olarak gösterilmez.')
    return out


_COND = re.compile(r'^\s*([a-z0-9_]+)\s*(=|≥|>=)\s*([A-Za-z0-9_.\-]+)\s*$')


def parse_condition(text, fields):
    """Şemadaki ask_when / required_when metnini ("sex = female ve age_years ≥ 18") koşul listesine çevirir.
    Tanınmayan biçim -> ValueError (sessiz geçilmez)."""
    out = []
    for part in text.split(' ve '):
        m = _COND.match(part)
        if not m or m.group(1) not in fields:
            raise ValueError(f'ayrıştırılamayan koşul: {text!r}')
        f, op, v = m.groups()
        if op == '=':
            val = True if v == 'true' else False if v == 'false' else v
            out.append(dict(field=f, op='eq', value=val))
        else:
            out.append(dict(field=f, op='gte', value=float(v)))
    return out


def required_fields(mid, e, usage=None):
    tmap = {u['model_feature']: u['transform'] for u in (usage or [])}
    fs = []
    for f in e['features']:
        fs += T.TRANSFORM_FIELDS[tmap.get(f['name'], f['transform'])](f['input_field'])
    fs += EL.ELIGIBILITY_FIELDS.get(mid, [])
    req = [f for f in dict.fromkeys(fs) if not f.endswith('?')]
    cond = [f[:-1] for f in dict.fromkeys(fs) if f.endswith('?') and f[:-1] not in req]
    return dict(required=req, conditional=cond,
                note='conditional: yalnız ilgili soru geçerliyse sorulur (ask_when; ör. kadında GDM, tansiyon tanısı varsa ilaç)')


class Service:
    def __init__(self, load_models=True):
        self.started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.config = json.loads(APP_CONFIG.read_text(encoding='utf8'))
        self.global_problems = []
        for rel, h in self.config['registry_files_sha256'].items():
            got = sha256_file(V2 / rel)
            if got != h:
                self.global_problems.append(f'{rel} SHA256 beklenenden farklı ({got[:12]}…)')
        self.registry = json.loads(MODELS_JSON.read_text(encoding='utf8'))
        self.schema = json.loads(SCHEMA_JSON.read_text(encoding='utf8'))
        if self.registry.get('clinical_probability_eligibility') is not False:
            self.global_problems.append('registry clinical_probability_eligibility false değil')
        miss_t = set(self.schema['transforms']) ^ set(T.TRANSFORMS)
        if miss_t:
            self.global_problems.append(f'şema dönüşümleri ile uygulama uyuşmuyor: {sorted(miss_t)}')
        self.conversions = parse_unit_conversions(self.schema)
        self.extra_fields = {}                          # v2: uygunluk soruları şema fields içinde
        self.disclaimer = self.config['disclaimer_tr']
        self.module_labels = self.config['module_labels']
        self.changes = {}
        for ch in self.schema.get('changes_from_v1', []):
            self.changes.setdefault(ch['model'], []).append(ch)
        self.packages = self._packages()
        self.models = {}
        for mid, e in self.registry['models'].items():
            if not e.get('app_visible'):
                continue
            st = dict(entry=e, obj=None, enabled=False, problems=list(self.global_problems))
            usage = self.schema['model_usage'].get(mid)
            allowed = {(c['feature'], c['old_transform'], c['new_transform']) for c in self.changes.get(mid, [])}
            st['usage'] = usage
            st['problems'] += ['input_schema.model_usage kaydı yok'] if usage is None else FT.consistency_problems(e, usage, allowed)
            if e.get('clinical_probability_eligibility') is not False:
                st['problems'].append('model clinical_probability_eligibility false değil')
            if mid not in EL.RULES:
                st['problems'].append('uygunluk kuralı tanımlı değil')
            mp = V2 / e['model_file']['path']
            if not mp.exists():
                st['problems'].append('model dosyası yok')
            elif sha256_file(mp) != e['model_file']['sha256']:          # yüklemeden ÖNCE
                st['problems'].append('model dosyası SHA256 registry ile uyuşmuyor')
            if not st['problems'] and load_models:
                try:
                    st['obj'] = load_model(e['model_file']['path'], e['runtime']['extra_sys_path_for_pickle'])
                except Exception as ex:
                    st['problems'].append(f'yükleme hatası: {type(ex).__name__}: {ex}')
            st['enabled'] = st['obj'] is not None and not st['problems']
            self.models[mid] = st
        self.groups = {}
        for mid, st in self.models.items():
            self.groups.setdefault(st['entry']['disease_key'], []).append(mid)
        from .ecg_af import AFPipeline
        self.af = AFPipeline()

    # ------------------------------------------------------------------ durum
    def _packages(self):
        exp = self.config['expected_packages']
        cur = {'python': sys.version.split()[0]}
        for k in exp:
            if k == 'python':
                continue
            try:
                cur[k] = importlib.import_module(k).__version__
            except Exception:
                cur[k] = None
        mism = {k: dict(expected=exp[k], installed=cur.get(k)) for k in exp if cur.get(k) != exp[k]}
        if mism:
            self.global_problems.append(f'paket sürümleri beklenenden farklı: {json.dumps(mism)}')
        return dict(installed=cur, expected=exp, ok=not mism)

    def health(self):
        ms = [dict(model_id=m, enabled=s['enabled'], problems=s['problems']) for m, s in self.models.items()]
        ok = all(s['enabled'] for s in self.models.values()) and self.af.enabled and not self.global_problems
        return dict(status='ok' if ok else 'degraded', started_utc=self.started_utc, phase='XLIV',
                    schema_version=self.schema['schema_version'],
                    registry=dict(files=self.config['registry_files_sha256'], problems=self.global_problems),
                    packages=self.packages, runtime=self.config['runtime'], models=ms,
                    disabled_models=[m['model_id'] for m in ms if not m['enabled']],
                    af_pipeline=self.af.status(), clinical_probability_eligibility=False,
                    note='Yalnız localhost. Model olasılığı hiçbir uç noktada dönülmez.')

    def models_public(self):
        out = []
        for mid, st in self.models.items():
            e = st['entry']
            out.append(dict(model_id=mid, disease=e['disease'], disease_key=e['disease_key'], role=e['role'],
                            app_mode=e['app_mode'], module_label=self.module_label(mid), enabled=st['enabled'],
                            schema_v2_changes=[{k: c[k] for k in ('feature', 'old_transform', 'new_transform', 'reason')}
                                               for c in self.changes.get(mid, [])],
                            endpoint='/ecg/af' if mid == 'af_S4_DEVICE' else '/predict',
                            fields=required_fields(mid, e, st['usage']), target_definition=e['target_definition'],
                            population=e['population'], missing_input_rule=e['missing_input_rule'],
                            evidence=evidence_summary(e), limitations=e['limitations'],
                            clinical_probability_eligibility=False))
        return dict(models=out, note='Yalnız app_visible=true modeller. Kararlar "araştırma sınıflaması"dır.')

    def _form_section(self, name, spec, form_input):
        """Form bölümü (Phase XLV sunum kuralı; app_config.json > form). Model mantığını etkilemez."""
        if not form_input:
            return None
        rules = self.config['form']['section_rules']
        src = spec.get('input_source')
        if name in rules['temel_fields']:
            return 'temel'
        if src in rules['laboratuvar_sources']:
            return 'laboratuvar'
        if src in rules['klinik_sources']:
            return 'klinik'
        if src == 'kullanici' and spec.get('unit') in rules['olcumler_units']:
            return 'olcumler'
        if src == 'kullanici':
            return 'oyku'
        return 'diger'

    def schema_public(self):
        fields = {}
        for k, v in self.schema['fields'].items():
            src = str(v.get('input_source', ''))
            fi = not (v['type'] == 'device' or src.startswith('ecg_pipeline'))
            fields[k] = dict(v, form_input=fi, form_section=self._form_section(k, v, fi))
            for key in ('ask_when', 'required_when'):
                if key in v:
                    fields[k][key + '_rule'] = parse_condition(v[key], self.schema['fields'])
        units = {}
        for (f, u), c in self.conversions.items():
            units.setdefault(f, []).append(dict(from_unit=u, to_unit=c['to_unit'], op=c['op']))
        return dict(schema_version=self.schema['schema_version'], policy=self.schema['policy'], fields=fields,
                    changes_from_v1=self.schema.get('changes_from_v1', []),
                    known_limitations_v2=self.schema.get('known_limitations_v2', []),
                    unit_conversions=units, unit_conversion_note=self.schema['unit_conversion_note'],
                    request_format={'fields': {'<alan>': '<değer> veya {"value": <sayı>, "unit": "<birim>"}'}},
                    models={m: required_fields(m, s['entry'], s['usage']) for m, s in self.models.items()},
                    form=dict(sections=self.config['form']['sections'],
                              category_labels_tr=self.config['form']['category_labels_tr'],
                              virtual_field_labels_tr=self.config['form']['virtual_field_labels_tr'],
                              rule_note='ask_when_rule / required_when_rule: koşulların tümü (VE) sağlanınca soru '
                                        'gösterilir / zorunludur; şemadaki metinden sunucuda ayrıştırıldı.'))

    # ------------------------------------------------------------------ tahmin
    def module_label(self, mid):
        return self.module_labels.get(mid, self.module_labels['_default'])

    def _base(self, mid):
        e = self.models[mid]['entry']
        return dict(model_id=mid, disease=e['disease'], disease_key=e['disease_key'], role=e['role'],
                    app_mode=e['app_mode'], module_label=self.module_label(mid), status=None, reasons=[], missing_fields=[], unknown_categories=[],
                    decision=None, evidence=evidence_summary(e), limitations=e['limitations'],
                    clinical_probability_eligibility=False)

    def feature_vector(self, mid, F):
        """Parity testleri için: sunucunun ürettiği feature sonucu (tahmin YOK)."""
        return FT.build(self.models[mid]['entry'], F, self.models[mid]['usage'])

    def precheck(self, mid, F):
        """Tahmin ÖNCESİ adımlar (uygunluk + dönüşüm + eksik/kategori kontrolü). Model ÇALIŞTIRILMAZ.
        Döner: (r, fr). r['status'] None ise model çalışabilir durumdadır; değilse ABSTAIN / NOT_APPLICABLE.
        /predict ve /eligibility aynı işlevi kullanır (panel ile sonuç ekranı tutarlı kalır)."""
        st = self.models[mid]
        r = self._base(mid)
        if not st['enabled']:
            r['status'] = STATUS_ABSTAIN
            r['reasons'] = ['model devre dışı: ' + '; '.join(st['problems'])]
            return r, None
        na, ab, emiss = EL.check(mid, F)
        fr = FT.build(st['entry'], F, st['usage'])
        if na or fr.not_applicable:
            r['status'] = STATUS_NA
            r['reasons'] = na + fr.not_applicable
            return r, fr
        if ab or emiss or fr.missing or fr.unknown or fr.internal:
            r['status'] = STATUS_ABSTAIN
            r['missing_fields'] = list(dict.fromkeys(emiss + fr.missing))
            r['unknown_categories'] = [dict(field=f, value=v) for f, v in fr.unknown]
            r['reasons'] = ab + (['eksik zorunlu alan(lar): ' + ', '.join(r['missing_fields'])] if fr.missing else []) \
                + [f'şemada olmayan kategori: {f}={v}' for f, v in fr.unknown] + [f'iç tutarlılık: {x}' for x in fr.internal]
            if any(f == 'race_ethnicity' for f in fr.missing):
                r['reasons'].append('ırk/etnik köken yanıtsız: policy.optional_race gereği varsayılan sınıf atanmaz')
            return r, fr
        return r, fr

    def predict_model(self, mid, F):
        st = self.models[mid]
        e = st['entry']
        r, fr = self.precheck(mid, F)
        if r['status'] is not None:
            return r
        X = FT.to_frame(e, fr.values)
        thr = float(e['thresholds']['primary']['value'])
        above = bool(float(st['obj'].predict_proba(X)[0, 1]) >= thr)   # olasılık saklanmaz/dönülmez
        r['status'] = STATUS_OK
        r['decision'] = dict(
            research_class='ESIK_USTU' if above else 'ESIK_ALTI',
            label_tr=('Eşik üstü' if above else 'Eşik altı') + ' — araştırma sınıflaması (klinik karar değildir)',
            threshold='birincil donmuş eşik (registry; değiştirilmez)', threshold_rule=e['thresholds']['primary']['rule'])
        if fr.structural_blank:
            r['reasons'].append('yapısal boşluk (eğitimdeki tanım, eksik sayılmaz): ' + ', '.join(fr.structural_blank))
        return r

    def target_warnings(self, dkey, F):
        w = []
        def add(fields, msg):
            w.append(dict(code='TARGET_DEFINING_INPUT', fields=fields,
                          message_tr=msg + ' Bu durumda model yerine doğrudan klinik eşik kullanın.'))
        if dkey == 'diabetes':
            fs = [f for f in ('hba1c_pct', 'glucose_fasting_mgdl') if F.get(f) is not None]
            if fs:
                add(fs, 'Diyabet hedefini tanımlayan ölçüm girildi (HbA1c / açlık plazma glukozu).')
        elif dkey == 'hypertension':
            pairs = [(F.get(f'sbp_{i}_mmhg'), F.get(f'dbp_{i}_mmhg')) for i in (1, 2, 3)]
            s = [a for a, _ in pairs if a is not None]
            d = [b for _, b in pairs if b is not None]
            if (s and sum(s) / len(s) >= 140) or (d and sum(d) / len(d) >= 90):
                add([f for i in (1, 2, 3) for f in (f'sbp_{i}_mmhg', f'dbp_{i}_mmhg') if F.get(f) is not None],
                    'Ölçülen tansiyon ortalaması ≥ 140/90 mmHg (hipertansiyon hedefini tanımlar).')
            if F.get('on_bp_medication') is True:
                add(['on_bp_medication'], 'Tansiyon ilacı kullanımı hipertansiyon hedef tanımının parçasıdır.')
        elif dkey == 'anemia':
            if F.get('hemoglobin_gdl') is not None:
                add(['hemoglobin_gdl'], 'Anemi hedefini tanımlayan hemoglobin değeri girildi.')
        elif dkey == 'kidney':
            fs = [f for f in ('creatinine_mgdl', 'urine_albumin_mgl', 'urine_creatinine_mgdl') if F.get(f) is not None]
            if 'creatinine_mgdl' in fs or {'urine_albumin_mgl', 'urine_creatinine_mgdl'} <= set(fs):
                add(fs, 'Böbrek hedefini tanımlayan ölçüm girildi (kreatinin → eGFR ve/veya idrar albümin/kreatinin → UACR).')
        return w

    def predict(self, raw_fields):
        F, notes = validate_fields(raw_fields, self.schema, self.extra_fields, self.conversions)
        results = []
        for dkey, ids in self.groups.items():
            if dkey == 'af':
                for mid in ids:
                    r = self._base(mid)
                    r['status'] = STATUS_NA
                    r['reasons'] = ['AF modeli yalnız EKG kaydı yüklenerek çalışır: POST /ecg/af (kilitli AF-ECGDELI-OCTAVE-v1)']
                    r['warnings'] = []
                    results.append(r)
                continue
            prim = [m for m in ids if self.models[m]['entry']['role'].startswith('primary')]
            sec = [m for m in ids if self.models[m]['entry']['role'].startswith('secondary')]
            if sec:
                rb = self.predict_model(sec[0], F)
                if rb['status'] == STATUS_OK:
                    r = rb
                    r['selected_over'] = prim[0] if prim else None
                else:
                    r = self.predict_model(prim[0], F)
                    r['fallback_from'] = dict(model_id=sec[0], status=rb['status'], reasons=rb['reasons'],
                                              missing_fields=rb['missing_fields'],
                                              note='B modeli (laboratuvarlı) çalışmadı; birincil A modeline düşüldü')
            else:
                r = self.predict_model(prim[0], F)
            r['warnings'] = self.target_warnings(dkey, F)
            results.append(r)
        return dict(results=results, unit_conversion_notes=notes, clinical_probability_eligibility=False,
                    note='Kararlar donmuş eşiğe göre "araştırma sınıflaması"dır; model olasılığı klinik olasılık değildir ve dönülmez.')

    # ------------------------------------------------------------------ uygunluk (Phase XLV; model ÇALIŞTIRMAZ)
    def validate_partial(self, raw_fields):
        """Canlı form için: alan hatalarını 422 yerine liste olarak döner, hatalı alanları dışarıda bırakıp kalanı
        doğrular. Aynı validate_fields kullanılır (birim dönüşümü ve aralık tek kaynak)."""
        if not isinstance(raw_fields, dict):
            raise ValidationError422([dict(loc=['fields'], msg='fields bir nesne olmalı')])
        raw, errors = dict(raw_fields), []
        for _ in range(len(raw) + 2):
            try:
                F, notes = validate_fields(raw, self.schema, self.extra_fields, self.conversions)
                return F, notes, errors
            except ValidationError422 as ex:
                bad = set()
                for e in ex.errors:
                    loc = e.get('loc', [])
                    name = loc[1] if len(loc) > 1 else None
                    errors.append(dict(field=name, msg=e['msg']))
                    if name is not None:
                        bad.add(name)
                if not bad:
                    return {}, [], errors
                for b in bad:
                    raw.pop(b, None)
        return {}, [], errors

    def af_unavailable_reason(self):
        """AF pipeline devre dışıyken panelde gösterilecek kısa gerekçe (ayrıntı: af.problems)."""
        env_missing = any(p.startswith(('Octave/ECGDeli AF çalışma ortamı yok', 'Octave yok')) for p in self.af.problems)
        return ('Octave/ECGDeli AF çalışma ortamı yok' if env_missing
                else 'AF pipeline devre dışı: kilit/SHA256 doğrulaması başarısız')

    def eligibility(self, raw_fields):
        """app_visible her model için durum: READY (çalışabilir) / MISSING (eksik alan veya yanıtsız uygunluk sorusu) /
        OUT_OF_SCOPE (popülasyon dışı) / ABSTAIN (diğer: bilinmeyen kategori, gebelik 'bilmiyorum', model devre dışı).
        Tahmin YAPILMAZ, olasılık/eşik kullanılmaz."""
        F, notes, errors = self.validate_partial(raw_fields)
        out = []
        for mid, st in self.models.items():
            r, fr = self.precheck(mid, F)
            ecg = mid == 'af_S4_DEVICE'
            miss = list(r['missing_fields'])
            if ecg:
                had_ecg = any(m.startswith('ecg_af_') for m in miss)
                miss = [m for m in miss if not m.startswith('ecg_af_')]
                if r['status'] is None or (r['status'] == STATUS_ABSTAIN and had_ecg):
                    miss.append('ecg_record')            # EKG kaydı yalnız /ecg/af ile yüklenir
            if r['status'] == STATUS_NA:
                state = 'OUT_OF_SCOPE'
            elif r['status'] is None and not miss:
                state = 'READY'
            elif miss:
                state = 'MISSING'
            else:
                state = 'ABSTAIN'
            reasons = [x for x in r['reasons'] if not (ecg and x.startswith('eksik zorunlu alan'))]
            details = []
            if ecg and not self.af.enabled:
                # Phase XLVI: AF çalışma ortamı (kilit, pipeline, Octave, ECGDeli) yoksa veya doğrulanamıyorsa EKG
                # yüklense de karar üretilemez. Panel "Eksik: EKG kaydı" yerine "Karar verilemez" göstermelidir.
                state, miss = 'ABSTAIN', []
                reasons = [self.af_unavailable_reason()] + [x for x in r['reasons'] if x.startswith('model devre dışı')]
                details = list(self.af.problems)
            elif ecg and state == 'MISSING' and 'ecg_record' in miss:
                reasons.append('AF modeli yalnız EKG kaydı (.hea + .dat/.mat) yüklenerek çalışır: POST /ecg/af')
            item = dict(model_id=mid, disease=r['disease'], disease_key=r['disease_key'], role=r['role'],
                        app_mode=r['app_mode'], module_label=r['module_label'], endpoint='/ecg/af' if ecg else '/predict',
                        state=state, missing_fields=miss, unknown_categories=r['unknown_categories'], reasons=reasons,
                        details=details)
            if ecg:
                item['af_pipeline_available'] = bool(self.af.enabled)
            out.append(item)
        warnings = []
        for dkey in self.groups:
            for w in self.target_warnings(dkey, F):
                warnings.append(dict(w, disease_key=dkey))
        return dict(models=out, field_errors=errors, unit_conversion_notes=notes, warnings=warnings,
                    clinical_probability_eligibility=False,
                    note='Yalnız uygunluk/eksik alan durumu; model çalıştırılmaz, karar üretilmez.')

    def predict_af(self, header_name, header_bytes, signal_name, signal_bytes, raw_fields):
        F, notes = validate_fields(raw_fields, self.schema, self.extra_fields, self.conversions)
        mid = 'af_S4_DEVICE'
        r = self._base(mid)
        feats, info = self.af.extract(header_name, header_bytes, signal_name, signal_bytes)
        r['pipeline'] = dict(version=info['pipeline_version'], pre_step='ilk 10 sn (Phase XXIX/XXXIII read_first10s, birebir)',
                             record_samples=info.get('record_samples'), window=info.get('window'),
                             octave_seconds=info.get('octave_seconds'),
                             wall_seconds=info.get('wall_seconds'))
        if feats is None:
            r['status'] = STATUS_ABSTAIN
            r['reasons'] = [f'EKG pipeline başarısız: {info["abstain_reason"]}']
            r['busy'] = bool(info.get('busy'))
            if info.get('display'):
                r['display'] = info['display']
            return r, None
        import math
        nan = [k for k, v in feats.items() if v is None or (isinstance(v, float) and math.isnan(v))]
        F2 = dict(F)
        F2.update({f'ecg_af_{k}': v for k, v in feats.items() if k not in nan})
        r2 = self.predict_model(mid, F2)
        r2['pipeline'] = r['pipeline']
        if info.get('display'):
            r2['display'] = info['display']
        if nan:
            r2['reasons'].insert(0, 'pipeline şu feature(lar)ı üretemedi (NaN): ' + ', '.join(nan))
        r2['warnings'] = []
        return r2, feats
