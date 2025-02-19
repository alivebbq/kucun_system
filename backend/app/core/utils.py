from datetime import datetime
import random

def generate_order_no(type: str) -> str:
    """生成订单编号"""
    # 格式：类型(I/O) + 日期 + 4位随机数
    prefix = "I" if type == "in" else "O"
    date = datetime.now().strftime("%Y%m%d")
    random_num = str(random.randint(1000, 9999))
    return f"{prefix}{date}{random_num}" 