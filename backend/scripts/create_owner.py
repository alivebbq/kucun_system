import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.models import Store, User  # 从 __init__.py 导入
from app.services.user import UserService, pwd_context  # 导入模块级 pwd_context

def create_owner(
    db: Session,
    store_name: str,
    store_address: str,
    username: str,
    password: str,
    owner_name: str = None
):
    # 创建商店
    store = Store(
        name=store_name,
        address=store_address
    )
    db.add(store)
    db.flush()  # 获取store.id
    
    # 创建店主账号
    owner = User(
        username=username,
        password=pwd_context.hash(password),  # 使用导入的 pwd_context
        name=owner_name,
        is_owner=True,
        store_id=store.id,
        permissions=[]  # 店主不需要额外权限
    )
    db.add(owner)
    
    try:
        db.commit()
        print(f"成功创建店铺 '{store_name}' 和店主账号 '{username}'")
    except Exception as e:
        db.rollback()
        print(f"创建失败: {str(e)}")

def main():
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 获取用户输入
    store_name = input("请输入店铺名称: ")
    store_address = input("请输入店铺地址: ")
    username = input("请输入店主用户名: ")
    password = input("请输入店主密码: ")
    owner_name = input("请输入店主姓名(可选): ").strip() or None
    
    # 创建数据库会话
    with Session(engine) as db:
        create_owner(
            db=db,
            store_name=store_name,
            store_address=store_address,
            username=username,
            password=password,
            owner_name=owner_name
        )

if __name__ == "__main__":
    main() 