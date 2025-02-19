from .store import Store  # 首先导入 Store 模型
from .company import Company, Payment  # 导入 Company 模型
from .inventory import Inventory, Transaction, StockOrder, StockOrderItem  # 再导入 inventory 模型
from .user import User  # 最后导入 User 模型
from .log import OperationLog  # 再导入 log 模型
# 确保所有模型都被正确加载
__all__ = [
    'User', 
    'Store', 
    'Inventory', 
    'Transaction', 
    'OperationLog', 
    'Company',
    'Payment',
    'StockOrder', 
    'StockOrderItem'
] 