"""Donmuş model yükleyici. Yeniden fit YOK; yalnız joblib.load.

Phase21/25 pickle'ları kendi `common` / `pipeline_components` modüllerini ister (registry: extra_sys_path_for_pickle).
İki fazın modül adları aynı olduğundan her yükleme yalıtılır: yol geçici eklenir, yükleme sonrası o yoldan gelen
modüller sys.modules'tan çıkarılır (yüklenen nesne sınıf referansını korur)."""
import hashlib
import sys
import warnings
from pathlib import Path

from .paths import V2

sys.dont_write_bytecode = True


def sha256_file(p, bs=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _under(path_str, root):
    try:
        return Path(path_str).resolve().is_relative_to(root)
    except (OSError, ValueError):
        return False


def load_model(rel_path, extra_sys_path=None):
    """rel_path: V2 köküne göre model yolu. extra_sys_path: pickle'ın istediği src klasörü (V2'ye göre) veya None."""
    import joblib
    root = (V2 / extra_sys_path).resolve() if extra_sys_path else None
    before = set(sys.modules)
    if root is not None:
        sys.path.insert(0, str(root))
    try:
        from sklearn.exceptions import InconsistentVersionWarning
        with warnings.catch_warnings():
            # sürüm uyuşmazlığı sessizce kabul edilmez: yükleme hata verir, model devre dışı kalır
            warnings.simplefilter('error', category=InconsistentVersionWarning)
            return joblib.load(V2 / rel_path)
    finally:
        if root is not None:
            try:
                sys.path.remove(str(root))
            except ValueError:
                pass
            for name in list(set(sys.modules) - before):
                f = getattr(sys.modules.get(name), '__file__', None)
                if f and _under(f, root):
                    del sys.modules[name]
