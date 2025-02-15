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
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with InventoryService._get_lock(db, stock_in.barcode, store_id) as inventory:
                    if not inventory.is_active:
                        raise HTTPException(
                            status_code=400,
                            detail="商品已禁用，无法入库"
                        )
                    
                    # 更新库存数量
                    inventory.stock += stock_in.quantity
                    
                    # 记录交易
                    transaction = Transaction(
                        barcode=stock_in.barcode,
                        type="in",
                        quantity=stock_in.quantity,
                        price=stock_in.price,
                        total=stock_in.quantity * stock_in.price,
                        store_id=store_id,
                        operator_id=operator_id
                    )
                    
                    db.add(transaction)
                    db.commit()
                    db.refresh(inventory)
                    return inventory
                    
            except IntegrityError:
                db.rollback()
                retry_count += 1
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=500,
                        detail="操作失败，请重试"
                    )
                time.sleep(0.1 * retry_count)  # 递增延迟重试
                
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="入库操作失败"
                )

    @staticmethod
    def stock_out(db: Session, stock_out: StockOut, store_id: int, operator_id: int):
        """商品出库"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
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
                    
                    # 记录交易
                    transaction = Transaction(
                        barcode=stock_out.barcode,
                        type="out",
                        quantity=stock_out.quantity,
                        price=stock_out.price,
                        total=stock_out.quantity * stock_out.price,
                        store_id=store_id,
                        operator_id=operator_id
                    )
                    
                    db.add(transaction)
                    db.commit()
                    db.refresh(inventory)
                    return inventory
                    
            except IntegrityError:
                db.rollback()
                retry_count += 1
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=500,
                        detail="操作失败，请重试"
                    )
                time.sleep(0.1 * retry_count)
                
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="出库操作失败"
                )
    
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
        """获取交易记录时包含操作人信息"""
        base_query = db.query(
            Transaction,
            Inventory.name,
            User.name.label('operator_name')
        ).join(
            Inventory,
            Transaction.barcode == Inventory.barcode
        ).join(
            User,
            Transaction.operator_id == User.id
        ).filter(
            Transaction.store_id == store_id
        )
        
        # 添加过滤条件，只在有值时添加
        if barcode and barcode.strip():
            base_query = base_query.filter(Transaction.barcode == barcode)
        if type and type.strip():
            base_query = base_query.filter(Transaction.type == type)
        if start_date:
            base_query = base_query.filter(Transaction.timestamp >= start_date)
        if end_date:
            base_query = base_query.filter(Transaction.timestamp <= end_date)
        
        # 获取总数
        total = base_query.count()
        
        # 获取分页数据
        results = base_query.order_by(Transaction.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return {
            "items": [
                {
                    "id": transaction.id,
                    "barcode": transaction.barcode,
                    "name": name,
                    "type": transaction.type,
                    "quantity": transaction.quantity,
                    "price": transaction.price,
                    "total": transaction.total,
                    "timestamp": transaction.timestamp,
                    "operator_id": transaction.operator_id,
                    "operator_name": operator_name
                }
                for transaction, name, operator_name in results
            ],
            "total": total
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
        # 修改利润计算逻辑，使用实际交易记录
        profit_rankings = []
        for inv in db.query(Inventory).filter(Inventory.store_id == store_id).all():
            # 获取销售记录
            out_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'out',
                    Transaction.store_id == store_id,
                    Transaction.timestamp.between(start_date, end_date)
                ).all()
            
            # 获取对应时期的进货记录
            in_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'in',
                    Transaction.store_id == store_id,
                    Transaction.timestamp <= end_date
                ).order_by(Transaction.timestamp.asc()).all()
            
            # 计算销售收入和成本
            total_revenue = sum(r.total for r in out_records)
            total_cost = Decimal('0')
            remaining_quantity = 0
            
            for in_record in in_records:
                if remaining_quantity >= sum(r.quantity for r in out_records):
                    break
                used_quantity = min(
                    in_record.quantity,
                    sum(r.quantity for r in out_records) - remaining_quantity
                )
                total_cost += used_quantity * in_record.price
                remaining_quantity += used_quantity
            
            if total_cost > 0:
                profit_rankings.append({
                    "barcode": inv.barcode,
                    "name": inv.name,
                    "total_cost": total_cost,
                    "total_revenue": total_revenue,
                    "profit": total_revenue - total_cost,
                    "profit_rate": float((total_revenue - total_cost) / total_cost * 100)
                })
        
        # 获取销售额排名
        sales_rankings = []
        sales_query = db.query(
            Transaction.barcode,
            Inventory.name,
            func.sum(Transaction.quantity).label('quantity'),
            func.sum(Transaction.total).label('revenue')
        ).join(Inventory, Transaction.barcode == Inventory.barcode)\
        .filter(
            Transaction.timestamp.between(start_date, end_date),
            Transaction.type == 'out',
            Transaction.store_id == store_id
        ).group_by(Transaction.barcode, Inventory.name)

        for barcode, name, quantity, revenue in sales_query:
            sales_rankings.append({
                "barcode": barcode,
                "name": name,
                "quantity": quantity,
                "revenue": revenue
            })
        
        # 按销售额降序排序
        sales_rankings.sort(key=lambda x: x['revenue'], reverse=True)

        # 获取销售汇总
        summary_query = db.query(
            # 进货总额
            func.sum(case(
                (Transaction.type == 'in', Transaction.total),
                else_=0
            )).label('total_purchase'),
            # 销售总额
            func.sum(case(
                (Transaction.type == 'out', Transaction.total),
                else_=0
            )).label('total_sales')
        ).filter(
            Transaction.timestamp.between(start_date, end_date),
            Transaction.store_id == store_id
        ).first()

        total_purchase = (summary_query[0] or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_sales = (summary_query[1] or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 计算总销售成本（使用先进先出原则）
        total_sales_cost = Decimal('0')
        for inv in db.query(Inventory).all():
            # 获取销售记录
            out_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'out',
                    Transaction.timestamp.between(start_date, end_date)
                ).all()
            
            # 获取进货记录
            in_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'in',
                    Transaction.timestamp <= end_date
                ).order_by(Transaction.timestamp.asc()).all()
            
            # 计算该商品的销售成本
            remaining_quantity = 0
            total_out_quantity = sum(r.quantity for r in out_records)
            
            for in_record in in_records:
                if remaining_quantity >= total_out_quantity:
                    break
                used_quantity = min(
                    in_record.quantity,
                    total_out_quantity - remaining_quantity
                )
                total_sales_cost += used_quantity * in_record.price
                remaining_quantity += used_quantity

        # 计算总利润和利润率
        total_profit = (total_sales - total_sales_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        profit_rate = (float(total_profit / total_sales_cost * 100) if total_sales_cost > 0 else 0)

        summary = {
            "total_purchase": total_purchase,    # 进货总额
            "total_sales": total_sales,         # 销售总额
            "sales_cost": total_sales_cost,     # 销售成本（使用先进先出原则）
            "total_profit": total_profit,       # 总利润
            "profit_rate": profit_rate          # 利润率
        }

        return {
            "profit_rankings": profit_rankings,
            "sales_rankings": sales_rankings,
            "summary": summary
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