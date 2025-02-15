import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.models.user import Store, User  # 直接从 user 模块导入
from app.services.user import UserService, pwd_context  # 导入 pwd_context
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_account():
    """创建演示账号和商店"""
    try:
        # 确保数据库表已创建
        Base.metadata.create_all(bind=engine)
        
        with Session(engine) as db:
            # 检查演示账号是否已存在
            existing_user = db.query(User).filter(User.username == "demo").first()
            if existing_user:
                # 更新已存在的演示账号权限和店主状态
                existing_user.permissions = (
                    "inventory,stock_in,stock_out,transactions,analysis,performance,"
                    "users,logs,dashboard"
                )
                existing_user.is_owner = True
                db.commit()
                logger.info("演示账号权限已更新")
                return
            
            # 创建演示商店
            demo_store = Store(
                name="演示商店",
                address="演示地址"
            )
            db.add(demo_store)
            db.flush()

            # 创建演示账号
            demo_user = User(
                username="demo",
                name="演示账号",
                hashed_password=pwd_context.hash("123456"),
                is_owner=True,  # 设为店主
                is_active=True,
                store_id=demo_store.id,
                # 设置所有权限
                permissions=(
                    "inventory,stock_in,stock_out,transactions,analysis,performance,"
                    "users,logs,dashboard,manage_users,manage_inventory"  # 添加管理权限
                )
            )
            db.add(demo_user)
            
            try:
                db.commit()
                logger.info("演示账号创建成功")
            except Exception as e:
                db.rollback()
                logger.error(f"创建演示账号失败: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"创建演示账号时出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        create_demo_account()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1) 