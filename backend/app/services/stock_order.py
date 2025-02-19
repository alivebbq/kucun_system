from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException
from app.models.inventory import StockOrder, StockOrderItem, Transaction, Inventory
from app.schemas.inventory import StockOrderCreate, StockOrderUpdate
from app.core.utils import generate_order_no
from app.models.company import Company

class StockOrderService:
    @staticmethod
    def get_orders(
        db: Session,
        store_id: int,
        skip: Optional[int] = None,
        limit: int = 20,
        search: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None
    ):
        """获取出入库单列表"""
        try:
            # 使用 joinedload 预加载 company 和 operator 关系
            query = db.query(StockOrder).options(
                joinedload(StockOrder.company),
                joinedload(StockOrder.operator)
            ).filter(StockOrder.store_id == store_id)
            
            # 添加搜索条件
            if search and search.strip():
                query = query.filter(
                    or_(
                        StockOrder.order_no.ilike(f"%{search}%"),
                        StockOrder.company.has(Company.name.ilike(f"%{search}%"))
                    )
                )
            
            if type:
                query = query.filter(StockOrder.type == type)
                
            if status:
                query = query.filter(StockOrder.status == status)
                
            # 计算总数
            total = query.count()
            
            # 先排序，再分页
            query = query.order_by(StockOrder.created_at.desc())
            
            # 分页
            if skip is not None:
                query = query.offset(skip)
            if limit:
                query = query.limit(limit)
            
            orders = query.all()
            
            # 确保每个订单都有 company_name 和 operator_name
            for order in orders:
                if order.company:
                    order.company_name = order.company.name
                else:
                    order.company_name = None
                
                if order.operator:
                    order.operator_name = order.operator.name
                else:
                    order.operator_name = None
            
            return {
                "items": orders,
                "total": total
            }
        except Exception as e:
            print(f"Error getting orders: {str(e)}")
            raise

    @staticmethod
    def get_order(db: Session, order_id: int, store_id: int) -> Optional[StockOrder]:
        """获取出入库单详情"""
        return db.query(StockOrder)\
            .filter(
                StockOrder.id == order_id,
                StockOrder.store_id == store_id
            ).first()

    @staticmethod
    def create_order(
        db: Session,
        order: StockOrderCreate,
        store_id: int,
        operator_id: int
    ) -> StockOrder:
        """创建出入库单"""
        # 生成订单编号
        order_no = generate_order_no(order.type)
        
        # 创建订单
        db_order = StockOrder(
            order_no=order_no,
            type=order.type,
            company_id=order.company_id,
            store_id=store_id,
            operator_id=operator_id,
            status="draft",
            notes=order.notes
        )
        
        # 计算总金额
        total_amount = 0
        
        # 添加订单明细
        for item in order.items:
            # 验证商品是否存在
            inventory = db.query(Inventory).filter(
                Inventory.id == item.inventory_id,
                Inventory.store_id == store_id
            ).first()
            
            if not inventory:
                raise HTTPException(
                    status_code=400,
                    detail=f"商品ID {item.inventory_id} 不存在"
                )
            
            # 创建订单明细
            order_item = StockOrderItem(
                inventory_id=item.inventory_id,
                barcode=item.barcode,
                quantity=item.quantity,
                price=item.price,
                total=item.quantity * item.price,
                notes=item.notes
            )
            
            total_amount += order_item.total
            db_order.items.append(order_item)
        
        db_order.total_amount = total_amount
        
        try:
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def confirm_order(db: Session, order_id: int, store_id: int) -> StockOrder:
        """确认出入库单"""
        order = StockOrderService.get_order(db, order_id, store_id)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
            
        if order.status != "draft":
            raise HTTPException(
                status_code=400,
                detail=f"订单状态为{order.status}，不能确认"
            )
            
        try:
            # 更新库存
            for item in order.items:
                inventory = item.inventory
                
                # 检查库存
                if order.type == "out" and inventory.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"商品 {inventory.name} 库存不足"
                    )
                
                # 更新库存
                if order.type == "in":
                    inventory.stock += item.quantity
                else:
                    inventory.stock -= item.quantity
                
                # 创建交易记录
                transaction = Transaction(
                    inventory_id=item.inventory_id,
                    barcode=item.barcode,
                    type=order.type,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    store_id=store_id,
                    operator_id=order.operator_id,
                    company_id=order.company_id,
                    notes=item.notes
                )
                db.add(transaction)
            
            # 更新订单状态
            order.status = "confirmed"
            db.commit()
            db.refresh(order)
            return order
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def cancel_order(db: Session, order_id: int, store_id: int) -> StockOrder:
        """取消出入库单"""
        order = StockOrderService.get_order(db, order_id, store_id)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
            
        if order.status != "draft":
            raise HTTPException(
                status_code=400,
                detail="只能取消草稿状态的订单"
            )
            
        try:
            order.status = "cancelled"
            db.commit()
            db.refresh(order)
            return order
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 