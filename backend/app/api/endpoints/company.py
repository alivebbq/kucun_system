from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.company import (
    Company, CompanyCreate, Payment, PaymentCreate, CompanyBalance, CompanyTransaction, CompanyTransactionResponse, CompanyCreateResponse, CompanyBalanceResponse, CompanyUpdate
)
from app.services.company import CompanyService

router = APIRouter(prefix="/api/v1")

@router.get("/companies/", response_model=List[Company])
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
        print(f"Found {len(companies)} companies")
        return companies
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

@router.get("/companies/balance", response_model=CompanyBalanceResponse)
def get_company_balances(
    skip: int = 0,
    limit: int = 10,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取所有公司的应收应付情况"""
    return CompanyService.get_company_balances(
        db, 
        current_user.store_id,
        skip=skip,
        limit=limit,
        type=type
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

@router.get("/companies/{company_id}/transactions", response_model=CompanyTransactionResponse)
def get_company_transactions(
    company_id: int,
    skip: int = 0,
    limit: int = 10,
    type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取公司的所有交易记录"""
    return CompanyService.get_company_transactions(
        db, 
        company_id, 
        current_user.store_id,
        type=type,
        skip=skip,
        limit=limit
    )

@router.post("/payments/", response_model=Payment)
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

@router.get("/payments/", response_model=List[Payment])
def list_payments(
    company_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取收付款记录"""
    return CompanyService.get_payments(
        db, 
        current_user.store_id,
        company_id
    ) 