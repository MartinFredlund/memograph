from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image as PILImage

from app.auth.schemas import UserRole
from app.auth.service import create_access_token, create_user
from app.events.schemas import EventCreate
from app.events.service import create_event
from app.images import service as image_service
from app.images import storage as storage_module
from app.people.schemas import PersonCreate
from app.people.service import create_person
from app.places.schemas import PlaceCreate
from app.places.service import create_place


@pytest.fixture
def fake_storage(monkeypatch):
    """In-memory replacement for the MinIO-backed storage module.

    Using a plain dict keyed by object_key is enough to verify round-trip
    behavior (upload, re-download, delete) without starting another container.
    The real MinIO client is exercised via a manual smoke test instead.
    """
    store: dict[str, bytes] = {}

    def fake_upload(object_key: str, data: bytes, content_type: str) -> None:
        store[object_key] = data

    def fake_download(object_key: str) -> bytes:
        return store[object_key]

    def fake_delete(object_key: str) -> None:
        store.pop(object_key, None)

    def fake_presigned_url(
        object_key: str,
        expires_minutes: int = 60,
        download_filename: str | None = None,
    ) -> str:
        """Deterministic stand-in for the real presigned URL. Encodes the
        inputs as query params so tests can assert the service passed the
        right object_key and filename through."""
        url = f"https://fake-minio.test/{object_key}?expires={expires_minutes}"
        if download_filename is not None:
            url += f"&filename={download_filename}"
        return url

    monkeypatch.setattr(storage_module, "upload", fake_upload)
    monkeypatch.setattr(storage_module, "download", fake_download)
    monkeypatch.setattr(storage_module, "delete", fake_delete)
    monkeypatch.setattr(storage_module, "presigned_url", fake_presigned_url)
    return store


def _make_user(db_session, role: UserRole, username: str) -> dict:
    user = create_user(db_session, username, "unused-hash", role)
    return {
        "uid": user["uid"],
        "token": create_access_token(user["uid"], username, role),
    }


@pytest.fixture
def editor_user(db_session) -> dict:
    return _make_user(db_session, UserRole.EDITOR, "editor-a")


@pytest.fixture
def other_editor_user(db_session) -> dict:
    return _make_user(db_session, UserRole.EDITOR, "editor-b")


@pytest.fixture
def admin_user(db_session) -> dict:
    return _make_user(db_session, UserRole.ADMIN, "admin-a")


def make_test_image(width: int = 100, height: int = 50, fmt: str = "JPEG") -> bytes:
    """Generate a solid-color image as bytes. Default dims are asymmetric so
    callers can verify rotation swaps width/height."""
    img = PILImage.new("RGB", (width, height), color="red")
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_jpeg_with_orientation(
    width: int = 100, height: int = 50, orientation: int = 6
) -> bytes:
    """JPEG carrying an explicit EXIF Orientation tag.

    Orientation 6 means 'rotate 90° CW when displaying' — mimics what a
    phone emits when the user holds it in portrait. Used to regression-test
    that rotate_image normalizes orientation instead of double-rotating.
    """
    img = PILImage.new("RGB", (width, height), color="red")
    exif = img.getexif()
    exif[274] = orientation  # 274 == EXIF Orientation tag (0x0112)
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


@pytest.fixture
def seeded_image(db_session, fake_storage, editor_user) -> dict:
    """An image uploaded by `editor_user`, planted directly via the service.

    Bypasses the HTTP upload endpoint to keep tests focused on rotate/delete.
    """
    return image_service.create_image(
        session=db_session,
        uploader_uid=editor_user["uid"],
        filename="test.jpg",
        content=make_test_image(),
        content_type="image/jpeg",
    )


@pytest.fixture
def seeded_oriented_image(db_session, fake_storage, editor_user) -> dict:
    """An image whose EXIF Orientation is 6 (rotate-90-CW-on-display)."""
    return image_service.create_image(
        session=db_session,
        uploader_uid=editor_user["uid"],
        filename="oriented.jpg",
        content=make_jpeg_with_orientation(),
        content_type="image/jpeg",
    )


@pytest.fixture
def seeded_person(db_session) -> dict:
    """A bare Person node to point face-tag relationships at."""
    return create_person(db_session, PersonCreate(name="Alice Example"))


@pytest.fixture
def seeded_place(db_session) -> dict:
    return create_place(db_session, PlaceCreate(name="Grandma's House"))


@pytest.fixture
def other_seeded_place(db_session) -> dict:
    """Second place, used to verify the 'exactly one TAKEN_AT' invariant."""
    return create_place(db_session, PlaceCreate(name="Beach House"))


@pytest.fixture
def seeded_event(db_session) -> dict:
    return create_event(db_session, EventCreate(name="Christmas 2024"))


@pytest.fixture
def other_seeded_event(db_session) -> dict:
    """Second event, used to verify the 'exactly one FROM_EVENT' invariant."""
    return create_event(db_session, EventCreate(name="New Year's Eve 2024"))
