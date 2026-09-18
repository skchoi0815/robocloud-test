import hashlib
from datetime import datetime

def prefix_shard(device_id: str) -> str:
    # 2글자 prefix = 256 shards, 3500 PUT/s x 256
    return hashlib.md5(device_id.encode()).hexdigest()[:2]

def sharded_key(device_id: str, ts: datetime) -> str:
    shard = prefix_shard(device_id)
    return f"{shard}/{device_id}/{ts.strftime('%Y/%m/%d/%H')}/{ts.isoformat()}.json"
