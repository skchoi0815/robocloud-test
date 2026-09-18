import hashlib
import os

class EdgeIDS:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.file_hashes = {}
        self.miner_keywords = ['xmrig', 'minerd', 'cryptonight', 'ethminer', 'cgminer']

    def _hash_file(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()

    def init_baseline(self, filepath: str):
        self.file_hashes[filepath] = self._hash_file(filepath)

    def check_file_integrity(self, filepath: str) -> dict:
        cur = self._hash_file(filepath)
        orig = self.file_hashes.get(filepath)
        if orig is None:
            return {'status': 'NO_BASELINE'}
        if cur != orig:
            return {'type': 'FILE_INTEGRITY_VIOLATION', 'severity': 'CRITICAL',
                    'file': filepath, 'status': 'VIOLATED'}
        return {'status': 'OK'}

    def check_process(self, command: str) -> dict | None:
        low = command.lower()
        if any(k in low for k in self.miner_keywords):
            return {'type': 'CRYPTOMINER_DETECTED', 'severity': 'CRITICAL', 'action': 'KILL'}
        if ('nc' in low or 'netcat' in low) and ('-e' in low or '-c' in low):
            return {'type': 'REVERSE_SHELL_DETECTED', 'severity': 'CRITICAL', 'action': 'KILL'}
        return None

    def verify_cert_fingerprint(self, expected: str, actual: str) -> bool:
        # TLS pinning - 다르면 MITM으로 보고 끊어야 함 (p577)
        return expected == actual
