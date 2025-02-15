import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.models.user import Store, User  # 直接从 user 模块导入
from app.services.user import UserService, pwd_context  # 导入 pwd_context
import logging
from datetime import datetime, timedelta
import random
from decimal import Decimal
from app.db.session import SessionLocal
from app.models.inventory import Inventory, Transaction

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

def create_demo_data():
    db = SessionLocal()
    try:
        # 1. 创建演示商店
        store = Store(
            name="演示商店",
            address="演示地址"
        )
        db.add(store)
        db.flush()

        # 2. 创建演示账号
        demo_user = User(
            username="demo",
            name="演示账号",
            hashed_password=pwd_context.hash("123456"),
            is_owner=True,
            store_id=store.id,
            permissions="inventory,stock_in,stock_out,performance,analysis"
        )
        db.add(demo_user)
        db.flush()

        # 3. 创建商品数据
        products = [
            {"name": "特级茉莉花茶", "price_range": (35, 45), "warning_stock": 30, "sales_weight": 1.2},    # 日常茶，热销
            {"name": "金骏眉红茶", "price_range": (80, 100), "warning_stock": 25, "sales_weight": 1.0},     # 中档红茶
            {"name": "铁观音", "price_range": (150, 180), "warning_stock": 20, "sales_weight": 0.8},        # 高档乌龙
            {"name": "大红袍", "price_range": (200, 250), "warning_stock": 15, "sales_weight": 0.6},        # 名贵岩茶
            {"name": "普洱生茶", "price_range": (120, 150), "warning_stock": 20, "sales_weight": 0.7},      # 生普
            {"name": "普洱熟茶", "price_range": (100, 130), "warning_stock": 20, "sales_weight": 0.7},      # 熟普
            {"name": "龙井茶", "price_range": (180, 220), "warning_stock": 15, "sales_weight": 0.8},        # 高档绿茶
            {"name": "碧螺春", "price_range": (160, 200), "warning_stock": 15, "sales_weight": 0.7},        # 高档绿茶
            {"name": "白毫银针", "price_range": (280, 320), "warning_stock": 10, "sales_weight": 0.5},      # 名贵白茶
            {"name": "黑茶", "price_range": (60, 80), "warning_stock": 35, "sales_weight": 1.1}             # 日常茶，热销
        ]

        # 生成过去3个月的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 改为生成1个月的数据
        current_date = start_date

        # 为所有商品生成一个统一的时间序列
        time_points = []
        temp_date = start_date
        while temp_date <= end_date:
            if random.random() < 0.8:  # 80%的时间点会发生交易
                time_points.append(temp_date)
            temp_date += timedelta(hours=random.randint(2, 6))

        for i, product in enumerate(products):
            # 创建商品
            barcode = f"8900{str(i+1).zfill(6)}"
            inventory = Inventory(
                barcode=barcode,
                name=product["name"],
                unit="盒",
                warning_stock=product["warning_stock"],
                stock=0,
                store_id=store.id,
                is_active=True
            )
            db.add(inventory)
            db.flush()

            # 生成交易记录
            for transaction_time in time_points:
                # 入库记录
                if random.random() < 0.2:  # 20%概率进货
                    quantity = random.randint(10, 20)  # 进一步减少单次进货量
                    price = round(random.uniform(*product["price_range"]), 2)
                    transaction = Transaction(
                        barcode=barcode,
                        type="in",
                        quantity=quantity,
                        price=Decimal(str(price)),
                        total=Decimal(str(quantity * price)),
                        timestamp=transaction_time,
                        store_id=store.id,
                        operator_id=demo_user.id
                    )
                    db.add(transaction)
                    inventory.stock += quantity

                # 出库记录
                if random.random() < 0.6 * product["sales_weight"]:  # 根据商品权重调整销售概率
                    if inventory.stock > 0:
                        max_sale = min(inventory.stock, 12)  # 减小单次最大销售量
                        quantity = random.randint(1, max_sale)
                        price = round(random.uniform(
                            product["price_range"][0] * 1.3,
                            product["price_range"][1] * 1.4
                        ), 2)
                        transaction = Transaction(
                            barcode=barcode,
                            type="out",
                            quantity=quantity,
                            price=Decimal(str(price)),
                            total=Decimal(str(quantity * price)),
                            timestamp=transaction_time,
                            store_id=store.id,
                            operator_id=demo_user.id
                        )
                        db.add(transaction)
                        inventory.stock -= quantity

        db.commit()
        print("演示数据创建成功！")
        
    except Exception as e:
        print(f"创建演示数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def reset_demo_data(store_id: int, demo_user_id: int):
    """重置演示数据但保留现有商店和用户"""
    db = SessionLocal()
    try:
        # 3. 创建商品数据
        products = [
            {"name": "特级茉莉花茶", "price_range": (35, 45), "warning_stock": 30, "sales_weight": 1.2},    # 日常茶，热销
            {"name": "金骏眉红茶", "price_range": (80, 100), "warning_stock": 25, "sales_weight": 1.0},     # 中档红茶
            {"name": "铁观音", "price_range": (150, 180), "warning_stock": 20, "sales_weight": 0.8},        # 高档乌龙
            {"name": "大红袍", "price_range": (200, 250), "warning_stock": 15, "sales_weight": 0.6},        # 名贵岩茶
            {"name": "普洱生茶", "price_range": (120, 150), "warning_stock": 20, "sales_weight": 0.7},      # 生普
            {"name": "普洱熟茶", "price_range": (100, 130), "warning_stock": 20, "sales_weight": 0.7},      # 熟普
            {"name": "龙井茶", "price_range": (180, 220), "warning_stock": 15, "sales_weight": 0.8},        # 高档绿茶
            {"name": "碧螺春", "price_range": (160, 200), "warning_stock": 15, "sales_weight": 0.7},        # 高档绿茶
            {"name": "白毫银针", "price_range": (280, 320), "warning_stock": 10, "sales_weight": 0.5},      # 名贵白茶
            {"name": "黑茶", "price_range": (60, 80), "warning_stock": 35, "sales_weight": 1.1}             # 日常茶，热销
        ]

        # 生成过去3个月的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 改为生成1个月的数据
        current_date = start_date

        # 为所有商品生成一个统一的时间序列
        time_points = []
        temp_date = start_date
        while temp_date <= end_date:
            if random.random() < 0.8:  # 80%的时间点会发生交易
                time_points.append(temp_date)
            temp_date += timedelta(hours=random.randint(2, 6))

        for i, product in enumerate(products):
            # 创建商品
            barcode = f"8900{str(i+1).zfill(6)}"
            inventory = Inventory(
                barcode=barcode,
                name=product["name"],
                unit="盒",
                warning_stock=product["warning_stock"],
                stock=0,
                store_id=store_id,
                is_active=True
            )
            db.add(inventory)
            db.flush()

            # 生成交易记录
            for transaction_time in time_points:
                # 入库记录
                if random.random() < 0.2:  # 20%概率进货
                    quantity = random.randint(10, 20)  # 进一步减少单次进货量
                    price = round(random.uniform(*product["price_range"]), 2)
                    transaction = Transaction(
                        barcode=barcode,
                        type="in",
                        quantity=quantity,
                        price=Decimal(str(price)),
                        total=Decimal(str(quantity * price)),
                        timestamp=transaction_time,
                        store_id=store_id,
                        operator_id=demo_user_id
                    )
                    db.add(transaction)
                    inventory.stock += quantity

                # 出库记录
                if random.random() < 0.6 * product["sales_weight"]:  # 根据商品权重调整销售概率
                    if inventory.stock > 0:
                        max_sale = min(inventory.stock, 12)  # 减小单次最大销售量
                        quantity = random.randint(1, max_sale)
                        price = round(random.uniform(
                            product["price_range"][0] * 1.3,
                            product["price_range"][1] * 1.4
                        ), 2)
                        transaction = Transaction(
                            barcode=barcode,
                            type="out",
                            quantity=quantity,
                            price=Decimal(str(price)),
                            total=Decimal(str(quantity * price)),
                            timestamp=transaction_time,
                            store_id=store_id,
                            operator_id=demo_user_id
                        )
                        db.add(transaction)
                        inventory.stock -= quantity

        db.commit()
        print("演示数据重置成功！")
        
    except Exception as e:
        print(f"重置演示数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        create_demo_account()
        create_demo_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1) 