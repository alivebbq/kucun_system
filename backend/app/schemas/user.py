from pydantic import BaseModel, constr
from typing import List, Optional, Union
from datetime import datetime
from pydantic import validator
from app.models.user import VALID_PERMISSIONS

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    name: Optional[str] = None
    permissions: List[str] = []

class UserCreate(UserBase):
    username: constr(min_length=3, max_length=50)
    name: Optional[str] = None
    password: constr(min_length=6)
    permissions: Union[List[str], str] = []
    is_owner: bool = False

    @validator('permissions')
    def validate_permissions(cls, v):
        invalid_perms = set(v) - set(VALID_PERMISSIONS)
        if invalid_perms:
            raise ValueError(
                f'无效的权限: {", ".join(invalid_perms)}。\n'
                f'有效的权限包括: {", ".join(VALID_PERMISSIONS)}'
            )
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    permissions: Optional[Union[List[str], str]] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_owner: bool
    is_active: bool
    store_id: int
    permissions: Union[List[str], str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

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

class TokenData(BaseModel):
    username: Optional[str] = None 