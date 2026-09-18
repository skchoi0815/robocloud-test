import time
import hashlib
import numpy as np

class MeshMessage:
    def __init__(self, source, destination, payload, ttl=10):
        content = f"{source}{destination}{time.time()}"
        self.msg_id = hashlib.md5(content.encode()).hexdigest()[:8]
        self.source = source
        self.destination = destination
        self.payload = payload
        self.ttl = ttl
        self.path = []

def forward_message(msg: MeshMessage, seen: set):
    # TTL 깎고, 본 놈이면 drop
    if msg.msg_id in seen:
        return None
    seen.add(msg.msg_id)
    msg.ttl -= 1
    if msg.ttl <= 0:
        return None
    return msg

def compute_consensus(observations):
    # observations: [{'position':[x,y,z], 'confidence':0.9}, ...]
    # 2초 지난 건 버림
    now = time.time()
    obs = [o for o in observations if now - o.get('timestamp', now) < 2.0]
    if len(obs) < 2:
        return None
    total = sum(o['confidence'] for o in obs)
    if total == 0:
        return None
    pos = np.zeros(3)
    for o in obs:
        pos += np.array(o['position']) * (o['confidence'] / total)
    positions = np.array([o['position'] for o in obs])
    uncertainty = float(np.std(positions, axis=0).mean())
    return {'position': pos.tolist(), 'confidence': total/len(obs),
            'uncertainty': uncertainty, 'count': len(obs)}

def match_handoff(detection_pos, predicted_pos, features_match: bool, threshold: float = 10.0):
    # 4.7초 사고 fix: 거리 + 외형 둘 다 맞아야 confirm
    dist = float(np.linalg.norm(np.array(detection_pos) - np.array(predicted_pos)))
    if dist < threshold and features_match:
        return True
    return False
