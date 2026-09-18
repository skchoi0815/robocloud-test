import boto3, json
from moto import mock_aws
from token_rotation import BearerTokenRotation

def make_rot():
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.create_table(TableName='device-fleet',
        KeySchema=[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}],
        AttributeDefinitions=[{'AttributeName':'PK','AttributeType':'S'},{'AttributeName':'SK','AttributeType':'S'}],
        BillingMode='PAY_PER_REQUEST')
    return BearerTokenRotation(table_name='device-fleet')

@mock_aws
def test_needs_rotation_when_no_token():
    r = make_rot()
    assert r._needs_rotation('TURRET-031') is True

@mock_aws
def test_rotate_creates_token():
    r = make_rot()
    r._rotate_device_token('TURRET-031')
    sec = r.secrets_manager.get_secret_value(SecretId='device/TURRET-031/bearer-token')
    data = json.loads(sec['SecretString'])
    assert len(data['token']) >= 40
    assert data['rotation_count'] == 1
    assert r._needs_rotation('TURRET-031') is False

@mock_aws
def test_emergency_revoke():
    r = make_rot()
    r._rotate_device_token('TURRET-031')
    r.emergency_revoke_token('TURRET-031', reason='Jake laptop stolen')
    sec = r.secrets_manager.get_secret_value(SecretId='device/TURRET-031/bearer-token')
    data = json.loads(sec['SecretString'])
    assert data['status'] == 'REVOKED'
    assert r._needs_rotation('TURRET-031') is True
