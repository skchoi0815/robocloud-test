import json
import boto3
import pytest
from moto import mock_aws

REGION = 'us-east-1'

@mock_aws
def test_s3_upload_triggers_processing():
    s3 = boto3.client('s3', region_name=REGION)
    sns = boto3.client('sns', region_name=REGION)
    sqs = boto3.client('sqs', region_name=REGION)

    # 1. infra 만들기 - Ch4 그대로
    s3.create_bucket(Bucket='device-uploads')
    topic_arn = sns.create_topic(Name='upload-events')['TopicArn']
    queue_url = sqs.create_queue(QueueName='processing-queue')['QueueUrl']
    queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])['Attributes']['QueueArn']

    sns.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)

    # 2. Device가 S3에 업로드 - Ch6 presigned 후 PUT이라고 가정
    test_key = 'TURRET-001/01HYVV6KX9.jpg'
    s3.put_object(
        Bucket='device-uploads',
        Key=test_key,
        Body=b'test image data',
        Metadata={'device_id': 'TURRET-001', 'object_type': 'image'},
        ContentType='image/jpeg'
    )

    # 3. S3 Event를 SNS로 발행 - 실제는 S3 notification이 하지만 moto에선 직접 쏜다
    s3_event = {
        'Records': [{
            'eventName': 'ObjectCreated:Put',
            's3': {
                'bucket': {'name': 'device-uploads'},
                'object': {'key': test_key}
            }
        }]
    }
    sns.publish(TopicArn=topic_arn, Message=json.dumps(s3_event))

    # 4. SQS에서 받았는지 확인 - SNS fanout 됐나?
    resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1)
    assert 'Messages' in resp, "SQS에 메시지 없음 - SNS 구독 확인"
    outer = json.loads(resp['Messages'][0]['Body'])
    inner = json.loads(outer['Message'])
    assert inner['Records'][0]['eventName'] == 'ObjectCreated:Put'
    assert 'TURRET-001' in inner['Records'][0]['s3']['object']['key']

@mock_aws
def test_dynamodb_result_write():
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.create_table(
        TableName='detection-results',
        KeySchema=[
            {'AttributeName': 'device_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'device_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.put_item(Item={
        'device_id': 'TURRET-001',
        'timestamp': 1714752131,
        'detection': 'DRONE',
        'confidence': '0.87'
    })
    got = table.get_item(Key={'device_id': 'TURRET-001', 'timestamp': 1714752131})['Item']
    assert got['detection'] == 'DRONE'
