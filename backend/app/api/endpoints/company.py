from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.inventory import StockOrder
from app.models.company import Payment
from app.schemas.company import (
    Company, CompanyCreate, Payment as PaymentSchema,
    PaymentCreate, CompanyBalance, CompanyTransaction,
    CompanyTransactionResponse, CompanyCreateResponse,
    CompanyBalanceResponse, CompanyUpdate, CompanyListResponse
)
from app.services.company import CompanyService

router = APIRouter(prefix="/api/v1")

@router.get("/companies/", response_model=CompanyListResponse)
def list_companies(
    db: Session = Depends(get_db),
    type: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """获取公司列表"""
    print(f"\n=== Getting Companies ===")
    print(f"User: {current_user.username}")
    print(f"Store ID: {current_user.store_id}")
    print(f"Type Filter: {type}")
    
    try:
        companies = CompanyService.get_companies(db, current_user.store_id, type)
        return {
            "items": companies,
            "total": len(companies)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/companies/balance", response_model=CompanyBalanceResponse)
def get_company_balances(
    skip: int = 0,
    limit: int = 10,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取所有公司的应收应付情况"""
    return CompanyService.get_company_balances(
        db, 
        current_user.store_id,
        skip=skip,
        limit=limit,
        type=type,
        search=search
    )

@router.get("/companies/total-balance", response_model=dict)
def get_company_total_balance(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取所有公司的总应收应付金额"""
    return CompanyService.get_company_total_balance(
        db, 
        current_user.store_id,
        type=type
    )

@router.post("/companies/", response_model=CompanyCreateResponse)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建新公司"""
    return CompanyService.create_company(db, company, current_user.store_id)

@router.put("/companies/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新公司信息"""
    return CompanyService.update_company(
        db, 
        company_id, 
        company_update, 
        current_user.store_id
    )

@router.get("/companies/{company_id}/transactions", response_model=List[CompanyTransactionResponse])
def get_company_transactions(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取公司的交易记录"""
    transactions = []
    
    # 获取入库单记录
    stock_in_orders = (
        db.query(StockOrder)
        .filter(
            StockOrder.company_id == company_id,
            StockOrder.type == 'in',
            StockOrder.status == 'confirmed',
            StockOrder.store_id == current_user.store_id
        )
        .all()
    )
    for order in stock_in_orders:
        transactions.append({
            "id": order.id,
            "type": "stock_in",
            "order_id": order.id,
            "order_no": order.order_no,
            "amount": float(order.total_amount),
            "timestamp": order.created_at,
            "notes": order.notes,
            "operator_name": order.operator.name
        })
    
    # 获取出库单记录
    stock_out_orders = (
        db.query(StockOrder)
        .filter(
            StockOrder.company_id == company_id,
            StockOrder.type == 'out',
            StockOrder.status == 'confirmed',
            StockOrder.store_id == current_user.store_id
        )
        .all()
    )
    for order in stock_out_orders:
        transactions.append({
            "id": order.id,
            "type": "stock_out",
            "order_id": order.id,
            "order_no": order.order_no,
            "amount": float(order.total_amount),
            "timestamp": order.created_at,
            "notes": order.notes,
            "operator_name": order.operator.name
        })
    
    # 获取收付款记录
    payments = (
        db.query(Payment)
        .filter(
            Payment.company_id == company_id,
            Payment.store_id == current_user.store_id
        )
        .all()
    )
    for payment in payments:
        transactions.append({
            "id": payment.id,
            "type": payment.type,
            "amount": float(payment.amount),
            "timestamp": payment.created_at,
            "notes": payment.notes,
            "operator_name": payment.operator.name
        })
    
    # 按时间倒序排序
    transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return transactions

@router.post("/payments/", response_model=PaymentSchema)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建收付款记录"""
    return CompanyService.create_payment(
        db, 
        payment, 
        current_user.store_id,
        current_user.id
    )