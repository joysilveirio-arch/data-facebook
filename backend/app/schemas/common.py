from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class MessageOut(BaseModel):
    message: str
    ok: bool = True

class PageOut(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: List[T]