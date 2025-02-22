from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint, Boolean, UniqueConstraint, Index, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

# 新增订单状态枚举
class OrderStatus(str, enum.Enum):
    DRAFT = "draft"      # 待处理
    CONFIRMED = "confirmed"  # 已确认
    CANCELLED = "cancelled"  # 已取消

# 新增出入库单表
class StockOrder(Base):
    __tablename__ = "stock_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(20), nullable=False, unique=True, index=True)  # 单据编号
    type = Column(String(3), nullable=False)  # in/out
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    status = Column(String, nullable=False, default=OrderStatus.DRAFT)
    notes = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    company = relationship("Company", back_populates="stock_orders")
    operator = relationship("User", back_populates="stock_orders")
    store = relationship("Store", back_populates="stock_orders")
    items = relationship("StockOrderItem", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(type.in_(['in', 'out']), name='check_order_type'),
        CheckConstraint(status.in_([s.value for s in OrderStatus]), name='check_order_status'),
        CheckConstraint('total_amount >= 0', name='check_order_total_amount_positive'),
        Index('idx_order_store_time', store_id, created_at)
    )

# 新增出入库单明细表
class StockOrderItem(Base):
    __tablename__ = "stock_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("stock_orders.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    barcode = Column(String(13), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    notes = Column(String(200))
    
    # 关联关系
    order = relationship("StockOrder", back_populates="items")
    inventory = relationship("Inventory", back_populates="order_items")
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
        CheckConstraint('price >= 0', name='check_order_item_price_positive'),
        CheckConstraint('total = quantity * price', name='check_order_item_total_calculation'),
        Index('idx_order_item_order', order_id)
    )

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(13), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    unit = Column(String(20))
    stock = Column(Integer, default=0)
    warning_stock = Column(Integer, default=10)  # 警戒库存
    is_active = Column(Boolean, default=True)  # 添加是否启用字段
    remark = Column(Text, nullable=True)  # 添加备注字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # 添加复合唯一约束
    __table_args__ = (
        UniqueConstraint('barcode', 'store_id', name='uq_inventory_barcode_store'),
        UniqueConstraint('name', 'store_id', name='uq_inventory_name_store'),
        CheckConstraint('warning_stock >= 0', name='check_warning_stock_positive'),
        CheckConstraint('stock >= 0', name='check_stock_positive'),  # 添加库存非负检查
        Index('idx_inventory_store_name', store_id),  # 用于店铺内商品名称搜索
    )
    
    # 关联关系
    store = relationship("Store", back_populates="inventory")
    transactions = relationship("Transaction", back_populates="inventory")
    order_items = relationship("StockOrderItem", back_populates="inventory")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    barcode = Column(String)
    type = Column(String)  # in/out
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))
    store_id = Column(Integer, ForeignKey("stores.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(String(200), nullable=True)  # 添加备注字段
    
    # 关联关系
    inventory = relationship("Inventory", back_populates="transactions")
    store = relationship("Store", back_populates="transactions")
    operator = relationship("User", back_populates="transactions")
    company = relationship("Company", back_populates="transactions")
    
    __table_args__ = (
        CheckConstraint(type.in_(['in', 'out']), name='check_transaction_type'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('total = quantity * price', name='check_total_calculation'),
        Index('idx_trans_store_time', store_id)
    )
