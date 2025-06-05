"""
常量定义模块
避免循环导入，集中管理项目中的常量
"""

# 回测相关常量
INITIAL_CAPITAL = 1_000_000  # 初始资金（100万）

# 交易日常量
TRADING_DAYS_PER_YEAR = 252  # 每年交易日数

# 数值精度常量
PROFIT_THRESHOLD = 0.01  # 盈利天数判断阈值
LOSS_THRESHOLD = -0.01   # 亏损天数判断阈值 