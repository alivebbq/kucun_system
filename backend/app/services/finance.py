from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional, Tuple, List
from datetime import datetime, date
from fastapi import HTTPException
from app.models.finance import OtherTransaction
from app.schemas.finance import OtherTransactionCreate

class FinanceService:
    @staticmethod
    def get_transactions(
        db: Session,
        store_id: int,
        skip: int = 0,
        limit: int = 20,
        type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[List[OtherTransaction], int]:
        """获取收支记录列表"""
        query = db.query(OtherTransaction).options(
            joinedload(OtherTransaction.operator)
        ).filter(OtherTransaction.store_id == store_id)
        
        if type:
            query = query.filter(OtherTransaction.type == type)
            
        if start_date:
            query = query.filter(OtherTransaction.transaction_date >= start_date)
            
        if end_date:
            query = query.filter(OtherTransaction.transaction_date <= end_date)
            
        total = query.count()
        items = query.order_by(OtherTransaction.transaction_date.desc())\
            .offset(skip).limit(limit).all()
            
        # 手动设置 operator_name
        for item in items:
            if item.operator:
                item.operator_name = item.operator.name
            
        return items, total

    @staticmethod
    def create_transaction(
        db: Session,
        transaction: OtherTransactionCreate,
        store_id: int,
        operator_id: int
    ) -> OtherTransaction:
        """创建收支记录"""
        db_transaction = OtherTransaction(
            store_id=store_id,
            type=transaction.type,
            amount=transaction.amount,
            transaction_date=transaction.transaction_date,
            notes=transaction.notes,
            operator_id=operator_id
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    @staticmethod
    def delete_transaction(
        db: Session,
        transaction_id: int,
        store_id: int
    ) -> None:
        """删除收支记录"""
        transaction = db.query(OtherTransaction).filter(
            OtherTransaction.id == transaction_id,
            OtherTransaction.store_id == store_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        try:
            db.delete(transaction)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 