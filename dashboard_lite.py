def classify_threat(alt, speed):
    if alt < 50 and speed > 10:
        return 'HIGH_THREAT'
    if alt < 100:
        return 'MEDIUM_THREAT'
    return 'MONITORING'

def parse_fused_track(msg: dict):
    return {
        'id': msg['trackId'],
        'confidence': msg['confidence'],
        'status': classify_threat(msg['alt'], msg['speed'])
    }
