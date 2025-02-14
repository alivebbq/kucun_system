import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.models import Store, User

def check_data():
    with Session(engine) as db:
        # 检查店铺
        stores = db.query(Store).all()
        print("\n=== 店铺列表 ===")
        for store in stores:
            print(f"ID: {store.id}, 名称: {store.name}, 地址: {store.address}")
        
        # 检查用户
        users = db.query(User).all()
        print("\n=== 用户列表 ===")
        for user in users:
            print(f"ID: {user.id}, 用户名: {user.username}, 姓名: {user.name}, 是否店主: {user.is_owner}")

if __name__ == "__main__":
    check_data() 