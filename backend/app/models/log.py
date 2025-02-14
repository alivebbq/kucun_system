from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False)  # 操作类型，如 'cancel_transaction'
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    details = Column(JSON, nullable=False)  # 存储操作详情
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # 关联
    operator = relationship("User", back_populates="operation_logs")
    store = relationship("Store", back_populates="operation_logs") 