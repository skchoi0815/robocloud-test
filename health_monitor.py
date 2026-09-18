class HealthMonitor:
    def __init__(self, registry):
        self.registry = registry

    def check_device_health(self, device_id: str) -> dict:
        report = {'device_id': device_id, 'score': 100, 'issues': [], 'auto_remediation': []}
        device = self.registry.get_device(device_id)
        if not device:
            report['score'] = 0
            report['issues'].append({'severity': 'CRITICAL', 'type': 'NOT_FOUND'})
            report['status'] = 'CRITICAL'
            return report
        # 1. WebSocket 연결 = 생명줄
        if device.get('status') != 'ONLINE' or not device.get('connection_id'):
            report['score'] -= 50
            report['issues'].append({'severity': 'CRITICAL', 'type': 'NO_CONNECTION'})
            report['status'] = 'CRITICAL'
            return report
        # 2. 온도
        temp = float(device.get('temperature_celsius', 0))
        if temp > 70:
            report['score'] -= 20
            report['issues'].append({'severity': 'MEDIUM', 'type': 'HIGH_TEMPERATURE', 'value': temp})
            report['auto_remediation'].append('Reduced compute load')
        # 3. FPS
        fps = float(device.get('avg_fps', 30))
        if fps != 0 and fps < 15:
            report['score'] -= 15
            report['issues'].append({'severity': 'MEDIUM', 'type': 'LOW_FPS', 'value': fps})
        # 4. 디스크
        disk = float(device.get('disk_usage_percent', 0))
        if disk > 90:
            report['score'] -= 25
            report['issues'].append({'severity': 'HIGH', 'type': 'DISK_SPACE_LOW'})
            report['auto_remediation'].append('Triggered disk cleanup')
        # 판정
        if report['score'] >= 80:
            report['status'] = 'HEALTHY'
        elif report['score'] >= 60:
            report['status'] = 'DEGRADED'
        else:
            report['status'] = 'CRITICAL'
        return report
