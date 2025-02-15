from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.services.inventory import InventoryService
from app.schemas.inventory import (
    Inventory, InventoryCreate, InventoryUpdate,
    Transaction, StockIn, StockOut, InventoryStats,
    TransactionResponse, PerformanceStats, ProductAnalysis
)
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/api/v1")  # 添加前缀

@router.get("/inventory/", response_model=List[Inventory])
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取库存列表"""
    return InventoryService.get_inventory(db, current_user.store_id, skip=skip, limit=limit)

@router.get("/inventory/{barcode}", response_model=Inventory)
def get_inventory(
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
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
def get_performance_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取业绩统计"""
    # 如果没有指定日期，默认统计当前月份
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return InventoryService.get_performance_stats(
        db, 
        start_date, 
        end_date,
        current_user.store_id
    )

@router.get("/analysis/{barcode}", response_model=ProductAnalysis)
def get_product_analysis(
    barcode: str,
    months: int = Query(1, ge=1, le=12),  # 默认1个月，最多12个月
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
    
    return InventoryService.get_product_analysis(
        db, 
        barcode, 
        months,
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