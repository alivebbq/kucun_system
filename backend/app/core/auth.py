from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.services.user import UserService
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger = logging.getLogger(__name__)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 打印调试信息
        logger.debug(f"Validating token: {token}")
        
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token payload missing username")
            raise credentials_exception
            
        logger.debug(f"Token validated for user: {username}")
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise credentials_exception
        
    user = UserService.get_user_by_username(db, username)
    if user is None:
        logger.warning(f"User not found: {username}")
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user = Security(get_current_user)
):
    return current_user 