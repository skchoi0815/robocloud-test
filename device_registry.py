import boto3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Attr

class DeviceRegistry:
    def __init__(self, table_name='device-fleet', websocket_endpoint=None):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = self.dynamodb.Table(table_name)
        self.websocket_endpoint = websocket_endpoint
        self.apigateway = None

    def register_device(self, device_id: str, connection_id: str, metadata: dict = None) -> dict:
        metadata = metadata or {}
        now = datetime.now(timezone.utc).isoformat()
        existing_count = 0
        try:
            resp = self.table.get_item(Key={'PK': f'DEVICE#{device_id}', 'SK': 'METADATA'})
            if 'Item' in resp:
                existing_count = int(resp['Item'].get('connection_count', 0))
        except Exception:
            pass
        item = {
            'PK': f'DEVICE#{device_id}', 'SK': 'METADATA',
            'device_id': device_id,
            'registered_at': now, 'last_seen': now,
            'status': 'ONLINE',
            'connection_id': connection_id,
            'connected_at': now,
            'connection_count': existing_count + 1,
            'hardware_model': metadata.get('hardware_model', 'unknown'),
            'firmware_version': metadata.get('firmware', '0.0.0'),
            'software_version': metadata.get('software', '0.0.0'),
            'model_version': metadata.get('model_version', '0.0.0'),
            'deployment_group': metadata.get('group', 'default'),
            'site_id': metadata.get('site_id', ''),
            'update_channel': metadata.get('channel', 'stable'),
            'failed_updates': 0, 'update_locked': False,
            'avg_fps': Decimal('0'), 'avg_latency_ms': Decimal('0'),
            'temperature_celsius': Decimal('0'),
            'cpu_usage_percent': Decimal('0'),
            'memory_usage_percent': Decimal('0'),
            'disk_usage_percent': Decimal('0'),
        }
        self.table.put_item(Item=item)
        return item

    def update_telemetry(self, device_id: str, telemetry: dict) -> bool:
        telemetry = telemetry or {}
        try:
            self.table.update_item(
                Key={'PK': f'DEVICE#{device_id}', 'SK': 'METADATA'},
                UpdateExpression="SET last_seen = :now, temperature_celsius = :temp, cpu_usage_percent = :cpu, memory_usage_percent = :mem, disk_usage_percent = :disk, avg_fps = :fps, avg_latency_ms = :latency, software_version = :sw, model_version = :model",
                ExpressionAttributeValues={
                    ':now': datetime.now(timezone.utc).isoformat(),
                    ':temp': self._decimal(telemetry.get('temperature', 0)),
                    ':cpu': self._decimal(telemetry.get('cpu_percent', 0)),
                    ':mem': self._decimal(telemetry.get('memory_percent', 0)),
                    ':disk': self._decimal(telemetry.get('disk_percent', 0)),
                    ':fps': self._decimal(telemetry.get('avg_fps', 0)),
                    ':latency': self._decimal(telemetry.get('avg_latency_ms', 0)),
                    ':sw': telemetry.get('software_version', '0.0.0'),
                    ':model': telemetry.get('model_version', '0.0.0'),
                }
            )
            if float(telemetry.get('temperature', 0)) > 70:
                self._log_event(device_id, 'HIGH_TEMPERATURE', {'celsius': str(telemetry.get('temperature'))})
            return True
        except Exception as e:
            print(f"Telemetry update failed for {device_id}: {e}")
            return False

    def disconnect_device(self, connection_id: str) -> bool:
        try:
            resp = self.table.scan(FilterExpression=Attr('connection_id').eq(connection_id))
            if not resp.get('Items'):
                return False
            device_id = resp['Items'][0]['device_id']
            self.table.update_item(
                Key={'PK': f'DEVICE#{device_id}', 'SK': 'METADATA'},
                UpdateExpression='SET #st = :off REMOVE connection_id',
                ExpressionAttributeNames={'#st': 'status'},
                ExpressionAttributeValues={':off': 'OFFLINE'}
            )
            self._log_event(device_id, 'DISCONNECTED', {'connection_id': connection_id})
            return True
        except Exception as e:
            print(f"Disconnect failed: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[dict]:
        try:
            resp = self.table.get_item(Key={'PK': f'DEVICE#{device_id}', 'SK': 'METADATA'})
            return resp.get('Item')
        except Exception:
            return None

    def get_all_devices(self) -> List[dict]:
        devices = []
        resp = self.table.scan(FilterExpression=Attr('SK').eq('METADATA'))
        devices.extend(resp.get('Items', []))
        while 'LastEvaluatedKey' in resp:
            resp = self.table.scan(FilterExpression=Attr('SK').eq('METADATA'), ExclusiveStartKey=resp['LastEvaluatedKey'])
            devices.extend(resp.get('Items', []))
        return devices

    def get_fleet_status(self) -> Dict:
        all_devices = self.get_all_devices()
        online = [d for d in all_devices if d.get('status') == 'ONLINE']
        offline = [d for d in all_devices if d.get('status') != 'ONLINE']
        versions = {}
        for d in online:
            v = d.get('software_version', 'unknown')
            versions[v] = versions.get(v, 0) + 1
        issues = []
        for d in online:
            if float(d.get('temperature_celsius', 0)) > 65:
                issues.append({'device_id': d['device_id'], 'issue': 'HIGH_TEMP'})
            if float(d.get('avg_fps', 30)) < 15 and float(d.get('avg_fps', 30)) != 0:
                issues.append({'device_id': d['device_id'], 'issue': 'LOW_FPS'})
        return {
            'total_devices': len(all_devices),
            'online_devices': len(online),
            'offline_devices': len(offline),
            'health_percentage': (len(online)/len(all_devices)*100) if all_devices else 0,
            'version_distribution': versions,
            'issues': issues,
        }

    def _log_event(self, device_id: str, event_type: str, details: dict):
        self.table.put_item(Item={
            'PK': f'DEVICE#{device_id}',
            'SK': f'EVENT#{datetime.now(timezone.utc).isoformat()}',
            'event_type': event_type, 'details': details
        })

    @staticmethod
    def _decimal(v, default='0') -> Decimal:
        try:
            return Decimal(str(v))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)
