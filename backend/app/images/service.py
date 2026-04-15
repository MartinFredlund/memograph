from enum import Enum
from io import BytesIO
from typing import Any
from uuid import uuid4

from neo4j import Session
from PIL import Image, ImageOps

from app.auth.schemas import TokenPayload, UserRole
from app.images import storage

ROTATION_MAP = {
    90: Image.Transpose.ROTATE_90,
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_270,
}


class TagResult(str, Enum):
    OK = "ok"
    IMAGE_NOT_FOUND = "image_not_found"
    PERSON_NOT_FOUND = "person_not_found"


class DeleteResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"


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


def rotate_image(session: Session, uid: str, degrees: int) -> dict | None:
    """Rotate the image in place (overwrites object in storage, updates size_bytes)."""
    query = """
        MATCH (i:Image {uid: $uid})
        RETURN i.object_key AS object_key, i.content_type AS content_type
    """
    result = session.run(query, uid=uid)
    record = result.single()
    if record is None:
        return None
    data = storage.download(record["object_key"])
    img = Image.open(BytesIO(data))
    original_format = img.format
    img = ImageOps.exif_transpose(img)
    rotated = img.transpose(ROTATION_MAP[degrees])
    buf = BytesIO()
    save_kwargs: dict[str, Any] = {"format": original_format}
    if original_format == "JPEG":
        save_kwargs["quality"] = 95
        exif = img.info.get("exif")
        if exif:
            save_kwargs["exif"] = exif
    rotated.save(buf, **save_kwargs)
    new_bytes = buf.getvalue()
    storage.upload(record["object_key"], new_bytes, record["content_type"])
    update_result = session.run(
        "MATCH (i:Image {uid: $uid}) SET i.size_bytes = $size_bytes RETURN i",
        uid=uid,
        size_bytes=len(new_bytes),
    )
    update = update_result.single()
    return dict(update["i"]) if update else None


def delete_image(
    session: Session,
    uid: str,
    requester: TokenPayload,
) -> DeleteResult:
    result = session.run(
        "MATCH (i:Image {uid: $uid})-[:UPLOADED_BY]->(u:User) RETURN i.object_key AS object_key, u.uid AS uploader_uid",
        uid=uid,
    )
    record = result.single()
    if record is None:
        return DeleteResult.NOT_FOUND
    is_admin = requester.role == UserRole.ADMIN
    is_owner_editor = (
        requester.role == UserRole.EDITOR and record["uploader_uid"] == requester.sub
    )
    if not (is_admin or is_owner_editor):
        return DeleteResult.FORBIDDEN
    session.run("MATCH (i:Image {uid: $uid}) DETACH DELETE i", uid=uid)
    storage.delete(record["object_key"])
    return DeleteResult.OK


def add_tag(
    session: Session,
    image_uid: str,
    person_uid: str,
    tag_x: float,
    tag_y: float,
) -> tuple[TagResult, dict | None]:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    image_record = image_result.single()
    if image_record is None:
        return (TagResult.IMAGE_NOT_FOUND, None)
    person_result = session.run(
        "MATCH (p:Person {uid: $person_uid}) RETURN p.name AS name",
        person_uid=person_uid,
    )
    person_record = person_result.single()
    if person_record is None:
        return (TagResult.PERSON_NOT_FOUND, None)
    session.run(
        "MATCH (i:Image {uid: $image_uid}), (p:Person {uid: $person_uid}) MERGE (p)-[r:APPEARS_IN]->(i) SET r.tag_x = $tag_x, r.tag_y = $tag_y",
        image_uid=image_uid,
        person_uid=person_uid,
        tag_x=tag_x,
        tag_y=tag_y,
    )
    return (
        TagResult.OK,
        {
            "person_uid": person_uid,
            "person_name": person_record["name"],
            "tag_x": tag_x,
            "tag_y": tag_y,
        },
    )


def remove_tag(session: Session, image_uid: str, person_uid: str) -> TagResult:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    image_record = image_result.single()
    if image_record is None:
        return TagResult.IMAGE_NOT_FOUND
    person_result = session.run(
        "MATCH (p:Person {uid: $person_uid}) RETURN 1", person_uid=person_uid
    )
    person_record = person_result.single()
    if person_record is None:
        return TagResult.PERSON_NOT_FOUND
    session.run(
        "MATCH (:Person {uid: $person_uid}) -[a:APPEARS_IN]->(:Image {uid: $image_uid}) DELETE a",
        person_uid=person_uid,
        image_uid=image_uid,
    )
    return TagResult.OK
