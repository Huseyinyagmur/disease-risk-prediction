"""Phase XLVIII Görev 1 — aday sohbet modellerinin 15 Türkçe soruyla karşılaştırılması (bu makinede).

Her model aynı RAG hattından geçer (aynı indeks, aynı sistem istemi, sıcaklık 0, seed 42). Ölçülenler:
  * süre (sn; her modelde 1 ısınma çağrısı ölçüme girmez),
  * otomatik Türkçe akıcılık göstergeleri: İngilizce işlev sözcüğü oranı, Latin dışı karakter (CJK vb.) sayısı,
    Türkçe'ye özgü karakter oranı,
  * otomatik kaynağa sadakat göstergeleri: son kontrol ihlali, kaynakta olmayan sayı, atıf ([n]) var mı.
Ham yanıtlar phase_xlviii/results/model_selection/ altına yazılır (sorular sentetiktir; kişi verisi yoktur) ve elle
puanlanır (01_model_selection.md). Kullanım:
  app/backend/.venv/Scripts/python.exe -B phase_xlviii/scripts/compare_models.py
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))
from healthrisk_api.assistant import guard  # noqa: E402
from healthrisk_api.assistant.engine import Assistant, AssistantUnavailable  # noqa: E402
from healthrisk_api.service import Service  # noqa: E402

OUT = V2 / 'phase_xlviii/results/model_selection'
MODELS = ['llama3:latest', 'qwen2.5:7b', 'gemma3:4b']
QUESTIONS = [
    'Atriyal fibrilasyon nedir?',
    'Karaciğer fibrozisi ne demek ve FibroScan ne ölçer?',
    'Osteoporoz kimlerde daha sık görülür?',
    'HbA1c testi neyi gösterir?',
    'Kronik böbrek hastalığı nedir?',
    'Yüksek tansiyon belirti verir mi?',
    'Anemi nedir, tam kan sayımı ne işe yarar?',
    'KOAH nedir ve spirometri testi nasıl yapılır?',
    'Koroner arter hastalığı nedir?',
    'Eşik üstü sonucu ne anlama gelir?',
    '"Sonuç üretilmedi" neden olur?',
    'İç test ile dış doğrulama arasındaki fark nedir?',
    'Karaciğer fibrozisi modelinin kanıt düzeyi nedir?',
    'Deneysel modül ne demek?',
    'eGFR nedir?',
]
EN_STOP = {'the', 'and', 'of', 'is', 'to', 'with', 'your', 'you', 'for', 'are', 'that', 'this', 'can', 'in', 'or', 'it'}


def unload(m):
    try:
        httpx.post('http://127.0.0.1:11434/api/generate', json=dict(model=m, keep_alive=0), timeout=60, trust_env=False)
    except httpx.HTTPError:
        pass


def fluency(ans):
    body = ans.split('\n\nAraştırma prototipidir;')[0]
    words = re.findall(r"[^\W\d_]+", body.lower())
    n = max(len(words), 1)
    return dict(words=len(words), en_stopword_pct=round(100 * sum(w in EN_STOP for w in words) / n, 1),
                non_latin_chars=len(re.findall(r'[Ѐ-ӿ؀-ۿ぀-ヿ一-鿿가-힯]', body)),
                tr_char_pct=round(100 * len(re.findall(r'[çğıöşüÇĞİÖŞÜ]', body)) / max(len(body), 1), 2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    svc = Service(load_models=False)
    names = svc.config['ui']['disease_names_tr']
    rows = []
    for m in MODELS:
        for other in MODELS:
            unload(other)
        a = Assistant(svc.disclaimer, names, lambda f: f, chat_model=m)
        a.ask('Eşik altı ne demek?', debug=True)                   # ısınma (ölçülmez)
        for i, q in enumerate(QUESTIONS, 1):
            for attempt in range(3):                              # geçici CUDA/llama-server hatası: yeniden dene
                t0 = time.monotonic()
                try:
                    r = a.ask(q, debug=True)
                    break
                except AssistantUnavailable:
                    a._status = None
                    time.sleep(10)
            else:
                raise SystemExit(f'{m} q{i}: 3 denemede yanıt alınamadı')
            dt = time.monotonic() - t0
            retries = attempt
            raw = r.get('raw_answer', '')
            ctx_ids = [x['doc_id'] for x in r.get('retrieval', [])]
            row = dict(model=m, qid=i, question=q, route=r['route'], seconds=round(dt, 2), retries=retries, raw_answer=raw,
                       final_answer=r['answer'], violations=r.get('violations', []),
                       cited=bool(re.search(r'\[\d\]', raw)), sources=[s['doc_id'] for s in r['sources']],
                       retrieval=r.get('retrieval', []), **fluency(raw))
            rows.append(row)
            print(f'{m:14s} q{i:02d} {row["route"]:15s} {dt:6.1f}s en%={row["en_stopword_pct"]:4.1f} '
                  f'nonlat={row["non_latin_chars"]} viol={row["violations"]}', flush=True)
        unload(m)
    tags = httpx.get('http://127.0.0.1:11434/api/tags', timeout=10, trust_env=False).json()['models']
    meta = {t['name']: dict(digest=t['digest'], size=t['size'], details=t['details']) for t in tags}
    (OUT / 'answers.json').write_text(json.dumps(dict(models=meta, options=a.options, rows=rows), ensure_ascii=False, indent=1),
                                      encoding='utf8')
    summ = {}
    for m in MODELS:
        rs = [r for r in rows if r['model'] == m]
        summ[m] = dict(n=len(rs), mean_seconds=round(sum(r['seconds'] for r in rs) / len(rs), 2),
                       max_seconds=max(r['seconds'] for r in rs),
                       llm_route=sum(r['route'] == 'llm' for r in rs),
                       postcheck_fail=sum(r['route'] == 'postcheck_fail' for r in rs),
                       no_source=sum(r['route'] == 'no_source' for r in rs),
                       cited=sum(r['cited'] for r in rs),
                       mean_en_stopword_pct=round(sum(r['en_stopword_pct'] for r in rs) / len(rs), 2),
                       answers_with_non_latin=sum(r['non_latin_chars'] > 0 for r in rs),
                       mean_tr_char_pct=round(sum(r['tr_char_pct'] for r in rs) / len(rs), 2))
    (OUT / 'summary_auto.json').write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding='utf8')
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
