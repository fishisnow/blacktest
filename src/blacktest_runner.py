"""
vnpy趋势跟踪策略回测系统
支持上证50、沪深300、创业板指、上证指数、深证成指回测
"""
from datetime import datetime

from vnpy.trader.object import Interval
from vnpy_ctastrategy.backtesting import BacktestingEngine

from src.conf.backtest_config import BacktestConfig
from src.storage.data_loader import DataLoader
from src.storage.database_manager import BacktestResultsDB
from result_analyzer import ResultAnalyzer

INITIAL_CAPITAL = 1_000_000


class BacktestRunner:
    def __init__(self, config: BacktestConfig = None):
        self.engine = BacktestingEngine()
        self.data_loader = DataLoader()

        # 使用配置化的分析器和数据库管理器
        self.config = config
        self.db_manager = BacktestResultsDB(config.results_db_path) if config else None
        self.analyzer = ResultAnalyzer(config, self.db_manager)

        self.data_loaded = False

    def _convert_to_vt_symbol(self, symbol: str) -> str:
        # 如果已经包含交易所后缀
        if '.' in symbol:
            code, exchange_suffix = symbol.split('.')
            if exchange_suffix.upper() in ['SH', 'SSE']:
                return f"{code}.SSE"
            elif exchange_suffix.upper() in ['SZ', 'SZSE']:
                return f"{code}.SZSE"

        raise ValueError(f"不支持的代码: {symbol}")

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
            size=1,  # 合约乘数
            pricetick=0.01,  # 最小价格变动
            capital=INITIAL_CAPITAL,  # 初始资金
        )

    def add_strategy(self, strategy_class, setting: dict):
        """添加策略"""
        self.engine.add_strategy(strategy_class, setting)

    def load_data(self, symbol: str, start_date: str, end_date: str):
        """将数据保存到vnpy数据库，然后从数据库加载"""
        from vnpy.trader.database import get_database

        # 1. 从tushare获取数据
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
