import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.store import Store
from app.models.inventory import Inventory, Transaction
from app.models.log import OperationLog
from app.services.user import pwd_context
import logging
from datetime import datetime, timedelta
import random
from decimal import Decimal
import argparse
from app.models.company import Company, CompanyType

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_or_update_demo_account(db: Session) -> tuple[Store, User]:
    """创建或更新演示账号和商店"""
    # 检查演示账号是否已存在
    demo_user = db.query(User).filter(User.username == "demo").first()
    demo_store = None
    
    if demo_user:
        # 更新已存在的演示账号权限和店主状态
        demo_user.permissions = (
            "inventory,stock_in,stock_out,transactions,analysis,performance,"
            "users,logs,dashboard"
        )
        demo_user.is_owner = True
        demo_store = demo_user.store
        logger.info("演示账号权限已更新")
    else:
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
            is_owner=True,
            is_active=True,
            store_id=demo_store.id,
            permissions=(
                "inventory,stock_in,stock_out,transactions,analysis,performance,"
                "users,logs,dashboard"
            )
        )
        db.add(demo_user)
        logger.info("演示账号创建成功")
    
    return demo_store, demo_user

def generate_demo_products() -> list[dict]:
    """生成演示商品数据"""
    return [
        {"name": "特级茉莉花茶", "price_range": (35, 45), "warning_stock": 30, "sales_weight": 1.2},
        {"name": "金骏眉红茶", "price_range": (80, 100), "warning_stock": 25, "sales_weight": 1.0},
        {"name": "铁观音", "price_range": (150, 180), "warning_stock": 20, "sales_weight": 0.8},
        {"name": "大红袍", "price_range": (200, 250), "warning_stock": 15, "sales_weight": 0.6},
        {"name": "普洱生茶", "price_range": (120, 150), "warning_stock": 20, "sales_weight": 0.7},
        {"name": "普洱熟茶", "price_range": (100, 130), "warning_stock": 20, "sales_weight": 0.7},
        {"name": "龙井茶", "price_range": (180, 220), "warning_stock": 15, "sales_weight": 0.8},
        {"name": "碧螺春", "price_range": (160, 200), "warning_stock": 15, "sales_weight": 0.7},
        {"name": "白毫银针", "price_range": (280, 320), "warning_stock": 10, "sales_weight": 0.5},
        {"name": "黑茶", "price_range": (60, 80), "warning_stock": 35, "sales_weight": 1.1}
    ]

