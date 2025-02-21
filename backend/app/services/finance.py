from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text, desc
from typing import Optional, Tuple, List
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from app.models.finance import OtherTransaction
from app.models.user import User
from app.models.company import Payment, Company
from app.schemas.company import CompanyType
from app.schemas.finance import (
    OtherTransactionCreate, 
    ProfitStatistics,
)

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

    @staticmethod
    def get_profit_statistics(
        db: Session,
        store_id: int,
        start_date: date,
        end_date: date
    ) -> ProfitStatistics:
        """获取利润统计"""
        # 1. 统计已收货款
        received_payments = db.query(func.sum(Payment.amount))\
            .join(Company)\
            .filter(
                Payment.store_id == store_id,
                Payment.type == 'receive',
                Payment.created_at.between(start_date, end_date)
            ).scalar() or Decimal('0')

        # 2. 统计其他收入
        other_income = db.query(func.sum(OtherTransaction.amount))\
            .filter(
                OtherTransaction.store_id == store_id,
                OtherTransaction.type == 'income',
                OtherTransaction.transaction_date.between(start_date, end_date)
            ).scalar() or Decimal('0')

        # 3. 统计已付货款
        paid_payments = db.query(func.sum(Payment.amount))\
            .join(Company)\
            .filter(
                Payment.store_id == store_id,
                Payment.type == 'pay',
                Payment.created_at.between(start_date, end_date)
            ).scalar() or Decimal('0')

        # 4. 统计其他支出
        other_expense = db.query(func.sum(OtherTransaction.amount))\
            .filter(
                OtherTransaction.store_id == store_id,
                OtherTransaction.type == 'expense',
                OtherTransaction.transaction_date.between(start_date, end_date)
            ).scalar() or Decimal('0')

        # 5. 计算总收入、总支出和利润
        total_income = received_payments + other_income
        total_expense = paid_payments + other_expense
        profit = total_income - total_expense

        return ProfitStatistics(
            received_payments=received_payments,
            other_income=other_income,
            total_income=total_income,
            paid_payments=paid_payments,
            other_expense=other_expense,
            total_expense=total_expense,
            profit=profit
        )

    @staticmethod
    def get_payment_records(
        db: Session, 
        store_id: int,
        start_date: date,
        end_date: date,
        type: Optional[CompanyType] = None,
        skip: int = 0,
        limit: int = 10 
    ):
        """获取收付款记录列表"""
        payments = (
            db.query(
                func.date(Payment.created_at).label('payment_date'),
                Company.name.label("company_name"),
                Payment.amount,
                Payment.notes,
                User.name.label("operator_name")
            )
            .join(Company, Payment.company_id == Company.id)
            .join(User, Payment.operator_id == User.id)
            .filter(
                Payment.store_id == store_id,
                Payment.created_at.between(start_date, end_date),
                Company.type == type
            )
            .order_by(Payment.created_at.desc())
        )

        total = payments.count()
        records = payments.offset(skip).limit(limit).all()

        return {
            "items": [
                {
                    "payment_date": record.payment_date,
                    "company_name": record.company_name,
                    "amount": float(record.amount),
                    "notes": record.notes,
                    "operator_name": record.operator_name
                }
                for record in records
            ],
            "total": total
        }