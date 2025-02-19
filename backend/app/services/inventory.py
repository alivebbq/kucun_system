from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from contextlib import contextmanager
import time

from app.models.inventory import Inventory, Transaction
from app.models.user import User
from app.models.log import OperationLog
from app.models.company import Company
from app.schemas.inventory import (
    InventoryCreate, 
    InventoryUpdate, 
    StockIn, 
    StockOut
)

class InventoryService:
    @staticmethod
    def get_inventory(db: Session, store_id: int, skip: int = 0, limit: int = 100):
        return db.query(Inventory)\
            .filter(Inventory.store_id == store_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_inventory_by_barcode(db: Session, barcode: str, store_id: int):
        return db.query(Inventory)\
            .filter(
                Inventory.barcode == barcode,
                Inventory.store_id == store_id
            ).first()
    
    @staticmethod
    def get_inventory_by_barcode_or_name(db: Session, search_text: str, store_id: int):
        """通过条形码或商品名称搜索商品"""
        return db.query(Inventory)\
            .filter(
                Inventory.store_id == store_id,
                # 使用 or_ 来组合条件
                or_(
                    Inventory.barcode == search_text,
                    Inventory.name.ilike(f'%{search_text}%')
                )
            ).first()
    
    @staticmethod
    def create_inventory(db: Session, inventory: InventoryCreate, store_id: int):
        """创建新商品"""
        try:
            # 先检查条形码是否已存在
            existing_inventory = db.query(Inventory).filter(
                Inventory.barcode == inventory.barcode,
                Inventory.store_id == store_id
            ).first()
            
            if existing_inventory:
                raise HTTPException(
                    status_code=400,
                    detail=f"条形码 '{inventory.barcode}' 已存在"
                )
            
            # 检查商品名称是否重复
            existing_name = db.query(Inventory).filter(
                Inventory.name == inventory.name,
                Inventory.store_id == store_id
            ).first()
            
            if existing_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"商品名称 '{inventory.name}' 已存在"
                )
            
            # 创建新商品
            db_inventory = Inventory(
                **inventory.model_dump(),
                stock=0,
                store_id=store_id
            )
            
            db.add(db_inventory)
            db.commit()
            db.refresh(db_inventory)
            return db_inventory
            
        except HTTPException:
            # 直接重新抛出 HTTP 异常
            raise
        except Exception as e:
            db.rollback()
            # 检查是否是数据库唯一性约束错误
            if 'unique constraint' in str(e).lower():
                if 'barcode' in str(e).lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"条形码 '{inventory.barcode}' 已存在"
                    )
                elif 'name' in str(e).lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"商品名称 '{inventory.name}' 已存在"
                    )
            raise HTTPException(
                status_code=500,
                detail=f"创建商品失败: {str(e)}"
            )
    
    @staticmethod
    def update_inventory(db: Session, barcode: str, inventory: InventoryUpdate, store_id: int):
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode, store_id)
        if not db_inventory:
            return None
        
        update_data = inventory.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_inventory, field, value)
        
        db.commit()
        db.refresh(db_inventory)
        return db_inventory
    
    @contextmanager
    def _get_lock(db: Session, barcode: str, store_id: int):
        """获取商品的行级锁"""
        try:
            # 使用 SELECT FOR UPDATE 获取行级锁
            stmt = select(Inventory).where(
                Inventory.barcode == barcode,
                Inventory.store_id == store_id
            ).with_for_update()
            
            inventory = db.execute(stmt).scalar_one_or_none()
            if not inventory:
                raise HTTPException(status_code=404, detail="商品不存在")
            
            yield inventory
            
        except DBAPIError as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="数据库锁定失败，请重试"
            )

    @staticmethod
    def stock_in(db: Session, stock_in: StockIn, store_id: int, operator_id: int):
        """商品入库"""
        print("Received stock_in data:", stock_in.dict())
        with InventoryService._get_lock(db, stock_in.barcode, store_id) as inventory:
            if not inventory.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="商品已禁用，无法入库"
                )
            
            # 验证 company_id
            if not stock_in.company_id:
                raise HTTPException(
                    status_code=400,
                    detail="必须指定供应商"
                )
            
            # 更新库存数量
            inventory.stock += stock_in.quantity
            
            # 添加交易记录
            transaction = Transaction(
                inventory_id=inventory.id,
                barcode=stock_in.barcode,
                type="in",
                quantity=stock_in.quantity,
                price=stock_in.price,
                total=stock_in.quantity * stock_in.price,
                store_id=store_id,
                operator_id=operator_id,
                company_id=stock_in.company_id,
                notes=stock_in.notes
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(inventory)
            return inventory

    @staticmethod
    def stock_out(db: Session, stock_out: StockOut, store_id: int, operator_id: int):
        """商品出库"""
        with InventoryService._get_lock(db, stock_out.barcode, store_id) as inventory:
            if not inventory.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="商品已禁用，无法出库"
                )
            
            if inventory.stock < stock_out.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"库存不足 (当前库存: {inventory.stock})"
                )
            
            # 更新库存数量
            inventory.stock -= stock_out.quantity
            
            # 添加公司相关信息
            transaction = Transaction(
                inventory_id=inventory.id,
                barcode=stock_out.barcode,
                type="out",
                quantity=stock_out.quantity,
                price=stock_out.price,
                total=stock_out.quantity * stock_out.price,
                store_id=store_id,
                operator_id=operator_id,
                company_id=stock_out.company_id,
                notes=stock_out.notes
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(inventory)
            return inventory
    
    @staticmethod
    def get_inventory_stats(db: Session, store_id: int) -> dict:
        # 计算库存总值（使用最近的进货价格）
        inventory_values = []
        for inv in db.query(Inventory).filter(Inventory.store_id == store_id).all():
            last_in_price = db.query(Transaction.price)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'in',
                    Transaction.store_id == store_id
                )\
                .order_by(Transaction.timestamp.desc())\
                .first()
            if last_in_price:
                inventory_values.append(inv.stock * last_in_price[0])
        
        total_value = sum(inventory_values, Decimal('0'))
        
        # 获取今日销售额（所有商品）
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now()
        
        today_sales = db.query(
            func.sum(Transaction.total)
        ).filter(
            Transaction.type == 'out',
            Transaction.store_id == store_id,
            Transaction.timestamp.between(today_start, today_end)
        ).scalar() or Decimal('0')
        
        # 获取近7天销售额（所有商品）
        week_start = datetime.now() - timedelta(days=7)
        week_sales = db.query(
            func.sum(Transaction.total)
        ).filter(
            Transaction.type == 'out',
            Transaction.store_id == store_id,
            Transaction.timestamp.between(week_start, today_end)
        ).scalar() or Decimal('0')
        
        # 获取库存预警商品列表
        low_stock_items = db.query(
            Inventory.barcode,
            Inventory.name,
            Inventory.stock,
            Inventory.warning_stock,
            Inventory.unit
        ).filter(
            Inventory.store_id == store_id,
            Inventory.stock <= Inventory.warning_stock
        ).all()
        
        # 转换为字典列表
        low_stock_list = [
            {
                "barcode": item.barcode,
                "name": item.name,
                "stock": item.stock,
                "warning_stock": item.warning_stock,
                "unit": item.unit
            }
            for item in low_stock_items
        ]
        
        # 获取热销产品
        hot_products = InventoryService.get_hot_products(db, store_id)
        
        return {
            "total_value": total_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            "today_sales": today_sales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            "week_sales": week_sales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            "low_stock_items": low_stock_list,
            "hot_products": hot_products
        }
    
    @staticmethod
    def get_transactions(
        db: Session,
        store_id: int,
        barcode: Optional[str] = None,
        type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """获取交易记录"""
        # 基础查询
        query = (
            db.query(
                Transaction,
                Inventory.name.label('name'),
                User.name.label('operator_name'),
                Company.name.label('company_name')
            )
            .join(Inventory, Transaction.barcode == Inventory.barcode)
            .join(User, Transaction.operator_id == User.id)
            .outerjoin(Company, Transaction.company_id == Company.id)
            .filter(Transaction.store_id == store_id)
        )
        
        # 添加过滤条件
        if type and type.strip():
            query = query.filter(Transaction.type == type)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        # 添加排序条件，按时间倒序排列
        query = query.order_by(Transaction.timestamp.desc())
        
        # 获取分页数据
        transactions = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        items = []
        for t, name, operator_name, company_name in transactions:
            items.append({
                "id": t.id,
                "barcode": t.barcode,
                "type": t.type,
                "name": name,
                "quantity": t.quantity,
                "price": t.price,
                "total": t.total,
                "timestamp": t.timestamp,
                "operator_id": t.operator_id,
                "operator_name": operator_name,
                "company_id": t.company_id,
                "company_name": company_name,
                "notes": t.notes
            })
        
        return {
            "items": items,
            "total": query.count()
        }
    
    @staticmethod
    def delete_inventory(db: Session, barcode: str, store_id: int):
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode, store_id)
        if not db_inventory:
            return None
        
        try:
            # 先删除关联的交易记录
            db.query(Transaction).filter(
                Transaction.barcode == barcode,
                Transaction.store_id == store_id
            ).delete()
            # 再删除商品
            db.delete(db_inventory)
            db.commit()
            return db_inventory
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="删除失败，请确保商品没有关联的数据"
            )
    
    @staticmethod
    def get_performance_stats(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        store_id: int
    ) -> dict:
        # 初始化变量
        total_purchase = Decimal('0')
        total_sales = Decimal('0')
        total_sales_cost = Decimal('0')
        profit_rankings = []
        sales_rankings = []

        # 获取所有商品
        for inv in db.query(Inventory).filter(Inventory.store_id == store_id).all():
            # 获取销售记录
            out_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'out',
                    Transaction.timestamp.between(start_date, end_date),
                    Transaction.store_id == store_id
                ).all()
            
            # 获取进货记录
            in_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'in',
                    Transaction.timestamp <= end_date,
                    Transaction.store_id == store_id
                ).order_by(Transaction.timestamp.asc()).all()
            
            # 计算销售总额
            sales_quantity = sum(r.quantity for r in out_records)
            sales_revenue = sum(r.total for r in out_records)
            total_sales += sales_revenue

            # 计算进货总额
            purchase_total = sum(r.total for r in in_records)
            total_purchase += purchase_total

            # 计算销售成本（使用FIFO方法）
            cost = Decimal('0')
            remaining_quantity = sales_quantity
            for record in in_records:
                if remaining_quantity <= 0:
                    break
                used_quantity = min(record.quantity, remaining_quantity)
                cost += used_quantity * record.price
                remaining_quantity -= used_quantity
            
            total_sales_cost += cost

            # 计算利润
            profit = sales_revenue - cost
            profit_rate = (profit / cost * 100) if cost > 0 else 0

            # 添加到排名列表
            if sales_quantity > 0:
                profit_rankings.append({
                    "barcode": inv.barcode,
                    "name": inv.name,
                    "total_cost": float(cost),
                    "total_revenue": float(sales_revenue),
                    "profit": float(profit),
                    "profit_rate": float(profit_rate)
                })

                sales_rankings.append({
                    "barcode": inv.barcode,
                    "name": inv.name,
                    "quantity": sales_quantity,
                    "revenue": float(sales_revenue)
                })

        # 按利润和销售额排序
        profit_rankings.sort(key=lambda x: x["profit"], reverse=True)
        sales_rankings.sort(key=lambda x: x["revenue"], reverse=True)

        # 计算总利润和利润率
        total_profit = total_sales - total_sales_cost
        profit_rate = float(total_profit / total_sales_cost * 100) if total_sales_cost > 0 else 0

        return {
            "profit_rankings": profit_rankings[:10],  # 只返回前10名
            "sales_rankings": sales_rankings[:10],    # 只返回前10名
            "summary": {
                "total_purchase": float(total_purchase),
                "total_sales": float(total_sales),
                "total_sales_cost": float(total_sales_cost),
                "total_profit": float(total_profit),
                "profit_rate": profit_rate
            }
        }
    
    @staticmethod
    def get_hot_products(db: Session, store_id: int) -> List[dict]:
        # 获取近7天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 查询近7天销售额前10的商品
        hot_products = db.query(
            Transaction.barcode,
            Inventory.name,
            func.sum(Transaction.quantity).label('quantity'),
            func.sum(Transaction.total).label('revenue')
        ).join(
            Inventory, Transaction.barcode == Inventory.barcode
        ).filter(
            Transaction.type == 'out',
            Transaction.store_id == store_id,
            Transaction.timestamp.between(start_date, end_date)
        ).group_by(
            Transaction.barcode,
            Inventory.name
        ).order_by(
            func.sum(Transaction.total).desc()
        ).limit(10).all()
        
        return [
            {
                "barcode": item.barcode,
                "name": item.name,
                "quantity": item.quantity,
                "revenue": Decimal(str(item.revenue)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }
            for item in hot_products
        ]
    
    @staticmethod
    def get_product_analysis(
        db: Session,
        barcode: str,
        months: int,
        store_id: int
    ) -> dict:
        # 设置时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # 修改所有查询，添加 store_id 过滤
        price_trends = []
        sales_analysis = []
        
        # 计算每天的间隔
        days_per_point = 1  # 默认每天一个点
        if months > 1:
            days_per_point = (months * 30) // 30  # 确保总共有30个数据点
        
        # 生成日期点
        current_date = end_date
        while current_date >= start_date:
            point_end = current_date
            point_start = current_date - timedelta(days=days_per_point)
            
            # 获取该时间段的平均进价
            avg_cost = db.query(
                func.avg(Transaction.price)
            ).filter(
                Transaction.barcode == barcode,
                Transaction.type == 'in',
                Transaction.store_id == store_id,
                Transaction.timestamp.between(point_start, point_end)
            ).scalar() or Decimal('0')
            
            # 获取该时间段的平均售价
            avg_price = db.query(
                func.avg(Transaction.price)
            ).filter(
                Transaction.barcode == barcode,
                Transaction.type == 'out',
                Transaction.store_id == store_id,
                Transaction.timestamp.between(point_start, point_end)
            ).scalar() or Decimal('0')
            
            price_trends.append({
                "date": point_start,
                "cost": avg_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "price": avg_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            })
            
            # 获取销售记录
            out_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == barcode,
                    Transaction.type == 'out',
                    Transaction.store_id == store_id,
                    Transaction.timestamp.between(point_start, point_end)
                ).all()
            
            # 获取进货记录用于计算成本
            in_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == barcode,
                    Transaction.type == 'in',
                    Transaction.store_id == store_id,
                    Transaction.timestamp <= point_end
                ).order_by(Transaction.timestamp.asc()).all()
            
            # 计算销售额
            total_sales = Decimal('0')
            total_cost = Decimal('0')
            
            if out_records:
                total_sales = Decimal(str(sum(r.total for r in out_records)))
                
                # 计算销售成本
                remaining_quantity = 0
                total_out_quantity = sum(r.quantity for r in out_records)
                
                for in_record in in_records:
                    if remaining_quantity >= total_out_quantity:
                        break
                    used_quantity = min(
                        in_record.quantity,
                        total_out_quantity - remaining_quantity
                    )
                    total_cost += used_quantity * in_record.price
                    remaining_quantity += used_quantity
            
            profit = total_sales - total_cost
            
            sales_analysis.append({
                "date": point_start,
                "sales": total_sales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "profit": profit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            })
            
            current_date = point_start
        
        return {
            "price_trends": price_trends,
            "sales_analysis": sales_analysis
        }
    
    @staticmethod
    def get_statistics(db: Session, store_id: int) -> dict:
        """获取仪表盘统计数据"""
        try:
            # 计算库存总值（使用最近的进货价格）
            inventory_values = []
            for inv in db.query(Inventory).filter(Inventory.store_id == store_id).all():
                last_in_price = db.query(Transaction.price)\
                    .filter(
                        Transaction.barcode == inv.barcode,
                        Transaction.type == 'in',
                        Transaction.store_id == store_id
                    )\
                    .order_by(Transaction.timestamp.desc())\
                    .first()
                if last_in_price:
                    inventory_values.append(inv.stock * last_in_price[0])
            
            total_value = sum(inventory_values, Decimal('0'))
            
            # 获取今日销售额
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_sales = db.query(
                func.sum(Transaction.total)
            ).filter(
                Transaction.type == 'out',
                Transaction.store_id == store_id,
                Transaction.timestamp >= today_start
            ).scalar() or Decimal('0')
            
            # 获取近7天销售额
            week_start = datetime.now() - timedelta(days=7)
            week_sales = db.query(
                func.sum(Transaction.total)
            ).filter(
                Transaction.type == 'out',
                Transaction.store_id == store_id,
                Transaction.timestamp >= week_start
            ).scalar() or Decimal('0')
            
            # 获取库存预警商品
            low_stock_items = db.query(
                Inventory.barcode,
                Inventory.name,
                Inventory.stock,
                Inventory.warning_stock,
                Inventory.unit
            ).filter(
                Inventory.store_id == store_id,
                Inventory.stock <= Inventory.warning_stock
            ).all()
            
            # 转换为字典列表
            low_stock_list = [
                {
                    "barcode": item.barcode,
                    "name": item.name,
                    "stock": item.stock,
                    "warning_stock": item.warning_stock,
                    "unit": item.unit
                }
                for item in low_stock_items
            ]
            
            # 获取热销产品
            hot_products = InventoryService.get_hot_products(db, store_id)
            
            return {
                "total_value": total_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "today_sales": today_sales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "week_sales": week_sales.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "low_stock_items": low_stock_list,
                "hot_products": hot_products
            }
            
        except Exception as e:
            raise 

    @staticmethod
    def toggle_status(db: Session, barcode: str, store_id: int) -> Optional[Inventory]:
        """切换商品状态"""
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode, store_id)
        if not db_inventory:
            return None
        
        db_inventory.is_active = not db_inventory.is_active
        db.commit()
        db.refresh(db_inventory)
        return db_inventory

    @staticmethod
    def search_inventory(db: Session, search_text: str, store_id: int, limit: int = 10):
        """搜索商品，返回多个结果"""
        return db.query(Inventory)\
            .filter(
                Inventory.store_id == store_id,
                or_(
                    Inventory.barcode == search_text,
                    Inventory.name.ilike(f'%{search_text}%')
                )
            )\
            .limit(limit)\
            .all()

    @staticmethod
    def cancel_transaction(db: Session, transaction_id: int, store_id: int, operator_id: int):
        """撤销交易"""
        print(f"Cancelling transaction {transaction_id} for store {store_id} by operator {operator_id}")
        
        # 获取交易记录
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.store_id == store_id
        ).first()
        
        if not transaction:
            print(f"Transaction {transaction_id} not found for store {store_id}")
            return None
        
        # 获取商品信息用于日志记录
        inventory = db.query(Inventory).filter(
            Inventory.barcode == transaction.barcode,
            Inventory.store_id == store_id
        ).first()
        
        if not inventory:
            return None
        
        try:
            # 记录原始状态用于日志
            original_stock = inventory.stock
            
            # 更新库存
            if transaction.type == "in":
                if inventory.stock < transaction.quantity:
                    raise ValueError("库存不足，无法撤销")
                inventory.stock -= transaction.quantity
            else:
                inventory.stock += transaction.quantity
            
            # 创建操作日志
            log = OperationLog(
                operation_type="cancel_transaction",
                operator_id=operator_id,
                store_id=store_id,
                details={
                    "transaction_id": transaction.id,
                    "barcode": transaction.barcode,
                    "product_name": inventory.name,
                    "type": transaction.type,
                    "quantity": transaction.quantity,
                    "price": str(transaction.price),
                    "original_stock": original_stock,
                    "new_stock": inventory.stock,
                    "timestamp": transaction.timestamp.isoformat()
                }
            )
            db.add(log)
            
            # 删除交易记录
            db.delete(transaction)
            db.commit()
            db.refresh(inventory)
            
            return inventory
            
        except Exception as e:
            db.rollback()
            raise 

    @staticmethod
    def get_stock_in_records(db: Session, skip: int = 0, limit: int = 100):
        """获取入库记录，包含公司信息"""
        records = (
            db.query(Transaction)
            .join(Company, Transaction.company_id == Company.id)
            .filter(Transaction.type == "in")
            .order_by(Transaction.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # 确保每条记录都包含公司信息
        for record in records:
            if record.company:
                record.company_name = record.company.name
        
        return records 

    @staticmethod
    def get_stock_out_records(db: Session, skip: int = 0, limit: int = 100):
        """获取出库记录，包含公司信息"""
        records = (
            db.query(Transaction)
            .join(Company, Transaction.company_id == Company.id)
            .filter(Transaction.type == "out")
            .order_by(Transaction.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # 确保每条记录都包含公司信息
        for record in records:
            if record.company:
                record.company_name = record.company.name
        
        return records 