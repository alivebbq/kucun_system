from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from app.models.finance import TransactionType

class OtherTransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(..., ge=0)
    transaction_date: date
    notes: Optional[str] = None

class OtherTransactionCreate(OtherTransactionBase):
    pass

class OtherTransaction(OtherTransactionBase):
    id: int
    store_id: int
    operator_id: int
    operator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedOtherTransactionResponse(BaseModel):
    items: List[OtherTransaction]
    total: int
    page: int
    page_size: int 