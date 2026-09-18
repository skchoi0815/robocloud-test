import pytest
from unittest.mock import patch
from presigned_url_handler import generate_presigned_url, validate_upload_request

@pytest.fixture
def upload_request():
    return {'object_type': 'image', 'content_type': 'image/jpeg',
            'size_bytes': 2621440, 'ulid': '01HYVV6KX9R8SBZ3JX2W8YQB3G'}

@patch('presigned_url_handler.s3_client')
def test_generate_presigned_url_for_valid_request(mock_s3, upload_request):
    mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/bucket/key?signature=...'
    result = generate_presigned_url(device_id='TURRET-001', **upload_request)
    assert 'upload_url' in result
    assert result['object_key'] == f"TURRET-001/{upload_request['ulid']}.jpg"
    call_args = mock_s3.generate_presigned_url.call_args
    assert call_args.args[0] == 'put_object'
    assert call_args.kwargs['Params']['ContentType'] == 'image/jpeg'
    assert call_args.kwargs['Params']['ServerSideEncryption'] == 'AES256'

def test_reject_oversized_upload(upload_request):
    upload_request['size_bytes'] = 50_000_000
    with pytest.raises(ValueError, match='exceeds maximum'):
        validate_upload_request(upload_request)

def test_reject_invalid_content_type(upload_request):
    upload_request['content_type'] = 'application/x-executable'
    with pytest.raises(ValueError, match='content type not allowed'):
        validate_upload_request(upload_request)

@pytest.mark.parametrize("object_type,max_size", [
    ('image', 10*1024*1024), ('video', 100*1024*1024), ('audio', 50*1024*1024)])
def test_size_limits_by_type(object_type, max_size, upload_request):
    upload_request['object_type'] = object_type
    upload_request['size_bytes'] = max_size - 1
    validate_upload_request(upload_request)
    upload_request['size_bytes'] = max_size + 1
    with pytest.raises(ValueError):
        validate_upload_request(upload_request)

@patch('presigned_url_handler.s3_client')
def test_presigned_url_expires_in_5_minutes(mock_s3, upload_request):
    generate_presigned_url(device_id='TURRET-001', **upload_request)
    assert mock_s3.generate_presigned_url.call_args.kwargs['ExpiresIn'] == 300
