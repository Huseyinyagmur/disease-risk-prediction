"""Kilitli bilgi tabanı indeksi: manifest SHA256'ları doğrulanır, kosinüs benzerliğiyle en ilgili k parça döner."""
import hashlib
import json
from pathlib import Path

import numpy as np


class IndexError_(Exception):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class KnowledgeBase:
    def __init__(self, kb_dir: Path, expected_manifest_sha: str):
        self.dir = kb_dir
        man_p = kb_dir / 'index' / 'manifest.json'
        if not man_p.exists():
            raise IndexError_('indeks bulunamadı (kb/index/manifest.json)')
        if _sha(man_p) != expected_manifest_sha:
            raise IndexError_('indeks manifest SHA256 kilitle uyuşmuyor')
        self.manifest = json.loads(man_p.read_text(encoding='utf8'))
        for rel, h in self.manifest['files'].items():
            if _sha((kb_dir / 'index' / rel).resolve()) != h:
                raise IndexError_(f'indeks dosyası SHA256 uyuşmuyor: {rel}')
        for rel, h in self.manifest['documents'].items():
            if _sha(kb_dir / rel) != h:
                raise IndexError_(f'bilgi tabanı belgesi SHA256 uyuşmuyor: {rel}')
        self.chunks = [json.loads(x) for x in (kb_dir / 'index' / 'chunks.jsonl').read_text(encoding='utf8').splitlines() if x]
        vec = np.frombuffer((kb_dir / 'index' / 'embeddings.f32').read_bytes(), dtype='<f4')
        self.vecs = vec.reshape(len(self.chunks), self.manifest['dim'])
        self.embed_model = self.manifest['embed_model']
        self.urls = {c['url'] for c in self.chunks if c.get('url')}
        self.by_doc = {}
        for c in self.chunks:
            self.by_doc.setdefault(c['doc_id'], []).append(c)

    def search(self, qvec, k: int):
        q = np.asarray(qvec, dtype='f4')
        q = q / (np.linalg.norm(q) or 1.0)
        s = self.vecs @ q
        idx = np.argsort(-s)[:k]
        return [(float(s[i]), self.chunks[i]) for i in idx]

    def doc_chunks(self, doc_id: str, n: int = 2):
        return self.by_doc.get(doc_id, [])[:n]
