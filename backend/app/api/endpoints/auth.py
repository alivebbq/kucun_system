from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.user import UserService
from app.core.auth import create_access_token, get_current_active_user
from app.schemas.user import Token, User

router = APIRouter(prefix="/api/v1/auth")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    print("\n=== Login Request ===")
    print(f"Username: {form_data.username}")
    
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    UserService.update_last_login(db, user)
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/users/me", response_model=User)
async def get_current_user(current_user = Depends(get_current_active_user)):
    """获取当前登录用户信息"""
    return current_user