from datetime import datetime
from lambda_scaling import RECOMMENDED, total_reserved, validate_allocations, sqs_batch_config
from s3_optimization import prefix_shard, sharded_key

def test_reserved_under_80pct():
    # 100+200+150+50=500, limit 1000의 80% = 800 → OK
    assert total_reserved(RECOMMENDED) == 500
    assert validate_allocations(RECOMMENDED, account_limit=1000) is True

def test_reserved_over_limit_fails():
    bad = {'a': 500, 'b': 500}
    try:
        validate_allocations(bad, account_limit=1000)
        assert False, "should have raised"
    except ValueError as e:
        assert "exceeds 80%" in str(e)

def test_sqs_batch_limits_concurrency():
    cfg = sqs_batch_config()
    assert cfg['BatchSize'] == 25
    assert cfg['MaximumConcurrency'] == 50

def test_s3_prefix_distributes():
    shards = set(prefix_shard(f'TURRET-{i:03d}') for i in range(100))
    # 100대가 1개 prefix에 몰리면 S3 3500 제한에 걸림
    assert len(shards) > 10

def test_s3_key_format():
    ts = datetime(2024, 7, 18, 23, 47, 0)
    k = sharded_key('TURRET-001', ts)
    assert k.startswith(prefix_shard('TURRET-001') + '/TURRET-001/2024/07/18/23/')
    assert k.endswith('.json')
