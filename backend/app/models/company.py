from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

class CompanyType(str, enum.Enum):
    SUPPLIER = "SUPPLIER"  # 修改为大写
    CUSTOMER = "CUSTOMER"  # 修改为大写

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    contact = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    store = relationship("Store", back_populates="companies")
    transactions = relationship("Transaction", back_populates="company")
    payments = relationship("Payment", back_populates="company")

    # 添加联合唯一约束
    __table_args__ = (
        UniqueConstraint('name', 'store_id', name='uix_company_name_store'),
    )

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String(10), nullable=False)  # receive(收款) / pay(付款)
    notes = Column(String(200))
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    company = relationship("Company", back_populates="payments")
    store = relationship("Store", back_populates="payments")
    operator = relationship("User", back_populates="payments") 