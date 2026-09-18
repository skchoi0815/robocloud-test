import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from credential_vendor import handler

@pytest.fixture
def valid_request():
    return {
        'httpMethod': 'POST',
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'device_id': 'TURRET-001','device_secret': 'test-secret-key'})
    }

@patch('credential_vendor.dynamodb')
@patch('credential_vendor.sts_client')
def test_valid_device_gets_credentials(mock_sts, mock_dynamo, valid_request):
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {
        'device_id': 'TURRET-001',
        'device_secret_hash': 'hashed-secret',
        'status': 'active',
        'iam_role_arn': 'arn:aws:iam::123456789012:role/DeviceRole'}}
    mock_dynamo.Table.return_value = mock_table
    mock_sts.assume_role.return_value = {'Credentials': {
        'AccessKeyId': 'ASIA...', 'SecretAccessKey': 'secret',
        'SessionToken': 'token',
        'Expiration': (datetime.now() + timedelta(hours=1)).isoformat()}}
    response = handler(valid_request, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['credentials']['AccessKeyId'].startswith('ASIA')
    assert 'SessionPolicies' in mock_sts.assume_role.call_args.kwargs

@patch('credential_vendor.dynamodb')
def test_unknown_device_rejected(mock_dynamo, valid_request):
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    mock_dynamo.Table.return_value = mock_table
    response = handler(valid_request, None)
    assert response['statusCode'] == 403

@patch('credential_vendor.dynamodb')
def test_inactive_device_rejected(mock_dynamo, valid_request):
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {'device_id': 'TURRET-001','status': 'decommissioned'}}
    mock_dynamo.Table.return_value = mock_table
    response = handler(valid_request, None)
    assert response['statusCode'] == 403

@patch('credential_vendor.dynamodb')
def test_wrong_secret_rejected(mock_dynamo, valid_request):
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {
        'device_id': 'TURRET-001','device_secret_hash': 'different-hash','status': 'active'}}
    mock_dynamo.Table.return_value = mock_table
    response = handler(valid_request, None)
    assert response['statusCode'] == 401

def test_missing_device_id_fails_validation():
    invalid_request = {'httpMethod': 'POST','body': json.dumps({'device_secret': 'test'})}
    response = handler(invalid_request, None)
    assert response['statusCode'] == 400
