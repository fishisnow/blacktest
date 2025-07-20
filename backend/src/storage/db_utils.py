"""
数据库工具模块
提供统一的数据库访问接口
"""
from .database_manager import BacktestResultsDB


def get_db_manager():
    """获取数据库管理器实例"""
    return BacktestResultsDB.get_instance()


def init_database(db_path: str = None):
    """初始化数据库"""
    return BacktestResultsDB.get_instance(db_path)


def reset_database():
    """重置数据库实例（主要用于测试）"""
    BacktestResultsDB.reset_instance() 