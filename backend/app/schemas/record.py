
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecordBase(BaseModel):
    comment_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID úniku ba Facebook post/comment",
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Testu post ka komentáriu",
    )
    author_name: Optional[str] = Field(default=None, max_length=255)
    author_id: Optional[str] = Field(default=None, max_length=100)
    post_title: Optional[str] = Field(default=None, max_length=10000)
    date: Optional[str] = Field(default=None, max_length=50)
    likes_count: int = Field(default=0, ge=0)
    source_url: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("comment_id", "text")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field ne'e labele mamuk.")
        return value

    @field_validator("author_name", "author_id", "post_title", "date", "source_url")
    @classmethod
    def optional_text_trim(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class RecordCreate(RecordBase):
    dataset_id: Optional[int] = Field(default=None, ge=1)


class RecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    text: Optional[str] = Field(default=None, min_length=1, max_length=50000)
    author_name: Optional[str] = Field(default=None, max_length=255)
    author_id: Optional[str] = Field(default=None, max_length=100)
    post_title: Optional[str] = Field(default=None, max_length=10000)
    date: Optional[str] = Field(default=None, max_length=50)
    likes_count: Optional[int] = Field(default=None, ge=0)
    source_url: Optional[str] = Field(default=None, max_length=1000)
    dataset_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("comment_id", "text")
    @classmethod
    def updated_required_text_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field ne'e labele mamuk.")
        return value

    @field_validator("author_name", "author_id", "post_title", "date", "source_url")
    @classmethod
    def updated_optional_text_trim(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comment_id: str
    text: str
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    post_title: Optional[str] = None
    date: Optional[str] = None
    likes_count: Optional[int] = 0
    source_url: Optional[str] = None
    dataset_id: Optional[int] = None
    text_clean: Optional[str] = None
    label: Optional[str] = None
    predicted_label: Optional[str] = None
    prediction_confidence: Optional[float] = None
    created_at: Optional[datetime] = None
