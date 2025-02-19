from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    users = relationship("User", back_populates="store")
    inventory = relationship("Inventory", back_populates="store")
    transactions = relationship("Transaction", back_populates="store")
    operation_logs = relationship("OperationLog", back_populates="store")
    companies = relationship("Company", back_populates="store")
    payments = relationship("Payment", back_populates="store")
    stock_orders = relationship("StockOrder", back_populates="store") 