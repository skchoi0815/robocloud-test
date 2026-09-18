import boto3, os
from decimal import Decimal
from moto import mock_aws
import agent_tools

def make_tables():
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    for tn, pk in [('tracks','track_id'),('devices','device_id'),('audit','audit_id')]:
        dyn.create_table(TableName=tn,
            KeySchema=[{'AttributeName':pk,'KeyType':'HASH'}],
            AttributeDefinitions=[{'AttributeName':pk,'AttributeType':'S'}],
            BillingMode='PAY_PER_REQUEST')
    os.environ['TRACKS_TABLE']='tracks'
    os.environ['DEVICES_TABLE']='devices'
    os.environ['AUDIT_TABLE']='audit'

@mock_aws
def test_get_active_tracks():
    make_tables()
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.Table('tracks').put_item(Item={'track_id':'trk-d9e8','region':'sector_gamma','status':'ACTIVE','confidence':Decimal('0.98'),'velocity':Decimal('25'),'altitude':Decimal('45'),'distance_to_facility':Decimal('320'),'threat_level':'HIGH'})
    dyn.Table('tracks').put_item(Item={'track_id':'trk-low','region':'sector_gamma','status':'ACTIVE','confidence':Decimal('0.5'),'velocity':Decimal('5')})
    tracks = agent_tools.get_active_tracks('sector_gamma', min_confidence=0.7)
    assert len(tracks) == 1
    assert tracks[0]['track_id'] == 'trk-d9e8'

@mock_aws
def test_threat_assessment_high():
    make_tables()
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.Table('tracks').put_item(Item={'track_id':'trk-d9e8','velocity':Decimal('25'),'altitude':Decimal('45'),'distance_to_facility':Decimal('320'),'heading_towards_facility':True})
    r = agent_tools.get_threat_assessment('trk-d9e8')
    assert r['threat_level'] == 'HIGH'
    assert r['threat_score'] == 100
    assert r['recommendation'] == 'ENGAGE'

@mock_aws
def test_assign_turret_success():
    make_tables()
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.Table('tracks').put_item(Item={'track_id':'trk-d9e8','velocity':Decimal('25')})
    dyn.Table('devices').put_item(Item={'device_id':'turret-04','status':'IDLE','region':'sector_gamma','connection_id':'conn-1','battery_level':87})
    r = agent_tools.assign_turret_to_track('turret-04','trk-d9e8',action='track')
    assert r['status'] == 'SUCCESS'
    dev = dyn.Table('devices').get_item(Key={'device_id':'turret-04'})['Item']
    assert dev['status'] == 'ACTIVE'
    assert dev['current_track'] == 'trk-d9e8'

@mock_aws
def test_assign_fails_no_connection():
    make_tables()
    dyn = boto3.resource('dynamodb', region_name='us-east-1')
    dyn.Table('tracks').put_item(Item={'track_id':'trk-d9e8'})
    dyn.Table('devices').put_item(Item={'device_id':'turret-05','status':'IDLE','region':'sector_gamma'})
    r = agent_tools.assign_turret_to_track('turret-05','trk-d9e8')
    assert r['status'] == 'ERROR'
