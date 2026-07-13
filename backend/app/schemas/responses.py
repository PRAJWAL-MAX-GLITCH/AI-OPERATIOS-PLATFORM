from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

DataT = TypeVar('DataT')

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Application specific error code")
    message: str = Field(..., description="Human readable error message")

class ApiResponse(BaseModel, Generic[DataT]):
    """
    Standard envelope for all API responses.
    Ensures that clients always parse a consistent JSON structure.
    """
    data: Optional[DataT] = None
    meta: Optional[dict[str, Any]] = None
    error: Optional[ErrorDetail] = None

class PaginatedMeta(BaseModel):
    total: int
    page: int
    size: int
    pages: int

class PaginatedResponse(ApiResponse[list[DataT]], Generic[DataT]):
    """
    Standard envelope for paginated list responses.
    """
    meta: PaginatedMeta
