"""
数据加载器
支持从多个数据源获取指数和股票数据，支持本地SQLite缓存
使用抽象的数据提供器接口，支持 tushare、futu openapi 等多种数据源
从.env文件读取配置以增强安全性
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from vnpy.trader.object import BarData, Interval, Exchange

from backend.src.data_provider.base_data_provider import BaseDataProvider
from backend.src.conf.config import config_manager
from backend.src.data_provider.data_provider_factory import data_provider_factory
from backend.src.utils.date_utils import trading_date_utils

load_dotenv()


class DataLoader:
    """数据加载器，支持多数据源和本地SQLite缓存"""

    def __init__(self, db_path: str = "market_data.db"):
        """初始化数据加载器"""
        self.db_path = db_path
        self.config_manager = config_manager
        self.factory = data_provider_factory

        # 初始化数据提供器工厂
        self.factory.initialize()

        # 初始化数据库
        self._init_database()

        # 显示配置信息
        self.config_manager.print_config_summary()

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
                data_source TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER DEFAULT 0,
                turnover REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, data_type, data_source, trade_date)
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_type_source_date 
            ON market_data(symbol, data_type, data_source, trade_date)
        ''')

        conn.commit()
        conn.close()
        print(f"数据库已初始化: {self.db_path}")

    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> Optional[List[BarData]]:
        """获取指数或股票数据，支持多数据源，优先从缓存读取"""
        print(f"开始获取 {symbol} 数据...")

        # 1. 先从缓存中获取数据
        cached_data = self._get_cached_data(symbol, start_date, end_date)
        missing_dates = self._get_missing_dates(cached_data, start_date, end_date)

        if not missing_dates:
            print(f"从缓存获取到完整数据，共 {len(cached_data)} 条记录")
            return cached_data

        print(f"缓存中有 {len(cached_data)} 条记录，需要从远程获取 {len(missing_dates)} 个日期段的数据")

        # 2. 从远程获取缺失的数据（尝试多个数据源）
        new_data = []
        for date_range in missing_dates:
            remote_data = self._get_remote_data_multi_source(symbol, date_range[0], date_range[1])
            if remote_data:
                new_data.extend(remote_data)

        # 3. 合并缓存数据和新数据
        all_data = cached_data + new_data
        all_data.sort(key=lambda x: x.datetime)

        print(f"获取数据完成，共 {len(all_data)} 条记录")
        return all_data

    def _get_remote_data_multi_source(self, symbol: str, start_date: str, end_date: str) -> Optional[List[BarData]]:
        """从多个数据源获取远程数据"""
        # 查找支持该股票代码的数据提供器（按优先级排序）
        providers = self.factory.find_providers_for_symbol(symbol)

        if not providers:
            print(f"没有数据源支持股票代码: {symbol}")
            return None

        print(f"获取交易日范围: {start_date} ~ {end_date}")

        # 按优先级尝试各个数据源
        for provider in providers:
            print(f"尝试从 {provider.get_data_source_name()} 获取数据...")
            try:
                data = provider.get_historical_data(symbol, start_date, end_date)
                if data:
                    # 保存到缓存
                    self._save_to_cache(symbol, data, self._get_data_type(symbol, provider), provider.get_data_source_name())
                    print(f"从 {provider.get_data_source_name()} 获取到 {len(data)} 条数据")
                    return data
                else:
                    print(f"{provider.get_data_source_name()} 返回空数据")
            except Exception as e:
                print(f"从 {provider.get_data_source_name()} 获取数据失败: {e}")

        print(f"所有数据源都无法获取范围 {start_date} ~ {end_date} 的数据")
        return None

    def _determine_market(self, symbol: str) -> str:
        # 根据代码格式判断
        if symbol.endswith('.SH') or symbol.endswith('.SZ'):
            return "CN"
        elif symbol.startswith('HK.'):
            return "HK"
        else:
            return "US"  # 默认

    def _get_data_type(self, symbol: str, provider: BaseDataProvider) -> str:
        """获取数据类型（股票或指数）"""
        try:
            symbol_info = provider.get_symbol_info(symbol)
            if symbol_info:
                return symbol_info.get('type', 'stock')
        except:
            pass
        return 'stock'  # 默认为股票

    def _get_cached_data(self, symbol: str, start_date: str, end_date: str) -> List[BarData]:
        """从缓存获取数据（合并所有数据源）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT symbol, data_source, trade_date, open_price, high_price, low_price, 
                   close_price, volume, turnover
            FROM market_data
            WHERE symbol = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date
        '''

        cursor.execute(query, (symbol, start_date.replace('-', ''), end_date.replace('-', '')))
        rows = cursor.fetchall()
        conn.close()

        bars = []

        for row in rows:
            dt = datetime.strptime(row[2], '%Y%m%d')

            # 确定交易所
            exchange = Exchange.NASDAQ  # 默认值

            # 尝试从数据提供器获取交易所信息
            providers = self.factory.find_providers_for_symbol(symbol)
            if providers:
                symbol_info = providers[0].get_symbol_info(symbol)
                if symbol_info and 'exchange' in symbol_info:
                    exchange = symbol_info['exchange']

            bar = BarData(
                symbol=row[0],
                exchange=exchange,
                datetime=dt,
                interval=Interval.DAILY,
                volume=int(row[7]),
                turnover=float(row[8]),
                open_price=float(row[3]),
                high_price=float(row[4]),
                low_price=float(row[5]),
                close_price=float(row[6]),
                gateway_name=f"CACHE_{row[1]}"
            )
            bars.append(bar)

        return bars

    def _get_missing_dates(self, cached_data: List[BarData], start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """获取缺失的日期范围，使用交易日历优化"""
        if not cached_data:
            return [(start_date, end_date)]

        # 获取缓存中的日期集合
        cached_dates = {bar.datetime.strftime('%Y-%m-%d') for bar in cached_data}

        # 确定市场类型（从缓存数据中获取）
        market = "CN"  # 默认中国市场
        if cached_data:
            symbol = cached_data[0].symbol
            market = self._determine_market(symbol)

        # 使用交易日历获取所有交易日
        try:
            all_trading_days = trading_date_utils.get_trading_days_in_range(start_date, end_date, market)
            all_trading_dates = set(all_trading_days)
        except Exception as e:
            print(f"获取交易日列表失败，回退到工作日: {e}")
            # 回退到原来的工作日逻辑
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            all_dates = pd.date_range(start=start_dt, end=end_dt, freq='B')
            all_trading_dates = {date.strftime('%Y-%m-%d') for date in all_dates}

        # 找出缺失的交易日
        missing_dates = sorted(all_trading_dates - cached_dates)

        if not missing_dates:
            return []

        # 将连续的日期合并为范围
        ranges = []
        range_start = missing_dates[0]
        range_end = missing_dates[0]

        for i in range(1, len(missing_dates)):
            current_date = datetime.strptime(missing_dates[i], '%Y-%m-%d')
            prev_date = datetime.strptime(missing_dates[i - 1], '%Y-%m-%d')

            # 如果是连续的交易日（考虑周末和节假日间隔）
            if (current_date - prev_date).days <= 7:  # 放宽间隔限制，考虑长假期
                range_end = missing_dates[i]
            else:
                ranges.append((range_start, range_end))
                range_start = missing_dates[i]
                range_end = missing_dates[i]

        ranges.append((range_start, range_end))
        return ranges

    def _save_to_cache(self, symbol, bars: List[BarData], data_type: str, data_source: str):
        """保存数据到缓存"""
        if not bars:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for bar in bars:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, data_type, data_source, trade_date, open_price, high_price, low_price, 
                     close_price, volume, turnover)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    data_type,
                    data_source,
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
        print(f"已保存 {len(bars)} 条数据到缓存 (来源: {data_source})")

    def clear_cache(self, symbol: Optional[str] = None, data_source: Optional[str] = None):
        """清空缓存数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if symbol and data_source:
            cursor.execute('DELETE FROM market_data WHERE symbol = ? AND data_source = ?', (symbol, data_source))
            print(f"已清空 {symbol} 来自 {data_source} 的缓存数据")
        elif symbol:
            cursor.execute('DELETE FROM market_data WHERE symbol = ?', (symbol,))
            print(f"已清空 {symbol} 的所有缓存数据")
        elif data_source:
            cursor.execute('DELETE FROM market_data WHERE data_source = ?', (data_source,))
            print(f"已清空来自 {data_source} 的所有缓存数据")
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
            SELECT symbol, data_type, data_source, COUNT(*) as count, 
                   MIN(trade_date) as min_date, 
                   MAX(trade_date) as max_date
            FROM market_data 
            GROUP BY symbol, data_type, data_source
        ''')

        results = cursor.fetchall()
        conn.close()

        cache_info = {}
        for row in results:
            symbol = row[0]
            data_type = row[1]
            data_source = row[2]

            if symbol not in cache_info:
                cache_info[symbol] = {}

            cache_info[symbol][data_source] = {
                'count': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'type': data_type,
                'name': self._get_symbol_name(symbol)
            }

        return cache_info

    def _get_symbol_name(self, symbol: str) -> str:
        """获取股票/指数名称"""
        providers = self.factory.find_providers_for_symbol(symbol)
        if providers:
            symbol_info = providers[0].get_symbol_info(symbol)
            if symbol_info and 'name' in symbol_info:
                return symbol_info['name']
        return symbol

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
                'volume': bar.volume,
                'source': bar.gateway_name
            })

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"数据已保存到 {filename}")

    def get_supported_symbols(self) -> dict:
        """获取所有支持的股票代码"""
        supported = {}

        # 获取所有数据源支持的股票代码
        symbol_sources = self.factory.get_supported_symbols_all()

        for symbol, sources in symbol_sources.items():
            # 获取第一个支持该股票的数据源的详细信息
            providers = self.factory.find_providers_for_symbol(symbol)
            if providers:
                symbol_info = providers[0].get_symbol_info(symbol)
                if symbol_info:
                    supported[symbol] = {
                        'name': symbol_info.get('name', symbol),
                        'type': symbol_info.get('type', 'stock'),
                        'sources': [source.value for source in sources]
                    }

        return supported

    def test_all_connections(self) -> dict:
        """测试所有数据源连接"""
        return self.factory.test_all_providers()

    def cleanup(self):
        """清理资源"""
        self.factory.cleanup()


