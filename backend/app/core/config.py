from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "kucun_system"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 移除硬编码的默认值，完全依赖环境变量
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    
    # 数据库URL也从环境变量读取
    DATABASE_URL: str
    
    # JWT配置
    SECRET_KEY: str
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
    
    # CORS配置
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # 本地开发环境
        "http://118.89.95.7:8000"  # 生产环境 IP + 端口
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True  # 区分大小写
        # 允许从环境变量加载额外的配置
        extra = "ignore"  # 添加这行来忽略额外的配置项

settings = Settings() 