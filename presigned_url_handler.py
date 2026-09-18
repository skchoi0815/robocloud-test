import boto3
from datetime import datetime, timezone, timedelta

s3_client = boto3.client('s3', region_name='us-east-1')
BUCKET = 'device-uploads'

ALLOWED_TYPES = {
    'image/jpeg', 'image/png',
    'audio/wav', 'audio/opus', 'audio/webm',
    'video/mp4', 'video/webm'
}
MAX_SIZES = {
    'image': 10 * 1024 * 1024,
    'video': 100 * 1024 * 1024,
    'audio': 50 * 1024 * 1024,
}
EXT_MAP = {
    'image/jpeg': '.jpg', 'image/png': '.png',
    'audio/wav': '.wav', 'audio/opus': '.opus',
    'audio/webm': '.webm', 'video/mp4': '.mp4',
    'video/webm': '.webm',
}

def validate_upload_request(req):
    ct = req.get('content_type')
    ot = req.get('object_type')
    size = req.get('size_bytes', 0)
    if ct not in ALLOWED_TYPES:
        raise ValueError(f'content type not allowed: {ct}')
    max_size = MAX_SIZES.get(ot, 10*1024*1024)
    if size > max_size:
        raise ValueError(f'size {size} exceeds maximum {max_size} for {ot}')

def generate_presigned_url(device_id, object_type, content_type, size_bytes, ulid):
    req = {'object_type': object_type, 'content_type': content_type, 'size_bytes': size_bytes}
    validate_upload_request(req)
    ext = EXT_MAP.get(content_type, '.bin')
    object_key = f"{device_id}/{ulid}{ext}"
    url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': BUCKET,
            'Key': object_key,
            'ContentType': content_type,
            'ServerSideEncryption': 'AES256',
        },
        ExpiresIn=300
    )
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=300)).isoformat()
    return {'upload_url': url, 'object_key': object_key, 'expires_at': expires_at}
