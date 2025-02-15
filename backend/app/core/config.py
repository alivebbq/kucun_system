from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "kucun_system"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"
    POSTGRES_DB: str = "kucun_system"
    POSTGRES_PORT: str = "5432"
    
    # 使用简单的连接字符串
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/kucun_system"
    
    # JWT配置
    SECRET_KEY: str = "aabb00"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 扫码枪配置
    SCANNER_PORT: Optional[str] = "COM1"
    SCANNER_BAUDRATE: int = 9600
    
    # 数据库配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    SQL_ECHO: bool = False  # 是否打印SQL语句
    
    # 并发和重试配置
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 0.1
    
    class Config:
        env_file = ".env"
        # 允许从环境变量加载额外的配置
        extra = "ignore"  # 添加这行来忽略额外的配置项

settings = Settings() 