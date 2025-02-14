from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, 
    JSON, DateTime
)
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
    operation_logs = relationship("OperationLog", back_populates="store")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    name = Column(String(50), nullable=True)
    hashed_password = Column(String(100))
    is_owner = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    permissions = Column(String(200), default="")  # 存储为逗号分隔的字符串
    created_at = Column(DateTime, default=datetime.now)  # 使用本地时间
    last_login = Column(DateTime, nullable=True)
    
    # 关联
    store = relationship("Store", back_populates="users")
    transactions = relationship("Transaction", back_populates="operator")
    operation_logs = relationship("OperationLog", back_populates="operator")

    @property
    def permission_list(self):
        """获取权限列表"""
        if not self.permissions:
            return []
        return [p.strip() for p in self.permissions.split(',') if p.strip()]
    
    @permission_list.setter
    def permission_list(self, permissions):
        """设置权限列表"""
        if isinstance(permissions, list):
            self.permissions = ','.join(permissions)
        else:
            self.permissions = str(permissions) 