import boto3
from moto import mock_aws
from device_registry import DeviceRegistry
from health_monitor import HealthMonitor

def make_reg():
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.create_table(TableName='device-fleet',
        KeySchema=[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}],
        AttributeDefinitions=[{'AttributeName':'PK','AttributeType':'S'},{'AttributeName':'SK','AttributeType':'S'}],
        BillingMode='PAY_PER_REQUEST')
    return DeviceRegistry(table_name='device-fleet')

@mock_aws
def test_healthy_device():
    reg = make_reg()
    reg.register_device('TURRET-001', 'c1', {'software':'2.3.1'})
    reg.update_telemetry('TURRET-001', {'temperature':55,'avg_fps':28})
    h = HealthMonitor(reg).check_device_health('TURRET-001')
    assert h['status'] == 'HEALTHY'
    assert h['score'] == 100

@mock_aws
def test_high_temp_triggers_remediation():
    reg = make_reg()
    reg.register_device('TURRET-001', 'c1', {})
    reg.update_telemetry('TURRET-001', {'temperature':75,'avg_fps':28})
    h = HealthMonitor(reg).check_device_health('TURRET-001')
    assert h['status'] == 'HEALTHY'  # 100-20=80, 턱걸이
    assert 'Reduced compute load' in h['auto_remediation']

@mock_aws
def test_offline_is_critical():
    reg = make_reg()
    reg.register_device('TURRET-001', 'c1', {})
    reg.disconnect_device('c1')
    h = HealthMonitor(reg).check_device_health('TURRET-001')
    assert h['status'] == 'CRITICAL'
    assert h['issues'][0]['type'] == 'NO_CONNECTION'
