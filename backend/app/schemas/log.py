from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class OperatorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class OperationLogResponse(BaseModel):
    id: int
    operation_type: str
    operator: OperatorResponse
    details: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True 