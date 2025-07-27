"""
回测结果数据库管理器
支持存储和查询回测结果
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any
import os

import pandas as pd

from backend.src.constants import INITIAL_CAPITAL
from backend.src.utils.statistics_calculator import StatisticsCalculator


class BacktestResultsDB:
    """回测结果数据库管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super(BacktestResultsDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        # 只初始化一次
        if self._initialized:
            return
            
        # 确定数据库路径
        if db_path is None:
            # 默认路径：项目根目录下的 backtest_results.db
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            self.db_path = os.path.join(project_root, 'backtest_results.db')
        else:
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(db_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if db_path.startswith('../'):
                    # 处理 ../backtest_results.db 这种路径
                    project_root = os.path.dirname(os.path.dirname(current_dir))
                    relative_path = db_path.replace('../', '')
                    self.db_path = os.path.join(project_root, relative_path)
                elif db_path.startswith('../../'):
                    # 处理 ../../backtest_results.db 这种路径
                    project_root = os.path.dirname(os.path.dirname(current_dir))
                    relative_path = db_path.replace('../../', '')
                    self.db_path = os.path.join(project_root, relative_path)
                else:
                    self.db_path = os.path.abspath(db_path)
            else:
                self.db_path = db_path
        
        print(f"数据库路径: {self.db_path}")
        self.init_database()
        self._initialized = True
    
    @classmethod
    def get_instance(cls, db_path: str = None):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 回测运行记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 主键ID，自增
                    run_id TEXT UNIQUE NOT NULL,                             -- 回测运行唯一标识，格式：YYYYMMDD_HHMMSS
                    symbol TEXT NOT NULL,                                    -- 交易标的代码，如：000001.SZ
                    strategy_name TEXT NOT NULL,                             -- 策略名称
                    start_date TEXT NOT NULL,                                -- 回测开始日期，格式：YYYY-MM-DD
                    end_date TEXT NOT NULL,                                  -- 回测结束日期，格式：YYYY-MM-DD
                    strategy_params TEXT NOT NULL,                           -- 策略参数，JSON格式存储
                    run_time TEXT NOT NULL,                                  -- 回测执行时间，ISO格式
                    status TEXT DEFAULT 'running',                           -- 回测状态：running/completed/failed
                    html_path TEXT,                                          -- HTML报告文件路径
                    png_path TEXT,                                           -- PNG图表文件路径
                    excel_path TEXT,                                         -- Excel报告文件路径
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP          -- 记录创建时间
                )
            """)
            
            # 回测统计结果表 - 包含所有需要的列
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 主键ID，自增
                    run_id TEXT NOT NULL,                                    -- 关联回测运行ID
                    total_return REAL,                                       -- 总收益率(%)
                    annual_return REAL,                                      -- 年化收益率(%)
                    max_drawdown REAL,                                       -- 最大回撤(%)
                    sharpe_ratio REAL,                                       -- 夏普比率
                    profit_factor REAL,                                      -- 盈利因子（总盈利/总亏损）
                    win_rate REAL,                                           -- 胜率(%)，盈利交易数/总交易数
                    total_trades INTEGER,                                    -- 总交易次数（开仓+平仓）
                    total_pnl REAL,                                          -- 总盈亏金额
                    max_profit REAL,                                         -- 最大单笔盈利
                    max_loss REAL,                                           -- 最大单笔亏损
                    stats_json TEXT,                                         -- 原始统计数据JSON
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)  -- 外键约束
                )
            """)
            
            # 交易记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 主键ID，自增
                    run_id TEXT NOT NULL,                                    -- 关联回测运行ID
                    trade_datetime TEXT NOT NULL,                            -- 交易时间，ISO格式
                    symbol TEXT NOT NULL,                                    -- 交易标的代码
                    direction TEXT NOT NULL,                                 -- 交易方向：LONG/SHORT
                    offset TEXT NOT NULL,                                    -- 开平标志：OPEN/CLOSE
                    price REAL NOT NULL,                                     -- 成交价格
                    volume INTEGER NOT NULL,                                 -- 成交数量（股数）
                    pnl REAL DEFAULT 0,                                      -- 交易盈亏（vnpy计算，通常为0）
                    commission REAL DEFAULT 0,                               -- 交易佣金
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)  -- 外键约束
                )
            """)
            
            # 每日结果表 - 添加唯一约束防止重复数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_daily_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 主键ID，自增
                    run_id TEXT NOT NULL,                                    -- 关联回测运行ID
                    date TEXT NOT NULL,                                      -- 日期，格式：YYYY-MM-DD
                    balance REAL NOT NULL,                                   -- 现金余额
                    total_value REAL NOT NULL,                               -- 总资产价值（现金+持仓市值）
                    pnl REAL NOT NULL,                                       -- 当日盈亏
                    net_pnl REAL NOT NULL,                                   -- 当日净盈亏（扣除佣金）
                    commission REAL NOT NULL,                                -- 当日佣金
                    position REAL DEFAULT 0,                                 -- 持仓数量
                    UNIQUE(run_id, date),                                    -- 唯一约束：每个运行每天只能有一条记录
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)  -- 外键约束
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def save_backtest_run(self, config: 'BacktestConfig') -> str:
        """保存回测运行记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_runs 
                (run_id, symbol, strategy_name, start_date, end_date, strategy_params, run_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                config.run_id,
                config.symbol,
                config.strategy_name,
                config.start_date,
                config.end_date,
                json.dumps(config.strategy_params, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return config.run_id
    
    def save_backtest_results(self, run_id: str, stats: pd.DataFrame, 
                             trades: List, daily_results: List,
                             html_path: str = None, png_path: str = None, 
                             excel_path: str = None):
        """保存完整的回测结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 更新运行记录状态和文件路径
            cursor.execute("""
                UPDATE backtest_runs 
                SET status = 'completed', html_path = ?, png_path = ?, excel_path = ?
                WHERE run_id = ?
            """, (html_path, png_path, excel_path, run_id))
            
            # 计算统计指标
            calculated_stats = StatisticsCalculator.calculate_backtest_statistics(
                daily_results, trades, INITIAL_CAPITAL)
            
            # 将 DataFrame 转换为字典并序列化
            stats_dict = stats.to_dict()
            # 处理非JSON兼容的键（如datetime.date）
            def convert_keys(obj):
                if isinstance(obj, dict):
                    return {str(k): convert_keys(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_keys(item) for item in obj]
                else:
                    return obj
            
            stats_dict_converted = convert_keys(stats_dict)
            stats_json = json.dumps(stats_dict_converted, ensure_ascii=False, default=str)
            
            # 保存统计结果 - 使用计算出的统计指标
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_stats 
                (run_id, total_return, annual_return, max_drawdown, sharpe_ratio, 
                 profit_factor, win_rate, total_trades, total_pnl, max_profit, max_loss, stats_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                calculated_stats['total_return'],
                calculated_stats['annual_return'],
                calculated_stats['max_drawdown'],
                calculated_stats['sharpe_ratio'],
                calculated_stats['profit_factor'],
                calculated_stats['win_rate'],
                calculated_stats['total_trades'],
                calculated_stats['total_pnl'],
                calculated_stats['max_profit'],
                calculated_stats['max_loss'],
                stats_json
            ))
            
            # 保存交易记录
            for trade in trades:
                cursor.execute("""
                    INSERT INTO backtest_trades 
                    (run_id, trade_datetime, symbol, direction, offset, price, volume, pnl, commission)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    str(getattr(trade, 'datetime', '')),
                    getattr(trade, 'symbol', ''),
                    str(getattr(trade, 'direction', '')),
                    str(getattr(trade, 'offset', '')),
                    getattr(trade, 'price', 0),
                    getattr(trade, 'volume', 0),
                    getattr(trade, 'pnl', 0),
                    getattr(trade, 'commission', 0)
                ))
            
            # 保存每日结果
            for result in daily_results:
                cursor.execute("""
                    INSERT INTO backtest_daily_results 
                    (run_id, date, balance, total_value, pnl, net_pnl, commission)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    str(getattr(result, 'date', '')),
                    getattr(result, 'balance', 0),
                    getattr(result, 'total_value', 0),
                    getattr(result, 'pnl', 0),
                    getattr(result, 'net_pnl', 0),
                    getattr(result, 'commission', 0)
                ))
            
            conn.commit()
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """获取所有回测运行记录"""
        with self.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT br.*, bs.total_return, bs.annual_return, bs.max_drawdown, bs.sharpe_ratio, 
                       bs.profit_factor, bs.win_rate, bs.total_trades, bs.total_pnl, 
                       bs.max_profit, bs.max_loss
                FROM backtest_runs br
                LEFT JOIN backtest_stats bs ON br.run_id = bs.run_id
                ORDER BY br.created_at DESC
            """, conn)
            
            return df.to_dict('records')
    
    def get_run_details(self, run_id: str) -> Dict[str, Any]:
        """获取特定运行的详细信息"""
        with self.get_connection() as conn:
            # 基本信息
            run_info = pd.read_sql_query("""
                SELECT * FROM backtest_runs WHERE run_id = ?
            """, conn, params=[run_id])
            
            if run_info.empty:
                return None
            
            # 统计信息
            stats = pd.read_sql_query("""
                SELECT * FROM backtest_stats WHERE run_id = ?
            """, conn, params=[run_id])
            
            # 交易记录
            trades = pd.read_sql_query("""
                SELECT * FROM backtest_trades WHERE run_id = ? ORDER BY trade_datetime
            """, conn, params=[run_id])
            
            # 每日结果
            daily_results = pd.read_sql_query("""
                SELECT * FROM backtest_daily_results WHERE run_id = ? ORDER BY date
            """, conn, params=[run_id])
            
            return {
                'run_info': run_info.to_dict('records')[0],
                'stats': stats.to_dict('records')[0] if not stats.empty else {},
                'trades': trades.to_dict('records'),
                'daily_results': daily_results.to_dict('records')
            }
    
    def compare_runs(self, run_ids: List[str]) -> Dict[str, Any]:
        """比较多个回测运行结果"""
        with self.get_connection() as conn:
            placeholders = ','.join(['?'] * len(run_ids))
            
            comparison_data = pd.read_sql_query(f"""
                SELECT br.run_id, br.symbol, br.strategy_name, br.strategy_params,
                       bs.total_return, bs.annual_return, bs.max_drawdown, 
                       bs.sharpe_ratio, bs.win_rate, bs.total_trades
                FROM backtest_runs br
                LEFT JOIN backtest_stats bs ON br.run_id = bs.run_id
                WHERE br.run_id IN ({placeholders})
                ORDER BY bs.total_return DESC
            """, conn, params=run_ids)
            
            return comparison_data.to_dict('records') 