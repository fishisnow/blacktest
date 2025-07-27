"""
Futu OpenAPI 数据提供器
继承自 BaseDataProvider，实现 Futu 特定的数据获取逻辑
"""
from typing import Optional, List, Dict, Any
from futu import *
from vnpy.trader.object import BarData, Interval

from backend.src.data_provider.base_data_provider import BaseDataProvider
from backend.src.conf.config import DataSource
from backend.src.symbol.symbols import get_symbols_by_market, get_symbol_info


class FutuDataProvider(BaseDataProvider):
    """Futu OpenAPI 数据提供器"""

    def __init__(self, host: str = '127.0.0.1', port: int = 11111, timeout: int = 30):
        """
        初始化 Futu 数据提供器
        
        Args:
            host: Futu OpenD 主机地址
            port: Futu OpenD 端口
            timeout: 超时时间
        """
        super().__init__(DataSource.FUTU)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.quote_ctx = None

    def connect(self) -> bool:
        """连接到 Futu OpenAPI"""
        try:
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            self.is_connected = True
            print(f"成功连接到 Futu OpenAPI: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"连接 Futu OpenAPI 失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None
        self.is_connected = False
        print("已断开 Futu OpenAPI 连接")

    def get_historical_data(self, symbol: str, start_date: str, end_date: str,
                            **kwargs) -> Optional[List[BarData]]:
        """
        获取历史 K 线数据
        
        Args:
            symbol: 股票代码 (如 'US.AAPL', 'HK.00700')
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            **kwargs: 其他参数
        
        Returns:
            BarData 列表或 None
        """
        if not self.is_connected:
            if not self.connect():
                return None

        if not self.is_symbol_supported(symbol):
            print(f"Futu 不支持的股票代码: {symbol}")
            supported_symbols = self.get_supported_symbols()
            print(f"支持的代码: {list(supported_symbols.keys())}")
            return None

        symbol_info = get_symbol_info(symbol)
        name = symbol_info["name"]

        print(f"从 Futu 获取 {name} ({symbol}) 的历史数据...")

        try:
            # 获取所有数据（分页处理）
            all_data = []
            page_req_key = None
            max_count = 1000  # 每页最大数量

            while True:
                if page_req_key is None:
                    # 第一页
                    ret, data, page_req_key = self.quote_ctx.request_history_kline(
                        code=symbol,
                        start=start_date,
                        end=end_date,
                        max_count=max_count
                    )
                else:
                    # 后续页
                    ret, data, page_req_key = self.quote_ctx.request_history_kline(
                        code=symbol,
                        start=start_date,
                        end=end_date,
                        max_count=max_count,
                        page_req_key=page_req_key
                    )

                if ret != RET_OK:
                    print(f"获取数据失败: {data}")
                    break

                if data is not None and not data.empty:
                    all_data.append(data)
                    print(f"获取到 {len(data)} 条数据")

                # 如果没有更多页面，退出循环
                if page_req_key is None:
                    break

            if not all_data:
                print("未获取到任何数据")
                return None

            # 合并所有数据
            combined_data = pd.concat(all_data, ignore_index=True)
            print(f"总共获取到 {len(combined_data)} 条历史数据")

            # 转换为 BarData 格式
            bars = self._convert_to_bar_data(combined_data, symbol)
            return bars

        except Exception as e:
            print(f"获取 {name} 历史数据失败: {e}")
            return None

    def get_supported_symbols(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的股票代码列表（返回美股和港股）"""
        # 返回美股和港股市场的股票代码
        us_symbols = get_symbols_by_market("US")
        hk_symbols = get_symbols_by_market("HK")
        
        # 合并两个市场的股票代码
        supported_symbols = {**us_symbols, **hk_symbols}
        return supported_symbols

    def test_connection(self) -> bool:
        """测试连接"""
        if not self.connect():
            return False

        try:
            # 尝试获取一个简单的数据来测试连接
            ret, data = self.quote_ctx.get_market_state(['US.AAPL'])
            if ret == RET_OK:
                print("Futu OpenAPI 连接测试成功")
                return True
            else:
                print(f"Futu OpenAPI 连接测试失败: {data}")
                return False
        except Exception as e:
            print(f"Futu OpenAPI 连接测试异常: {e}")
            return False
        finally:
            self.disconnect()

    def _convert_to_bar_data(self, df: pd.DataFrame, symbol: str) -> List[BarData]:
        """将 Futu DataFrame 转换为 BarData 列表"""
        bars = []
        symbol_info = get_symbol_info(symbol)
        exchange = symbol_info["exchange"]

        for index, row in df.iterrows():
            # 处理日期时间
            time_key = row['time_key']
            dt = datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')

            # 创建 BarData 对象
            bar = BarData(
                symbol=symbol.split('.')[-1],
                exchange=exchange,
                datetime=dt,
                interval=Interval.DAILY,
                volume=int(row.get('volume', 0)),
                turnover=float(row.get('turnover', 0)),
                open_price=float(row['open']),
                high_price=float(row['high']),
                low_price=float(row['low']),
                close_price=float(row['close']),
                gateway_name="FUTU"
            )
            bars.append(bar)

        # 按时间排序
        bars.sort(key=lambda x: x.datetime)
        print(f"成功转换 {len(bars)} 条 Futu 数据")
        return bars


if __name__ == "__main__":
    # 测试 Futu 数据提供器
    provider = FutuDataProvider()

    # 显示支持的股票代码
    print("Futu 支持的股票代码:")
    symbols = provider.get_supported_symbols()
    for code, info in symbols.items():
        print(f"  {code}: {info['name']} ({info['market']}) - {info['type']}")

    # 测试连接
    print(f"\n测试连接到 Futu OpenAPI...")
    if provider.test_connection():
        print("连接测试成功！")

        # 测试获取数据
        print(f"\n测试获取苹果股票历史数据...")
        bars = provider.get_historical_data(
            symbol="US.AAPL",
            start_date="2024-01-01",
            end_date="2024-01-10"
        )

        if bars:
            print(f"获取数据成功，共 {len(bars)} 条记录")
            # 显示前几条数据
            for i, bar in enumerate(bars[:5]):
                print(f"  {bar.datetime.strftime('%Y-%m-%d')}: "
                      f"开盘={bar.open_price:.2f}, "
                      f"最高={bar.high_price:.2f}, "
                      f"最低={bar.low_price:.2f}, "
                      f"收盘={bar.close_price:.2f}")
        else:
            print("获取数据失败")
    else:
        print("连接测试失败！请检查:")
        print("1. Futu OpenD 是否已启动")
        print("2. 连接参数是否正确")
        print("3. 网络连接是否正常")
