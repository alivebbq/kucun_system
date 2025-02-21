from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional
from app.models.user import User, VALID_PERMISSIONS
from app.schemas.user import UserCreate, UserUpdate

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
    def validate_permissions(permissions: list) -> bool:
        """验证权限列表是否合法"""
        invalid_permissions = [p for p in permissions if p not in VALID_PERMISSIONS]
        if invalid_permissions:
            raise ValueError(
                f"无效的权限: {', '.join(invalid_permissions)}。\n"
                f"有效的权限包括: {', '.join(VALID_PERMISSIONS)}"
            )
        return True

    @staticmethod
    def create_user(db: Session, user_data: UserCreate, store_id: int) -> User:
        """创建新用户"""
        # 验证权限
        if user_data.permissions:
            UserService.validate_permissions(user_data.permissions)
            
        try:
            # 检查用户名是否已存在
            if db.query(User).filter(User.username == user_data.username).first():
                return None
            
            # 处理权限列表
            if isinstance(user_data.permissions, list):
                permissions = ','.join(user_data.permissions)
            else:
                permissions = user_data.permissions.strip('[]() ').split(',')
                permissions = [p.strip('\'\" ') for p in permissions if p.strip()]
                permissions = ','.join(permissions)
            
            hashed_password = pwd_context.hash(user_data.password)
            db_user = User(
                username=user_data.username,
                name=user_data.name,
                hashed_password=hashed_password,
                is_owner=user_data.is_owner,
                store_id=store_id,
                permissions=permissions,
                created_at=datetime.now()
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def update_user(db: Session, username: str, user_update: UserUpdate, store_id: int):
        """更新用户信息"""
        db_user = db.query(User).filter(
            User.username == username,
            User.store_id == store_id
        ).first()
        
        if not db_user:
            return None
        
        # 更新权限时的处理
        if user_update.permissions is not None:
            if isinstance(user_update.permissions, list):
                db_user.permissions = ','.join(user_update.permissions)
            else:
                permissions = user_update.permissions.strip('[]() ').split(',')
                permissions = [p.strip('\'\" ') for p in permissions if p.strip()]
                db_user.permissions = ','.join(permissions)
        
        # 更新其他字段
        if user_update.name is not None:
            db_user.name = user_update.name
        if user_update.password is not None:
            db_user.hashed_password = pwd_context.hash(user_update.password)
        if user_update.is_active is not None:
            db_user.is_active = user_update.is_active
        
        db.commit()
        db.refresh(db_user)
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
    def get_password_hash(password: str) -> str:
        """获取密码哈希值"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = UserService.get_user_by_username(db, username)
        if not user or not UserService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def update_last_login(db: Session, user: User):
        """更新用户最后登录时间"""
        user.last_login = datetime.now()
        db.commit()
        db.refresh(user)
        return user 