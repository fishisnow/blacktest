# 富途风格回测系统前端

基于 React + TypeScript + ECharts 构建的专业股票回测前端系统，采用富途终端的暗黑风格设计。

## ✨ 功能特性

- 🎯 **股票选择**: 支持A股、港股、美股多市场股票搜索和选择
- ⚙️ **策略参数**: 可视化参数设置，支持移动平均线、ATR等策略参数调整
- 📈 **K线图表**: 基于ECharts的专业K线图，支持缩放、十字准线、交易标记
- 📊 **收益分析**: 实时收益曲线图，对比策略表现与标的走势
- 🏆 **指标展示**: 丰富的回测指标，包括收益率、夏普比率、最大回撤等
- 📋 **交易明细**: 详细的交易记录表格，支持分页和筛选
- 📚 **历史记录**: 回测历史记录管理和查看
- 🌙 **暗黑主题**: 富途终端风格的专业暗黑主题
- 📱 **响应式**: 适配不同分辨率显示器，包括高分辨率屏幕

## 🛠 技术栈

- **框架**: React 18 + TypeScript
- **样式**: Styled-Components + CSS-in-JS
- **图表**: ECharts 5 + echarts-for-react
- **路由**: React Router DOM
- **UI组件**: Ant Design 5
- **HTTP客户端**: Axios
- **日期处理**: Day.js

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd frontend

# 安装依赖
npm install
# 或
yarn install
```

### 开发环境运行

```bash
# 启动开发服务器
npm start
# 或
yarn start
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

### 生产环境构建

```bash
# 构建生产版本
npm run build
# 或
yarn build
```

### 代码检查

```bash
# 运行ESLint检查
npm run lint
# 或
yarn lint
```

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # React组件
│   │   ├── Charts/        # 图表组件
│   │   │   ├── ChartArea.tsx       # 图表区域容器
│   │   │   ├── KLineChart.tsx      # K线图组件
│   │   │   └── PerformanceChart.tsx # 收益曲线图组件
│   │   ├── Navigation/    # 导航组件
│   │   │   └── TopNavigation.tsx   # 顶部导航栏
│   │   ├── Panels/        # 面板组件
│   │   │   ├── ParameterPanel.tsx  # 参数设置面板
│   │   │   └── MetricsPanel.tsx    # 指标展示面板
│   │   └── Tables/        # 表格组件
│   │       └── TradeTable.tsx      # 交易明细表格
│   ├── pages/             # 页面组件
│   │   └── HistoryPage.tsx         # 历史记录页面
│   ├── services/          # API服务
│   │   └── BacktestService.ts      # 回测服务
│   ├── styles/            # 样式相关
│   │   ├── theme.ts               # 主题配置
│   │   └── GlobalStyle.ts         # 全局样式
│   ├── types/             # TypeScript类型定义
│   │   └── trading.ts             # 交易相关类型
│   ├── utils/             # 工具函数
│   ├── App.tsx            # 主应用组件
│   └── index.tsx          # 应用入口
├── package.json           # 项目配置
└── tsconfig.json         # TypeScript配置
```

## 🎨 主题定制

### 富途风格主题

系统采用富途终端的专业暗黑主题，主要颜色配置：

```typescript
export const futuTheme = {
  colors: {
    // 主背景色
    background: '#0D1117',
    backgroundSecondary: '#161B22',
    
    // 富途特色金融颜色
    futuGreen: '#00C853',    // 上涨/盈利
    futuRed: '#FF4444',      // 下跌/亏损
    futuBlue: '#1890FF',     // 主要操作
    futuOrange: '#FF9500',   // 警告/中性
    
    // 文字颜色
    textPrimary: '#F0F6FC',
    textSecondary: '#8B949E',
    // ...更多配置
  }
}
```

### 自定义主题

1. 修改 `src/styles/theme.ts` 中的颜色配置
2. 更新 `src/styles/GlobalStyle.ts` 中的全局样式
3. 调整 ECharts 主题配置

## 📊 图表功能

### K线图特性

- ✅ 标准K线图显示（开、高、低、收）
- ✅ 移动平均线（MA5、MA10、MA20）
- ✅ 成交量柱状图
- ✅ 交易信号标记
- ✅ 缩放和平移操作
- ✅ 十字准线和数据提示
- ✅ 自适应时间轴
- ✅ 高分辨率显示优化

### 收益曲线图特性

- ✅ 策略收益率曲线
- ✅ 标的价格走势对比
- ✅ 每日盈亏柱状图
- ✅ 回撤曲线显示
- ✅ 多种时间范围支持
- ✅ 悬停数据详情

## 🔧 API接口

### 后端服务配置

修改 `src/services/BacktestService.ts` 中的API基础URL：

```typescript
const API_BASE_URL = 'http://localhost:8000/api'  // 后端服务地址
```

### 主要接口

- `GET /stocks` - 获取股票列表
- `POST /backtest` - 执行回测
- `GET /backtest/history` - 获取历史记录
- `GET /market-data/{symbol}` - 获取股票行情数据

## 🎯 使用指南

### 基本操作流程

1. **选择股票**: 在左侧面板搜索并选择目标股票
2. **设置参数**: 调整回测时间范围和策略参数
3. **执行回测**: 点击"开始回测"按钮运行分析
4. **查看结果**: 在图表区域查看K线图和收益曲线
5. **分析指标**: 查看底部的详细回测指标
6. **查看交易**: 浏览交易明细表格
7. **历史记录**: 在历史页面管理回测记录

### 快捷键

- `Ctrl + R` - 刷新页面
- `鼠标滚轮` - 图表缩放
- `鼠标拖拽` - 图表平移
- `Esc` - 重置图表视图

## 🔍 问题排查

### 常见问题

1. **图表不显示**
   - 检查浏览器控制台是否有JavaScript错误
   - 确认ECharts库正确加载
   - 检查数据格式是否正确

2. **API请求失败**
   - 确认后端服务正常运行
   - 检查API地址配置
   - 查看网络请求状态

3. **样式显示异常**
   - 清除浏览器缓存
   - 检查CSS样式是否正确加载
   - 确认主题配置无误

### 调试模式

在开发环境中启用调试模式：

```typescript
// 在src/App.tsx中添加
const DEBUG_MODE = process.env.NODE_ENV === 'development'
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 🔗 相关资源

- [React 官方文档](https://reactjs.org/)
- [ECharts 官方文档](https://echarts.apache.org/)
- [TypeScript 手册](https://www.typescriptlang.org/)
- [Styled Components 文档](https://styled-components.com/)
- [富途证券](https://www.futunn.com/)

---

<div align="center">
  <strong>专业 • 可靠 • 高效</strong>
  <br>
  <em>让量化投资更简单</em>
</div> 