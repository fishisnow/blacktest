"""
vnpy趋势跟踪策略回测系统
支持上证50、沪深300、创业板指、上证指数、深证成指回测
"""
from datetime import datetime

from vnpy.trader.object import Interval
from vnpy_ctastrategy.backtesting import BacktestingEngine

from backend.src.conf.backtest_config import BacktestConfig
from backend.src.storage.data_loader import DataLoader
from backend.src.storage.db_utils import get_db_manager, init_database
from backend.src.result_analyzer import ResultAnalyzer
from backend.src.constants import INITIAL_CAPITAL


class BacktestRunner:
    def __init__(self, config: BacktestConfig = None):
        self.engine = BacktestingEngine()
        self.data_loader = DataLoader()

        # 使用配置化的分析器和数据库管理器
        self.config = config
        # 如果有配置，使用配置中的数据库路径初始化，否则使用默认路径
        if config and config.results_db_path:
            self.db_manager = init_database(config.results_db_path)
        else:
            self.db_manager = get_db_manager()
        self.analyzer = ResultAnalyzer(config, self.db_manager)

        self.data_loaded = False

    def _convert_to_vt_symbol(self, symbol: str) -> str:
        """
        将股票代码转换为vnpy标准格式
        支持：
        - A股：000001.SZ -> 000001.SZSE, 000001.SH -> 000001.SSE
        - 港股：00700.HK -> 00700.SEHK
        - 美股：AAPL.US -> AAPL.NASDAQ
        """
        # 如果已经包含交易所后缀
        if '.' in symbol:
            code, exchange_suffix = symbol.split('.')
            exchange_upper = exchange_suffix.upper()

            # A股 - 上海证券交易所
            if exchange_upper == 'SH':
                return f"{code}.SSE"
            # A股 - 深圳证券交易所
            elif exchange_upper == 'SZ':
                return f"{code}.SZSE"
            # 港股 - 香港交易所 港股代码格式相反
            elif code == 'HK':
                code = exchange_upper
                return f"{code}.SEHK"
            # 美股 - 纳斯达克（vnpy中美股通常用NASDAQ）
            elif exchange_upper in 'US':
                return f"{code}.NASDAQ"
            else:
                raise ValueError(f"不支持的交易所后缀: {exchange_suffix}")

        raise ValueError(f"无法识别的股票代码格式: {symbol}")

    def setup_engine(self, symbol: str, start_date: datetime, end_date: datetime):
        """设置回测引擎"""
        # 自动转换股票代码为vt_symbol格式
        vt_symbol = self._convert_to_vt_symbol(symbol)
        self.engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=Interval.DAILY,
            start=start_date,
            end=end_date,
            rate=0.0003,  # 手续费率
            slippage=0.0001,  # 滑点
            size=100,  # 合约乘数 - 中国股票1手=100股
            pricetick=0.01,  # 最小价格变动
            capital=INITIAL_CAPITAL,  # 初始资金
        )

    def add_strategy(self, strategy_class, setting: dict):
        """添加策略"""
        self.engine.add_strategy(strategy_class, setting)

    def load_data(self, symbol: str, start_date: str, end_date: str):
        """将数据保存到vnpy数据库，然后从数据库加载"""
        from vnpy.trader.database import get_database

        data = self.data_loader.get_index_data(symbol, start_date, end_date)
        if data is None or len(data) == 0:
            print("无法获取数据")
            return False

        # 2. 获取vnpy数据库实例
        database = get_database()

        # 3. 将数据保存到vnpy数据库
        print(f"开始将 {len(data)} 条数据保存到vnpy数据库...")
        database.save_bar_data(data)
        print("数据保存完成")

        # 4. 使用引擎的load_data方法从数据库加载
        self.engine.load_data()
        print(f"成功从数据库加载历史数据")
        self.data_loaded = True
        return True

    def run_backtest(self):
        """运行回测"""
        if not self.data_loaded:
            print("警告：没有加载数据，无法运行回测")
            return
        self.engine.run_backtesting()

    def show_results(self):
        """显示回测结果"""
        # 获取回测统计数据
        stats = self.engine.calculate_result()
        print("回测统计结果:")
        for key, value in stats.items():
            print(f"{key}: {value}")

        # 获取交易记录
        trades = self.engine.get_all_trades()
        daily_results = self.engine.get_all_daily_results()

        # 保存配置到数据库
        if self.db_manager and self.config:
            self.db_manager.save_backtest_run(self.config)

        # 分析和可视化结果
        self.analyzer.analyze_results(stats, trades, daily_results)
