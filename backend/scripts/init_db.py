import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, Base
from app.models.user import Store, User
from app.services.user import pwd_context
from sqlalchemy.orm import Session
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("开始初始化数据库...")
        
        # 删除所有表
        logger.info("删除现有表...")
        Base.metadata.drop_all(bind=engine)
        
        # 创建所有表
        logger.info("创建新表...")
        Base.metadata.create_all(bind=engine)
        
        # 创建测试数据
        db = Session(engine)
        try:
            # 创建商店
            logger.info("创建测试商店...")
            store = Store(
                name="测试商店",
                address="测试地址",
                created_at=datetime.now()
            )
            db.add(store)
            db.flush()  # 确保获取到 store.id
            logger.info(f"商店创建成功，ID: {store.id}")
            
            # 创建店主账号
            logger.info("创建店主账号...")
            owner = User(
                username="a101",
                name="店主",
                hashed_password=pwd_context.hash("123456"),
                is_owner=True,
                is_active=True,
                store_id=store.id,
                permissions="owner",
                created_at=datetime.now()
            )
            db.add(owner)
            db.flush()  # 确保获取到 owner.id
            logger.info(f"店主账号创建成功，ID: {owner.id}")
            
            # 提交事务
            db.commit()
            logger.info("所有更改已提交到数据库")
            
            print("\n数据库初始化完成！")
            print(f"店主账号：{owner.username}")
            print(f"店主密码：123456")
            
        except Exception as e:
            logger.error(f"创建测试数据时出错: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
                
    except Exception as e:
        logger.error(f"初始化数据库时出错: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 