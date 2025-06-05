# 回测统计指标计算逻辑详解

## 概述

本文档详细阐述了回测系统中各个统计指标的计算逻辑。所有指标计算都由 `StatisticsCalculator` 类统一实现，确保在数据库存储和界面显示时使用相同的计算方法。

## 核心常量

```python
INITIAL_CAPITAL = 1_000_000      # 初始资金（100万）
TRADING_DAYS_PER_YEAR = 252      # 每年交易日数
PROFIT_THRESHOLD = 0.01          # 盈利天数判断阈值
LOSS_THRESHOLD = -0.01           # 亏损天数判断阈值
```

## 数据输入

统计计算需要两类主要数据：
- **每日结果数据** (`daily_results`): 包含每日的净盈亏、资产价值等信息
- **交易记录数据** (`trades`): 包含每笔交易的详细信息（开仓/平仓、价格、数量、盈亏等）

## 统计指标详解

### 1. 总收益率 (Total Return)

**定义**: 策略期间的总体收益表现，以百分比形式表示。

**计算公式**:
```
总收益率 = (累积总盈亏 / 初始资金) × 100%
```

**计算逻辑**:
1. 遍历每日结果，累加每日净盈亏 (`net_pnl`)
2. 最终累积盈亏除以初始资金，转换为百分比

**代码实现**:
```python
cumulative_pnl += net_pnl
return_ratio = (cumulative_pnl / initial_capital) * 100
```

### 2. 年化收益率 (Annual Return)

**定义**: 将总收益率换算为年化表现，便于与其他投资产品比较。

**计算公式**:
```
年化收益率 = 平均日收益率 × 每年交易日数 × 100%
```

**计算逻辑**:
1. 计算每日收益率：`(当日总盈亏 - 前日总盈亏) / 初始资金`
2. 计算平均日收益率
3. 乘以252个交易日年化

**代码实现**:
```python
daily_return = (curr_pnl - prev_pnl) / initial_capital
avg_daily_return = sum(daily_returns) / len(daily_returns)
annual_return = avg_daily_return * TRADING_DAYS_PER_YEAR * 100
```

### 3. 最大回撤 (Max Drawdown)

**定义**: 从最高点到最低点的最大损失幅度，衡量策略的风险控制能力。

**计算公式**:
```
回撤 = (当前资产 - 历史最高资产) / 历史最高资产
最大回撤 = min(所有回撤) × 100%
```

**计算逻辑**:
1. 计算每日的累积资产：`初始资金 + 累积盈亏`
2. 维护历史最高资产记录
3. 计算每日回撤幅度
4. 取最大回撤的绝对值

**代码实现**:
```python
cumulative_assets = [initial_capital + d['total_pnl'] for d in processed_results]
# 维护历史最高值
for asset in cumulative_assets:
    if asset > current_max:
        current_max = asset
    cumulative_max.append(current_max)
# 计算回撤
drawdowns = [(asset - max_val) / max_val for asset, max_val in zip(cumulative_assets, cumulative_max)]
max_drawdown = abs(min(drawdowns) * 100)
```

### 4. 夏普比率 (Sharpe Ratio)

**定义**: 风险调整后的收益指标，衡量每承担一单位风险所获得的超额回报。

**计算公式**:
```
夏普比率 = (年化收益率 - 无风险利率) / 年化波动率
注：本系统假设无风险利率为0
```

**计算逻辑**:
1. 计算日收益率序列
2. 计算收益率的标准差（波动率）
3. 年化处理后计算夏普比率

**代码实现**:
```python
# 计算波动率
variance = sum([(r - avg_daily_return) ** 2 for r in daily_returns]) / len(daily_returns)
std_daily_return = variance ** 0.5
annual_volatility = std_daily_return * (TRADING_DAYS_PER_YEAR ** 0.5) * 100

# 计算夏普比率
sharpe_ratio = (avg_daily_return * TRADING_DAYS_PER_YEAR) / (std_daily_return * (TRADING_DAYS_PER_YEAR ** 0.5))
```

### 5. 年化波动率 (Annual Volatility)

**定义**: 策略收益的年化标准差，衡量收益的稳定性。

**计算公式**:
```
年化波动率 = 日收益率标准差 × √252 × 100%
```

**计算逻辑**:
1. 计算日收益率的标准差
2. 乘以√252进行年化处理

### 6. 总交易次数 (Total Trades)

**定义**: 策略期间的总交易笔数，包括开仓和平仓操作。

**计算逻辑**:
1. 统计所有交易记录的数量
2. 不区分开仓/平仓，不区分盈亏状态

**代码实现**:
```python
all_trades = []
for trade in trades:
    # 统计所有交易（开仓+平仓）
    all_trades.append(pnl)
total_trades = len(all_trades)
```

### 7. 胜率 (Win Rate)

**定义**: 盈利交易占总平仓交易数量的比例。

