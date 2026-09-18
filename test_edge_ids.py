from edge_ids import EdgeIDS

def test_file_integrity_ok(tmp_path):
    ids = EdgeIDS('TURRET-031')
    f = tmp_path / "config.json"
    f.write_text('{"a":1}')
    ids.init_baseline(str(f))
    assert ids.check_file_integrity(str(f))['status'] == 'OK'

def test_file_integrity_violated(tmp_path):
    ids = EdgeIDS('TURRET-031')
    f = tmp_path / "sudoers"
    f.write_text('root ALL')
    ids.init_baseline(str(f))
    f.write_text('root ALL\nhacker ALL')  # 변조
    r = ids.check_file_integrity(str(f))
    assert r['type'] == 'FILE_INTEGRITY_VIOLATION'
    assert r['severity'] == 'CRITICAL'

def test_cryptominer_detected():
    ids = EdgeIDS('TURRET-042')
    r = ids.check_process('./xmrig --donate-level 1 -o pool.com:4444')
    assert r['type'] == 'CRYPTOMINER_DETECTED'
    assert r['action'] == 'KILL'

def test_cert_pinning_blocks_mitm():
    ids = EdgeIDS('TURRET-031')
    assert ids.verify_cert_fingerprint('abc123', 'abc123') is True
    assert ids.verify_cert_fingerprint('abc123', 'evil456') is False
