import base64

import pytest

from app.images.service import decode_cursor, encode_cursor


def test_round_trip():
    """Encoding then decoding must return the original values exactly.

    Pagination relies on this: the cursor is opaque to clients, but the
    server must get back the same (timestamp, uid) pair it put in, or the
    next page will skip or duplicate rows at the boundary.
    """
    uploaded_at_ms = 1_700_000_000_000
    uid = "8c3e6b4a-1234-4abc-9def-0123456789ab"

    cursor = encode_cursor(uploaded_at_ms, uid)

    assert decode_cursor(cursor) == (uploaded_at_ms, uid)


def test_cursor_is_url_safe():
    """Cursors travel as query-string values. '+' and '/' are valid in
    standard base64 but have special meaning in URLs — clients would have
    to percent-encode on every request. urlsafe_b64encode avoids that."""
    cursor = encode_cursor(1_700_000_000_000, "abc-123")

    assert "+" not in cursor
    assert "/" not in cursor


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "!!!not-base64!!!",
        base64.urlsafe_b64encode(b"not json").decode("ascii"),
        base64.urlsafe_b64encode(b'{"uid": "x"}').decode("ascii"),
        base64.urlsafe_b64encode(b'{"uploaded_at_ms": 1}').decode("ascii"),
        base64.urlsafe_b64encode(b"[1, 2]").decode("ascii"),
        base64.urlsafe_b64encode(b"null").decode("ascii"),
        "\u00f1",
    ],
    ids=[
        "empty",
        "not-base64",
        "base64-not-json",
        "missing-uploaded-at",
        "missing-uid",
        "json-array",
        "json-null",
        "non-ascii",
    ],
)
def test_decode_invalid_cursor_raises_value_error(bad: str):
    """Every malformed input must surface as ValueError so the router can
    translate it to a 400. Swallowing would turn client bugs into silent
    empty pages, which are painful to diagnose in production."""
    with pytest.raises(ValueError):
        decode_cursor(bad)
