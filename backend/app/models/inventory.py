from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint, Boolean, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(13), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    unit = Column(String(20))
    stock = Column(Integer, default=0)
    warning_stock = Column(Integer, default=10)  # 警戒库存
    is_active = Column(Boolean, default=True)  # 添加是否启用字段
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

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    barcode = Column(String(13), nullable=False)
    type = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 添加操作人ID
    
    # 关联关系
    store = relationship("Store", back_populates="transactions")
    inventory = relationship("Inventory", back_populates="transactions")
    operator = relationship("User", back_populates="transactions")  # 添加与操作人的关联
    
    __table_args__ = (
        CheckConstraint(type.in_(['in', 'out']), name='check_transaction_type'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('total = quantity * price', name='check_total_calculation'),
        Index('idx_trans_store_time', store_id)
    ) 