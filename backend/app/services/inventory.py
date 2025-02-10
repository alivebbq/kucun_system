from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.inventory import Inventory, Transaction
from app.schemas.inventory import InventoryCreate, InventoryUpdate, StockIn, StockOut, InventoryStats

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
            avg_purchase_price=Decimal('0.00'),
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
        
        # 计算新的加权平均成本
        total_value = (db_inventory.stock * db_inventory.avg_purchase_price) + (stock_in.quantity * stock_in.price)
        new_stock = db_inventory.stock + stock_in.quantity
        db_inventory.avg_purchase_price = total_value / new_stock if new_stock > 0 else stock_in.price
        db_inventory.stock = new_stock
        
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
        if not db_inventory or db_inventory.stock < stock_out.quantity:
            return None
        
        # 计算新的平均售价
        total_value = (db_inventory.stock * db_inventory.avg_selling_price) + (stock_out.quantity * stock_out.price)
        new_stock = db_inventory.stock - stock_out.quantity
        db_inventory.avg_selling_price = total_value / (db_inventory.stock + stock_out.quantity)
        
        db_inventory.stock = new_stock
        
        # 记录交易
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
    def get_inventory_stats(db: Session) -> InventoryStats:
        total_items = db.query(func.count(Inventory.id)).scalar()
        total_value = db.query(
            func.sum(Inventory.stock * Inventory.avg_purchase_price)
        ).scalar() or Decimal('0')
        low_stock_items = db.query(func.count(Inventory.id))\
            .filter(Inventory.stock <= Inventory.warning_stock)\
            .scalar()
        
        return InventoryStats(
            total_items=total_items,
            total_value=total_value,
            low_stock_items=low_stock_items
        )
    
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
        query = db.query(Transaction, Inventory.name)\
            .join(Inventory, Transaction.barcode == Inventory.barcode)
        
        # 添加过滤条件
        if barcode:
            query = query.filter(Transaction.barcode == barcode)
        if type:
            query = query.filter(Transaction.type == type)  # 根据交易类型过滤
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
            
        # 获取结果
        results = query.order_by(Transaction.timestamp.desc())\
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
        
        return transactions
    
    @staticmethod
    def delete_inventory(db: Session, barcode: str):
        db_inventory = InventoryService.get_inventory_by_barcode(db, barcode)
        if not db_inventory:
            return None
        
        # 删除商品
        db.delete(db_inventory)
        db.commit()
        return db_inventory 