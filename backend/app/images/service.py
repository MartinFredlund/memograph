from enum import Enum
from io import BytesIO
from typing import Any
from uuid import uuid4
import json
import base64
from neo4j import Session
from PIL import Image, ImageOps

from app.auth.schemas import TokenPayload, UserRole
from app.images import storage
from app.images.schemas import (
    ImageCountParams,
    ImageCountResponse,
    ImageListItem,
    ImageListParams,
    PaginatedImages,
)

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


class PlaceResult(str, Enum):
    OK = "ok"
    IMAGE_NOT_FOUND = "image_not_found"
    PLACE_NOT_FOUND = "place_not_found"


class EventResult(str, Enum):
    OK = "ok"
    IMAGE_NOT_FOUND = "image_not_found"
    EVENT_NOT_FOUND = "event_not_found"


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


def set_place(session: Session, image_uid: str, place_uid: str) -> PlaceResult:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    image_record = image_result.single()
    if image_record is None:
        return PlaceResult.IMAGE_NOT_FOUND
    place_result = session.run(
        "MATCH (p:Place {uid: $place_uid}) RETURN 1", place_uid=place_uid
    )
    place_record = place_result.single()
    if place_record is None:
        return PlaceResult.PLACE_NOT_FOUND
    query = """
        MATCH (i:Image {uid: $image_uid})
        OPTIONAL MATCH (i)-[r:TAKEN_AT]->(:Place)
        DELETE r
        WITH i
        MATCH (p:Place {uid: $place_uid})
        CREATE (i)-[:TAKEN_AT]->(p)
    """
    session.run(query, image_uid=image_uid, place_uid=place_uid)
    return PlaceResult.OK


def unset_place(session: Session, image_uid: str) -> PlaceResult:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    image_record = image_result.single()
    if image_record is None:
        return PlaceResult.IMAGE_NOT_FOUND
    session.run(
        "OPTIONAL MATCH (:Image {uid: $image_uid}) - [r:TAKEN_AT] -> () DELETE r",
        image_uid=image_uid,
    )
    return PlaceResult.OK


def set_event(session: Session, image_uid: str, event_uid: str) -> EventResult:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    if image_result.single() is None:
        return EventResult.IMAGE_NOT_FOUND
    event_result = session.run(
        "MATCH (e:Event {uid: $event_uid}) RETURN 1", event_uid=event_uid
    )
    if event_result.single() is None:
        return EventResult.EVENT_NOT_FOUND
    query = """
        MATCH (i:Image {uid: $image_uid})
        OPTIONAL MATCH (i)-[r:FROM_EVENT]->(:Event)
        DELETE r
        WITH i
        MATCH (e:Event {uid: $event_uid})
        CREATE (i)-[:FROM_EVENT]->(e)
    """
    session.run(query, image_uid=image_uid, event_uid=event_uid)
    return EventResult.OK


def unset_event(session: Session, image_uid: str) -> EventResult:
    image_result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN 1", image_uid=image_uid
    )
    if image_result.single() is None:
        return EventResult.IMAGE_NOT_FOUND
    session.run(
        "OPTIONAL MATCH (:Image {uid: $image_uid})-[r:FROM_EVENT]->() DELETE r",
        image_uid=image_uid,
    )
    return EventResult.OK


def get_download_url(session: Session, uid: str) -> str | None:
    result = session.run(
        "MATCH (i:Image {uid: $image_uid}) RETURN i.object_key AS object_key, i.filename AS filename",
        image_uid=uid,
    )
    record = result.single()
    if record is None:
        return None
    filename = record["filename"] or "image"
    return storage.presigned_url(
        object_key=record["object_key"], expires_minutes=5, download_filename=filename
    )


def encode_cursor(uploaded_at_ms: int, uid: str) -> str:
    payload = {"uploaded_at_ms": uploaded_at_ms, "uid": uid}
    raw = json.dumps(payload).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw)
    return encoded.decode("ascii")


def decode_cursor(cursor: str) -> tuple[int, str]:
    try:
        encoded = cursor.encode("ascii")
        raw = base64.urlsafe_b64decode(encoded)
        payload = json.loads(raw)
        return payload["uploaded_at_ms"], payload["uid"]
    except (ValueError, KeyError, TypeError) as e:
        raise ValueError("invalid cursor") from e


def list_images(session: Session, params: ImageListParams) -> PaginatedImages:
    query = """
        MATCH (i:Image)
        WHERE ($person_uid IS NULL OR EXISTS {(:Person {uid: $person_uid})-[:APPEARS_IN]->(i)})
        AND ($event_uid IS NULL OR EXISTS {(i)-[:FROM_EVENT]->(:Event {uid: $event_uid})})
        AND ($place_uid IS NULL OR EXISTS {(i)-[:TAKEN_AT]->(:Place {uid: $place_uid})})
        AND ($cursor_ts IS NULL OR i.uploaded_at < $cursor_ts
        OR (i.uploaded_at = $cursor_ts AND i.uid < $cursor_uid))
        WITH i
        ORDER BY i.uploaded_at DESC, i.uid DESC
        LIMIT $limit_plus_one
        OPTIONAL MATCH (p:Person)-[:APPEARS_IN]->(i)
        WITH i,
            [person IN collect(DISTINCT p) WHERE person IS NOT NULL
            | {person_uid: person.uid, person_name: person.name}] AS tags
        OPTIONAL MATCH (i)-[:FROM_EVENT]->(e:Event)
        OPTIONAL MATCH (i)-[:TAKEN_AT]->(pl:Place)
        RETURN i, tags,
        CASE WHEN e IS NOT NULL
            THEN {event_uid: e.uid, event_name: e.name}
        END AS event,
        CASE WHEN pl IS NOT NULL
            THEN {place_uid: pl.uid, place_name: pl.name}
        END AS place
        ORDER BY i.uploaded_at DESC, i.uid DESC
        """
    if params.cursor is None:
        cursor_ts, cursor_uid = None, None
    else:
        cursor_ts, cursor_uid = decode_cursor(params.cursor)
    records = list(
        session.run(
            query,
            person_uid=params.person_uid,
            event_uid=params.event_uid,
            place_uid=params.place_uid,
            cursor_ts=cursor_ts,
            cursor_uid=cursor_uid,
            limit_plus_one=params.page_size + 1,
        )
    )
    has_more = len(records) > params.page_size
    page_records = records[: params.page_size]

    items = [
        ImageListItem(
            **dict(rec["i"]), tags=rec["tags"], event=rec["event"], place=rec["place"]
        )
        for rec in page_records
    ]

    next_cursor = None
    if has_more:
        last_rec = page_records[-1]
        next_cursor = encode_cursor(last_rec["i"]["uploaded_at"], last_rec["i"]["uid"])
    return PaginatedImages(items=items, next_cursor=next_cursor)


def count_images(session: Session, params: ImageCountParams) -> ImageCountResponse:
    query = """
        MATCH (i:Image)
        WHERE ($person_uid IS NULL OR EXISTS {(:Person {uid: $person_uid})-[:APPEARS_IN]->(i)})
        AND ($event_uid IS NULL OR EXISTS {(i)-[:FROM_EVENT]->(:Event {uid: $event_uid})})
        AND ($place_uid IS NULL OR EXISTS {(i)-[:TAKEN_AT]->(:Place {uid: $place_uid})})
        RETURN count(i) AS count
    """
    result = session.run(
        query,
        person_uid=params.person_uid,
        event_uid=params.event_uid,
        place_uid=params.place_uid,
    )
    record = result.single()
    return ImageCountResponse(count=record["count"])
