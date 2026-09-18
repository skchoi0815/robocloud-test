# 교재 p641 - critical은 reserved, 나머지는 shared

RECOMMENDED = {
    'device-heartbeat-processor': 100,
    'detection-processor': 200,
    'websocket-handler': 150,
    'telemetry-aggregator': 50,
    'log-processor': None,  # shared pool
}

def total_reserved(alloc: dict) -> int:
    return sum(v for v in alloc.values() if v)

def validate_allocations(alloc: dict, account_limit: int = 1000) -> bool:
    total = total_reserved(alloc)
    if total > account_limit * 0.8:
        raise ValueError(f"Reserved {total} exceeds 80% of {account_limit}")
    return True

def sqs_batch_config():
    # p642 - thundering herd를 줄세우기
    return {
        'BatchSize': 25,
        'MaximumBatchingWindowInSeconds': 5,
        'MaximumConcurrency': 50,
        'BisectBatchOnFunctionError': True,
    }
