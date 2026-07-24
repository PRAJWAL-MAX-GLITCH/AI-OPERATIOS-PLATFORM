from pydantic import BaseModel
from typing import Optional, Any

class ResponseModel(BaseModel):
    message: str
    data: Optional[Any] = None
