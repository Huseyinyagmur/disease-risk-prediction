"""Kilitli AF-ECGDELI-OCTAVE-v1 pipeline'ının (phase_xxviii) uygulamadan çağrılması.

Pipeline kodu DEĞİŞTİRİLMEZ ve kopyalanmaz: phase_xxviii/pipeline/af_pipeline_v1.py, SHA256'sı kilitle
(af_pipeline_lock.json) doğrulandıktan sonra dosya yolundan içe aktarılır. Kilitteki Octave exe, ECGDeli kaynak ağacı
ve compat .m dosyalarının SHA256'ları da doğrulanır; herhangi biri uyuşmazsa /ecg/af devre dışıdır.
Zincir: [ön adım: ecg_window.read_first10s — Phase XXIX/XXXIII 'ilk 10 sn' sarmalayıcısının birebir kopyası, kilidin
ÖNÜNDE] -> run_ecgdeli(timeout) -> features_from_mat (kilitli pipeline işlevleri). Başlık ön kontrolü: fs != 500 Hz
veya örnek sayısı < 5000 (10 sn) -> ABSTAIN.
"""
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

from .ecg_window import read_first10s
from .model_loader import sha256_file
from .paths import AF_LOCK, AF_LOCK_SHA, AF_PIPELINE, V2

TIMEOUT_S = 60.0
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
AF_FEATURES = ['RR_Mean_Global', 'RR_Mean_Global_iqr', 'QRS_Dur_Global', 'QRS_Dur_Global_iqr', 'PR_Int_Global',
               'PR_Int_Global_iqr', 'P_Dur_Global', 'P_Dur_Global_iqr', 'QT_Int_Global', 'QT_Int_Global_iqr']
_NAME = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')


DISPLAY_DECIMATION = 2          # 500 Hz -> 250 Hz (yalnız görüntüleme)


def display_payload(sig, pl, mat_path=None):
    """Phase XLV: arayüz grafiği için lead II (ilk 10 sn, her 2. örnek; filtre yok) ve R tepe zamanları.
    R tepeleri kilitli pipeline'ın kendi load_fpt çıktısındaki FPT_MultiChannel 6. sütunudur — RR_Mean_Global
    feature'ının hesaplandığı sütunun aynısı. Feature'lara ve karara etkisi yoktur; yalnız gösterim içindir."""
    import numpy as np
    ii = [l.upper() for l in pl.LEADS].index('II')
    x = np.asarray(sig, float)[::DISPLAY_DECIMATION, ii]
    out = dict(lead='II', fs_hz=pl.FS / DISPLAY_DECIMATION, source_fs_hz=pl.FS, duration_s=len(sig) / pl.FS,
               signal_mv=[round(float(v), 4) if np.isfinite(v) else None for v in x], r_peaks_s=None, rr_ms=None,
               note=('Görüntüleme amaçlı: lead II, ilk 10 sn, 500 Hz -> 250 Hz (her 2. örnek, filtre yok). R tepeleri '
                     'ECGDeli FPT_MultiChannel 6. sütunu (RR feature\'ıyla aynı kaynak); zaman = (1 tabanlı indeks − 1) / 500.'))
    if mat_path is not None:
        multi, _ = pl.load_fpt(mat_path)
        r = multi[:, 5]
        r = r[np.isfinite(r)]
        out['r_peaks_s'] = [round(float(v - 1) / pl.FS, 4) for v in r]
        out['rr_ms'] = [round(float(v), 1) for v in np.diff(r) * 1000.0 / pl.FS]
    return out


def _tree_hash(root, pattern='*.m'):
    """phase_xxviii/scripts/t1_lock_pipeline.py tree_hash ile aynı tanım."""
    h = hashlib.sha256()
    files = sorted(Path(root).rglob(pattern))
    for f in files:
        h.update(f.relative_to(root).as_posix().encode() + b'\0' + sha256_file(f).encode() + b'\n')
    return h.hexdigest(), len(files)


