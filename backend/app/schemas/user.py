from pydantic import BaseModel, constr
from typing import List, Optional
from datetime import datetime
from pydantic import validator

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    name: Optional[str] = None
    permissions: List[str] = []

class UserCreate(UserBase):
    username: constr(min_length=3, max_length=50)
    name: Optional[str] = None
    password: constr(min_length=6)
    permissions: List[str] = []

    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = {
            'dashboard',        # 仪表盘
            'inventory',        # 库存管理
            'stock_in',        # 商品入库
            'stock_out',       # 商品出库
            'transactions',     # 交易记录
            'performance',      # 业绩统计
            'analysis'         # 商品分析
        }
        invalid_perms = set(v) - valid_permissions
        if invalid_perms:
            raise ValueError(
                f'无效的权限: {", ".join(invalid_perms)}。\n'
                f'有效的权限包括: {", ".join(valid_permissions)}'
            )
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None
    password: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    is_owner: bool
    is_active: bool = True
    permissions: List[str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('permissions', pre=True)
    def split_permissions(cls, v):
        if isinstance(v, str):
            return v.split(',') if v else []
        return v

class StoreBase(BaseModel):
    name: str
    address: Optional[str] = None

class StoreCreate(StoreBase):
    owner_username: str
    owner_password: str
    owner_name: Optional[str] = None

class Store(StoreBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User 