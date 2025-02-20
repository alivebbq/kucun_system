from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CompanyType(str, Enum):
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"

class CompanyBase(BaseModel):
    name: str
    type: CompanyType
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CompanyCreate(CompanyBase):
    initial_receivable: float = 0  # 添加初始应收款字段
    initial_payable: float = 0     # 添加初始应付款字段

class Company(CompanyBase):
    id: int
    store_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    company_id: int
    amount: Decimal
    type: str  # 'receive', 'pay', 'init_recv', 'init_pay'
    notes: Optional[str] = None

class Payment(PaymentCreate):
    id: int
    store_id: int
    operator_id: int
    created_at: datetime
    company: Company

    class Config:
        from_attributes = True

class CompanyBalance(BaseModel):
    company: Company
    receivable: Decimal  # 应收
    payable: Decimal    # 应付
    balance: Decimal    # 净额 

class CompanyTransaction(BaseModel):
    id: int
    type: str  # 'in', 'out', 'receive', 'pay'
    amount: Decimal
    timestamp: datetime
    notes: Optional[str] = None
    operator_name: str
    product_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None

    class Config:
        from_attributes = True

class CompanyTransactionResponse(BaseModel):
    id: int
    type: str
    order_id: Optional[int] = None
    order_no: Optional[str] = None
    amount: float
    timestamp: datetime
    notes: Optional[str] = None
    operator_name: str

    class Config:
        orm_mode = True

class CompanyCreateResponse(CompanyBase):
    id: int
    store_id: int
    created_at: datetime
    receivable: float
    payable: float

    class Config:
        from_attributes = True

class CompanyBalanceResponse(BaseModel):
    items: List[CompanyBalance]
    total: int

    class Config:
        from_attributes = True

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CompanyListResponse(BaseModel):
    items: List[Company]
    total: int

    class Config:
        from_attributes = True 