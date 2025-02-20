from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from decimal import Decimal
from app.models.company import Company, Payment
from app.models.inventory import Transaction, Inventory
from app.schemas.company import CompanyCreate, PaymentCreate, CompanyUpdate
from typing import Optional
from sqlalchemy import desc, text
from app.models.user import User
from sqlalchemy import literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

class CompanyService:
    @staticmethod
    def get_companies(db: Session, store_id: int, type: Optional[str] = None):
        """获取公司列表，支持按类型过滤"""
        try:
            query = db.query(Company).filter(Company.store_id == store_id)
            
            if type:
                query = query.filter(Company.type == type)
            
            companies = query.all()
            print(f"Found {len(companies)} companies for store_id: {store_id}")
            return companies
        except Exception as e:
            print(f"Error getting companies: {str(e)}")
            print(f"Store ID: {store_id}")
            print(f"Type Filter: {type}")
            raise
    
    @staticmethod
    def create_company(db: Session, company: CompanyCreate, store_id: int):
        """创建新公司并设置初始应收应付款"""
        # 检查公司名称是否已存在
        existing_company = db.query(Company).filter(
            Company.name == company.name,
            Company.store_id == store_id
        ).first()
        
        if existing_company:
            raise HTTPException(
                status_code=400,
                detail="公司名称已存在"
            )

        # 创建公司记录
        db_company = Company(
            name=company.name,
            type=company.type,
            contact=company.contact,
            phone=company.phone,
            address=company.address,
            store_id=store_id
        )
        
        try:
            db.add(db_company)
            db.commit()
            db.refresh(db_company)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="公司名称已存在"
            )

        # 如果有初始应收款，创建一个初始余额记录
        if company.initial_receivable > 0:
            initial_receivable = Payment(
                company_id=db_company.id,
                amount=company.initial_receivable,
                type='init_recv',
                notes='期初应收余额',
                store_id=store_id,
                operator_id=1
            )
            db.add(initial_receivable)

        # 如果有初始应付款，创建一个初始余额记录
        if company.initial_payable > 0:
            initial_payable = Payment(
                company_id=db_company.id,
                amount=company.initial_payable,
                type='init_pay',
                notes='期初应付余额',
                store_id=store_id,
                operator_id=1
            )
            db.add(initial_payable)

        db.commit()

        return {
            **db_company.__dict__,
            "receivable": float(company.initial_receivable),
            "payable": float(company.initial_payable)
        }
    
    @staticmethod
    def get_company_balances(
        db: Session,
        store_id: int,
        skip: int = 0,
        limit: int = 10,
        type: Optional[str] = None,
        search: Optional[str] = None  # 添加搜索参数
    ):
        """获取所有公司的应收应付情况"""
        query = db.query(Company).filter(Company.store_id == store_id)
        
        if type:
            query = query.filter(Company.type == type)
        
        if search:  # 添加搜索条件
            search = f"%{search}%"
            query = query.filter(
                or_(
                    Company.name.ilike(search),
                    Company.contact.ilike(search),
                    Company.phone.ilike(search)
                )
            )
        
        total = query.count()
        companies = query.offset(skip).limit(limit).all()
        
        balances = []
        for company in companies:
            # 计算应收总额（出库金额）
            receivable = db.query(func.sum(Transaction.total)).filter(
                Transaction.company_id == company.id,
                Transaction.type == "out",
                Transaction.store_id == store_id
            ).scalar() or Decimal('0')
            
            # 计算应付总额（入库金额）
            payable = db.query(func.sum(Transaction.total)).filter(
                Transaction.company_id == company.id,
                Transaction.type == "in",
                Transaction.store_id == store_id
            ).scalar() or Decimal('0')
            
            # 计算收付款记录
            payments = db.query(Payment).filter(
                Payment.company_id == company.id,
                Payment.store_id == store_id
            ).all()
            
            # 分别计算初始余额和后续收付款
            initial_receivable = Decimal('0')
            initial_payable = Decimal('0')
            received = Decimal('0')
            paid = Decimal('0')
            
            for payment in payments:
                if payment.type == 'init_recv':
                    initial_receivable = payment.amount
                elif payment.type == 'init_pay':
                    initial_payable = payment.amount
                elif payment.type == 'receive':
                    received += payment.amount
                elif payment.type == 'pay':
                    paid += payment.amount
            
            # 计算最终应收应付
            final_receivable = initial_receivable + receivable - received
            final_payable = initial_payable + payable - paid
            
            balances.append({
                "company": company,
                "receivable": final_receivable,
                "payable": final_payable,
                "balance": final_receivable - final_payable
            })
        
        return {
            "items": balances,
            "total": total
        }
    
    @staticmethod
    def create_payment(
        db: Session, 
        payment: PaymentCreate, 
        store_id: int,
        operator_id: int
    ):
        db_payment = Payment(
            **payment.model_dump(),
            store_id=store_id,
            operator_id=operator_id
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def get_company_transactions(
        db: Session, 
        company_id: int, 
        store_id: int,
        type: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ):
        """获取公司的所有交易记录，包括出入库和收付款"""
        # 获取交易记录
        transactions = (
            db.query(
                Transaction.id,
                Transaction.type.label('transaction_type'),
                Transaction.total.label('amount'),
                Transaction.timestamp.label('record_time'),
                literal(None).label('notes'),
                User.name.label('operator_name'),
                Inventory.name.label('product_name'),
                Transaction.quantity,
                Transaction.price
            ).join(
                User,
                Transaction.operator_id == User.id
            ).join(
                Inventory,
                Transaction.barcode == Inventory.barcode
            ).filter(
                Transaction.company_id == company_id,
                Transaction.store_id == store_id
            )
        )

        # 获取收付款记录
        payments = (
            db.query(
                Payment.id,
                Payment.type.label('transaction_type'),
                Payment.amount,
                Payment.created_at.label('record_time'),
                Payment.notes,
                User.name.label('operator_name'),
                literal(None).label('product_name'),
                literal(None).label('quantity'),
                literal(None).label('price')
            ).join(
                User,
                Payment.operator_id == User.id
            ).filter(
                Payment.company_id == company_id,
                Payment.store_id == store_id
            )
        )

        # 合并查询
        union_query = transactions.union_all(payments)
        
        # 应用类型筛选
        if type:
            union_query = union_query.filter(text("transaction_type = :type")).params(type=type)

        # 获取总记录数
        total = union_query.count()

        # 获取分页数据
        results = union_query\
            .order_by(desc('record_time'))\
            .offset(skip)\
            .limit(limit)\
            .all()

        return {
            "items": [
                {
                    "id": record.id,
                    "type": record.transaction_type,
                    "amount": float(record.amount),
                    "timestamp": record.record_time,
                    "notes": record.notes,
                    "operator_name": record.operator_name,
                    "product_name": record.product_name,
                    "quantity": float(record.quantity) if record.quantity else None,
                    "price": float(record.price) if record.price else None
                }
                for record in results
            ],
            "total": total
        }
    
    @staticmethod
    def update_company(db: Session, company_id: int, company_update: CompanyUpdate, store_id: int):
        """更新公司信息"""
        # 检查公司是否存在
        db_company = db.query(Company).filter(
            Company.id == company_id,
            Company.store_id == store_id
        ).first()
        
        if not db_company:
            raise HTTPException(
                status_code=404,
                detail="公司不存在"
            )
        
        # 如果要更新名称，检查新名称是否已存在
        if company_update.name and company_update.name != db_company.name:
            existing_company = db.query(Company).filter(
                Company.name == company_update.name,
                Company.store_id == store_id,
                Company.id != company_id
            ).first()
            
            if existing_company:
                raise HTTPException(
                    status_code=400,
                    detail="公司名称已存在"
                )
        
        # 更新公司信息
        update_data = company_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_company, key, value)
        
        try:
            db.commit()
            db.refresh(db_company)
            return db_company
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="公司名称已存在"
            )
    
    @staticmethod
    def get_company_total_balance(db: Session, store_id: int, type: Optional[str] = None):
        """获取指定类型公司的总应收/应付金额"""
        # 基础查询
        query = db.query(Company).filter(Company.store_id == store_id)
        
        # 应用类型筛选
        if type:
            query = query.filter(Company.type == type)
        
        companies = query.all()
        total_receivable = Decimal('0')
        total_payable = Decimal('0')
        
        for company in companies:
            # 计算应收总额（出库金额）
            receivable = db.query(func.sum(Transaction.total)).filter(
                Transaction.company_id == company.id,
                Transaction.type == "out",
                Transaction.store_id == store_id
            ).scalar() or Decimal('0')
            
            # 计算应付总额（入库金额）
            payable = db.query(func.sum(Transaction.total)).filter(
                Transaction.company_id == company.id,
                Transaction.type == "in",
                Transaction.store_id == store_id
            ).scalar() or Decimal('0')
            
            # 计算收付款记录
            payments = db.query(Payment).filter(
                Payment.company_id == company.id,
                Payment.store_id == store_id
            ).all()
            
            # 分别计算初始余额和后续收付款
            initial_receivable = Decimal('0')
            initial_payable = Decimal('0')
            received = Decimal('0')
            paid = Decimal('0')
            
            for payment in payments:
                if payment.type == 'init_recv':
                    initial_receivable = payment.amount
                elif payment.type == 'init_pay':
                    initial_payable = payment.amount
                elif payment.type == 'receive':
                    received += payment.amount
                elif payment.type == 'pay':
                    paid += payment.amount
            
            # 计算最终应收应付
            final_receivable = initial_receivable + receivable - received
            final_payable = initial_payable + payable - paid
            
            total_receivable += final_receivable
            total_payable += final_payable
        
        return {
            "total_receivable": total_receivable,
            "total_payable": total_payable
        } 