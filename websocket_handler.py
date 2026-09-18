import base64
import boto3
from datetime import datetime, timezone
import robotics_messages_v2_pb2 as proto

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
apigateway = boto3.client('apigatewaymanagementapi', region_name='us-east-1', endpoint_url='https://example.com')

def validate_token(token):
    return token == 'valid-bearer-token'

def connect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    qs = event.get('queryStringParameters', {}) or {}
    device_id = qs.get('device_id')
    token = qs.get('token')
    if not validate_token(token):
        return {'statusCode': 401}
    table = dynamodb.Table('connections')
    table.put_item(Item={
        'connection_id': connection_id,
        'device_id': device_id,
        'connected_at': datetime.now(timezone.utc).isoformat()
    })
    return {'statusCode': 200}

def disconnect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    table = dynamodb.Table('connections')
    table.delete_item(Key={'connection_id': connection_id})
    return {'statusCode': 200}

def message_handler(event, context):
    try:
        body = event.get('body', '')
        proto_bytes = base64.b64decode(body)
        envelope = proto.Message()
        envelope.ParseFromString(proto_bytes)
    except Exception:
        return {'statusCode': 400}
    if not envelope.HasField('ping'):
        return {'statusCode': 400}
    try:
        table = dynamodb.Table('connections')
        table.get_item(Key={'connection_id': event['requestContext']['connectionId']})
        pong = proto.Pong()
        pong.client_timestamp.CopyFrom(envelope.ping.client_timestamp)
        pong.server_timestamp.FromDatetime(datetime.now(timezone.utc))
        resp = proto.Message()
        resp.id = envelope.id
        resp.timestamp.FromDatetime(datetime.now(timezone.utc))
        resp.pong.CopyFrom(pong)
        data = resp.SerializeToString()
        encoded = base64.b64encode(data).decode('utf-8')
        apigateway.post_to_connection(
            ConnectionId=event['requestContext']['connectionId'],
            Data=encoded
        )
        return {'statusCode': 200}
    except Exception:
        return {'statusCode': 500}
