"""
vnpy趋势跟踪策略回测系统
支持上证50、沪深300、创业板指、上证指数、深证成指回测
"""
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# vnpy 4.0 新的导入路径
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy_ctastrategy.base import EngineType

from vnpy.trader.object import Interval
from vnpy.trader.constant import Exchange
from strategies.trend_following_strategy import TrendFollowingStrategy
from data_loader import DataLoader
from result_analyzer import ResultAnalyzer


class BacktestRunner:
    def __init__(self):
        self.engine = BacktestingEngine()
        # 使用.env文件中的token
        self.data_loader = DataLoader()
        self.analyzer = ResultAnalyzer()
        self.data_loaded = False

    def setup_engine(self, symbol: str, exchange: Exchange, start_date: datetime, end_date: datetime):
        """设置回测引擎"""
        self.engine.set_parameters(
            vt_symbol=f"{symbol}.{exchange.value}",
            interval=Interval.DAILY,
            start=start_date,
            end=end_date,
            rate=0.0003,  # 手续费率
            slippage=0.0001,  # 滑点
            size=1,  # 合约乘数
            pricetick=0.01,  # 最小价格变动
            capital=1000000,  # 初始资金
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

        # 调试信息
        print(f"\n🔍 调试信息:")
        print(f"交易记录数量: {len(trades)}")
        print(f"每日结果数量: {len(daily_results)}")
        
        if trades:
            print(f"交易记录示例属性: {[attr for attr in dir(trades[0]) if not attr.startswith('_')]}")
            print(f"第一笔交易详情:")
            trade = trades[0]
            for attr in ['datetime', 'time', 'symbol', 'direction', 'offset', 'price', 'volume', 'pnl', 'commission']:
                if hasattr(trade, attr):
                    print(f"  {attr}: {getattr(trade, attr)}")
        
        if daily_results:
            print(f"每日结果示例属性: {[attr for attr in dir(daily_results[0]) if not attr.startswith('_')]}")
            print(f"第一天结果详情:")
            result = daily_results[0]
            for attr in ['date', 'datetime', 'balance', 'total_value', 'pnl', 'net_pnl', 'commission']:
                if hasattr(result, attr):
                    print(f"  {attr}: {getattr(result, attr)}")

        # 分析和可视化结果
        self.analyzer.analyze_results(stats, trades, daily_results)


def main():
    """主函数"""
    print("vnpy趋势跟踪策略回测系统")
    print("=" * 50)

    # 定义回测参数
    indexes = {
        # "000016": "上证50",
        # "000300": "沪深300",
        # "399006": "创业板指",
        # "000001": "上证指数",
        # "399001": "深证成指"
        "688981": "中芯国际"
    }

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 1, 1)

    # 策略参数
    strategy_setting = {
        "fast_ma_length": 10,
        "slow_ma_length": 30,
        "atr_length": 14,
        "atr_multiplier": 2.0,
        "fixed_size": 1
    }

    for symbol, name in indexes.items():
        print(f"\n开始回测 {name} ({symbol})")
        print("-" * 30)

        runner = BacktestRunner()

        # 设置回测引擎
        # 根据symbol判断交易所
        if symbol in ["000016", "000300", "000001", "688981"]:  # 上交所：上证50、沪深300、上证指数、中芯国际(科创板)
            exchange = Exchange.SSE
        else:  # 深交所：创业板指、深证成指
            exchange = Exchange.SZSE
        runner.setup_engine(symbol, exchange, start_date, end_date)

        # 添加策略
        runner.add_strategy(TrendFollowingStrategy, strategy_setting)

        # 加载数据
        if runner.load_data(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")):
            # 运行回测
            runner.run_backtest()

            # 显示结果
            runner.show_results()
        else:
            print(f"无法加载 {name} 数据，跳过回测")


if __name__ == "__main__":
    main()
