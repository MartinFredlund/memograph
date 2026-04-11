from uuid import uuid4
from neo4j import Session

from app.images import storage


def create_image(
    session: Session,
    uploader_uid: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> dict:
    """Store the file in MinIO and create an :Image Node linked to the uploader."""
    image_uid = str(uuid4())
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    object_key = f"images/{image_uid}.{extension}"
    storage.upload(object_key, content, content_type)
    query = """
        MATCH (u:User {uid: $uploader_uid})
        CREATE (i:Image {
            uid: $uid,
            filename: $filename,
            object_key: $object_key,
            content_type: $content_type,
            size_bytes: $size_bytes,
            uploaded_at: timestamp()
        })
        CREATE (i)-[:UPLOADED_BY]->(u)
        RETURN i
    """
    result = session.run(
        query,
        uploader_uid=uploader_uid,
        uid=image_uid,
        filename=filename,
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(content),
    )
    record = result.single()
    return dict(record["i"])
