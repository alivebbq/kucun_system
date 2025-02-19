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