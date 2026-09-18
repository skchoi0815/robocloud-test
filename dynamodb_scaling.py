import hashlib
from datetime import datetime, timedelta

def make_sharded_pk(device_id: str, ts: datetime):
    hour_bucket = ts.strftime('%Y%m%d%H')
    h = int(hashlib.md5(device_id.encode()).hexdigest()[:8], 16)
    shard = h % 10
    return f'TELEMETRY#{hour_bucket}#{shard}', f'{ts.isoformat()}#{device_id}'

def query_keys_for_device(device_id: str):
    # 실전은 GSI1PK=DEVICE#id 로 쿼리. 테스트는 키포맷만 검증.
    return f'DEVICE#{device_id}'
