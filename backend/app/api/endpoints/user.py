from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserUpdate, Token
from app.services.user import UserService
from app.core.auth import create_access_token, get_current_user, get_current_active_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from app.models.user import VALID_PERMISSIONS
from pydantic import BaseModel, validator

router = APIRouter()

@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user

@router.get("/users", response_model=List[User])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取店铺的所有用户（仅店主可用）"""
    if not current_user.is_owner:
        raise HTTPException(
            status_code=403,
            detail="只有店主可以查看用户列表"
        )
    return UserService.get_store_users(db, current_user.store_id)

@router.post("/users", response_model=User)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新员工（仅店主可用）"""
    if not current_user.is_owner:
        raise HTTPException(
            status_code=403,
            detail="只有店主可以创建新用户"
        )

    # 检查用户名是否已存在
    if UserService.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )

    try:
        # 创建新用户
        return UserService.create_user(db, user, current_user.store_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"创建用户失败: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """更新用户信息"""
    try:
        # 获取要更新的用户
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不允许修改店主账号
        if db_user.is_owner:
            raise HTTPException(status_code=403, detail="不能修改店主账号")
        
        # 确保只能修改同一个店铺的用户
        if db_user.store_id != current_user.store_id:
            raise HTTPException(status_code=403, detail="无权修改其他店铺的用户")
        
        result = UserService.update_user(
            db=db,
            username=db_user.username,  # 使用用户名而不是ID
            user_update=user_update,
            store_id=current_user.store_id
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="更新失败")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["owner"])
):
    """删除员工（仅店主可用）"""
    if not UserService.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在或无法删除")
    return {"message": "删除成功"}

class UserCreate(BaseModel):
    username: str
    name: str
    password: str
    permissions: List[str]

    @validator('permissions')
    def validate_permissions(cls, v):
        invalid_permissions = [p for p in v if p not in VALID_PERMISSIONS]
        if invalid_permissions:
            raise ValueError(
                f"无效的权限: {', '.join(invalid_permissions)}。\n"
                f"有效的权限包括: {', '.join(VALID_PERMISSIONS)}"
            )
        return v 