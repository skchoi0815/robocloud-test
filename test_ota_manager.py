import boto3
import pytest
from moto import mock_aws
from device_registry import DeviceRegistry
from ota_manager import OTAManager, UpdateStrategy

REGION='us-east-1'
TABLE='device-fleet'

def make_fleet(n=10):
    dyn = boto3.resource('dynamodb', region_name=REGION)
    dyn.create_table(
        TableName=TABLE,
        KeySchema=[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}],
        AttributeDefinitions=[{'AttributeName':'PK','AttributeType':'S'},{'AttributeName':'SK','AttributeType':'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    reg = DeviceRegistry(table_name=TABLE)
    for i in range(n):
        reg.register_device(f'TURRET-{i:03d}', f'conn-{i}', {'software':'2.3.0','group':'alpha'})
    return reg

@mock_aws
def test_create_canary_campaign():
    reg = make_fleet(10)
    ota = OTAManager(reg)
    cid = ota.create_update_campaign('2.3.1', strategy=UpdateStrategy.CANARY, dry_run=True)
    camp = ota._get_campaign(cid)
    assert len(camp['stages']) == 2
    assert len(camp['stages'][0]['devices']) == 1  # canary 1대
    assert camp['stages'][0]['success_threshold'] == 100

@mock_aws
def test_create_staged_campaign():
    reg = make_fleet(10)
    ota = OTAManager(reg)
    cid = ota.create_update_campaign('2.4.0', strategy=UpdateStrategy.STAGED, dry_run=True)
    camp = ota._get_campaign(cid)
    assert len(camp['stages']) == 4
    assert camp['stages'][0]['percentage'] == 10

@mock_aws
def test_execute_stage_dry_run():
    reg = make_fleet(5)
    ota = OTAManager(reg)
    cid = ota.create_update_campaign('2.3.1', strategy=UpdateStrategy.CANARY, dry_run=True)
    res = ota.execute_stage(cid, 1)
    assert res['stage_result'] == 'SUCCESS'
    assert res['success_rate'] == 100
    camp = ota._get_campaign(cid)
    assert len(camp['successful_updates']) == 1

@mock_aws
def test_rollback_no_crash():
    reg = make_fleet(3)
    ota = OTAManager(reg)
    cid = ota.create_update_campaign('2.3.1', strategy=UpdateStrategy.CANARY, dry_run=True)
    ota.execute_stage(cid, 1)
    assert ota.rollback_campaign(cid, reason="test") is True
