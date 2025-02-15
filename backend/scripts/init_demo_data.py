import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.user import Store, User
from app.models.inventory import Inventory, Transaction
from app.models.log import OperationLog
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_demo_data():
    """初始化演示账号的数据"""
    try:
        with Session(engine) as db:
            # 获取演示账号和商店
            demo_user = db.query(User).filter(User.username == "demo").first()
            if not demo_user:
                logger.error("未找到演示账号，请先运行 create_demo_account.py")
                return

            # 先清除现有数据
            logger.info("清除现有数据...")
            db.query(Transaction).filter(Transaction.store_id == demo_user.store_id).delete()
            db.query(Inventory).filter(Inventory.store_id == demo_user.store_id).delete()
            db.query(OperationLog).filter(OperationLog.store_id == demo_user.store_id).delete()
            db.commit()
            
            logger.info("开始初始化新数据...")

            # 添加示例商品
            sample_products = [
                # 饮料类
                {
                    "barcode": "6901234567890",
                    "name": "可口可乐 330ml",
                    "unit": "瓶",
                    "stock": 200,
                    "warning_stock": 50,
                    "is_active": True
                },
                {
                    "barcode": "6901234567891",
                    "name": "百事可乐 330ml",
                    "unit": "瓶",
                    "stock": 180,
                    "warning_stock": 50,
                    "is_active": True
                },
                {
                    "barcode": "6901234567892",
                    "name": "农夫山泉 550ml",
                    "unit": "箱",
                    "stock": 100,
                    "warning_stock": 20,
                    "is_active": True
                },
                {
                    "barcode": "6901234567893",
                    "name": "红牛 250ml",
                    "unit": "罐",
                    "stock": 150,
                    "warning_stock": 30,
                    "is_active": True
                },
                # 零食类
                {
                    "barcode": "6901234567894",
                    "name": "乐事薯片原味",
                    "unit": "包",
                    "stock": 300,
                    "warning_stock": 50,
                    "is_active": True
                },
                {
                    "barcode": "6901234567895",
                    "name": "旺旺雪饼",
                    "unit": "包",
                    "stock": 250,
                    "warning_stock": 40,
                    "is_active": True
                },
                {
                    "barcode": "6901234567896",
                    "name": "好丽友派",
                    "unit": "盒",
                    "stock": 120,
                    "warning_stock": 30,
                    "is_active": True
                },
                # 方便面类
                {
                    "barcode": "6901234567897",
                    "name": "康师傅红烧牛肉面",
                    "unit": "箱",
                    "stock": 80,
                    "warning_stock": 15,
                    "is_active": True
                },
                {
                    "barcode": "6901234567898",
                    "name": "统一老坛酸菜面",
                    "unit": "箱",
                    "stock": 75,
                    "warning_stock": 15,
                    "is_active": True
                },
                # 日用品类
                {
                    "barcode": "6901234567899",
                    "name": "云南白药牙膏",
                    "unit": "支",
                    "stock": 100,
                    "warning_stock": 20,
                    "is_active": True
                },
                {
                    "barcode": "6901234567900",
                    "name": "舒肤佳香皂",
                    "unit": "块",
                    "stock": 200,
                    "warning_stock": 40,
                    "is_active": True
                },
                # 一些库存偏低的商品
                {
                    "barcode": "6901234567901",
                    "name": "维达抽纸",
                    "unit": "包",
                    "stock": 25,
                    "warning_stock": 30,
                    "is_active": True
                },
                {
                    "barcode": "6901234567902",
                    "name": "雀巢咖啡",
                    "unit": "罐",
                    "stock": 15,
                    "warning_stock": 20,
                    "is_active": True
                }
            ]

            # 添加商品
            for product in sample_products:
                try:
                    inventory = Inventory(
                        **product,
                        store_id=demo_user.store_id
                    )
                    db.add(inventory)
                except Exception as e:
                    logger.error(f"添加商品失败: {product['name']} - {str(e)}")
                    db.rollback()
                    raise
            
            db.flush()
            logger.info("商品数据添加成功")

            # 添加一些交易记录
            now = datetime.now()
            transactions = []
            
            # 为每个商品添加多条交易记录
            for product in sample_products:
                try:
                    # 最早的入库记录（一个月前）
                    transactions.append(Transaction(
                        barcode=product["barcode"],
                        type="in",
                        quantity=product["stock"] * 2,
                        price=Decimal("8.50"),
                        total=Decimal(str(product["stock"] * 2 * 8.5)),
                        timestamp=now - timedelta(days=30),
                        store_id=demo_user.store_id,
                        operator_id=demo_user.id
                    ))

                    # 两周前的出库记录
                    out_quantity = product["stock"] // 2
                    transactions.append(Transaction(
                        barcode=product["barcode"],
                        type="out",
                        quantity=out_quantity,
                        price=Decimal("12.00"),
                        total=Decimal(str(out_quantity * 12)),
                        timestamp=now - timedelta(days=14),
                        store_id=demo_user.store_id,
                        operator_id=demo_user.id
                    ))

                    # 一周前的入库记录
                    transactions.append(Transaction(
                        barcode=product["barcode"],
                        type="in",
                        quantity=product["stock"] // 4,
                        price=Decimal("9.00"),
                        total=Decimal(str(product["stock"] // 4 * 9)),
                        timestamp=now - timedelta(days=7),
                        store_id=demo_user.store_id,
                        operator_id=demo_user.id
                    ))

                    # 最近的出库记录
                    recent_out = product["stock"] // 4
                    transactions.append(Transaction(
                        barcode=product["barcode"],
                        type="out",
                        quantity=recent_out,
                        price=Decimal("13.50"),
                        total=Decimal(str(recent_out * 13.5)),
                        timestamp=now - timedelta(days=2),
                        store_id=demo_user.store_id,
                        operator_id=demo_user.id
                    ))

                    # 随机添加一些小批量的出入库记录
                    for _ in range(3):
                        small_quantity = product["stock"] // 10
                        is_in = _ % 2 == 0
                        transactions.append(Transaction(
                            barcode=product["barcode"],
                            type="in" if is_in else "out",
                            quantity=small_quantity,
                            price=Decimal("9.50") if is_in else Decimal("14.00"),
                            total=Decimal(str(small_quantity * (9.5 if is_in else 14))),
                            timestamp=now - timedelta(days=_ * 3),
                            store_id=demo_user.store_id,
                            operator_id=demo_user.id
                        ))
                except Exception as e:
                    logger.error(f"添加交易记录失败: {product['name']} - {str(e)}")
                    db.rollback()
                    raise

            # 批量添加交易记录
            try:
                db.bulk_save_objects(transactions)
                db.commit()
                logger.info("交易记录添加成功")
                logger.info("演示数据初始化完成")
            except Exception as e:
                db.rollback()
                logger.error(f"批量添加交易记录失败: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"初始化演示数据时出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        init_demo_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1) 