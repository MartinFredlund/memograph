from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image as PILImage

from app.auth.schemas import UserRole
from app.auth.service import create_access_token, create_user
from app.images import service as image_service
from app.images import storage as storage_module


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

    monkeypatch.setattr(storage_module, "upload", fake_upload)
    monkeypatch.setattr(storage_module, "download", fake_download)
    monkeypatch.setattr(storage_module, "delete", fake_delete)
    return store


def _make_user(db_session, role: UserRole, username: str) -> dict:
    user = create_user(db_session, username, "unused-hash", role)
    return {
        "uid": user["uid"],
        "token": create_access_token(user["uid"], role),
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
