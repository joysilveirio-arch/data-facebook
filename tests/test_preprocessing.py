from backend.services.preprocessing_service import clean_text

def test_clean_basic():
    out = clean_text("Hello WORLD!!! Check https://x.com @user #hashtag 123")
    assert "hello" in out
    assert "https" not in out
    assert "@user" not in out
    assert "hashtag" in out
    assert "123" not in out

def test_clean_tetum():
    out = clean_text("Ami nia familia furak los ❤️❤️")
    assert "familia" in out
    assert "furak" in out
    assert "❤️" not in out

def test_clean_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""