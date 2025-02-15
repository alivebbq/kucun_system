import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.user import User
from app.models.inventory import Inventory, Transaction
from app.models.log import OperationLog
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_demo_data():
    """重置演示账号的所有数据"""
    try:
        with Session(engine) as db:
            # 获取演示账号
            demo_user = db.query(User).filter(User.username == "demo").first()
            if not demo_user:
                logger.error("未找到演示账号")
                return

            store_id = demo_user.store_id
            
            logger.info("开始清除数据...")
            
            # 删除该商店的所有数据，按顺序删除以避免外键约束问题
            # 1. 删除交易记录
            db.query(Transaction).filter(Transaction.store_id == store_id).delete()
            
            # 2. 删除操作日志
            db.query(OperationLog).filter(OperationLog.store_id == store_id).delete()
            
            # 3. 删除库存记录
            db.query(Inventory).filter(Inventory.store_id == store_id).delete()
            
            # 4. 删除除了demo账号以外的所有用户
            db.query(User).filter(
                User.store_id == store_id,
                User.username != "demo"
            ).delete()
            
            # 提交删除操作
            db.commit()
            
            logger.info("演示数据已清除，开始重新初始化...")
            
            # 重新初始化数据
            from init_demo_data import init_demo_data
            init_demo_data()
            
            logger.info(f"演示账号数据重置完成 - {datetime.now()}")
            
    except Exception as e:
        logger.error(f"重置演示数据时出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        reset_demo_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1) 