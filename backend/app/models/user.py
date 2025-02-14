from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    users = relationship("User", back_populates="store")
    inventory = relationship("Inventory", back_populates="store")
    transactions = relationship("Transaction", back_populates="store")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    name = Column(String(50), nullable=True)
    hashed_password = Column(String(100))
    is_owner = Column(Boolean, default=False)  # 是否是店主
    is_active = Column(Boolean, default=True)  # 添加这个字段
    store_id = Column(Integer, ForeignKey("stores.id"))
    permissions = Column(String(200), default="")  # 存储为逗号分隔的字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 关联
    store = relationship("Store", back_populates="users") 