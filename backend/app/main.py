import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import inventory, user, log, auth, company, finance
from app.db.session import engine, Base
from app.middleware.logging import logging_middleware
from contextlib import asynccontextmanager
import signal
import sys
import logging
from app.core.config import settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加启动和关闭事件管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的操作
    print("\n=== Server Starting ===")
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    # 注册信号处理
    def signal_handler(sig, frame):
        print("\n=== Graceful Shutdown ===")
        print("Closing database connections...")
        try:
            engine.dispose()
            print("Database connections closed")
        except Exception as e:
            print(f"Error closing database: {e}")
        print("Server shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # 终止信号
    
    yield
    
    # 关闭时的操作
    print("\n=== Server Shutting Down ===")
    engine.dispose()
    print("Database connections closed")

# 创建应用实例时添加 lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="库存管理系统API文档",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# 先添加日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    return await logging_middleware(request, call_next)

# 然后配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 添加一个简单的根路由
@app.get("/api")
async def root():
    return {"message": "API is running"}

# 添加调试路由
@app.get("/api/v1/test")
async def test_route():
    return {"message": "Test route works!"}

# 用户相关路由
app.include_router(
    user.router, 
    prefix="/api/v1/auth",
    tags=["users"]
)

# 库存相关路由
app.include_router(
    inventory.router,
    tags=["inventory"]
)

# 日志相关路由
app.include_router(
    log.router,
    tags=["logs"]
)

# 认证相关路由
app.include_router(
    auth.router,
    tags=["auth"]
)

# 公司相关路由
app.include_router(
    company.router,
    tags=["companies"]
)

# 财务相关路由
app.include_router(
    finance.router,
    tags=["finance"]
)

# 打印所有路由
@app.on_event("startup")
async def print_routes():
    print("\n=== Registered Routes ===")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = route.methods
            path = route.path
            print(f"{methods}: {path}")
            # 添加更多调试信息
            if hasattr(route, "endpoint"):
                print(f"  Endpoint: {route.endpoint.__name__}")
    print("=======================\n")

# 添加启动脚本
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_delay=2  # 添加重载延迟
    ) 