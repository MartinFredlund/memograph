from minio import Minio
from pydantic import SecretStr

_client: Minio | None = None


def connect(endpoint: str, access_key: str, secret_key: SecretStr, bucket: str) -> None:
    global _client
    _client = Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key.get_secret_value(),
        secure=False,
    )
    # Create the bucket if it doesn't exist yet (first run)
    if not _client.bucket_exists(bucket):
        _client.make_bucket(bucket)


def get_client() -> Minio:
    if _client is None:
        raise RuntimeError("MinIO client not initialised — call connect() first")
    return _client
