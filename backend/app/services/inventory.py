from sqlalchemy.orm import Session
from sqlalchemy import func, case
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.models.inventory import Inventory, Transaction
from app.schemas.inventory import (
    InventoryCreate, 
    InventoryUpdate, 
    StockIn, 
    StockOut,
    InventoryStats,
    PerformanceStats
)

class InventoryService:
    @staticmethod
    def get_inventory(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Inventory).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_inventory_by_barcode(db: Session, barcode: str):
        return db.query(Inventory).filter(Inventory.barcode == barcode).first()
    
    @staticmethod
    def create_inventory(db: Session, inventory: InventoryCreate):
        db_inventory = Inventory(
            **inventory.model_dump(),
            stock=0
        )
        db.add(db_inventory)
        db.commit()
        db.refresh(db_inventory)
        return db_inventory
    
    @staticmethod
    def update_inventory(db: Session, barcode: str, inventory: InventoryUpdate):
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode)
        if not db_inventory:
            return None
        
        update_data = inventory.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_inventory, field, value)
        
        db.commit()
        db.refresh(db_inventory)
        return db_inventory
    
    @staticmethod
    def stock_in(db: Session, stock_in: StockIn):
        db_inventory = InventoryService.get_inventory_by_barcode(db, stock_in.barcode)
        if not db_inventory:
            return None
        
        # 更新库存数量
        db_inventory.stock += stock_in.quantity
        
        # 记录交易
        transaction = Transaction(
            barcode=stock_in.barcode,
            type="in",
            quantity=stock_in.quantity,
            price=stock_in.price,
            total=stock_in.quantity * stock_in.price
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(db_inventory)
        return db_inventory
    
    @staticmethod
    def stock_out(db: Session, stock_out: StockOut):
        db_inventory = InventoryService.get_inventory_by_barcode(db, stock_out.barcode)
        if not db_inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")
        
        if db_inventory.stock < stock_out.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        # 更新库存数量
        db_inventory.stock -= stock_out.quantity
        
        # 创建交易记录
        transaction = Transaction(
            barcode=stock_out.barcode,
            type="out",
            quantity=stock_out.quantity,
            price=stock_out.price,
            total=stock_out.quantity * stock_out.price
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(db_inventory)
        
        return db_inventory
    
    @staticmethod
    def get_inventory_stats(db: Session) -> dict:
        # 计算库存总值（使用最近的进货价格）
        inventory_values = []
        for inv in db.query(Inventory).all():
            last_in_price = db.query(Transaction.price)\
                .filter(Transaction.barcode == inv.barcode, Transaction.type == 'in')\
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
            Transaction.timestamp.between(today_start, today_end)
        ).scalar() or Decimal('0')
        
        # 获取近7天销售额（所有商品）
        week_start = datetime.now() - timedelta(days=7)
        week_sales = db.query(
            func.sum(Transaction.total)
        ).filter(
            Transaction.type == 'out',
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
        hot_products = InventoryService.get_hot_products(db)
        
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
        barcode: Optional[str] = None,
        type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ):
        # 基础查询
        base_query = db.query(Transaction, Inventory.name)\
            .join(Inventory, Transaction.barcode == Inventory.barcode)
        
        # 添加过滤条件
        if barcode:
            base_query = base_query.filter(Transaction.barcode == barcode)
        if type:
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
        
        # 将结果转换为字典格式
        transactions = []
        for transaction, name in results:
            transaction_dict = {
                "id": transaction.id,
                "barcode": transaction.barcode,
                "name": name,
                "type": transaction.type,
                "quantity": transaction.quantity,
                "price": transaction.price,
                "total": transaction.total,
                "timestamp": transaction.timestamp
            }
            transactions.append(transaction_dict)
        
        return {
            "items": transactions,
            "total": total
        }
    
    @staticmethod
    def delete_inventory(db: Session, barcode: str):
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode)
        if not db_inventory:
            return None
        
        try:
            # 先删除关联的交易记录
            db.query(Transaction).filter(Transaction.barcode == barcode).delete()
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
        end_date: datetime
    ) -> dict:
        # 修改利润计算逻辑，使用实际交易记录
        profit_rankings = []
        for inv in db.query(Inventory).all():
            # 获取销售记录
            out_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'out',
                    Transaction.timestamp.between(start_date, end_date)
                ).all()
            
            # 获取对应时期的进货记录
            in_records = db.query(Transaction)\
                .filter(
                    Transaction.barcode == inv.barcode,
                    Transaction.type == 'in',
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
            Transaction.type == 'out'
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
        ).filter(Transaction.timestamp.between(start_date, end_date)).first()

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
    def get_hot_products(db: Session) -> List[dict]:
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