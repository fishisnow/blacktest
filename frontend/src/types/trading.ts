import React from 'react'

// 股票符号信息
export interface StockSymbol {
  code: string        // 股票代码，如 "000001.SH"
  name: string        // 股票名称，如 "上证指数"
  market: 'CN' | 'HK' | 'US'  // 市场类型
  type: 'stock' | 'index'     // 证券类型
  exchange?: string   // 交易所
}

// 回测参数
export interface BacktestParams {
  symbol: string               // 股票代码
  startDate: string           // 开始日期 YYYY-MM-DD
  endDate: string             // 结束日期 YYYY-MM-DD
  strategy: string            // 策略名称
  parameters: StrategyParams  // 策略参数
}

// 策略参数
export interface StrategyParams {
  fastMaPeriod: number        // 快速均线周期
  slowMaPeriod: number        // 慢速均线周期
  atrPeriod: number          // ATR周期
  atrMultiplier: number      // ATR倍数
  positionMode: 'full' | 'half' | 'quarter' | 'fixed'  // 仓位模式
  fixedSize: number          // 固定手数（仅在fixed模式下使用）
}

// 回测状态
export type BacktestStatus = 'idle' | 'running' | 'completed' | 'error'

// K线数据
export interface CandleData {
  timestamp: number          // 时间戳
  date: string              // 日期字符串
  open: number              // 开盘价
  high: number              // 最高价
  low: number               // 最低价
  close: number             // 收盘价
  volume: number            // 成交量
}

// 交易记录
export interface TradeRecord {
  id: string                // 交易ID
  timestamp: number         // 时间戳
  date: string             // 日期时间
  symbol: string           // 股票代码
  direction: 'LONG' | 'SHORT'  // 方向：做多/做空
  offset: 'OPEN' | 'CLOSE'     // 开平：开仓/平仓
  price: number            // 成交价格
  volume: number           // 成交数量
  pnl: number              // 盈亏
  commission: number       // 手续费
  slippage: number         // 滑点
}

// 每日统计数据
export interface DailyResult {
  date: string             // 日期
  totalPnl: number         // 累计盈亏
  netPnl: number           // 当日净盈亏
  returnRatio: number      // 累计收益率 (%)
  drawdown: number         // 回撤 (%)
  maxDrawdown: number      // 最大回撤 (%)
  winLossRatio: number     // 盈亏天数比
  trades: number           // 当日交易次数
}

// 回测统计指标
export interface BacktestMetrics {
  // 收益指标
  totalReturn: number          // 总收益率 (%)
  annualReturn: number         // 年化收益率 (%)
  totalPnl: number            // 总盈亏
  
  // 风险指标
  maxDrawdown: number         // 最大回撤 (%)
  maxDrawdownDuration: number // 最大回撤持续天数
  volatility: number          // 波动率 (%)
  sharpeRatio: number         // 夏普比率
  sortinoRatio: number        // 索提诺比率
  calmarRatio: number         // 卡玛比率
  
  // 交易指标
  totalTrades: number         // 总交易次数
  winningTrades: number       // 盈利交易次数
  losingTrades: number        // 亏损交易次数
  winRate: number            // 胜率 (%)
  profitFactor: number       // 盈利因子
  avgWin: number             // 平均盈利
  avgLoss: number            // 平均亏损
  maxWin: number             // 最大盈利
  maxLoss: number            // 最大亏损
  
  // 时间指标
  tradingDays: number        // 交易天数
  profitableDays: number     // 盈利天数
  losingDays: number         // 亏损天数
  winLossRatio: number       // 盈亏天数比
  
  // 资金指标
  initialCapital: number     // 初始资金
  finalCapital: number       // 最终资金
  maxCapital: number         // 最高资金
  minCapital: number         // 最低资金
}

// 完整回测结果
export interface BacktestResults {
  runId: string                    // 运行ID
  symbol: string                   // 股票代码
  strategy: string                 // 策略名称
  startDate: string               // 开始日期
  endDate: string                 // 结束日期
  createdAt: string               // 创建时间
  
