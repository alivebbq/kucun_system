from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional
from app.models.user import User, Store
from app.schemas.user import UserCreate, UserUpdate, StoreCreate

# 将 pwd_context 移到类外面作为模块级变量
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_store_users(db: Session, store_id: int) -> List[User]:
        """获取指定商店的所有用户"""
        users = db.query(User).filter(User.store_id == store_id).all()
        
        # 转换权限字符串为列表
        for user in users:
            if user.permissions:
                user.permissions = user.permissions.split(',')
            else:
                user.permissions = []
        
        return users
    
    @staticmethod
    def create_user(db: Session, user: UserCreate, store_id: int) -> User:
        hashed_password = pwd_context.hash(user.password)
        permissions_str = ','.join(user.permissions) if user.permissions else ''
        db_user = User(
            username=user.username,
            name=user.name,
            hashed_password=hashed_password,
            store_id=store_id,
            permissions=permissions_str,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 转换权限字符串为列表
        if db_user.permissions:
            db_user.permissions = db_user.permissions.split(',')
        else:
            db_user.permissions = []
        
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            return None
            
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
        if "permissions" in update_data:
            update_data["permissions"] = ','.join(update_data["permissions"])
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
            
        db.commit()
        db.refresh(db_user)
        
        # 转换权限字符串为列表
        if db_user.permissions:
            db_user.permissions = db_user.permissions.split(',')
        else:
            db_user.permissions = []
        
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        db_user = UserService.get_user(db, user_id)
        if not db_user or db_user.is_owner:
            return False
            
        db.delete(db_user)
        db.commit()
        return True
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        print(f"Verifying password: {plain_password[:2]}***")
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        print(f"Authenticating user: {username}")
        user = UserService.get_user_by_username(db, username)
        if not user:
            print("User not found")
            return None
        
        if not UserService.verify_password(password, user.hashed_password):
            print("Password verification failed")
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        
        # 转换权限字符串为列表
        if user.permissions:
            user.permissions = user.permissions.split(',')
        else:
            user.permissions = []
        
        db.commit()
        return user 