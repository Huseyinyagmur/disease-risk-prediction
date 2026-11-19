"""Sunucuyu yalnız localhost'ta başlatır.  Kullanım:  .venv\\Scripts\\python.exe -B run_server.py [--port 8000]"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main():
    cfg = json.loads((HERE / 'config' / 'app_config.json').read_text(encoding='utf8'))
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=cfg['bind_port'])
    a = ap.parse_args()
    host = cfg['bind_host']
    if host not in ('127.0.0.1', '::1', 'localhost'):
        sys.exit(f'Güvenlik: bind_host yalnız localhost olabilir (verilen: {host})')
    import uvicorn
    from healthrisk_api.main import app, get_service
    get_service()                                  # modelleri başlangıçta yükle ve doğrula
    uvicorn.run(app, host=host, port=a.port, log_level='info', access_log=False)


if __name__ == '__main__':
    main()