def generate_time_points(days: int = 30) -> list[datetime]:
    """生成交易时间点"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    time_points = []
    temp_date = start_date
    
    while temp_date <= end_date:
        if random.random() < 0.8:  # 80%的时间点会发生交易
            time_points.append(temp_date)
        temp_date += timedelta(hours=random.randint(2, 6))
    
    return time_points

def create_inventory_and_transactions(
    db: Session,
    store_id: int,
    operator_id: int,
    products: list[dict],
    time_points: list[datetime]
):
    """创建商品和交易记录"""
    # 验证是否有公司数据
    supplier_count = db.query(Company).filter(
        Company.store_id == store_id,
        Company.type == CompanyType.SUPPLIER
    ).count()
    
    customer_count = db.query(Company).filter(
        Company.store_id == store_id,
        Company.type == CompanyType.CUSTOMER
    ).count()
    
    if supplier_count == 0 or customer_count == 0:
        raise ValueError("请先确保已创建供应商和客户数据")

    # 获取所有供应商和客户
    suppliers = db.query(Company).filter(
        Company.store_id == store_id,
        Company.type == CompanyType.SUPPLIER
    ).all()
    
    customers = db.query(Company).filter(
        Company.store_id == store_id,
        Company.type == CompanyType.CUSTOMER
    ).all()
    
    if not suppliers or not customers:
        logger.error("未找到供应商或客户数据")
        return

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
                supplier = random.choice(suppliers)  # 随机选择供应商
                quantity = random.randint(10, 20)
                price = round(random.uniform(*product["price_range"]), 2)
                transaction = Transaction(
                    barcode=barcode,
                    inventory_id=inventory.id,
                    type="in",
                    quantity=quantity,
                    price=Decimal(str(price)),
                    total=Decimal(str(quantity * price)),
                    timestamp=transaction_time,
                    store_id=store_id,
                    operator_id=operator_id,
                    company_id=supplier.id
                )
                db.add(transaction)
                inventory.stock += quantity

            # 出库记录
            if random.random() < 0.3 and inventory.stock > 0:
                customer = random.choice(customers)  # 随机选择客户
                max_quantity = min(inventory.stock, 15)
                if max_quantity > 0:
                    quantity = random.randint(1, max_quantity)
                    price = round(random.uniform(*product["price_range"]) * 1.2, 2)
                    transaction = Transaction(
                        barcode=barcode,
                        inventory_id=inventory.id,
                        type="out",
                        quantity=quantity,
                        price=Decimal(str(price)),
                        total=Decimal(str(quantity * price)),
                        timestamp=transaction_time,
                        store_id=store_id,
                        operator_id=operator_id,
                        company_id=customer.id
                    )
                    db.add(transaction)
                    inventory.stock -= quantity

        db.flush()

def clear_store_data(db: Session, store_id: int):
    """清除店铺所有数据"""
    logger.info("开始清除数据...")
    
    # 按顺序删除以避免外键约束问题
    db.query(Transaction).filter(Transaction.store_id == store_id).delete()
    db.query(OperationLog).filter(OperationLog.store_id == store_id).delete()
    db.query(Inventory).filter(Inventory.store_id == store_id).delete()
    db.query(User).filter(
        User.store_id == store_id,
        User.username != "demo"
    ).delete()
    
    logger.info("数据清除完成")

def initialize_demo_data(db: Session = None):
    """初始化演示数据"""
    if not db:
        db = SessionLocal()
    try:
        # 创建演示账号和商店
        store, user = create_or_update_demo_account(db)
        
        # 生成基础数据
        products = generate_demo_products()
        time_points = generate_time_points()
        
        # 添加演示公司
        demo_companies = [
            {
                "name": "新新超市",
                "type": CompanyType.CUSTOMER,
                "contact": "张经理",
                "phone": "13800138000",
                "address": "市中心路123号",
                "is_active": True
            },
            {
                "name": "顺丰物流",
                "type": CompanyType.SUPPLIER,
                "contact": "李经理",
                "phone": "13900139000",
                "address": "开发区456号",
                "is_active": True
            },
            {
                "name": "双星贸易",
                "type": CompanyType.SUPPLIER,
                "contact": "王总",
                "phone": "13700137000",
                "address": "商贸城789号",
                "is_active": True
            },
            {
                "name": "友谊超市",
                "type": CompanyType.CUSTOMER,
                "contact": "赵店长",
                "phone": "13800138000",
                "address": "建设路54号",
                "is_active": True
            },
            {
                "name": "德邦物流",
                "type": CompanyType.SUPPLIER,
                "contact": "刘主任",
                "phone": "13900139000",
                "address": "胜利路40号",
                "is_active": True
            },
            {
                "name": "红星幼儿园",
                "type": CompanyType.CUSTOMER,
                "contact": "田园长",
                "phone": "13700137000",
                "address": "幸福街12号",
                "is_active": True
            }
            
        ]

        # 先创建公司
        for company_data in demo_companies:
            company = db.query(Company).filter(
                Company.name == company_data["name"],
                Company.store_id == store.id
            ).first()
            
            if not company:
                company = Company(
                    **company_data,
                    store_id=store.id
                )
                db.add(company)
                logger.info(f"创建演示公司: {company_data['name']}")
        
        # 提交公司创建
        db.commit()
        
        # 再创建商品和交易记录
        create_inventory_and_transactions(db, store.id, user.id, products, time_points)
        
        db.commit()
        logger.info("演示数据初始化成功！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化演示数据失败: {str(e)}")
        raise
    finally:
        db.close()

def reset_demo_data(days: int = 30):
    """重置演示数据"""
    db = SessionLocal()
    try:
        # 获取演示账号
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            logger.error("未找到演示账号")
            return

        # 清除现有数据
        clear_store_data(db, demo_user.store_id)
        
        # 先提交清除操作
        db.commit()
        
        # 重新生成数据
        products = generate_demo_products()
        time_points = generate_time_points(days)
        create_inventory_and_transactions(
            db, 
            demo_user.store_id, 
            demo_user.id,  # 确保这里传入了正确的 operator_id
            products, 
            time_points
        )
        
        db.commit()
        logger.info(f"演示数据重置完成 - {datetime.now()}")
        
    except Exception as e:
        logger.error(f"重置演示数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# 店主账号创建函数
def create_owner(db: Session, store_name: str, store_address: str,
                username: str, password: str, owner_name: str = None):
    """创建店铺和店主账号"""
    try:
        # 创建商店
        store = Store(
            name=store_name,
            address=store_address
        )
        db.add(store)
        db.flush()
        
        # 创建店主账号
        owner = User(
            username=username,
            hashed_password=pwd_context.hash(password),
            name=owner_name,
            is_owner=True,
            store_id=store.id,
            permissions=[]  # 店主不需要额外权限
        )
        db.add(owner)
        db.commit()
        logger.info(f"成功创建店铺 '{store_name}' 和店主账号 '{username}'")
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建失败: {str(e)}")
        raise

def create_owner_interactive():
    """交互式创建店主账号"""
    db = SessionLocal()
    try:
        store_name = input("请输入店铺名称: ")
        store_address = input("请输入店铺地址: ")
        username = input("请输入店主用户名: ")
        password = input("请输入店主密码: ")
        owner_name = input("请输入店主姓名(可选): ").strip() or None
        
        create_owner(db, store_name, store_address, username, password, owner_name)
    finally:
        db.close()

# 命令行解析
def parse_args():
    parser = argparse.ArgumentParser(description='数据管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建店主命令
    owner_parser = subparsers.add_parser('create-owner', help='创建店铺和店主账号')
    
    # 演示数据命令
    demo_parser = subparsers.add_parser('demo', help='演示数据管理')
    demo_subparsers = demo_parser.add_subparsers(dest='demo_command')
    
    # demo init 命令
    demo_init = demo_subparsers.add_parser('init', help='初始化演示账号和数据')
    
    # demo reset 命令
    demo_reset = demo_subparsers.add_parser('reset', help='重置演示数据')
    demo_reset.add_argument('--days', type=int, default=30,
                           help='生成多少天的数据 (默认: 30)')
    
    return parser.parse_args()

def show_menu():
    """显示主菜单"""
    print("""
数据管理工具
===========

1. 创建店铺和店主账号
2. 初始化演示数据
3. 重置演示数据
4. 退出

请选择操作 (1-4): """, end='')

def get_days_input():
    """获取天数输入"""
    while True:
        try:
            days = input("请输入要生成的数据天数 (默认30天): ").strip()
            if not days:
                return 30
            days = int(days)
            if days <= 0:
                print("天数必须大于0")
                continue
            return days
        except ValueError:
            print("请输入有效的数字")

def main():
    # 确保数据库表已创建
    Base.metadata.create_all(bind=engine)
    
    while True:
        try:
            show_menu()
            choice = input().strip()
            
            if choice == '1':
                logger.info("开始创建店铺和店主账号...")
                create_owner_interactive()
                
            elif choice == '2':
                logger.info("开始初始化演示数据...")
                initialize_demo_data()
                
            elif choice == '3':
                days = get_days_input()
                logger.info(f"开始重置演示数据 (生成{days}天数据)...")
                reset_demo_data(days)
                
            elif choice == '4':
                print("感谢使用，再见！")
                break
                
            else:
                print("无效的选择，请重新输入")
                
            input("\n按回车键继续...")
            
        except Exception as e:
            logger.error(f"操作失败: {str(e)}")
            input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1) 