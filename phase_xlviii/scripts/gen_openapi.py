"""Phase XLVIII: app/docs/openapi.json'u FastAPI app.openapi() çıktısından yeniden üretir (/assistant/ask eklendi).
Kullanım: app/backend/.venv/Scripts/python.exe -B phase_xlviii/scripts/gen_openapi.py"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'app/backend'))
from healthrisk_api.main import app  # noqa: E402

out = V2 / 'app/docs/openapi.json'
old = json.loads(out.read_text(encoding='utf8'))
new = app.openapi()
out.write_text(json.dumps(new, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('yollar:', sorted(new['paths']), '| eklenen:', sorted(set(new['paths']) - set(old['paths'])),
      '| değişen eski yol:', sorted(k for k in old['paths'] if old['paths'][k] != new['paths'].get(k)))
