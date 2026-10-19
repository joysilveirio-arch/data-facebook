from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.core.config import settings

def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=settings.TFIDF_MAX_FEATURES,
        ngram_range=(settings.TFIDF_NGRAM_MIN, settings.TFIDF_NGRAM_MAX),
        min_df=1,
        sublinear_tf=True,
    )