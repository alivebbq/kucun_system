from .inventory import Inventory, Transaction  # 先导入 inventory
from .user import User, Store  # 后导入 user

# 这样可以确保所有模型都被正确加载
__all__ = ['User', 'Store', 'Inventory', 'Transaction'] 