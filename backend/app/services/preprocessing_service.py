# backend/services/preprocessing_service.py
import re
import unicodedata
from typing import List

# ---------- Normalisasi ----------
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@[\w\.\-]+")
_HASHTAG_RE = re.compile(r"#(\w+)")
_HTML_RE = re.compile(r"<[^>]+>")
_NUM_RE = re.compile(r"\d+")
_MULTISPACE_RE = re.compile(r"\s+")
_REPEAT_CHAR_RE = re.compile(r"(.)\1{2,}", re.UNICODE)

# Emoji ringan (tanpa dependency berat)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002600-\U000026FF"
    "\U0001F900-\U0001F9FF"
    "]+",
    flags=re.UNICODE,
)

# Stopword dasar (EN + ID + PT + sebagian Tetum umum)
STOPWORDS = set("""
a an the and or but if in on at to for of with is are was were be been being
this that these those it its as from by not no so
yang dan di ke dari untuk pada dengan adalah ini itu tidak bukan atau juga
akan sudah telah saja lebih sangat bisa dapat oleh karena agar kalau jika
o a os as um uma uns umas de do da dos das em no na nos nas por para com
e ou mas se que qual quando como porque nao não sim ja já foi era ser estar
la lah mak ne nee nia sira ba husi ho atu bele sai iha no mos deit
""".split())

def strip_accents(text: str) -> str:
    """Normalisasi aksen (aman untuk Tetum/ID/PT)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def remove_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)

def remove_mentions_hashtags(text: str) -> str:
    text = _MENTION_RE.sub(" ", text)
    text = _HASHTAG_RE.sub(r" \1 ", text)  # simpan kata hashtag
    return text

def remove_html(text: str) -> str:
    return _HTML_RE.sub(" ", text)

def remove_emojis(text: str) -> str:
    return _EMOJI_RE.sub(" ", text)

def collapse_repeats(text: str) -> str:
    return _REPEAT_CHAR_RE.sub(r"\1\1", text)

def normalize_whitespace(text: str) -> str:
    return _MULTISPACE_RE.sub(" ", text).strip()

def remove_numbers(text: str) -> str:
    return _NUM_RE.sub(" ", text)

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ]+", text)

def remove_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def clean_text(text: str, *, keep_emoji: bool = False, remove_stopword: bool = True) -> str:
    """
    Pipeline lengkap:
      lowercase -> hapus URL -> hapus HTML -> hapus mention/hashtag ->
      hapus emoji (opsional) -> normalisasi aksen -> collapse char ->
      hapus angka -> tokenisasi -> stopword removal -> gabung.
    """
    if not text:
        return ""
    t = text.lower()
    t = remove_html(t)
    t = remove_urls(t)
    t = remove_mentions_hashtags(t)
    if not keep_emoji:
        t = remove_emojis(t)
    t = strip_accents(t)
    t = collapse_repeats(t)
    t = remove_numbers(t)
    t = normalize_whitespace(t)

    tokens = tokenize(t)
    if remove_stopword:
        tokens = remove_stopwords(tokens)
    return " ".join(tokens)

def preprocess_records(db, record_ids=None, limit=None, force=False):
    # --- PERBAIKAN ADA DI BARIS INI ---
    from backend.app.models.text_record import TextRecord as Record
    
    q = db.query(Record)
    if record_ids:
        q = q.filter(Record.id.in_(record_ids))
    if not force:
        q = q.filter((Record.text_clean == None) | (Record.text_clean == ""))  # noqa
    if limit:
        q = q.limit(limit)
    items = q.all()
    for r in items:
        r.text_clean = clean_text(r.text)
    db.commit()
    return items