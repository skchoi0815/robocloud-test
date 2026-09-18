import base64
import robotics_messages_v2_pb2 as proto

class ProtobufCodec:
    def encode_telemetry(self, device_id, telemetry: dict) -> str:
        msg = proto.Telemetry()
        msg.device_id = device_id
        if 'temperature' in telemetry: msg.temperature_celsius = float(telemetry['temperature'])
        if 'cpu_percent' in telemetry: msg.cpu_percent = float(telemetry['cpu_percent'])
        if 'memory_percent' in telemetry: msg.memory_percent = float(telemetry['memory_percent'])
        if 'disk_percent' in telemetry: msg.disk_percent = float(telemetry['disk_percent'])
        if 'uptime_seconds' in telemetry: msg.uptime_seconds = int(telemetry['uptime_seconds'])
        if 'software_version' in telemetry: msg.software_version = str(telemetry['software_version'])
        if 'model_version' in telemetry: msg.model_version = str(telemetry['model_version'])
        return base64.b64encode(msg.SerializeToString()).decode('utf-8')

    def decode_telemetry(self, data: str) -> dict:
        try:
            raw = base64.b64decode(data)
        except Exception as e:
            raise ValueError(f'invalid base64: {e}')
        msg = proto.Telemetry()
        try:
            msg.ParseFromString(raw)
        except Exception as e:
            raise ValueError(f'invalid protobuf: {e}')
        # 빈바이트도 에러로 - 깨진 메시지 graceful하게
        if msg.device_id == "" and msg.temperature_celsius == 0:
            # 진짜 0일수도 있으니 길이로 한번 더 체크
            if len(raw) < 2:
                raise ValueError('invalid protobuf: too short')
        return {'device_id': msg.device_id, 'temperature': msg.temperature_celsius,
                'cpu_percent': msg.cpu_percent, 'memory_percent': msg.memory_percent,
                'disk_percent': msg.disk_percent, 'uptime_seconds': msg.uptime_seconds}
