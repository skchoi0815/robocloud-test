import boto3
import secrets
import json
from datetime import datetime, timedelta, timezone

class BearerTokenRotation:
    def __init__(self, table_name='device-fleet'):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.secrets_manager = boto3.client('secretsmanager', region_name='us-east-1')
        self.table = self.dynamodb.Table(table_name)

    def _needs_rotation(self, device_id: str) -> bool:
        try:
            secret = self.secrets_manager.get_secret_value(
                SecretId=f'device/{device_id}/bearer-token')
            data = json.loads(secret['SecretString'])
            if data.get('status') == 'REVOKED':
                return True
            expires_at = datetime.fromisoformat(data['expires_at'])
            return (expires_at - datetime.now(timezone.utc)) < timedelta(hours=4)
        except self.secrets_manager.exceptions.ResourceNotFoundException:
            return True

    def _rotate_device_token(self, device_id: str):
        new_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        count = 0
        try:
            old = self.secrets_manager.get_secret_value(SecretId=f'device/{device_id}/bearer-token')
            count = json.loads(old['SecretString']).get('rotation_count', 0)
        except Exception:
            pass
        payload = json.dumps({
            'token': new_token,
            'device_id': device_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': expires_at.isoformat(),
            'rotation_count': count + 1
        })
        sid = f'device/{device_id}/bearer-token'
        try:
            self.secrets_manager.put_secret_value(SecretId=sid, SecretString=payload)
        except self.secrets_manager.exceptions.ResourceNotFoundException:
            self.secrets_manager.create_secret(Name=sid, SecretString=payload)

    def emergency_revoke_token(self, device_id: str, reason: str):
        sid = f'device/{device_id}/bearer-token'
        payload = json.dumps({
            'token': 'REVOKED', 'device_id': device_id,
            'revoked_at': datetime.now(timezone.utc).isoformat(),
            'reason': reason, 'status': 'REVOKED'})
        try:
            self.secrets_manager.put_secret_value(SecretId=sid, SecretString=payload)
        except self.secrets_manager.exceptions.ResourceNotFoundException:
            self.secrets_manager.create_secret(Name=sid, SecretString=payload)
        print(f" REVOKED {device_id}: {reason}")
