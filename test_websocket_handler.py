import base64
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from websocket_handler import connect_handler, disconnect_handler, message_handler
import robotics_messages_v2_pb2 as proto

@pytest.fixture
def connect_event():
    return {
        'requestContext': {'connectionId': 'abc123xyz', 'routeKey': '$connect'},
        'queryStringParameters': {'device_id': 'TURRET-001', 'token': 'valid-bearer-token'}
    }

@patch('websocket_handler.dynamodb')
@patch('websocket_handler.validate_token')
def test_valid_device_connects(mock_validate, mock_dynamo, connect_event):
    mock_validate.return_value = True
    mock_table = MagicMock()
    mock_dynamo.Table.return_value = mock_table
    response = connect_handler(connect_event, None)
    assert response['statusCode'] == 200
    item = mock_table.put_item.call_args.kwargs['Item']
    assert item['connection_id'] == 'abc123xyz'
    assert item['device_id'] == 'TURRET-001'

@patch('websocket_handler.validate_token')
def test_invalid_token_rejected(mock_validate, connect_event):
    mock_validate.return_value = False
    response = connect_handler(connect_event, None)
    assert response['statusCode'] == 401

@patch('websocket_handler.dynamodb')
def test_disconnect_removes_connection(mock_dynamo):
    mock_table = MagicMock()
    mock_dynamo.Table.return_value = mock_table
    event = {'requestContext': {'connectionId': 'abc123xyz', 'routeKey': '$disconnect'}}
    response = disconnect_handler(event, None)
    assert response['statusCode'] == 200
    mock_table.delete_item.assert_called_once_with(Key={'connection_id': 'abc123xyz'})

def make_ping_event():
    ping = proto.Ping()
    ping.client_timestamp.FromDatetime(datetime.now(timezone.utc))
    env = proto.Message()
    env.id = '01HYVV6KX9R8SBZ3JX2W8YQB3G'
    env.timestamp.FromDatetime(datetime.now(timezone.utc))
    env.ping.CopyFrom(ping)
    b64 = base64.b64encode(env.SerializeToString()).decode('utf-8')
    return {'requestContext': {'connectionId': 'abc123xyz', 'routeKey': '$default'}, 'body': b64}

@patch('websocket_handler.apigateway')
@patch('websocket_handler.dynamodb')
def test_ping_message_gets_pong(mock_dynamo, mock_apigw):
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {'device_id': 'TURRET-001'}}
    mock_dynamo.Table.return_value = mock_table
    response = message_handler(make_ping_event(), None)
    assert response['statusCode'] == 200
    args = mock_apigw.post_to_connection.call_args.kwargs
    assert args['ConnectionId'] == 'abc123xyz'
    env = proto.Message()
    env.ParseFromString(base64.b64decode(args['Data']))
    assert env.HasField('pong')

def test_invalid_protobuf_rejected():
    event = {'requestContext': {'connectionId': 'abc123xyz', 'routeKey': '$default'}, 'body': 'not-valid!!!'}
    assert message_handler(event, None)['statusCode'] == 400
