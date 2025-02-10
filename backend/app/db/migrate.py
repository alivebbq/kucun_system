from decimal import Decimal
from sqlalchemy import text
from app.db.session import engine

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

if __name__ == "__main__":
    migrate() 