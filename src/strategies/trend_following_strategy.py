"""
趋势跟踪策略
基于移动平均线交叉和ATR止损的趋势跟踪策略
"""
from typing import Any

import numpy as np
import talib
from vnpy.trader.constant import Direction
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from src.blacktest_runner import INITIAL_CAPITAL


class TrendFollowingStrategy(CtaTemplate):
    """趋势跟踪策略"""

    author = "vnpy回测系统"

    # 策略参数
    fast_ma_length = 10  # 快速移动平均线周期
    slow_ma_length = 30  # 慢速移动平均线周期
    atr_length = 14  # ATR计算周期
    atr_multiplier = 2.0  # ATR止损倍数
    fixed_size = 1  # 固定交易手数（当position_mode为"固定手数"时使用）
    position_mode = "固定手数"  # 仓位模式: "固定手数", "1/4仓", "1/2仓", "全仓"

    # 策略变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0
    atr_value = 0.0

    # 信号标记
    long_entry = False
    short_entry = False
    long_stop = 0.0
    short_stop = 0.0

    # 盈亏跟踪
    entry_price = 0.0
    total_pnl = 0.0
    position_pnl = 0.0

    # 策略参数和变量列表， 父类会自动读取这些参数和变量
    parameters = [
        "fast_ma_length",
        "slow_ma_length",
        "atr_length",
        "atr_multiplier",
        "fixed_size",
        "position_mode"
    ]

    variables = [
        "fast_ma0",
        "fast_ma1",
        "slow_ma0",
        "slow_ma1",
        "atr_value",
        "long_entry",
        "short_entry",
        "long_stop",
        "short_stop",
        "entry_price",
        "total_pnl",
        "position_pnl"
    ]

    def __init__(self, cta_engine: Any, strategy_name: str, vt_symbol: str, setting: dict):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        # 存储买卖信号用于分析
        self.trade_signals = []

    def calculate_position_size(self, bar: BarData) -> int:
        """根据仓位模式计算交易手数"""
        if self.position_mode == "固定手数":
            return self.fixed_size

        # 对于分仓模式，使用初始资金作为基准计算
        # 这样可以确保不同仓位模式之间的比较公平性
        base_capital = INITIAL_CAPITAL

        if self.position_mode == "1/4仓":
            position_value = base_capital * 0.25  # 1/4仓位的资金
        elif self.position_mode == "1/2仓":
            position_value = base_capital * 0.5  # 1/2仓位的资金
        elif self.position_mode == "全仓":
            position_value = base_capital * 0.95  # 全仓，保留5%作为保证金
        else:
            # 默认返回固定手数
            return self.fixed_size

        # 计算对应的交易手数
        # 假设每手100股（这是A股的标准交易单位）
        size = int(position_value / (bar.close_price * 100))
        return max(1, size)  # 至少1手

    def on_init(self):
        """策略初始化"""
        print(f"策略初始化 - 资金管理模式: {self.position_mode}")
        self.load_bar(10)

    def on_start(self):
        """策略启动"""
        print(f"策略启动 - 当前资金管理模式: {self.position_mode}")

    def on_stop(self):
        """策略停止"""
        print("策略停止")

    def on_tick(self, tick: TickData):
        """处理tick数据"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """处理K线数据"""
        self.cancel_all()

        # 更新数组管理器
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算技术指标
        fast_ma_array = talib.SMA(am.close, self.fast_ma_length)
        slow_ma_array = talib.SMA(am.close, self.slow_ma_length)
        atr_array = talib.ATR(am.high, am.low, am.close, self.atr_length)

        # 更新当前指标值
        self.fast_ma0 = fast_ma_array[-1]
        self.fast_ma1 = fast_ma_array[-2]
        self.slow_ma0 = slow_ma_array[-1]
        self.slow_ma1 = slow_ma_array[-2]
        self.atr_value = atr_array[-1]

        # 计算持仓盈亏
        if self.pos != 0 and self.entry_price > 0:
            if self.pos > 0:  # 多头
                self.position_pnl = (bar.close_price - self.entry_price) * self.pos
            else:  # 空头
                self.position_pnl = (self.entry_price - bar.close_price) * abs(self.pos)
        else:
            self.position_pnl = 0.0

        # 判断交叉信号
        golden_cross = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 <= self.slow_ma1
        death_cross = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 >= self.slow_ma1

        # 计算止损价
        self.long_stop = bar.close_price - self.atr_value * self.atr_multiplier
        self.short_stop = bar.close_price + self.atr_value * self.atr_multiplier

        # 计算交易手数
        trade_size = self.calculate_position_size(bar)

        # 交易逻辑
        if self.pos == 0:
            # 无持仓时的开仓逻辑
            if golden_cross:
                self.buy(bar.close_price + 5, trade_size)
                self.long_entry = True
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': bar.close_price,
                    'signal': 'BUY',
                    'type': f'金叉开多({self.position_mode})',
                    'size': trade_size
                })

            elif death_cross:
                self.short(bar.close_price - 5, trade_size)
                self.short_entry = True
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': bar.close_price,
                    'signal': 'SHORT',
                    'type': f'死叉开空({self.position_mode})',
                    'size': trade_size
                })

        elif self.pos > 0:
            # 多头持仓
            if death_cross:
                self.sell(bar.close_price - 5, abs(self.pos))
                self.long_entry = False
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': bar.close_price,
                    'signal': 'SELL',
                    'type': '死叉平多',
                    'size': abs(self.pos)
                })
            elif bar.close_price <= self.long_stop:
                self.sell(self.long_stop, abs(self.pos))
                self.long_entry = False
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': self.long_stop,
                    'signal': 'SELL',
                    'type': 'ATR止损',
                    'size': abs(self.pos)
                })

        elif self.pos < 0:
            # 空头持仓
            if golden_cross:
                self.cover(bar.close_price + 5, abs(self.pos))
                self.short_entry = False
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': bar.close_price,
                    'signal': 'COVER',
                    'type': '金叉平空',
                    'size': abs(self.pos)
                })
            elif bar.close_price >= self.short_stop:
                self.cover(self.short_stop, abs(self.pos))
                self.short_entry = False
                self.trade_signals.append({
                    'datetime': bar.datetime,
                    'price': self.short_stop,
                    'signal': 'COVER',
                    'type': 'ATR止损',
                    'size': abs(self.pos)
                })

        # 更新UI
        self.put_event()

    def on_order(self, order: OrderData):
        """处理委托数据"""
        pass

    def on_trade(self, trade: TradeData):
        """处理成交数据"""
        # 更新入场价格
        if self.pos == 0:  # 新开仓
            self.entry_price = trade.price
        elif (self.pos > 0 and trade.direction == Direction.SHORT) or \
                (self.pos < 0 and trade.direction == Direction.LONG):
            # 平仓，计算盈亏
            if self.entry_price > 0:
                if self.pos > 0:  # 平多
                    realized_pnl = (trade.price - self.entry_price) * trade.volume
                else:  # 平空
                    realized_pnl = (self.entry_price - trade.price) * trade.volume
                self.total_pnl += realized_pnl
                print(f"交易完成 - 价格: {trade.price:.2f}, 盈亏: {realized_pnl:.2f}, 累计盈亏: {self.total_pnl:.2f}")

            # 如果完全平仓，重置入场价格
            if abs(self.pos) == trade.volume:
                self.entry_price = 0.0

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """处理停止单数据"""
        pass


class ArrayManager:
    """数组管理器，用于存储和计算技术指标"""

    def __init__(self, size: int = 100):
        """初始化"""
        self.count = 0
        self.size = size
        self.inited = False

        self.open_array = np.zeros(size)
        self.high_array = np.zeros(size)
        self.low_array = np.zeros(size)
        self.close_array = np.zeros(size)
        self.volume_array = np.zeros(size)

    @property
    def open(self) -> np.ndarray:
        """开盘价数组"""
        return self.open_array

    @property
    def high(self) -> np.ndarray:
        """最高价数组"""
        return self.high_array

    @property
    def low(self) -> np.ndarray:
        """最低价数组"""
        return self.low_array

    @property
    def close(self) -> np.ndarray:
        """收盘价数组"""
        return self.close_array

    @property
    def volume(self) -> np.ndarray:
        """成交量数组"""
        return self.volume_array

    def update_bar(self, bar: BarData):
        """更新K线数据"""
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]

        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume
