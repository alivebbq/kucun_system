from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.db.session import get_db
from app.core.auth import get_current_active_user
from app.services.finance import FinanceService
from app.schemas.finance import OtherTransactionCreate, OtherTransaction, PaginatedOtherTransactionResponse, ProfitStatistics, PaymentRecordOut
from app.schemas.company import CompanyType
from app.schemas.finance import Page

router = APIRouter(prefix="/api/v1")

@router.get("/finance/transactions", response_model=PaginatedOtherTransactionResponse)
def get_transactions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取收支记录列表"""
    skip = (page - 1) * page_size
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    items, total = FinanceService.get_transactions(
        db,
        current_user.store_id,
        skip=skip,
        limit=page_size,
        type=type,
        start_date=start,
        end_date=end
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("/finance/transactions", response_model=OtherTransaction)
def create_transaction(
    transaction: OtherTransactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建收支记录"""
    return FinanceService.create_transaction(
        db,
        transaction,
        current_user.store_id,
        current_user.id
    )

@router.delete("/finance/transactions/{transaction_id}", response_model=dict)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """删除收支记录"""
    try:
        FinanceService.delete_transaction(db, transaction_id, current_user.store_id)
        return {"message": "删除成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/finance/profit", response_model=ProfitStatistics)
def get_profit_statistics(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取利润统计"""
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    return FinanceService.get_profit_statistics(
        db,
        current_user.store_id,
        start,
        end
    )

@router.get("/finance/payment-records", response_model=Page[PaymentRecordOut])
async def get_payment_records(
    start_date: str,
    end_date: str,
    company_type: CompanyType,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取收付款记录"""
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    return FinanceService.get_payment_records(
        db=db,
        store_id=current_user.store_id,
        start_date=start,
        end_date=end,
        type=company_type
    )