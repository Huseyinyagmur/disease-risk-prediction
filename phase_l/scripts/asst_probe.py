"""Phase L madde 8: asistan yanıt hatası yoklaması (debug: ham LLM çıktısı + erişilen parçalar).
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_l/scripts/asst_probe.py <çıktı_json>  (before: düzeltme öncesi, after: sonrası)
Soru × oturum etiketi senaryoları sabittir (geliştirme yoklaması; ana test seti DEĞİL)."""
import json, sys
from pathlib import Path
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))
from healthrisk_api.assistant.engine import Assistant  # noqa: E402
from healthrisk_api.service import Service  # noqa: E402
svc = Service(load_models=False)
fui = svc.config['form']['field_ui_tr']
a = Assistant(svc.disclaimer, svc.config['ui']['disease_names_tr'], lambda f: fui[f]['label'] if f in fui else None)
L1 = [dict(disease_key='liver_fibrosis', outcome='ESIK_USTU', missing_fields=[]),
      dict(disease_key='osteoporosis', outcome='ESIK_ALTI', missing_fields=[]),
      dict(disease_key='af', outcome='ECG_REQUIRED', missing_fields=['ecg_record'])]
L2 = [dict(disease_key='af', outcome='ESIK_USTU', missing_fields=[])]
CASES = [('Eşik üstü ne demek?', []), ('Eşik altı ne demek?', []), ('Eşik üstü ne demek?', L1), ('Eşik altı ne demek?', L1),
         ('Eşik üstü ne demek?', L2), ('Sonucum eşik üstü çıktı, ne yapmalıyım?', L1)]
out = []
for q, labels in CASES:
    r = a.ask(q, labels, debug=True)
    out.append(dict(q=q, labels=[f"{x['disease_key']}:{x['outcome']}" for x in labels], route=r['route'],
                    answer=r['answer'][:-len(svc.disclaimer)].rstrip(), raw=r.get('raw_answer'),
                    violations=r.get('violations'), retrieval=r.get('retrieval', []),
                    sources=[s['doc_id'] + ' / ' + (s.get('section') or '') for s in r['sources']]))
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
for o in out:
    print('###', o['q'], o['labels'], o['route'], o['violations']); print(o['answer']); print('SRC', o['sources'])
