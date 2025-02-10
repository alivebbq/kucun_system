from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.services.inventory import InventoryService
from app.schemas.inventory import (
    Inventory, InventoryCreate, InventoryUpdate,
    Transaction, StockIn, StockOut, InventoryStats
)

router = APIRouter()

@router.get("/inventory/", response_model=List[Inventory])
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取库存列表"""
    return InventoryService.get_inventory(db, skip=skip, limit=limit)

@router.get("/inventory/{barcode}", response_model=Inventory)
def get_inventory(barcode: str, db: Session = Depends(get_db)):
    """根据条形码获取商品信息"""
    db_inventory = InventoryService.get_inventory_by_barcode(db, barcode)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.post("/inventory/", response_model=Inventory)
def create_inventory(
    inventory: InventoryCreate,
    db: Session = Depends(get_db)
):
    """创建新商品"""
    db_inventory = InventoryService.get_inventory_by_barcode(db, inventory.barcode)
    if db_inventory:
        raise HTTPException(status_code=400, detail="商品已存在")
    return InventoryService.create_inventory(db=db, inventory=inventory)

@router.put("/inventory/{barcode}", response_model=Inventory)
def update_inventory(
    barcode: str,
    inventory: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """更新商品信息"""
    db_inventory = InventoryService.update_inventory(db, barcode, inventory)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.post("/inventory/stock-in", response_model=Inventory)
def stock_in(
    stock_in: StockIn,
    db: Session = Depends(get_db)
):
    """商品入库"""
    db_inventory = InventoryService.stock_in(db, stock_in)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return db_inventory

@router.post("/inventory/stock-out", response_model=Inventory)
def stock_out(
    stock_out: StockOut,
    db: Session = Depends(get_db)
):
    """商品出库"""
    db_inventory = InventoryService.stock_out(db, stock_out)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在或库存不足")
    return db_inventory

@router.get("/inventory/stats", response_model=InventoryStats)
def get_inventory_stats(db: Session = Depends(get_db)):
    """获取库存统计信息"""
    return InventoryService.get_inventory_stats(db)

@router.get("/transactions/", response_model=List[Transaction])
def list_transactions(
    barcode: Optional[str] = None,
    type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取交易记录"""
    return InventoryService.get_transactions(
        db,
        barcode=barcode,
        type=type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.delete("/inventory/{barcode}")
def delete_inventory(
    barcode: str,
    db: Session = Depends(get_db)
):
    """删除商品"""
    db_inventory = InventoryService.delete_inventory(db, barcode)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"message": "删除成功"} 