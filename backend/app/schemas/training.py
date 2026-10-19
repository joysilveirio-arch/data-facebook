from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class TrainRequest(BaseModel):
    """Request parameters for machine learning model training."""

    model_config = ConfigDict(extra="forbid")

    test_size: float = Field(
        default=0.2,
        gt=0.0,
        lt=1.0,
        description="Proportion of the dataset reserved for testing (0, 1).",
    )

    max_depth: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum depth of the Decision Tree. None means unlimited.",
    )

    min_samples_split: int = Field(
        default=2,
        ge=2,
        description="Minimum number of samples required to split an internal node.",
    )

    random_state: int = Field(
        default=42,
        description="Random seed for reproducible training and evaluation.",
    )


class TrainResult(BaseModel):
    """Result returned after successful model training."""

    trained: bool
    version: Optional[str] = None

    n_samples: int = Field(ge=0)
    n_train: int = Field(ge=0)
    n_test: int = Field(ge=0)
    n_classes: int = Field(ge=0)

    classes: List[str] = Field(default_factory=list)

    # Metrics are represented as fractions from 0.0 to 1.0.
    accuracy: float = Field(ge=0.0, le=1.0)
    f1_macro: float = Field(ge=0.0, le=1.0)
    precision_macro: float = Field(ge=0.0, le=1.0)
    recall_macro: float = Field(ge=0.0, le=1.0)

    confusion_matrix: List[List[int]] = Field(
        default_factory=list
    )

    feature_count: int = Field(ge=0)


class TrainingStatus(BaseModel):
    """Current status of the training system."""

    ready: bool
    meta: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = None