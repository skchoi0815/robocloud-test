from field_survival import battery_soc, adaptive_power_mode, check_enclosure

def test_soc_full():
    assert 90 <= battery_soc(13.2) <= 100

def test_soc_dead():
    assert battery_soc(10.4) == 0
    assert battery_soc(10.5) == 0

def test_soc_mid():
    # 12.4V → 20 + 0.4*62.5 = 45%
    assert 40 < battery_soc(12.4) < 50

def test_power_modes():
    assert adaptive_power_mode(90, 15) == 'full'
    assert adaptive_power_mode(60, 0) == 'normal'
    assert adaptive_power_mode(30, 0) == 'economy'
    assert adaptive_power_mode(10, 0) == 'survival'  # Great Darkness Day 4

def test_humidity_critical():
    r = check_enclosure(25, 90)
    assert r['status'] == 'DEGRADED'
    assert r['alerts'][0]['action'] == 'enable_dehumidifier'

def test_normal_ops():
    r = check_enclosure(25, 60)
    assert r['status'] == 'OPERATIONAL'
