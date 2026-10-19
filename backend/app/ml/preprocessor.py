
import re
import unicodedata
from typing import List

_URL_RE = re.compile(r"(?:https?://\S+|www\.\S+)", re.IGNORECASE)
_MENTION_RE = re.compile(r"@[\w.-]+", re.UNICODE)
_HASHTAG_RE = re.compile(r"#([\w]+)", re.UNICODE)
_HTML_RE = re.compile(r"<[^>]*>")
_NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)*\b")
_MULTISPACE_RE = re.compile(r"\s+")
_REPEAT_CHAR_RE = re.compile(r"(.)\1{2,}", re.UNICODE)

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

# Importante: rai liafuan negasaun hanesan "la".
STOPWORDS = set("""
a an the and or but if in on at to for of with is are was were
be been being this that these those it its as from by so
yang dan di ke dari untuk pada dengan adalah ini itu atau juga
akan sudah telah saja lebih bisa dapat oleh karena agar kalau jika
o os as um uma uns umas de do da dos das em no na nos nas por para
e ou mas se que qual quando como porque sim foi era ser estar
lah ne nia sira ba husi ho atu bele sai iha mos deit
""".split())


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )


def clean_text(
    text: str,
    *,
    keep_emoji: bool = False,
    remove_stopword: bool = True,
) -> str:
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = text.strip()
    if not text:
        return ""

    t = text.lower()
    t = _HTML_RE.sub(" ", t)
    t = _URL_RE.sub(" ", t)
    t = _MENTION_RE.sub(" ", t)
    t = _HASHTAG_RE.sub(r" \1 ", t)

    if not keep_emoji:
        t = _EMOJI_RE.sub(" ", t)

    t = strip_accents(t)
    t = _REPEAT_CHAR_RE.sub(r"\1\1", t)
    t = _NUM_RE.sub(" ", t)

    # Rai karakter alfabétiku ASCII no espasu.
    t = re.sub(r"[^a-z\s]", " ", t)
    t = _MULTISPACE_RE.sub(" ", t).strip()

    if not t:
        return ""

    tokens = re.findall(r"[a-z]+", t)

    if remove_stopword:
        tokens = [
            token for token in tokens
            if token not in STOPWORDS and len(token) > 1
        ]

    return " ".join(tokens)


def clean_texts(
    texts: List[str],
    *,
    keep_emoji: bool = False,
    remove_stopword: bool = True,
) -> List[str]:
    return [
        clean_text(
            text,
            keep_emoji=keep_emoji,
            remove_stopword=remove_stopword,
        )
        for text in texts
    ]
