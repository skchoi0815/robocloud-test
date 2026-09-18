import boto3
import pytest
from moto import mock_aws
from device_registry import DeviceRegistry

REGION='us-east-1'
TABLE='device-fleet'

def make_registry():
    dyn = boto3.resource('dynamodb', region_name=REGION)
    dyn.create_table(
        TableName=TABLE,
        KeySchema=[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}],
        AttributeDefinitions=[{'AttributeName':'PK','AttributeType':'S'},{'AttributeName':'SK','AttributeType':'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    return DeviceRegistry(table_name=TABLE)

@mock_aws
def test_register_device():
    reg = make_registry()
    item = reg.register_device('TURRET-001', 'conn-abc', {'software':'2.3.1','group':'alpha'})
    assert item['device_id'] == 'TURRET-001'
    assert item['status'] == 'ONLINE'
    assert item['connection_id'] == 'conn-abc'
    got = reg.get_device('TURRET-001')
    assert got['connection_count'] == 1

@mock_aws
def test_update_telemetry():
    reg = make_registry()
    reg.register_device('TURRET-001', 'conn-abc', {})
    ok = reg.update_telemetry('TURRET-001', {'temperature':55,'cpu_percent':40,'avg_fps':28,'software_version':'2.3.1'})
    assert ok is True
    got = reg.get_device('TURRET-001')
    assert float(got['temperature_celsius']) == 55
    assert float(got['avg_fps']) == 28

@mock_aws
def test_disconnect_device():
    reg = make_registry()
    reg.register_device('TURRET-001', 'conn-abc', {})
    assert reg.disconnect_device('conn-abc') is True
    got = reg.get_device('TURRET-001')
    assert got['status'] == 'OFFLINE'

@mock_aws
def test_get_fleet_status():
    reg = make_registry()
    reg.register_device('TURRET-001', 'c1', {'software':'2.3.1'})
    reg.register_device('TURRET-002', 'c2', {'software':'2.3.1'})
    reg.update_telemetry('TURRET-001', {'temperature':72,'avg_fps':10})
    reg.disconnect_device('c2')
    status = reg.get_fleet_status()
    assert status['total_devices'] == 2
    assert status['online_devices'] == 1
    assert status['offline_devices'] == 1
    assert any(i['issue']=='HIGH_TEMP' for i in status['issues'])
