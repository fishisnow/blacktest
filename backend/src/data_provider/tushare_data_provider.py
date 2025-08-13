"""
Tushare 数据提供器
继承自 BaseDataProvider，实现 Tushare 特定的数据获取逻辑
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd
import tushare as ts
from vnpy.trader.object import BarData, Interval

from backend.src.data_provider.base_data_provider import BaseDataProvider
from backend.src.conf.config import DataSource
from backend.src.symbol.symbols import get_symbols_by_market, get_symbol_info


class TushareDataProvider(BaseDataProvider):
    """Tushare 数据提供器"""

    def __init__(self, token: Optional[str] = None):
        """
        初始化 Tushare 数据提供器
        
        Args:
            token: Tushare API Token
        """
        super().__init__(DataSource.TUSHARE)
        self.token = token
        self.pro_api = None

    def connect(self) -> bool:
        """连接到 Tushare"""
        try:
            if not self.token:
                print("Tushare Token 未设置")
                return False

            ts.set_token(self.token)
            self.pro_api = ts.pro_api()
            self.is_connected = True
            print("Tushare 连接成功")
            return True

        except Exception as e:
            print(f"Tushare 连接失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开连接"""
        self.pro_api = None
        self.is_connected = False
        print("Tushare 连接已断开")

    def get_historical_data(self, symbol: str, start_date: str, end_date: str,
                            **kwargs) -> Optional[List[BarData]]:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码 (如 '000300.SH', '600519.SH')
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            **kwargs: 其他参数
            
        Returns:
            BarData列表或None
        """
        if not self.is_connected:
            if not self.connect():
                return None

        if not self.is_symbol_supported(symbol):
            print(f"Tushare 不支持的代码: {symbol}")
            return None

        symbol_info = get_symbol_info(symbol)
        name = symbol_info["name"]
        data_type = symbol_info["type"]

        try:
            print(f"从 Tushare 获取 {name} ({symbol}) 的历史数据...")

            # 根据数据类型调用不同的API
            if data_type == "index":
                df = self.pro_api.index_daily(
                    ts_code=symbol,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
            elif data_type == "stock":
                df = self.pro_api.daily(
                    ts_code=symbol,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
            else:
                print(f"不支持的数据类型: {data_type}")
                return None

            if df is None or df.empty:
                print(f"Tushare 返回空数据")
                return None

            # 按日期升序排列
            df = df.sort_values('trade_date')
            print(f"从 Tushare 获取到 {len(df)} 条{name}数据")

            # 转换为 BarData 格式
            bars = self._convert_to_bar_data(df, symbol)
            return bars

        except Exception as e:
            print(f"从 Tushare 获取 {symbol} 数据失败: {e}")
            return None

    def get_supported_symbols(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的股票代码列表（仅返回 A股 相关的）"""
        # 返回 A股 市场的股票代码
        cn_symbols = get_symbols_by_market("CN", "stock")
        return cn_symbols

    def test_connection(self) -> bool:
        """测试连接"""
        if not self.connect():
            return False

        try:
            # 尝试获取一个简单的数据来测试连接
            df = self.pro_api.index_daily(
                ts_code='000001.SH',
                start_date='20240101',
                end_date='20240101'
            )
            print("Tushare 连接测试成功")
            return True

        except Exception as e:
            print(f"Tushare 连接测试失败: {e}")
            return False
        finally:
            self.disconnect()

    def _convert_to_bar_data(self, df: pd.DataFrame, symbol: str) -> List[BarData]:
        """将 Tushare DataFrame 转换为 BarData 列表"""
        bars = []
        symbol_info = get_symbol_info(symbol)
        exchange = symbol_info["exchange"]

        for index, row in df.iterrows():
            # 处理日期 - tushare返回的是YYYYMMDD格式
            date_str = str(row['trade_date'])
            dt = datetime.strptime(date_str, '%Y%m%d')

            # 创建BarData对象
            bar = BarData(
                symbol=symbol.split('.')[0],
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

        print(f"成功转换 {len(bars)} 条 Tushare 数据")
        return bars


if __name__ == "__main__":
    # 测试 Tushare 数据提供器
    import os
    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv('TUSHARE_TOKEN')

    if not token:
        print("请在 .env 文件中设置 TUSHARE_TOKEN")
        exit(1)

    provider = TushareDataProvider(token)

    # 显示支持的股票代码
    print("Tushare 支持的股票代码:")
    symbols = provider.get_supported_symbols()
    for code, info in symbols.items():
        print(f"  {code}: {info['name']} ({info['type']})")

    # 测试连接
    print(f"\n测试连接到 Tushare...")
    if provider.test_connection():
        print("连接测试成功！")

        # 测试获取数据
        print(f"\n测试获取沪深300指数历史数据...")
        bars = provider.get_historical_data("000300.SH", "2024-01-01", "2024-01-05")

        if bars:
            print(f"获取数据成功，共 {len(bars)} 条记录")
            # 显示前几条数据
            for i, bar in enumerate(bars[:3]):
                print(f"  {bar.datetime.strftime('%Y-%m-%d')}: "
                      f"开盘={bar.open_price:.2f}, "
                      f"最高={bar.high_price:.2f}, "
                      f"最低={bar.low_price:.2f}, "
                      f"收盘={bar.close_price:.2f}")
        else:
            print("获取数据失败")
    else:
        print("连接测试失败！请检查:")
        print("1. TUSHARE_TOKEN 是否正确设置")
        print("2. 网络连接是否正常")
        print("3. Tushare 服务是否可用")
