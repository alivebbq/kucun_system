import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from decimal import Decimal
from sqlalchemy import text, create_engine, Column, Float
from app.db.session import engine
from app.core.config import settings
from app.models.inventory import Base, Inventory

def migrate():
    with engine.connect() as connection:
        # 删除 avg_selling_price 字段
        try:
            connection.execute(
                text("ALTER TABLE inventory DROP COLUMN IF EXISTS avg_selling_price")
            )
            print("成功删除 avg_selling_price 字段")
        except Exception as e:
            print(f"删除 avg_selling_price 字段失败: {str(e)}")
        
        # 确保 selling_price 字段存在
        try:
            connection.execute(
                text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2)")
            )
            print("确保 selling_price 字段存在")
        except Exception as e:
            if "already exists" not in str(e):
                raise e
            print("selling_price 字段已存在")
        
        # 更新 avg_purchase_price 为 NULL 的记录
        connection.execute(
            text("UPDATE inventory SET avg_purchase_price = 0.00 WHERE avg_purchase_price IS NULL")
        )
        
        connection.commit()
        print("数据库迁移完成")

def upgrade_database():
    # 使用已存在的 engine 而不是创建新的
    with engine.connect() as connection:
        try:
            connection.execute(
                text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS avg_selling_price FLOAT DEFAULT 0.0")
            )
            connection.commit()
            print("成功添加 avg_selling_price 字段")
        except Exception as e:
            print(f"字段可能已存在或发生错误: {e}")

if __name__ == "__main__":
    migrate()
    upgrade_database() 