"""
数据加载器
支持从tushare获取指数和股票数据，支持本地SQLite缓存
从.env文件读取tushare token以增强安全性
"""
import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from vnpy.trader.object import BarData, Interval, Exchange
from vnpy.trader.constant import Interval as IntervalConstant

# 加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("警告: python-dotenv未安装，无法从.env文件读取配置")

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    print("tushare未安装，请安装后使用")


class DataLoader:
    """数据加载器，支持本地SQLite缓存"""
    
    def __init__(self, token: Optional[str] = None, db_path: str = "market_data.db"):
        """初始化数据加载器"""
        if not TUSHARE_AVAILABLE:
            raise ImportError("tushare未安装，请安装tushare后使用")
        
        # 获取token的优先级：
        # 1. 传入的token参数
        # 2. 环境变量TUSHARE_TOKEN 
        # 3. .env文件中的TUSHARE_TOKEN
        tushare_token = token
        if not tushare_token:
            tushare_token = os.getenv('TUSHARE_TOKEN')
            
        if tushare_token:
            ts.set_token(tushare_token)
            print("已成功设置Tushare Token")
        else:
            print("警告: 未找到Tushare Token，可能无法获取数据")
            print("请在.env文件中设置TUSHARE_TOKEN=your_token_here")
            
        self.db_path = db_path
        # 指数映射
        self.index_mapping = {
            "000016": {"name": "上证50", "ts_code": "000016.SH", "exchange": Exchange.SSE, "type": "index"},
            "000300": {"name": "沪深300", "ts_code": "000300.SH", "exchange": Exchange.SSE, "type": "index"},
            "399006": {"name": "创业板指", "ts_code": "399006.SZ", "exchange": Exchange.SZSE, "type": "index"},
            "000001": {"name": "上证指数", "ts_code": "000001.SH", "exchange": Exchange.SSE, "type": "index"},
            "399001": {"name": "深证成指", "ts_code": "399001.SZ", "exchange": Exchange.SZSE, "type": "index"},
        }
        
        # 股票映射
        self.stock_mapping = {
            "688981": {"name": "中芯国际", "ts_code": "688981.SH", "exchange": Exchange.SSE, "type": "stock"},
        }
        
        # 合并所有映射
        self.symbol_mapping = {**self.index_mapping, **self.stock_mapping}
        
        # 初始化数据库
        self._init_database()
        
    def _init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建通用数据表（同时支持指数和股票）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                data_type TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER DEFAULT 0,
                turnover REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, data_type, trade_date)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_type_date 
            ON market_data(symbol, data_type, trade_date)
        ''')
        
        conn.commit()
        conn.close()
        print(f"数据库已初始化: {self.db_path}")
        
    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> Optional[List[BarData]]:
        """获取指数或股票数据，优先从缓存读取"""
        if not TUSHARE_AVAILABLE:
            print("tushare不可用，无法获取数据")
            return None
            
        if symbol not in self.symbol_mapping:
            print(f"不支持的代码: {symbol}")
            print(f"支持的指数代码: {list(self.index_mapping.keys())}")
            print(f"支持的股票代码: {list(self.stock_mapping.keys())}")
            return None
            
        symbol_info = self.symbol_mapping[symbol]
        name = symbol_info["name"]
        data_type = symbol_info["type"]
        
        print(f"开始获取 {name} ({data_type}) 数据...")
        
        # 1. 先从缓存中获取数据
        cached_data = self._get_cached_data(symbol, data_type, start_date, end_date)
        missing_dates = self._get_missing_dates(cached_data, start_date, end_date)
        
        if not missing_dates:
            print(f"从缓存获取到完整数据，共 {len(cached_data)} 条记录")
            return cached_data
        
        print(f"缓存中有 {len(cached_data)} 条记录，需要从远程获取 {len(missing_dates)} 个日期段的数据")
        
        # 2. 从远程获取缺失的数据
        new_data = []
        for date_range in missing_dates:
            remote_data = self._get_remote_data(symbol, date_range[0], date_range[1])
            if remote_data:
                new_data.extend(remote_data)
                # 保存到缓存
                self._save_to_cache(remote_data, data_type)
        
        # 3. 合并缓存数据和新数据
        all_data = cached_data + new_data
        all_data.sort(key=lambda x: x.datetime)
        
        print(f"获取数据完成，共 {len(all_data)} 条记录")
        return all_data
    
    def _get_cached_data(self, symbol: str, data_type: str, start_date: str, end_date: str) -> List[BarData]:
        """从缓存获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT symbol, trade_date, open_price, high_price, low_price, 
                   close_price, volume, turnover
            FROM market_data
            WHERE symbol = ? AND data_type = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date
        '''
        
        cursor.execute(query, (symbol, data_type, start_date.replace('-', ''), end_date.replace('-', '')))
        rows = cursor.fetchall()
        conn.close()
        
        bars = []
        symbol_info = self.symbol_mapping[symbol]
        exchange = symbol_info["exchange"]
        
        for row in rows:
            dt = datetime.strptime(row[1], '%Y%m%d')
            bar = BarData(
                symbol=row[0],
                exchange=exchange,
                datetime=dt,
                interval=Interval.DAILY,
                volume=int(row[6]),
                turnover=float(row[7]),
                open_price=float(row[2]),
                high_price=float(row[3]),
                low_price=float(row[4]),
                close_price=float(row[5]),
                gateway_name="CACHE"
            )
            bars.append(bar)
        
        return bars
    
    def _get_missing_dates(self, cached_data: List[BarData], start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """获取缺失的日期范围"""
        if not cached_data:
            return [(start_date, end_date)]
        
        # 获取缓存中的日期集合
        cached_dates = {bar.datetime.strftime('%Y-%m-%d') for bar in cached_data}
        
        # 生成完整的日期范围（工作日）
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        all_dates = pd.date_range(start=start_dt, end=end_dt, freq='B')
        all_date_strs = {date.strftime('%Y-%m-%d') for date in all_dates}
        
        # 找出缺失的日期
        missing_dates = sorted(all_date_strs - cached_dates)
        
        if not missing_dates:
            return []
        
        # 将连续的日期合并为范围
        ranges = []
        range_start = missing_dates[0]
        range_end = missing_dates[0]
        
        for i in range(1, len(missing_dates)):
            current_date = datetime.strptime(missing_dates[i], '%Y-%m-%d')
            prev_date = datetime.strptime(missing_dates[i-1], '%Y-%m-%d')
            
            # 如果是连续的工作日
            if (current_date - prev_date).days <= 3:  # 考虑周末
                range_end = missing_dates[i]
            else:
                ranges.append((range_start, range_end))
                range_start = missing_dates[i]
                range_end = missing_dates[i]
        
        ranges.append((range_start, range_end))
        return ranges
    
    def _get_remote_data(self, symbol: str, start_date: str, end_date: str) -> Optional[List[BarData]]:
        """从tushare获取远程数据"""
        symbol_info = self.symbol_mapping[symbol]
        ts_code = symbol_info["ts_code"]
        name = symbol_info["name"]
        data_type = symbol_info["type"]
        
        try:
            pro = ts.pro_api()
            
            # 根据数据类型调用不同的API
            if data_type == "index":
                print(f"调用 index_daily 接口获取指数数据...")
                df = pro.index_daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
            elif data_type == "stock":
                print(f"调用 daily 接口获取股票数据...")
                df = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
            else:
                print(f"不支持的数据类型: {data_type}")
                return None
            
            if df is None or df.empty:
                print(f"tushare返回空数据，请检查日期范围和网络连接")
                return None
            
            # 按日期升序排列
            df = df.sort_values('trade_date')
            
            print(f"从tushare获取到 {len(df)} 条{name}数据")
            return self._convert_to_bar_data(df, symbol)
            
        except Exception as e:
            print(f"从tushare获取 {name} 数据失败: {e}")
            return None
    
    def _save_to_cache(self, bars: List[BarData], data_type: str):
        """保存数据到缓存"""
        if not bars:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for bar in bars:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, data_type, trade_date, open_price, high_price, low_price, 
                     close_price, volume, turnover)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bar.symbol,
                    data_type,
                    bar.datetime.strftime('%Y%m%d'),
                    bar.open_price,
                    bar.high_price,
                    bar.low_price,
                    bar.close_price,
                    bar.volume,
                    bar.turnover
                ))
            except Exception as e:
                print(f"保存数据到缓存失败: {e}")
        
        conn.commit()
        conn.close()
        print(f"已保存 {len(bars)} 条数据到缓存")
    
    def _convert_to_bar_data(self, df: pd.DataFrame, symbol: str) -> List[BarData]:
        """将tushare DataFrame转换为BarData列表"""
        bars = []
        symbol_info = self.symbol_mapping[symbol]
        exchange = symbol_info["exchange"]
        
        for index, row in df.iterrows():
            # 处理日期 - tushare返回的是YYYYMMDD格式
            date_str = str(row['trade_date'])
            dt = datetime.strptime(date_str, '%Y%m%d')
                
            # 创建BarData对象
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt,
                interval=Interval.DAILY,
                volume=int(row.get('vol', 0)) * 100,  # tushare成交量单位是手，转换为股
                turnover=float(row.get('amount', 0)) * 1000,  # tushare成交额单位是千元，转换为元
                open_price=float(row['open']),
                high_price=float(row['high']),
                low_price=float(row['low']),
                close_price=float(row['close']),
                gateway_name="TUSHARE"
            )
            bars.append(bar)
            
        print(f"成功转换 {len(bars)} 条数据")
        return bars
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清空缓存数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('DELETE FROM market_data WHERE symbol = ?', (symbol,))
            print(f"已清空 {symbol} 的缓存数据")
        else:
            cursor.execute('DELETE FROM market_data')
            print("已清空所有缓存数据")
        
        conn.commit()
        conn.close()
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取各代码的数据统计
        cursor.execute('''
            SELECT symbol, data_type, COUNT(*) as count, 
                   MIN(trade_date) as min_date, 
                   MAX(trade_date) as max_date
            FROM market_data 
            GROUP BY symbol, data_type
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        cache_info = {}
        for row in results:
            symbol = row[0]
            data_type = row[1]
            cache_info[symbol] = {
                'count': row[2],
                'start_date': row[3],
                'end_date': row[4],
                'type': data_type,
                'name': self.symbol_mapping.get(symbol, {}).get('name', symbol)
            }
        
        return cache_info
        
    def save_data_to_csv(self, bars: List[BarData], filename: str):
        """保存数据到CSV文件"""
        data = []
        for bar in bars:
            data.append({
                'datetime': bar.datetime,
                'symbol': bar.symbol,
                'open': bar.open_price,
                'high': bar.high_price,
                'low': bar.low_price,
                'close': bar.close_price,
                'volume': bar.volume
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"数据已保存到 {filename}")


if __name__ == "__main__":
    # 测试数据加载器
    # 注意：需要在.env文件中配置TUSHARE_TOKEN
    try:
        loader = DataLoader()
        
        # 显示缓存信息
        cache_info = loader.get_cache_info()
        print("当前缓存信息:")
        for symbol, info in cache_info.items():
            print(f"  {symbol} ({info['name']}) [{info['type']}]: {info['count']}条数据 "
                  f"({info['start_date']} ~ {info['end_date']})")
        
        # 测试股票数据
        print(f"\n测试获取中芯国际股票数据...")
        bars = loader.get_index_data("688981", "2023-01-01", "2023-12-31")
        if bars:
            print(f"获取数据成功，共 {len(bars)} 条记录")
            # 显示前5条数据作为示例
            for i, bar in enumerate(bars[:5]):
                print(f"  {bar.datetime.strftime('%Y-%m-%d')}: O={bar.open_price}, H={bar.high_price}, L={bar.low_price}, C={bar.close_price} [来源: {bar.gateway_name}]")
        else:
            print("获取数据失败")
                
    except ImportError as e:
        print(f"初始化失败: {e}")
        print("请先安装tushare和python-dotenv: pip install -r requirements.txt") 