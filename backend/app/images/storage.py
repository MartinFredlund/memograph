from datetime import timedelta
from io import BytesIO

from minio.error import S3Error

from app.config import get_settings
from app.db.minio_client import get_client


def upload(object_key: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes to the configured bucket under the given key."""
    client = get_client()
    bucket = get_settings().MINIO_BUCKET
    client.put_object(
        bucket_name=bucket,
        object_name=object_key,
        data=BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def download(object_key: str) -> bytes:
    """Fetch an object's raw bytes from the bucket."""
    client = get_client()
    bucket = get_settings().MINIO_BUCKET
    response = client.get_object(bucket_name=bucket, object_name=object_key)

    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def presigned_url(object_key: str, expires_minutes: int = 60) -> str:
    """Return a time-limited HTTPS URL the browser can use to fetch the object."""
    client = get_client()
    bucket = get_settings().MINIO_BUCKET
    return client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=timedelta(minutes=expires_minutes),
    )


def delete(object_key: str) -> None:
    """Remove an object from the bucket. No-op if already gone."""
    client = get_client()
    bucket = get_settings().MINIO_BUCKET
    try:
        client.remove_object(bucket, object_key)
    except S3Error:
        pass
