"""
Shared schema primitives: pagination envelope and error response shape.

Traces to: FRD.md SS5.2 (consistent error response shape across all endpoints).
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
