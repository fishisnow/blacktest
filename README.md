# vnpy趋势跟踪策略回测系统

基于vnpy框架的趋势跟踪策略回测系统，支持多种指数和股票的历史数据回测。

## 新功能 🎉

### 多数据源支持
- **Tushare**: 支持A股指数和股票数据
- **Futu OpenAPI**: 支持美股、港股、A股数据
- **智能故障转移**: 主要数据源失败时自动切换到备用数据源
- **统一接口**: 无论使用哪个数据源，接口保持一致
- **缓存优化**: 支持多数据源的本地缓存，提升性能

## 特性

- 📊 **多数据源**: 支持 Tushare 和 Futu OpenAPI
- 🔄 **智能切换**: 数据源故障时自动切换
- 💾 **本地缓存**: SQLite缓存，支持离线使用
- 📈 **丰富图表**: matplotlib + plotly 双重图表支持
- 🎯 **策略回测**: 内置趋势跟踪策略
- 📋 **详细报告**: 生成Excel和HTML报告
- ⚡ **高性能**: 增量数据获取，缓存优化

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据源

复制配置文件模板：
```bash
cp env_example.txt .env
```

编辑 `.env` 文件，配置您的数据源：

```bash
# Tushare 配置
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_PRIORITY=2

# Futu 配置  
FUTU_ENABLED=true
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
FUTU_PRIORITY=1
```

### 3. 测试数据源

```bash
# 测试多数据源配置
python example_multi_datasource.py

# 测试数据加载器
python data_loader.py

# 测试配置管理
python config.py
```

### 4. 运行回测

```bash
python main.py
```

## 数据源配置详解

### 支持的数据源

| 数据源 | 支持市场 | 优势 | 配置要求 |
|--------|----------|------|----------|
| **Tushare** | A股指数、股票 | 数据全面、稳定 | 需要API Token |
| **Futu OpenAPI** | 美股、港股、A股 | 实时性好、国际市场 | 需要Futu OpenD |

### 数据源优先级

系统支持配置数据源优先级，数字越小优先级越高：

```bash
# 优先使用 Futu，Tushare 作为备用
FUTU_PRIORITY=1
TUSHARE_PRIORITY=2

# 优先使用 Tushare，Futu 作为备用  
TUSHARE_PRIORITY=1
FUTU_PRIORITY=2
```

### Tushare 配置

1. **获取Token**: 
   - 注册 [Tushare](https://tushare.pro/) 账号
   - 获取API Token

2. **配置环境变量**:
   ```bash
   TUSHARE_TOKEN=your_token_here
   TUSHARE_PRIORITY=2
   TUSHARE_TIMEOUT=30
   TUSHARE_RETRY_COUNT=3
   ```

### Futu OpenAPI 配置

1. **安装 Futu OpenD**:
   - 下载并安装 [Futu OpenD](https://www.futunn.com/download/openAPI)
   - 启动 OpenD 程序

2. **配置环境变量**:
   ```bash
   FUTU_ENABLED=true
   FUTU_HOST=127.0.0.1
   FUTU_PORT=11111
   FUTU_PRIORITY=1
   FUTU_SESSION=ALL
   ```

## 支持的股票代码

### Tushare 支持的代码

| 代码 | 名称 | 类型 |
|------|------|------|
| 000016 | 上证50 | 指数 |
| 000300 | 沪深300 | 指数 |
| 399006 | 创业板指 | 指数 |
| 000001 | 上证指数 | 指数 |
| 399001 | 深证成指 | 指数 |
| 688981 | 中芯国际 | 股票 |

### Futu 支持的代码

| 代码 | 名称 | 市场 |
|------|------|------|
| AAPL | 苹果 | 美股 |
| MSFT | 微软 | 美股 |
| GOOGL | 谷歌 | 美股 |
| TSLA | 特斯拉 | 美股 |
| 00700 | 腾讯控股 | 港股 |
| 09988 | 阿里巴巴 | 港股 |

## 使用方法

### 1. 多数据源演示

```bash
python example_multi_datasource.py
```

### 2. 运行完整回测

```bash
python main.py
```

### 3. 测试单个数据源

```bash
# 测试 Futu 数据源
python futu_data_provider.py

# 测试 Tushare 数据源  
python example_tushare.py
```

### 4. 缓存管理

```bash
# 查看缓存信息
python cache_manager.py info

# 清空特定数据源缓存
python cache_manager.py clear --data-source futu

# 清空特定股票缓存
python cache_manager.py clear --symbol AAPL
```

## 缓存管理

### 缓存优势

- **多数据源缓存**: 分别缓存不同数据源的数据
- **智能合并**: 自动合并多个数据源的数据
- **增量更新**: 只获取缺失的日期数据
- **离线使用**: 有缓存后可在没有网络时使用

### 缓存操作

```python
from data_loader import DataLoader

loader = DataLoader()

# 清空特定股票的特定数据源缓存
loader.clear_cache('AAPL', 'futu')

# 清空特定股票的所有缓存
loader.clear_cache('AAPL')

# 清空特定数据源的所有缓存
loader.clear_cache(data_source='tushare')

# 查看缓存信息
cache_info = loader.get_cache_info()
```

## 故障转移机制

系统具有智能故障转移功能：

1. **主要数据源**: 优先使用配置的主要数据源
2. **自动切换**: 主要数据源失败时自动尝试备用数据源
3. **无缝体验**: 用户无需关心具体使用了哪个数据源
4. **错误处理**: 详细的错误信息和重试机制

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

## 故障排除

### 常见问题

1. **数据源连接失败**:
   ```bash
   # 检查配置
   python config.py
   
   # 测试连接
   python example_multi_datasource.py
   ```

2. **Futu 连接失败**:
   - 确保 Futu OpenD 已启动
   - 检查端口配置是否正确
   - 确认防火墙设置

3. **Tushare token错误**:
   - 检查token是否正确配置
   - 确认token是否有足够的权限

4. **缓存数据问题**:
   ```bash
   # 检查缓存完整性
   python cache_manager.py check
   
   # 清空问题缓存
   python cache_manager.py clear --symbol AAPL
   ```

## 依赖说明

- **vnpy**: 量化交易框架
- **pandas**: 数据处理
- **numpy**: 数值计算
- **matplotlib**: 静态图表
- **plotly**: 交互式图表
- **talib**: 技术指标计算
- **tushare**: A股数据源
- **futu-api**: Futu OpenAPI客户端

## 最佳实践

1. **数据源配置**: 根据主要交易市场选择合适的主要数据源
2. **缓存管理**: 定期清理过期缓存数据
3. **网络稳定**: 确保网络连接稳定，特别是首次获取数据时
4. **备份重要数据**: 对重要的缓存数据进行备份

## 许可证

本项目仅供学习和研究使用。

## 支持

如果您遇到任何问题，请：

1. 检查配置文件是否正确
2. 运行测试脚本诊断问题
3. 查看控制台输出的详细错误信息
4. 使用缓存管理工具检查数据完整性

```bash
# 完整的诊断流程
python config.py                    # 检查配置
python example_multi_datasource.py  # 测试数据源
python cache_manager.py info        # 检查缓存
``` 