from pydantic import BaseModel, constr, validator
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from enum import Enum

# 商品基础模式
class InventoryBase(BaseModel):
    barcode: constr(min_length=1, max_length=13)
    name: constr(min_length=1, max_length=255)
    unit: Optional[str] = None
    warning_stock: Optional[int] = 10

# 创建商品请求
class InventoryCreate(InventoryBase):
    pass

# 更新商品请求
class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    warning_stock: Optional[int] = None

# 商品响应
class Inventory(InventoryBase):
    id: int
    stock: int
    is_active: bool = True
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
    company_id: int
    notes: Optional[str] = None

# 出库请求
class StockOut(TransactionBase):
    company_id: int
    notes: Optional[str] = None

# 交易响应
class Transaction(TransactionBase):
    id: int
    type: str
    name: str
    total: Decimal
    timestamp: datetime
    operator_id: int
    operator_name: str
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# 库存预警商品
class LowStockItem(BaseModel):
    barcode: str
    name: str
    stock: int
    warning_stock: int
    unit: Optional[str]

# 热销商品
class HotProduct(BaseModel):
    barcode: str
    name: str
    quantity: int
    revenue: Decimal

# 库存统计响应
class InventoryStats(BaseModel):
    total_value: Decimal        # 库存总值
    today_sales: Decimal       # 今日销售额
    week_sales: Decimal        # 近7天销售额
    low_stock_items: List[LowStockItem]  # 库存预警商品列表
    hot_products: List[HotProduct]  # 近7天热销产品

# 交易记录响应模型
class TransactionResponse(BaseModel):
    items: List[Transaction]
    total: int

    class Config:
        from_attributes = True

# 业绩统计响应模型
class ProfitRanking(BaseModel):
    barcode: str
    name: str
    total_cost: Decimal      # 总成本
    total_revenue: Decimal   # 总收入
    profit: Decimal         # 利润
    profit_rate: float      # 利润率

class SalesRanking(BaseModel):
    barcode: str
    name: str
    quantity: int           # 销售数量
    revenue: Decimal        # 销售额

class SalesSummary(BaseModel):
    total_purchase: Decimal  # 进货总额
    total_sales: Decimal     # 销售总额
    total_sales_cost: Decimal      # 销售成本
    total_profit: Decimal    # 总利润
    profit_rate: float       # 利润率（基于销售成本）

class PerformanceStats(BaseModel):
    profit_rankings: List[ProfitRanking]
    sales_rankings: List[SalesRanking]
    summary: SalesSummary

class PricePoint(BaseModel):
    date: datetime
    cost: Decimal    # 成本价
    price: Decimal   # 售价

class SalesPoint(BaseModel):
    date: datetime
    sales: Decimal   # 销售额
    profit: Decimal  # 利润

class ProductAnalysis(BaseModel):
    price_trends: List[PricePoint]     # 价格趋势
    sales_analysis: List[SalesPoint]    # 销售和利润分析

class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

# 出入库单明细基础模型
class StockOrderItemBase(BaseModel):
    inventory_id: int
    barcode: str
    quantity: int
    price: Decimal
    notes: Optional[str] = None

# 创建出入库单明细请求
class StockOrderItemCreate(StockOrderItemBase):
    pass

# 出入库单明细响应
class StockOrderItem(StockOrderItemBase):
    id: int
    order_id: int
    total: Decimal

    class Config:
        from_attributes = True

# 出入库单基础模型
class StockOrderBase(BaseModel):
    type: str  # in/out
    company_id: int
    notes: Optional[str] = None

# 创建出入库单请求
class StockOrderCreate(StockOrderBase):
    items: List[StockOrderItemCreate]

# 更新出入库单请求
class StockOrderUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[OrderStatus] = None

# 出入库单响应
class StockOrder(BaseModel):
    id: int
    order_no: str
    type: str
    company_id: int
    company_name: Optional[str] = None
    operator_id: int
    operator_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    total_amount: float
    created_at: datetime
    items: List[StockOrderItem] = []

    class Config:
        from_attributes = True

    @validator('company_name', pre=True, always=True)
    def set_company_name(cls, v, values):
        """从关联的 company 对象中获取名称"""
        if hasattr(values.get('company'), 'name'):
            return values['company'].name
        return v

    @validator('operator_name', pre=True, always=True)
    def set_operator_name(cls, v, values):
        """从关联的 operator 对象中获取名称"""
        if hasattr(values.get('operator'), 'name'):
            return values['operator'].name
        return v

# 出入库单列表响应
class StockOrderList(BaseModel):
    items: List[StockOrder]
    total: int

# 出入库单确认响应
class StockOrderConfirmation(BaseModel):
    order_id: int
    status: OrderStatus
    message: str

class UpdateStockOrderRequest(BaseModel):
    company_id: int
    notes: str | None = None
    items: list[StockOrderItemCreate]

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": 1,
                "notes": "更新备注",
                "items": [
                    {
                        "inventory_id": 1,
                        "barcode": "8900000001",
                        "quantity": 10,
                        "price": 9.9,
                        "notes": "商品备注"
                    }
                ]
            }
        } 