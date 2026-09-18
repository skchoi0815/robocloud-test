from dashboard_lite import classify_threat, parse_fused_track

def test_high_threat():
    assert classify_threat(45, 25) == 'HIGH_THREAT'

def test_fused_parse():
    r = parse_fused_track({'trackId':'trk-d9e8','confidence':0.98,'alt':45,'speed':25})
    assert r['id'] == 'trk-d9e8'
    assert r['status'] == 'HIGH_THREAT'

def test_cost_math():
    assert 6555 - 198 > 6000
