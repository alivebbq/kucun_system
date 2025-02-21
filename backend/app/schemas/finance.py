from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, TypeVar, Generic
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

class ProfitStatistics(BaseModel):
    """利润统计"""
    # 收入统计
    received_payments: Decimal = 0  # 已收货款
    other_income: Decimal = 0       # 其他收入
    total_income: Decimal = 0       # 总收入
    
    # 支出统计
    paid_payments: Decimal = 0      # 已付货款
    other_expense: Decimal = 0      # 其他支出
    total_expense: Decimal = 0      # 总支出
    
    # 利润
    profit: Decimal = 0             # 利润(总收入-总支出) 

class PaymentDetail(BaseModel):
    """付款明细"""
    id: int
    amount: Decimal
    created_at: datetime
    notes: Optional[str] = None
    type: str  # receipt 或 payment
    company_id: int
    company_name: Optional[str] = None
    operator_id: int
    operator_name: Optional[str] = None

    class Config:
        from_attributes = True

# 添加泛型分页模型
T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int

    class Config:
        from_attributes = True

class PaymentRecordOut(BaseModel):
    payment_date: date
    company_name: str  
    amount: Decimal
    notes: Optional[str] = None
    operator_name: Optional[str] = None

    class Config:
        from_attributes = True 