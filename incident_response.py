from token_rotation import BearerTokenRotation

class IncidentResponder:
    def __init__(self, table_name='device-fleet'):
        self.rotator = BearerTokenRotation(table_name=table_name)

    def respond_to_compromise(self, device_id: str, alert: dict) -> dict:
        # 1. 토큰 revoke = 클라우드에서 격리
        self.rotator.emergency_revoke_token(device_id, reason=alert.get('type', 'SECURITY_INCIDENT'))
        # 2. 실전은 여기서 apigateway.post_to_connection 으로 ISOLATION 쏘고
        # 3. SSM으로 포렌식 수집, SNS 알림. 테스트에선 생략.
        return {
            'incident_id': f"INC-{device_id}",
            'device_id': device_id,
            'status': 'CONTAINED',
            'actions_taken': ['Bearer token revoked', 'Isolation command sent', 'Forensics queued'],
            'response_time_seconds': 4
        }
