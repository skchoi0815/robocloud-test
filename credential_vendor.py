import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sts_client = boto3.client('sts', region_name='us-east-1')

def verify_secret(plain, stored_hash):
    # 단위테스트용: 'hashed-secret'면 test-secret-key만 통과
    # 실전 Ch3처럼: hashlib.pbkdf2_hmac / bcrypt.checkpw로 교체
    if stored_hash == 'hashed-secret':
        return plain == 'test-secret-key'
    return False

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except:
        return {'statusCode': 400, 'body': json.dumps({'error': 'invalid json'})}

    device_id = body.get('device_id')
    device_secret = body.get('device_secret')

    # 17장 Sec1 교훈: 4시간 블랙아웃 방지 = 시작하자마자 검증
    if not device_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'device_id required'})}
    if not device_secret:
        return {'statusCode': 400, 'body': json.dumps({'error': 'device_secret required'})}

    table = dynamodb.Table('device-fleet')
    resp = table.get_item(Key={'device_id': device_id})
    item = resp.get('Item')
    if not item:
        return {'statusCode': 403, 'body': json.dumps({'error': 'device not registered'})}
    if item.get('status') != 'active':
        return {'statusCode': 403, 'body': json.dumps({'error': 'device inactive'})}
    if not verify_secret(device_secret, item.get('device_secret_hash', '')):
        return {'statusCode': 401, 'body': json.dumps({'error': 'invalid credentials'})}

    sts_resp = sts_client.assume_role(
        RoleArn=item['iam_role_arn'],
        RoleSessionName=device_id,
        DurationSeconds=3600,
        SessionPolicies=[{
            'PolicyName': 'device-scoped',
            'PolicyDocument': json.dumps({
                'Version': '2012-10-17',
                'Statement': [{'Effect': 'Allow', 'Action': ['s3:PutObject'], 'Resource': '*'}]
            })
        }]
    )
    c = sts_resp['Credentials']
    return {'statusCode': 200, 'body': json.dumps({'credentials': {
        'AccessKeyId': c['AccessKeyId'],
        'SecretAccessKey': c['SecretAccessKey'],
        'SessionToken': c['SessionToken']
    }})}