class AFPipeline:
    def __init__(self):
        self.problems = []
        self.module = None
        self.lock = None
        self._busy = threading.Lock()
        try:
            self._verify_and_import()
        except Exception as ex:                       # pragma: no cover - beklenmeyen durum /health'te raporlanır
            self.problems.append(f'beklenmeyen hata: {type(ex).__name__}: {ex}')
            self.module = None

    @property
    def enabled(self):
        return self.module is not None and not self.problems

    def _verify_and_import(self):
        # Ortam yoksa (ör. yalnız GitHub deposu klonlandı) açık gerekçe: Octave/ECGDeli ve kilitli pipeline dosyaları
        # depoda değildir; AF devre dışı kalır, diğer modeller etkilenmez.
        missing = [p for p in (AF_LOCK, AF_LOCK_SHA, AF_PIPELINE) if not p.exists()]
        if missing:
            self.problems.append('Octave/ECGDeli AF çalışma ortamı yok: kilitli AF pipeline dosyaları bulunamadı ('
                                 + ', '.join(p.relative_to(V2).as_posix() for p in missing)
                                 + '). AF için Octave 10.3.0 + ECGDeli v1.1 + kilitli pipeline ayrıca kurulmalıdır.')
            return
        lock_sha = sha256_file(AF_LOCK)
        if AF_LOCK_SHA.read_text(encoding='utf8').strip() != lock_sha:
            self.problems.append('af_pipeline_lock.json SHA256, af_pipeline_lock.sha256 ile uyuşmuyor')
            return
        lock = json.loads(AF_LOCK.read_text(encoding='utf8'))
        self.lock = lock
        if lock['pipeline_version'] != 'AF-ECGDELI-OCTAVE-v1':
            self.problems.append(f'beklenmeyen pipeline sürümü {lock["pipeline_version"]}')
        if sha256_file(AF_PIPELINE) != lock['pipeline_sha256']:
            self.problems.append('af_pipeline_v1.py SHA256 kilitle uyuşmuyor')
        exe = V2 / lock['octave']['exe']
        if not exe.exists():
            self.problems.append(f'Octave yok: {lock["octave"]["exe"]} bulunamadı (AF için Octave + ECGDeli ayrıca kurulmalıdır)')
        elif sha256_file(exe) != lock['octave']['exe_sha256']:
            self.problems.append('Octave exe SHA256 kilitle uyuşmuyor')
        for rel, h in lock['compat'].items():
            p = V2 / rel
            if not p.exists() or sha256_file(p) != h:
                self.problems.append(f'compat dosyası uyuşmuyor: {rel}')
        if self.problems:
            return
        spec = importlib.util.spec_from_file_location('af_pipeline_v1_locked', AF_PIPELINE)
        mod = importlib.util.module_from_spec(spec)
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)
        tree, n = _tree_hash(mod.ECGDELI_SOURCE)
        if tree != lock['ecgdeli']['source_tree_sha256'] or n != lock['ecgdeli']['n_m_files']:
            self.problems.append('ECGDeli kaynak ağacı SHA256 kilitle uyuşmuyor')
            return
        if mod.PIPELINE_VERSION != lock['pipeline_version'] or mod.FEATURES != AF_FEATURES:
            self.problems.append('pipeline sürümü/feature listesi beklenenden farklı')
            return
        from .ecg_window import verify_source
        wp = verify_source()
        if wp:
            self.problems += [f'ön adım (ilk 10 sn): {x}' for x in wp]
            return
        if str(mod.WFDB_VENDOR) not in sys.path:      # Phase XXIX/XXXIII main() ile aynı: vendored wfdb 4.3.1
            sys.path.insert(0, str(mod.WFDB_VENDOR))
        self.module = mod

    def status(self):
        from . import ecg_window as W
        return dict(enabled=self.enabled, pipeline_version=(self.lock or {}).get('pipeline_version'),
                    lock_file='phase_xxviii/config/af_pipeline_lock.json', problems=self.problems, timeout_seconds=TIMEOUT_S,
                    pre_step=dict(name='ilk 10 sn penceresi (read_first10s)', source_file=W.SOURCE_FILE,
                                  source_file_sha256=W.SOURCE_FILE_SHA256, source_function_sha256=W.SOURCE_FUNC_SHA256,
                                  also_identical_logic=W.XXIX_FILE, placement='kilitli pipeline öncesi; kilit dosyası değişmedi'))

    @staticmethod
    def parse_header(text):
        """WFDB başlığı: kayıt adı ve sinyal dosya adları. Biçim hatasında ValueError."""
        lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')]
        if not lines:
            raise ValueError('boş .hea')
        head = lines[0].split()
        rec, nsig = head[0], int(head[1])
        if len(lines) < 1 + nsig:
            raise ValueError('.hea sinyal satırı sayısı eksik')
        files = {l.split()[0] for l in lines[1:1 + nsig]}
        return rec, files

    @staticmethod
    def header_fs_nsamp(text):
        """Başlık satırından örnekleme frekansı ve örnek sayısı (yoksa None)."""
        head = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')][0].split()
        fs = float(head[2].split('/')[0].split('(')[0]) if len(head) > 2 else None
        ns = int(head[3]) if len(head) > 3 else None
        return fs, ns

    def extract(self, header_name, header_bytes, signal_name, signal_bytes, timeout=TIMEOUT_S):
        """Döner: (features | None, info). info['abstain_reason'] başarısızlıkta doludur."""
        t0 = time.monotonic()
        info = dict(pipeline_version='AF-ECGDELI-OCTAVE-v1', abstain_reason=None)
        if not self.enabled:
            info['abstain_reason'] = 'AF pipeline devre dışı: ' + '; '.join(self.problems)
            return None, info
        if len(header_bytes) > MAX_UPLOAD_BYTES or len(signal_bytes) > MAX_UPLOAD_BYTES:
            info['abstain_reason'] = 'dosya boyutu sınırı aşıldı'
            return None, info
        hstem, hext = Path(header_name).stem, Path(header_name).suffix.lower()
        if hext != '.hea' or not _NAME.match(hstem):
            info['abstain_reason'] = 'başlık dosyası <kayıt>.hea biçiminde olmalı (harf, rakam, _ veya -)'
            return None, info
        try:
            rec, files = self.parse_header(header_bytes.decode('ascii'))
        except Exception as ex:
            info['abstain_reason'] = f'.hea okunamadı: {ex}'
            return None, info
        try:
            fs, ns = self.header_fs_nsamp(header_bytes.decode('ascii'))
        except Exception as ex:
            info['abstain_reason'] = f'.hea okunamadı: {ex}'
            return None, info
        if fs != 500:
            info['abstain_reason'] = f'örnekleme frekansı 500 Hz değil (başlık: {fs})'
            return None, info
        if ns is None or ns < 5000:
            info['abstain_reason'] = f'kayıt 10 sn\'den kısa veya örnek sayısı yok (başlık: {ns} örnek; en az 5000 gerekir)'
            return None, info
        info['record_samples'] = ns
        info['window'] = 'ilk 10 sn (5000 örnek)' + (' — kayıt daha uzun, kırpıldı' if ns > 5000 else '')
        sname = Path(signal_name).name
        if rec != hstem or files != {sname} or Path(sname).suffix.lower() not in ('.dat', '.mat') \
                or not _NAME.match(Path(sname).stem):
            info['abstain_reason'] = (f'başlık ({rec}; sinyal dosyası {sorted(files)}) ile yüklenen dosyalar '
                                      f'({hstem}.hea, {sname}) uyuşmuyor; tek .dat veya .mat sinyal dosyası beklenir')
            return None, info
        if not self._busy.acquire(blocking=False):
            info['abstain_reason'] = 'AF pipeline meşgul (aynı anda tek kayıt işlenir); tekrar deneyin'
            info['busy'] = True
            return None, info
        tmp = Path(tempfile.mkdtemp(prefix='hr_af_'))
        try:
            (tmp / f'{hstem}.hea').write_bytes(header_bytes)
            (tmp / sname).write_bytes(signal_bytes)
            pl = self.module
            try:
                sig = read_first10s(tmp / hstem, pl)        # ön adım: ilk 5000 örnek; read_wfdb_500 ile aynı kontroller
            except AssertionError as ex:
                info['abstain_reason'] = f'kayıt pipeline girdi koşulunu sağlamıyor (500 Hz, 12 lead, ilk 10 s, mV, lead sırası): {ex}'
                return None, info
            except Exception as ex:
                info['abstain_reason'] = f'WFDB okunamadı: {type(ex).__name__}: {ex}'
                return None, info
            remaining = timeout - (time.monotonic() - t0)
            if remaining <= 1:
                info['abstain_reason'] = 'zaman aşımı'
                return None, info
            st = pl.run_ecgdeli(sig, tmp / 'work', 'rec', timeout=remaining)
            info['octave_seconds'] = st.get('seconds')
            if not st.get('delineation_completed'):
                info['abstain_reason'] = 'ECGDeli delineasyonu tamamlanamadı' + (' (zaman aşımı)' if (time.monotonic() - t0) >= timeout else '')
                try:
                    info['display'] = display_payload(sig, pl)
                except Exception:                     # gösterim hatası sonucu etkilemez
                    pass
                return None, info
            feats = pl.features_from_mat(tmp / 'work' / 'rec.mat')
            try:
                info['display'] = display_payload(sig, pl, tmp / 'work' / 'rec.mat')
            except Exception as ex:                   # gösterim hatası sonucu etkilemez
                info['display_error'] = type(ex).__name__
            info['wall_seconds'] = time.monotonic() - t0
            if info['wall_seconds'] > timeout:
                info['abstain_reason'] = 'zaman aşımı (60 sn)'
                return None, info
            return {k: feats[k] for k in AF_FEATURES}, info
        finally:
            self._busy.release()
            shutil.rmtree(tmp, ignore_errors=True)
