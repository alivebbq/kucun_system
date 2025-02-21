from fastapi import APIRouter
from app.api.endpoints import inventory, company, auth, finance

api_router = APIRouter()

# 认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# 商品相关路由
api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"]
)

# 公司相关路由
api_router.include_router(
    company.router,
    prefix="/companies",
    tags=["companies"]
)

# 财务相关路由
api_router.include_router(
    finance.router,
    prefix="/finance",
    tags=["finance"]
) 