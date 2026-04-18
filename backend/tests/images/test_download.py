from uuid import uuid4

from app.images.storage import _safe_attachment_filename


# --- Unit tests: filename sanitization ---


def test_safe_attachment_filename_strips_double_quotes():
    """Double quotes would close the quoted filename in Content-Disposition
    early, producing a malformed header. Stripping them is the single most
    important sanitization step for this helper."""
    assert _safe_attachment_filename('my"photo".jpg') == "myphoto.jpg"


def test_safe_attachment_filename_keeps_spaces():
    """Spaces are valid inside a quoted filename= value. The helper must
    not strip them (a previous version did, silently mangling filenames
    like 'Christmas 2024.jpg')."""
    assert _safe_attachment_filename("family vacation.jpg") == "family vacation.jpg"


def test_safe_attachment_filename_keeps_non_ascii():
    """Modern browsers handle non-ASCII in quoted filenames reasonably well.
    We don't strip them — the user expects to download 'åsa.jpg' as
    'åsa.jpg', not 'sa.jpg'."""
    assert _safe_attachment_filename("åsa.jpg") == "åsa.jpg"


def test_safe_attachment_filename_falls_back_when_empty():
    """If every character was stripped (e.g. input was all control chars
    or just a bare quote), return a safe default so the header is never
    'filename=\"\"'."""
    assert _safe_attachment_filename('"') == "image"
    assert _safe_attachment_filename("") == "image"


# --- Endpoint tests: GET /api/images/{uid}/download ---


async def test_download_happy_path(client, seeded_image, editor_user):
    response = await client.get(
        f"/api/images/{seeded_image['uid']}/download",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    # The fake presigned URL encodes the object_key and filename —
    # asserting both appear confirms the service passed them through
    # without mutation.
    assert seeded_image["object_key"] in location
    assert f"filename={seeded_image['filename']}" in location


async def test_download_image_not_found(client, fake_storage, editor_user):
    response = await client.get(
        f"/api/images/{uuid4()}/download",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_download_unauthenticated(client, seeded_image):
    """No Authorization header → 401. Guards against accidentally
    removing the auth dependency in a future refactor."""
    response = await client.get(
        f"/api/images/{seeded_image['uid']}/download",
        follow_redirects=False,
    )

    assert response.status_code == 401


async def test_download_viewer_allowed(client, seeded_image, viewer_token):
    """Viewers can download — downloading is part of 'view photos'
    per the RBAC table. If you ever change this to require_editor,
    this test will fail: reconsider before doing so."""
    response = await client.get(
        f"/api/images/{seeded_image['uid']}/download",
        headers={"Authorization": f"Bearer {viewer_token}"},
        follow_redirects=False,
    )

    assert response.status_code == 302
