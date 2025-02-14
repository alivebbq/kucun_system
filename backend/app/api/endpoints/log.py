from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.log import OperationLog
from app.core.auth import get_current_active_user
from app.schemas.log import OperationLogResponse

# 添加路由前缀
router = APIRouter(prefix="/api/v1")

@router.get("/logs", response_model=List[OperationLogResponse])
def get_operation_logs(
    start_date: datetime = None,
    end_date: datetime = None,
    operation_type: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取操作日志（仅店主可用）"""
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="只有店主可以查看操作日志")
    
    query = db.query(OperationLog).filter(OperationLog.store_id == current_user.store_id)
    
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(OperationLog.created_at <= end_date)
    if operation_type:
        query = query.filter(OperationLog.operation_type == operation_type)
    
    return query.order_by(OperationLog.created_at.desc()).all() 