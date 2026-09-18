import time
from swarm_mesh import MeshMessage, forward_message, compute_consensus, match_handoff

def test_ttl_expires():
    m = MeshMessage('003', 'broadcast', {'type':'detect'}, ttl=1)
    seen = set()
    assert forward_message(m, seen) is None  # 1-1=0 → 죽음

def test_loop_prevented():
    m = MeshMessage('003', 'broadcast', {'type':'detect'}, ttl=10)
    seen = set()
    assert forward_message(m, seen) is not None
    assert forward_message(m, seen) is None  # 두번째는 drop

def test_consensus_weighted():
    now = time.time()
    obs = [
        {'position': [100,200,0], 'confidence': 0.9, 'timestamp': now},
        {'position': [102,198,0], 'confidence': 0.9, 'timestamp': now},
    ]
    c = compute_consensus(obs)
    assert c is not None
    assert 100 <= c['position'][0] <= 102
    assert c['count'] == 2

def test_consensus_needs_two():
    now = time.time()
    assert compute_consensus([{'position':[0,0,0],'confidence':0.9,'timestamp':now}]) is None

def test_handoff_with_features():
    # 거리 가깝고 외형 맞으면 confirm
    assert match_handoff([100,100,0],[102,101,0], features_match=True) is True
    # 거리 가까워도 외형 다르면 새 트랙 - 유령트랙 방지
    assert match_handoff([100,100,0],[102,101,0], features_match=False) is False
