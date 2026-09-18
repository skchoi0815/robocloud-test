from locust import User, task, between, events
import time, base64
from datetime import datetime, timezone
from protobuf_codec import ProtobufCodec
from presigned_url_handler import validate_upload_request
import robotics_messages_v2_pb2 as proto

codec = ProtobufCodec()

class EdgeDevice(User):
    wait_time = between(0.1, 0.5)
    def on_start(self):
        self.device_id = f"TURRET-{int(time.time()*1000)%10000}"

    @task(10)
    def send_telemetry(self):
        start = time.perf_counter()
        data = codec.encode_telemetry(self.device_id, {
            'temperature': 45.0 + (time.time() % 20),
            'cpu_percent': 60.0, 'memory_percent': 70.0,
            'uptime_seconds': int(time.time())
        })
        codec.decode_telemetry(data)
        elapsed = (time.perf_counter()-start)*1000
        events.request.fire(
            request_type="proto", name="telemetry_encode_decode",
            response_time=elapsed, response_length=len(data), exception=None)

    @task(3)
    def request_presigned_url(self):
        start = time.perf_counter()
        try:
            validate_upload_request({
                'object_type': 'image', 'content_type': 'image/jpeg',
                'size_bytes': 2_500_000})
            elapsed = (time.perf_counter()-start)*1000
            events.request.fire(request_type="validate", name="presigned_validate",
                response_time=elapsed, response_length=0, exception=None)
        except Exception as e:
            events.request.fire(request_type="validate", name="presigned_validate",
                response_time=0, response_length=0, exception=e)

    @task(1)
    def send_ping(self):
        start = time.perf_counter()
        ping = proto.Ping()
        ping.client_timestamp.FromDatetime(datetime.now(timezone.utc))
        env = proto.Message()
        env.id = "test-id"
        env.timestamp.FromDatetime(datetime.now(timezone.utc))
        env.ping.CopyFrom(ping)
        b64 = base64.b64encode(env.SerializeToString()).decode('utf-8')
        # decode back
        env2 = proto.Message()
        env2.ParseFromString(base64.b64decode(b64))
        elapsed = (time.perf_counter()-start)*1000
        events.request.fire(request_type="proto", name="ping_pong",
            response_time=elapsed, response_length=len(b64),
            exception=None if env2.HasField('ping') else Exception("no ping"))

@events.request.add_listener
def on_request(request_type, name, response_time, **kwargs):
    if response_time and response_time > 1000:
        print(f"SLOW: {name} took {response_time:.0f}ms")
