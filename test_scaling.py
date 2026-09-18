from datetime import datetime
from dynamodb_scaling import make_sharded_pk, query_keys_for_device

def test_shard_distributes():
    ts = datetime(2024, 7, 18, 23, 47, 0)
    pks = set()
    for i in range(100):
        pk, sk = make_sharded_pk(f'TURRET-{i:03d}', ts)
        pks.add(pk)
        assert pk.startswith('TELEMETRY#2024071823#')
        assert f'TURRET-{i:03d}' in sk
    # 100대가 1개 파티션에 안 몰려야 함 - WALL 방지
    assert len(pks) > 1

def test_same_device_same_shard():
    ts = datetime(2024, 7, 18, 23, 47, 0)
    pk1, _ = make_sharded_pk('TURRET-0312', ts)
    pk2, _ = make_sharded_pk('TURRET-0312', ts)
    assert pk1 == pk2

def test_gsi_key_format():
    assert query_keys_for_device('TURRET-001') == 'DEVICE#TURRET-001'
