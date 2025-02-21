from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class TransactionType(str, enum.Enum):
    """收支类型"""
    INCOME = "income"  # 收入
    EXPENSE = "expense"  # 支出

class OtherTransaction(Base):
    """其他收支记录"""
    __tablename__ = "other_transactions"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)  # 收入/支出
    amount = Column(Numeric(10, 2), nullable=False)  # 金额
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 操作人
    transaction_date = Column(DateTime, nullable=False)  # 交易日期
    notes = Column(String(500))  # 备注
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联关系
    store = relationship("Store", back_populates="other_transactions")
    operator = relationship("User", back_populates="other_transactions") 