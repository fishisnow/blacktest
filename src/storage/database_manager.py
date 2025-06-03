"""
回测结果数据库管理器
支持存储和查询回测结果
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd


class BacktestResultsDB:
    """回测结果数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 回测运行记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    strategy_params TEXT NOT NULL,
                    run_time TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    html_path TEXT,
                    png_path TEXT,
                    excel_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 回测统计结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    total_return REAL,
                    annual_return REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    profit_factor REAL,
                    win_rate REAL,
                    total_trades INTEGER,
                    total_pnl REAL,
                    max_profit REAL,
                    max_loss REAL,
                    stats_json TEXT,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)
                )
            """)
            
            # 交易记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    trade_datetime TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    offset TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    pnl REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)
                )
            """)
            
            # 每日结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_daily_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    balance REAL NOT NULL,
                    total_value REAL NOT NULL,
                    pnl REAL NOT NULL,
                    net_pnl REAL NOT NULL,
                    commission REAL NOT NULL,
                    position REAL DEFAULT 0,
                    FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)
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
            
            # 保存统计结果
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_stats 
                (run_id, total_return, annual_return, max_drawdown, sharpe_ratio, 
                 profit_factor, win_rate, total_trades, stats_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                stats.get('total_return', 0) if 'total_return' in stats.columns else 0,
                stats.get('annual_return', 0) if 'annual_return' in stats.columns else 0,
                stats.get('max_drawdown', 0) if 'max_drawdown' in stats.columns else 0,
                stats.get('sharpe_ratio', 0) if 'sharpe_ratio' in stats.columns else 0,
                stats.get('profit_factor', 0) if 'profit_factor' in stats.columns else 0,
                stats.get('win_rate', 0) if 'win_rate' in stats.columns else 0,
                stats.get('total_trades', 0) if 'total_trades' in stats.columns else 0,
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
                SELECT br.*, bs.total_return, bs.max_drawdown, bs.sharpe_ratio
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