**计算公式**:
```
胜率 = 盈利平仓交易数 / 总平仓交易数 × 100%
```

**计算逻辑**:
1. 只统计平仓交易（`offset` 包含 'CLOSE' 或 '平仓'）
2. 统计其中盈利的交易数量
3. 计算比例

**代码实现**:
```python
# 只统计平仓交易的盈亏
is_close = 'CLOSE' in str(offset).upper() or '平仓' in str(offset)
if is_close:
    profitable_trades.append(pnl)

# 计算胜率
winning_trades = len([p for p in profitable_trades if p > 0])
win_rate = (winning_trades / len(profitable_trades) * 100)
```

### 8. 盈利因子 (Profit Factor)

**定义**: 总盈利与总亏损的比值，衡量策略的盈利能力。

**计算公式**:
```
盈利因子 = 总盈利金额 / 总亏损金额的绝对值
```

**计算逻辑**:
1. 基于平仓交易计算
2. 分别统计盈利和亏损金额
3. 计算比值（亏损为0时，盈利因子为0）

**代码实现**:
```python
total_profit = sum([p for p in profitable_trades if p > 0])
total_loss = abs(sum([p for p in profitable_trades if p < 0]))
profit_factor = total_profit / total_loss if total_loss > 0 else 0
```

### 9. 最大单笔盈利/亏损 (Max Profit/Loss)

**定义**: 单笔交易的最大盈利金额和最大亏损金额。

**计算逻辑**:
1. 基于平仓交易的盈亏记录
2. 分别取最大值和最小值

**代码实现**:
```python
max_profit = max(profitable_trades) if profitable_trades else 0
max_loss = min(profitable_trades) if profitable_trades else 0
```

### 10. 总盈亏 (Total PnL)

**定义**: 策略期间的总盈亏金额（绝对数值）。

**计算逻辑**:
1. 等同于累积总盈亏
2. 以货币单位表示的绝对收益

### 11. 盈利天数/亏损天数比 (Win/Loss Days Ratio)

**定义**: 盈利天数与亏损天数的比值，反映策略的稳定性。

**计算公式**:
```
盈利天数/亏损天数比 = 盈利天数 / 亏损天数
```

**计算逻辑**:
1. 遍历每日净盈亏
2. 使用阈值判断盈利/亏损天数（避免浮点数精度问题）
3. 计算比值（亏损天数为0时，返回盈利天数）

**代码实现**:
```python
if net_pnl > PROFIT_THRESHOLD:  # 0.01
    win_count += 1
elif net_pnl < LOSS_THRESHOLD:  # -0.01
    loss_count += 1

if loss_count > 0:
    win_loss_ratio = win_count / loss_count
else:
    win_loss_ratio = float(win_count) if win_count > 0 else 0.0
```

## 特殊处理机制

### 1. 数据格式兼容性
- 支持字典格式和对象格式的输入数据
- 统一的数据访问接口

### 2. 边界条件处理
- 空数据返回默认统计值
- 除零错误的防护机制
- 浮点数精度问题的阈值处理

### 3. 错误容错
- 数据类型自动转换
- 缺失字段的默认值处理
- 异常情况的降级策略

## 指标解读建议

### 收益类指标
- **总收益率**: 反映策略的绝对表现
- **年化收益率**: 便于与其他投资品种比较
- **总盈亏**: 直观的金额收益

### 风险类指标
- **最大回撤**: 越小越好，反映风险控制能力
- **年化波动率**: 反映收益的稳定性
- **夏普比率**: 综合考虑收益和风险，越高越好

### 交易质量指标
- **胜率**: 盈利交易的比例，但不是唯一标准
- **盈利因子**: >1 表示盈利大于亏损
- **总交易次数**: 反映策略的活跃程度

### 稳定性指标
- **盈利天数/亏损天数比**: 反映策略的持续性
- **最大单笔盈利/亏损**: 反映策略的极端表现

## 注意事项

1. **数据质量**: 统计指标的准确性完全依赖于输入数据的质量
2. **时间周期**: 不同时间周期的回测结果可比性有限
3. **市场环境**: 统计指标反映的是历史表现，不代表未来结果
4. **策略参数**: 相同策略不同参数会产生显著不同的统计结果

## 使用示例

```python
from src.utils.statistics_calculator import StatisticsCalculator
from src.constants import INITIAL_CAPITAL

# 计算统计指标
stats = StatisticsCalculator.calculate_backtest_statistics(
    daily_results=daily_results,
    trades=trades,
    initial_capital=INITIAL_CAPITAL
)

# 获取关键指标
print(f"总收益率: {stats['total_return']:.2f}%")
print(f"最大回撤: {stats['max_drawdown']:.2f}%")
print(f"夏普比率: {stats['sharpe_ratio']:.2f}")
print(f"胜率: {stats['win_rate']:.1f}%")
```

---

*本文档基于系统版本 2025.06 编写，如有更新请及时同步。* 