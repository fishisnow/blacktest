# vnpy趋势跟踪策略回测系统

基于vnpy框架开发的量化交易回测系统，专门用于A股和港股指数的趋势跟踪策略回测。

## 功能特性

- 🚀 **多指数支持**: 支持上证50、沪深300、创业板指、上证指数、深证成指
- 📈 **趋势跟踪策略**: 基于移动平均线交叉和ATR止损的趋势跟踪策略
- 📊 **完整回测分析**: 包含账户资产曲线、买卖信号标记、详细统计指标
- 🎯 **可视化图表**: 支持matplotlib和plotly两种图表展示方式
- 💾 **多格式导出**: 支持PNG、HTML、Excel等多种格式的结果导出
- 🗃️ **本地数据缓存**: SQLite数据库缓存，提高数据获取效率

## 项目结构

```
blacktest/
├── main.py                          # 主程序入口
├── data_loader.py                   # 数据加载器（支持缓存）
├── result_analyzer.py               # 结果分析器
├── cache_manager.py                 # 缓存管理工具
├── example_tushare.py               # Tushare使用示例
├── requirements.txt                 # 项目依赖
├── market_data.db                   # SQLite数据缓存（自动生成）
├── strategies/                      # 策略文件夹
│   ├── __init__.py
│   └── trend_following_strategy.py  # 趋势跟踪策略
└── README.md                        # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 数据缓存系统

### 缓存机制

- **自动缓存**: 从tushare获取的数据会自动保存到本地SQLite数据库
- **优先读取**: 获取数据时优先从本地缓存读取，大幅提高加载速度
- **增量更新**: 智能检测缺失数据，只从远程获取需要的部分
- **数据来源标识**: 每条数据都标记来源（CACHE或TUSHARE）

### 缓存管理工具

使用 `cache_manager.py` 工具管理本地数据缓存：

```bash
# 显示缓存信息
python cache_manager.py info

# 清空指定指数的缓存
python cache_manager.py clear --symbol 000300

# 清空所有缓存
python cache_manager.py clear

# 导出数据到CSV
python cache_manager.py export 000300 2023-01-01 2023-12-31 output.csv

# 检查数据完整性
python cache_manager.py check

# 压缩数据库文件
python cache_manager.py vacuum

# 显示支持的指数代码
python cache_manager.py symbols

# 指定数据库文件路径
python cache_manager.py --db custom_data.db info
```

## 使用方法

### 1. 运行完整回测

```bash
python main.py
```

这将对所有支持的指数进行回测。

### 2. 测试数据加载器

```bash
python data_loader.py
```

### 3. 缓存使用示例

```bash
python example_tushare.py
```

### 4. 测试结果分析器

```bash
python result_analyzer.py
```

## 策略说明

### 趋势跟踪策略参数

- **fast_ma_length**: 快速移动平均线周期 (默认: 10)
- **slow_ma_length**: 慢速移动平均线周期 (默认: 30)
- **atr_length**: ATR计算周期 (默认: 14)
- **atr_multiplier**: ATR止损倍数 (默认: 2.0)
- **fixed_size**: 固定交易手数 (默认: 1)

### 交易逻辑

1. **开仓信号**:
   - 金叉 (快速MA上穿慢速MA): 开多仓
   - 死叉 (快速MA下穿慢速MA): 开空仓

2. **平仓信号**:
   - 反向交叉信号
   - ATR止损触发

## 数据源配置

### Tushare配置

1. **获取Token**: 
   - 注册 [Tushare](https://tushare.pro/) 账号
   - 获取API Token

2. **设置Token**:
   ```python
   # 方法1: 代码中设置
   loader = DataLoader(token="your_tushare_token")
   
   # 方法2: 环境变量
   export TUSHARE_TOKEN="your_tushare_token"
   ```

### 支持的指数

| 代码 | 名称 | 数据源 |
|------|------|--------|
| 000016 | 上证50 | Tushare |
| 000300 | 沪深300 | Tushare |
| 399006 | 创业板指 | Tushare |
| 000001 | 上证指数 | Tushare |
| 399001 | 深证成指 | Tushare |

## 回测结果

系统会生成以下输出：

1. **控制台输出**: 详细的回测统计信息
2. **PNG图表**: `backtest_results.png` - matplotlib静态图表
3. **HTML图表**: `backtest_results.html` - plotly交互式图表
4. **Excel报告**: `backtest_report.xlsx` - 详细数据报告

### 主要统计指标

- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- 盈利因子
- 胜率
- 交易次数

## 性能优化

### 缓存优势

- **首次获取**: 从tushare下载数据并缓存到本地
- **后续使用**: 直接从本地读取，速度提升10倍以上
- **增量更新**: 只获取缺失的日期数据，减少API调用
- **离线使用**: 有缓存后可在没有网络时使用历史数据

### 最佳实践

1. **定期更新**: 运行时会自动获取最新数据
2. **缓存管理**: 定期清理过期或无用的缓存数据
3. **备份数据**: 重要的缓存数据建议备份
4. **Token配置**: 正确配置tushare token以获得稳定的数据服务

## 自定义策略

要添加新的策略，请：

1. 在 `strategies/` 文件夹中创建新的策略文件
2. 继承 `CtaTemplate` 类
3. 实现必要的方法：`on_bar()`, `on_init()`, `on_start()`, `on_stop()`
4. 在 `main.py` 中导入并使用新策略

## 故障排除

### 常见问题

1. **tushare token错误**:
   ```
   解决方案: 检查token是否正确配置，是否有足够的权限
   ```

2. **数据获取失败**:
   ```
   解决方案: 检查网络连接，确认tushare服务状态
   ```

3. **缓存数据不一致**:
   ```bash
   # 检查数据完整性
   python cache_manager.py check
   
   # 清空有问题的缓存
   python cache_manager.py clear --symbol 000300
   ```

4. **数据库文件损坏**:
   ```bash
   # 压缩修复数据库
   python cache_manager.py vacuum
   ```

## 注意事项

1. **数据获取**: 需要有效的tushare token才能获取数据
2. **网络连接**: 首次获取数据需要稳定的网络连接
3. **缓存大小**: 长期使用可能积累大量缓存数据，注意定期清理
4. **图表显示**: 如果在服务器环境运行，可能需要配置显示后端

## 依赖说明

- **vnpy**: 量化交易框架
- **pandas**: 数据处理
- **numpy**: 数值计算
- **matplotlib**: 静态图表
- **plotly**: 交互式图表
- **talib**: 技术指标计算
- **tushare**: A股数据源

## 许可证

本项目仅供学习和研究使用。

## 支持

如果您遇到任何问题，请检查：

1. 所有依赖是否正确安装
2. Tushare token是否正确配置
3. 网络连接是否正常
4. 缓存数据是否完整

使用缓存管理工具进行诊断：
```bash
python cache_manager.py info
python cache_manager.py check
```

如果问题仍然存在，请查看控制台输出的错误信息进行调试。 