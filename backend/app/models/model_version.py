from sqlalchemy import Column, String, Integer, Float, Text, Boolean
from backend.app.models.base import BaseModel

class ModelVersion(BaseModel):
    __tablename__ = "model_versions"

    version = Column(String(50), nullable=False, unique=True, index=True)
    algorithm = Column(String(50), default="DecisionTree")
    vectorizer = Column(String(50), default="TfidfVectorizer")
    artifact_path = Column(String(500), nullable=True)
    meta_path = Column(String(500), nullable=True)

    n_samples = Column(Integer, default=0)
    n_train = Column(Integer, default=0)
    n_test = Column(Integer, default=0)
    n_classes = Column(Integer, default=0)
    feature_count = Column(Integer, default=0)

    accuracy = Column(Float, default=0.0)
    f1_macro = Column(Float, default=0.0)
    precision_macro = Column(Float, default=0.0)
    recall_macro = Column(Float, default=0.0)
    confusion_matrix_json = Column(Text, nullable=True)
    classes_json = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ModelVersion id={self.id} version={self.version} acc={self.accuracy}>"