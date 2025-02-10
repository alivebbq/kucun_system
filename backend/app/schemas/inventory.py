from pydantic import BaseModel, constr
from decimal import Decimal
from typing import Optional
from datetime import datetime

# 商品基础模式
class InventoryBase(BaseModel):
    barcode: constr(min_length=1, max_length=13)
    name: constr(min_length=1, max_length=255)
    unit: Optional[str] = None
    selling_price: Optional[Decimal] = None
    warning_stock: Optional[int] = 10

# 创建商品请求
class InventoryCreate(InventoryBase):
    pass

# 更新商品请求
class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    selling_price: Optional[Decimal] = None
    warning_stock: Optional[int] = None

# 商品响应
class Inventory(InventoryBase):
    id: int
    avg_purchase_price: Decimal
    stock: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 交易基础模式
class TransactionBase(BaseModel):
    barcode: constr(min_length=1, max_length=13)
    quantity: int
    price: Decimal

# 入库请求
class StockIn(TransactionBase):
    pass

# 出库请求
class StockOut(TransactionBase):
    pass

# 交易响应
class Transaction(TransactionBase):
    id: int
    type: str
    name: str
    total: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True

# 库存统计响应
class InventoryStats(BaseModel):
    total_items: int
    total_value: Decimal
    low_stock_items: int 