"""Phase XLVII: arayüz metin katmanı (app_config.json > form.field_ui_tr ve ui). Yalnız sunum; model mantığı sınanmaz.

Denetlenenler: her form alanının sade etiketi var ve etiket/yardım metninde kaynak değişken kodu (NHANES/UCI) yok;
kodlar yalnız 'source' (teknik ayrıntı) içinde. Terim sözlüğü tüm durum kodlarını kapsar. Her görünür model ve hastalık
için ad, kanıt açıklaması ve 'Ne yapmalıyım?' metni var; yönlendirmeler tedavi önerisi içermez."""
import re

CODE_RE = re.compile(r'\b(NHANES|UCI|RIDRETH\w*|[A-Z]{3}\d{3}[A-Z]?|cp|restecg|oldpeak|thalach|exang)\b')


def _schema(client):
    return client.get('/schema').json()


def test_schema_exposes_ui_layers(client, service):
    s = _schema(client)
    assert s['ui'] == service.config['ui']
    assert s['form']['field_ui_tr'] == service.config['form']['field_ui_tr']


def test_every_form_field_has_plain_label_without_source_codes(client):
    s = _schema(client)
    ui = s['form']['field_ui_tr']
    form_fields = [k for k, v in s['fields'].items() if v['form_input']]
    assert set(form_fields) == set(ui), set(form_fields) ^ set(ui)
    for k in form_fields:
        lab, hlp = ui[k]['label'], ui[k].get('help', '')
        assert lab.strip(), k
        assert not CODE_RE.search(lab) and not CODE_RE.search(hlp), (k, lab, hlp)
        assert k not in lab and k not in hlp, k                      # ham alan adı etikette yok


def test_source_codes_only_from_schema_text(client):
    """'source' içindeki NHANES değişken kodları şema metninde (label_tr/note) geçen kodlardır (uydurma kod yok)."""
    s = _schema(client)
    for k, u in s['form']['field_ui_tr'].items():
        if 'source' not in u or not u['source'].startswith('NHANES'):
            continue
        spec = s['fields'][k]
        text = spec['label_tr'] + ' ' + str(spec.get('note', ''))
        for code in re.findall(r'[A-Z]{3}\d{3}[A-Z]?|RIDRETH1', u['source']):
            assert code in text, (k, code)


def test_terms_cover_all_states(client):
    t = _schema(client)['ui']['terms_tr']
    assert set(t['eligibility']) == {'READY', 'MISSING', 'OUT_OF_SCOPE', 'ABSTAIN'}
    assert set(t['result']) == {'OK', 'ABSTAIN', 'NOT_APPLICABLE'}
    assert set(t['decision']) == {'ESIK_USTU', 'ESIK_ALTI'}
    assert set(t['tiers']) == {'internal_test', 'temporal', 'external'}
    assert t['result']['ABSTAIN'] == 'Sonuç üretilmedi'
    assert t['result']['NOT_APPLICABLE'] == 'Bu analiz size uygun değil'
    for group in t.values():
        for v in group.values():
            assert not re.search(r'[A-Z]{2,}_[A-Z]{2,}|ABSTAIN|NOT_APPLICABLE', v), v


def test_model_and_disease_texts_complete(client):
    s = _schema(client)
    ui = s['ui']
    ms = client.get('/models').json()['models']
    for m in ms:
        assert m['model_id'] in ui['model_names_tr'], m['model_id']
        assert m['model_id'] in ui['evidence_plain_tr'], m['model_id']
        assert m['disease_key'] in ui['disease_names_tr'], m['disease_key']
        assert m['disease_key'] in ui['disease_hints_tr'], m['disease_key']
        assert m['model_id'] not in ui['evidence_plain_tr'][m['model_id']]
    assert {g['module_label'] for g in ui['analysis_groups_tr']} >= {m['module_label'] for m in ms}


def test_next_steps_are_guidance_not_treatment(client):
    ns = _schema(client)['ui']['next_steps_tr']
    assert set(ns['_default']) == {'ESIK_USTU', 'ESIK_ALTI', 'ABSTAIN', 'NOT_APPLICABLE'}
    assert 'dışlamaz' in ns['_default']['ESIK_ALTI']
    assert 'FibroScan' in ns['liver_fibrosis']['ESIK_USTU']
    for dk, d in ns.items():
        for k, v in d.items():
            assert k in ns['_default'], (dk, k)
            assert 'hekim' in v or 'EKG' in v, (dk, k, v)
            assert not re.search(r'tedavi|ilaç(ı|ını)? (başla|kullan|al)|tanınız|tanı(sı)? konul', v, re.I), (dk, k, v)


def test_ui_texts_do_not_touch_model_logic(service):
    """Metin katmanı eşik/olasılık/uygunluk alanı içermez."""
    flat = repr(service.config['ui']) + repr(service.config['form']['field_ui_tr'])
    for bad in ('threshold', 'predict_proba', 'eligibility_rule'):
        assert bad not in flat
