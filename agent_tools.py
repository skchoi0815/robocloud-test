import os
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timezone
from typing import List, Dict, Any

REGION='us-east-1'

def _tracks_table():
    return boto3.resource('dynamodb', region_name=REGION).Table(os.getenv('TRACKS_TABLE','tracks'))
def _devices_table():
    return boto3.resource('dynamodb', region_name=REGION).Table(os.getenv('DEVICES_TABLE','devices'))
def _audit_table():
    return boto3.resource('dynamodb', region_name=REGION).Table(os.getenv('AUDIT_TABLE','audit'))

def get_active_tracks(region: str, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
    resp = _tracks_table().scan()
    out = []
    for item in resp.get('Items', []):
        if item.get('region') != region: continue
        if not str(item.get('status','')).startswith('ACTIVE'): continue
        if float(item.get('confidence', 0)) < min_confidence: continue
        out.append({
            'track_id': item['track_id'],
            'confidence': float(item['confidence']),
            'velocity': float(item.get('velocity', 0)),
            'altitude': float(item.get('altitude', 0)),
            'distance_to_facility': float(item.get('distance_to_facility', 999)),
            'threat_level': item.get('threat_level', 'UNKNOWN'),
        })
    return out

def get_threat_assessment(track_id: str) -> Dict[str, Any]:
    resp = _tracks_table().get_item(Key={'track_id': track_id})
    track = resp.get('Item')
    if not track:
        return {'error': 'Track not found'}
    velocity = float(track.get('velocity', 0))
    altitude = float(track.get('altitude', 100))
    distance = float(track.get('distance_to_facility', 999))
    towards = bool(track.get('heading_towards_facility', False))
    score = 0
    if velocity > 20: score += 30
    if altitude < 50: score += 20
    if distance < 500: score += 30
    if towards: score += 20
    level = 'HIGH' if score > 60 else ('MEDIUM' if score > 30 else 'LOW')
    return {'track_id': track_id, 'threat_level': level, 'threat_score': score,
            'recommendation': 'ENGAGE' if score > 60 else 'MONITOR'}

def get_available_turrets(region: str) -> List[Dict[str, Any]]:
    resp = _devices_table().scan(
        FilterExpression=Attr('status').eq('IDLE'))
    return [ {'device_id': i['device_id'], 'battery_level': int(i.get('battery_level',100))}
             for i in resp.get('Items', []) if i.get('region') == region ]

def assign_turret_to_track(turret_id: str, track_id: str, action: str = 'track') -> Dict[str, Any]:
    track = _tracks_table().get_item(Key={'track_id': track_id}).get('Item')
    if not track:
        return {'status': 'ERROR', 'message': f'Track {track_id} not found'}
    device = _devices_table().get_item(Key={'device_id': turret_id}).get('Item')
    if not device:
        return {'status': 'ERROR', 'message': f'Device {turret_id} not found'}
    if not device.get('connection_id'):
        return {'status': 'ERROR', 'message': f'Device {turret_id} not connected'}
    # 실전은 여기서 protobuf + apigateway.post_to_connection 쏜다. 테스트는 DynamoDB만.
    _devices_table().update_item(
        Key={'device_id': turret_id},
        UpdateExpression='SET #st = :a, current_track = :t',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={':a': 'ACTIVE', ':t': track_id})
    _audit_table().put_item(Item={
        'audit_id': f"{turret_id}#{int(datetime.now(timezone.utc).timestamp()*1000)}",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': 'TURRET_ASSIGNMENT', 'turret_id': turret_id, 'track_id': track_id})
    return {'status': 'SUCCESS', 'message': f'Turret {turret_id} is now tracking {track_id}'}
