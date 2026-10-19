import os
from backend.app.services.dataset_service import _map_row

def test_map_row_basic():
    row = {
        "commentId": "abc123",
        "text": "Bonita los mana!",
        "author/name": "Ana",
        "author/id": "42",
        "postTitle": "Wedding",
        "date": "2026-10-01T01:35:17.000Z",
        "likesCount": "5",
        "facebookUrl": "https://fb.com/x",
    }
    data = _map_row(row)
    assert data["comment_id"] == "abc123"
    assert data["text"] == "Bonita los mana!"
    assert data["author_name"] == "Ana"
    assert data["likes_count"] == 5

def test_map_row_missing_comment_id():
    data = _map_row({"text": "hello"})
    assert data["comment_id"] is None