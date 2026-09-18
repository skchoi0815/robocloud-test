import boto3, json
from moto import mock_aws
from incident_response import IncidentResponder
from token_rotation import BearerTokenRotation

def make_table():
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.create_table(TableName='device-fleet',
        KeySchema=[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}],
        AttributeDefinitions=[{'AttributeName':'PK','AttributeType':'S'},{'AttributeName':'SK','AttributeType':'S'}],
        BillingMode='PAY_PER_REQUEST')

@mock_aws
def test_contain_revokes_token():
    make_table()
    r = BearerTokenRotation()
    r._rotate_device_token('TURRET-042')
    resp = IncidentResponder().respond_to_compromise('TURRET-042', {'type': 'CRYPTOMINER_DETECTED', 'severity': 'CRITICAL'})
    assert resp['status'] == 'CONTAINED'
    assert resp['response_time_seconds'] <= 12
    sec = r.secrets_manager.get_secret_value(SecretId='device/TURRET-042/bearer-token')
    assert json.loads(sec['SecretString'])['status'] == 'REVOKED'

@mock_aws
def test_contain_actions_logged():
    make_table()
    resp = IncidentResponder().respond_to_compromise('TURRET-031', {'type': 'REVERSE_SHELL_DETECTED'})
    assert 'Bearer token revoked' in resp['actions_taken']
    assert resp['device_id'] == 'TURRET-031'
