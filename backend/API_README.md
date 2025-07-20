# 回测系统 FastAPI 服务器

本文档介绍如何启动和使用回测系统的 FastAPI 服务器。

## 🚀 启动服务器

### 方法 1: 使用启动脚本（推荐）

```bash
# 在项目根目录下执行
cd blacktest
python backend/start_api.py
```

### 方法 2: 直接使用 uvicorn

```bash
# 在项目根目录下执行
cd blacktest
uvicorn backend.src.api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 方法 3: 使用 conda 环境

```bash
# 激活 conda 环境
conda activate blacktest

# 启动服务器
python backend/start_api.py
```

## 📋 API 接口文档

服务器启动后，可以通过以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🛠️ API 接口说明

### 1. 获取股票列表
```
GET /api/stocks
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "code": "000001.SH",
      "name": "上证指数",
      "market": "CN",
      "type": "index",
      "exchange": "SSE"
    }
  ],
  "message": "成功获取股票代码",
  "timestamp": 1703123456789
}
```

### 2. 获取股票价格数据
```
GET /api/market-data/{symbol}?start_date=2023-01-01&end_date=2023-12-31
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": 1672531200000,
      "date": "2023-01-01",
      "open": 100.0,
      "high": 105.0,
      "low": 98.0,
      "close": 103.0,
      "volume": 1000000
    }
  ],
  "message": "成功获取价格数据",
  "timestamp": 1703123456789
}
```

### 3. 执行回测
```
POST /api/backtest
```

**请求体示例：**
```json
{
  "symbol": "000001.SH",
  "startDate": "2023-01-01",
  "endDate": "2023-12-31",
  "strategy": "TrendFollowingStrategy",
  "parameters": {
    "fastMaPeriod": 10,
    "slowMaPeriod": 30,
    "atrPeriod": 14,
    "atrMultiplier": 2.0,
    "positionMode": "fixed",
    "fixedSize": 1
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "runId": "20231201_143022",
    "symbol": "000001.SH",
    "strategy": "TrendFollowingStrategy",
    "startDate": "2023-01-01",
    "endDate": "2023-12-31",
    "candleData": [...],
    "trades": [...],
    "dailyResults": [...],
    "metrics": {
      "totalReturn": 15.32,
      "annualReturn": 15.32,
      "maxDrawdown": -8.45,
      "sharpeRatio": 1.25,
      "winRate": 62.5
    },
    "status": "completed"
  },
  "message": "回测执行成功",
  "timestamp": 1703123456789
}
```

### 4. 获取历史回测记录
```
GET /api/backtest/history
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "runId": "20231201_143022",
      "symbol": "000001.SH",
      "strategy": "TrendFollowingStrategy",
      "startDate": "2023-01-01",
      "endDate": "2023-12-31",
      "createdAt": "2023-12-01T14:30:22",
      "metrics": {...},
      "status": "completed"
    }
  ],
  "message": "成功获取历史记录",
  "timestamp": 1703123456789
}
```

### 5. 删除回测记录
```
DELETE /api/backtest/{runId}
```

**响应示例：**
```json
{
  "success": true,
  "message": "成功删除回测记录",
  "timestamp": 1703123456789
}
```

## 🔧 配置说明

### 环境变量
服务器支持通过环境变量进行配置：

- `REACT_APP_API_URL`: API 基础地址（默认: http://localhost:8000/api）
- `TUSHARE_TOKEN`: Tushare API Token
- `FUTU_HOST`: Futu OpenAPI 主机地址
- `FUTU_PORT`: Futu OpenAPI 端口

### 数据源配置
在 `.env` 文件中配置数据源：

```env
# Tushare 配置
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_ENABLED=true
TUSHARE_PRIORITY=2

# Futu 配置
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
FUTU_ENABLED=false
FUTU_PRIORITY=1
```

## 🐛 常见问题

### 1. 导入错误
如果遇到模块导入错误，请确保：
- 已激活正确的 conda 环境
- 已安装所有依赖包：`pip install -r requirements.txt`
- Python 路径设置正确

### 2. 数据获取失败
如果数据获取失败，请检查：
- 网络连接是否正常
- 数据源配置是否正确
- API Token 是否有效

### 3. 端口被占用
如果 8000 端口被占用，可以修改启动脚本中的端口号：
```python
uvicorn.run(
    "backend.src.api_server:app",
    host="0.0.0.0",
    port=8001,  # 修改为其他端口
    reload=True
)
```

## 📞 技术支持

如有问题，请检查：
1. 服务器日志输出
2. API 文档页面是否可以访问
3. 前端控制台是否有错误信息 