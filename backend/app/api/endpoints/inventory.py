from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.services.inventory import InventoryService
from app.services.stock_order import StockOrderService
from app.core.auth import get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.inventory import (
    Inventory, InventoryCreate, InventoryUpdate,
    Transaction, StockIn, StockOut, InventoryStats,
    TransactionResponse, PerformanceStats, ProductAnalysis,
    StockOrderCreate, StockOrder, StockOrderList,
    StockOrderUpdate, StockOrderConfirmation, UpdateStockOrderRequest
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")  # 添加前缀

class InventoryResponse(BaseModel):
    items: List[Inventory]
    total: int

    class Config:
        from_attributes = True

@router.get("/inventory/", response_model=InventoryResponse)
def list_inventory(
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取库存列表"""
    skip = (page - 1) * page_size
    items = InventoryService.get_inventory(
        db, 
        store_id=current_user.store_id,
        skip=skip,
        limit=page_size,
        search=search
    )
    total = InventoryService.get_inventory_count(
        db,
        store_id=current_user.store_id,
        search=search
    )
    return InventoryResponse(items=items, total=total)

@router.get("/inventory/barcode/{barcode}", response_model=Inventory)
def get_inventory_by_barcode(
    barcode: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """根据条形码获取商品信息"""
    db_inventory = InventoryService.get_inventory_by_barcode(db, barcode, current_user.store_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.post("/inventory/", response_model=Inventory)
def create_inventory(
    inventory: InventoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """创建新商品"""
    try:
        # 验证条形码格式
        if not inventory.barcode.strip():
            raise HTTPException(
                status_code=400,
                detail="条形码不能为空"
            )
        
        # 验证商品名称
        if not inventory.name.strip():
            raise HTTPException(
                status_code=400,
                detail="商品名称不能为空"
            )
        
        # 验证警戒库存
        if inventory.warning_stock < 0:
            raise HTTPException(
                status_code=400,
                detail="警戒库存不能小于0"
            )
        
        return InventoryService.create_inventory(
            db=db,
            inventory=inventory,
            store_id=current_user.store_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建商品失败: {str(e)}"
        )

@router.put("/inventory/{barcode}", response_model=Inventory)
def update_inventory(
    barcode: str,
    inventory: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新商品信息"""
    db_inventory = InventoryService.update_inventory(db, barcode, inventory, current_user.store_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.post("/inventory/stock-in", response_model=Inventory)
def stock_in(
    stock_in: StockIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """商品入库"""
    return InventoryService.stock_in(
        db, 
        stock_in, 
        current_user.store_id,
        current_user.id
    )

@router.post("/inventory/stock-out", response_model=Inventory)
def stock_out(
    stock_out: StockOut,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """商品出库"""
    return InventoryService.stock_out(
        db, 
        stock_out, 
        current_user.store_id,
        current_user.id
    )

@router.get("/stats", response_model=InventoryStats)
def get_inventory_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取库存统计信息"""
    return InventoryService.get_inventory_stats(db, current_user.store_id)

@router.get("/transactions", response_model=TransactionResponse)
def list_transactions(
    barcode: Optional[str] = None,
    type: Optional[str] = None,
    company_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取交易记录"""
    return InventoryService.get_transactions(
        db,
        current_user.store_id,
        barcode=barcode,
        type=type,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.delete("/transactions/{transaction_id}", response_model=Inventory)
def cancel_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """撤销交易"""
    try:
        print(f"Attempting to cancel transaction {transaction_id}")
        result = InventoryService.cancel_transaction(
            db, 
            transaction_id, 
            current_user.store_id,
            current_user.id
        )
        if not result:
            print(f"Transaction {transaction_id} not found")
            raise HTTPException(status_code=404, detail="交易记录不存在")
        print(f"Successfully cancelled transaction {transaction_id}")
        return result
    except ValueError as e:
        print(f"Error cancelling transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/", response_model=PerformanceStats)
async def get_performance_stats(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取业绩统计"""
    # 如果没有提供日期，默认为当前月份
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.fromisoformat(start_date)
    
    if not end_date:
        end_date = datetime.now()
    else:
        end_date = datetime.fromisoformat(end_date)
    
    return InventoryService.get_performance_stats(
        db, 
        start_date, 
        end_date,
        current_user.store_id
    )

@router.get("/analysis/{barcode}", response_model=ProductAnalysis)
def get_product_analysis(
    barcode: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取商品分析数据"""
    db_inventory = InventoryService.get_inventory_by_barcode(
        db, 
        barcode, 
        current_user.store_id
    )
    if not db_inventory:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    return InventoryService.get_product_analysis(
        db, 
        barcode,
        start,
        end,
        current_user.store_id
    )

@router.get("/statistics")
async def get_statistics(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # 打印调试信息
        print(f"\n=== Getting Statistics for User ===")
        print(f"User: {current_user.username}")
        print(f"Store ID: {current_user.store_id}")
        
        # 获取统计数据
        stats = InventoryService.get_statistics(db, current_user.store_id)
        
        print(f"Statistics: {stats}")
        print("=== End Statistics Request ===\n")
        
        return stats
    except Exception as e:
        print(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )

@router.put("/inventory/{barcode}/toggle", response_model=Inventory)
def toggle_inventory_status(
    barcode: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """切换商品状态"""
    db_inventory = InventoryService.toggle_status(db, barcode, current_user.store_id)
    if not db_inventory:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.get("/inventory/search/{search_text}", response_model=List[Inventory])
def search_inventory(
    search_text: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """搜索商品"""
    return InventoryService.search_inventory(
        db, 
        search_text, 
        current_user.store_id
    )

@router.get("/stock-in", response_model=List[StockIn])
def get_stock_in_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    records = InventoryService.get_stock_in_records(db, skip=skip, limit=limit)
    # 确保返回的数据包含company信息
    return records 

@router.get("/stock-out", response_model=List[StockOut])
def get_stock_out_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    records = InventoryService.get_stock_out_records(db, skip=skip, limit=limit)
    # 确保返回的数据包含公司信息
    return records 

# 获取出入库单列表
@router.get("/stock-orders", response_model=StockOrderList)
def get_stock_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, gt=0),
    limit: int = Query(20, gt=0),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取出入库单列表"""
    # 计算skip
    skip = (page - 1) * limit
    orders = StockOrderService.get_orders(
        db=db,
        store_id=current_user.store_id,
        skip=skip,
        limit=limit,
        search=search,
        type=type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    return orders

# 获取出入库单详情
@router.get("/stock-orders/{order_id}", response_model=StockOrder)
def get_stock_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取出入库单详情"""
    order = StockOrderService.get_order(
        db=db,
        order_id=order_id,
        store_id=current_user.store_id
    )
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order

# 创建出入库单
@router.post("/stock-orders", response_model=StockOrder)
def create_stock_order(
    order: StockOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建出入库单"""
    return StockOrderService.create_order(
        db=db,
        order=order,
        store_id=current_user.store_id,
        operator_id=current_user.id
    )

# 确认出入库单
@router.post("/stock-orders/{order_id}/confirm", response_model=StockOrderConfirmation)
def confirm_stock_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认出入库单"""
    order = StockOrderService.confirm_order(
        db=db,
        order_id=order_id,
        store_id=current_user.store_id
    )
    return {
        "order_id": order.id,
        "status": order.status,
        "message": "订单已确认"
    }

# 取消出入库单
@router.post("/stock-orders/{order_id}/cancel", response_model=StockOrderConfirmation)
def cancel_stock_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消出入库单"""
    order = StockOrderService.cancel_order(
        db=db,
        order_id=order_id,
        store_id=current_user.store_id
    )
    return {
        "order_id": order.id,
        "status": order.status,
        "message": "订单已取消"
    }

# 更新出入库单
@router.put("/stock-orders/{order_id}", response_model=StockOrder)
def update_stock_order(
    order_id: int,
    data: UpdateStockOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新出入库单"""
    # 检查订单是否存在
    order = StockOrderService.get_order(
        db=db,
        order_id=order_id,
        store_id=current_user.store_id
    )
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 检查订单状态
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="只能修改待处理状态的订单")
    
    # 更新订单
    try:
        updated_order = StockOrderService.update_order(
            db=db, 
            order_id=order_id,
            data=data,
            store_id=current_user.store_id,
            operator_id=current_user.id
        )
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/inventory/id/{inventory_id}", response_model=Inventory)
def get_inventory_by_id(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取商品信息"""
    inventory = InventoryService.get_inventory_by_id(
        db, 
        inventory_id, 
        current_user.store_id
    )
    if not inventory:
        raise HTTPException(status_code=404, detail="商品不存在")
    return inventory 

# 添加获取总数的接口
@router.get("/inventory/count")
def get_inventory_count(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取库存商品总数"""
    return {
        "total": InventoryService.get_inventory_count(
            db,
            store_id=current_user.store_id,
            search=search
        )
    } 