from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(13), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    unit = Column(String(20))
    stock = Column(Integer, default=0)
    warning_stock = Column(Integer, default=10)  # 警戒库存
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # 使用字符串引用避免循环导入
    store = relationship("Store", back_populates="inventory")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(13), ForeignKey("inventory.barcode"), nullable=False)
    type = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # 使用字符串引用避免循环导入
    store = relationship("Store", back_populates="transactions")
    
    __table_args__ = (
        CheckConstraint(type.in_(['in', 'out']), name='check_transaction_type'),
    ) 