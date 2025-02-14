from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库引擎
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # 自动检测断开的连接
        pool_size=5,         # 连接池大小
        max_overflow=10,     # 超过 pool_size 后最多可以创建的连接数
        pool_timeout=30,     # 连接池获取连接的超时时间
        pool_recycle=1800,   # 连接在连接池中重复使用的时间，超过后会被回收
        echo=True  # 打印 SQL 语句，方便调试
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 