if __name__ == "__main__":
    # 测试数据加载器
    try:
        loader = DataLoader()

        # 显示支持的股票代码
        print("\n支持的股票代码:")
        symbols = loader.get_supported_symbols()
        for symbol, info in symbols.items():
            sources = ', '.join(info['sources'])
            print(f"  {symbol}: {info['name']} ({info['type']}) - 数据源: {sources}")

        # 测试所有连接
        print("\n测试数据源连接:")
        test_results = loader.test_all_connections()
        for source, result in test_results.items():
            status = "✓ 成功" if result else "✗ 失败"
            print(f"  {source.value}: {status}")

        # 显示缓存信息
        cache_info = loader.get_cache_info()
        print("\n当前缓存信息:")
        for symbol, sources in cache_info.items():
            print(f"  {symbol} ({loader._get_symbol_name(symbol)}):")
            for source, info in sources.items():
                print(f"    {source}: {info['count']}条数据 ({info['start_date']} ~ {info['end_date']})")

        # 测试获取数据（如果有支持的代码）
        if symbols:
            test_symbol = list(symbols.keys())[0]
            print(f"\n测试获取 {test_symbol} 数据...")
            bars = loader.get_index_data(test_symbol, "2024-01-01", "2024-01-10")
            if bars:
                print(f"获取数据成功，共 {len(bars)} 条记录")
                # 显示前5条数据作为示例
                for i, bar in enumerate(bars[:5]):
                    print(
                        f"  {bar.datetime.strftime('%Y-%m-%d')}: O={bar.open_price}, H={bar.high_price}, L={bar.low_price}, C={bar.close_price} [来源: {bar.gateway_name}]")
            else:
                print("获取数据失败")

    except Exception as e:
        print(f"初始化失败: {e}")
        print("请检查:")
        print("1. 是否安装了所需的依赖包")
        print("2. 是否正确配置了数据源")
        print("3. 网络连接是否正常")
    finally:
        # 清理资源
        try:
            loader.cleanup()
        except:
            pass
