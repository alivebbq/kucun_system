from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "库存管理系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "inventory_db"
    POSTGRES_PORT: str = "5432"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 扫码枪配置
    SCANNER_PORT: Optional[str] = "COM1"
    SCANNER_BAUDRATE: int = 9600
    
    class Config:
        env_file = ".env"

settings = Settings() 