  // 核心数据
  candleData: CandleData[]        // K线数据
  trades: TradeRecord[]           // 交易记录
  dailyResults: DailyResult[]     // 每日统计
  metrics: BacktestMetrics        // 回测指标
  
  // 策略参数
  parameters: StrategyParams      // 使用的策略参数
  
  // 执行信息
  executionTime: number           // 执行耗时（毫秒）
  dataPoints: number              // 数据点数量
  status: BacktestStatus          // 状态
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp: number
}

// 股票列表响应
export interface StockListResponse extends ApiResponse<StockSymbol[]> {}

// 回测响应
export interface BacktestResponse extends ApiResponse<BacktestResults> {}

// 历史结果响应
export interface HistoryResponse extends ApiResponse<BacktestResults[]> {}

// 股票价格数据响应
export interface PriceDataResponse extends ApiResponse<CandleData[]> {}

// 图表数据类型
export interface ChartSeries {
  name: string
  type: 'line' | 'candlestick' | 'bar' | 'scatter'
  data: any[]
  color?: string
  yAxisIndex?: number
}

// 图表配置
export interface ChartConfig {
  title?: string
  xAxis: {
    type: 'category' | 'value' | 'time'
    data?: any[]
  }
  yAxis: Array<{
    type: 'value'
    name?: string
    position?: 'left' | 'right'
    min?: number | 'dataMin'
    max?: number | 'dataMax'
  }>
  series: ChartSeries[]
  grid?: {
    top?: string | number
    bottom?: string | number
    left?: string | number
    right?: string | number
  }
  dataZoom?: Array<{
    type: 'inside' | 'slider'
    start?: number
    end?: number
    xAxisIndex?: number[]
    yAxisIndex?: number[]
  }>
  tooltip?: {
    trigger: 'axis' | 'item'
    formatter?: string | Function
  }
  legend?: {
    show: boolean
    data?: string[]
  }
}

// 表格列配置
export interface TableColumn {
  key: string
  title: string
  dataIndex: string
  width?: number
  align?: 'left' | 'center' | 'right'
  render?: (value: any, record: any, index: number) => React.ReactNode
  sorter?: boolean | Function
  fixed?: 'left' | 'right'
}

// 分页配置
export interface PaginationConfig {
  current: number
  pageSize: number
  total: number
  showSizeChanger?: boolean
  showQuickJumper?: boolean
  showTotal?: (total: number, range: [number, number]) => string
}

// 筛选器配置
export interface FilterConfig {
  market?: 'CN' | 'HK' | 'US' | 'ALL'
  type?: 'stock' | 'index' | 'ALL'
  dateRange?: [string, string]
  returnRange?: [number, number]
  drawdownRange?: [number, number]
}

// 消息类型
export interface Message {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  content: string
  timestamp: number
  duration?: number
}

// 应用状态类型
export interface AppState {
  // 用户界面状态
  currentPage: 'backtest' | 'history'
  sidebarCollapsed: boolean
  theme: 'dark' | 'light'
  
  // 数据状态
  stockList: StockSymbol[]
  selectedSymbol: StockSymbol | null
  backtestParams: BacktestParams
  backtestResults: BacktestResults | null
  backtestStatus: BacktestStatus
  historyResults: BacktestResults[]
  
  // 加载状态
  loading: {
    stockList: boolean
    backtest: boolean
    history: boolean
    chart: boolean
  }
  
  // 错误状态
  errors: {
    stockList: string | null
    backtest: string | null
    history: string | null
    chart: string | null
  }
  
  // 消息队列
  messages: Message[]
}

// 图表主题类型
export interface ChartTheme {
  backgroundColor: string
  textColor: string
  axisColor: string
  gridColor: string
  tooltipBackgroundColor: string
  candlestick: {
    upColor: string
    downColor: string
  }
  line: {
    colors: string[]
  }
} 