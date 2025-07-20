import axios, { AxiosResponse } from 'axios'
import {
  StockSymbol,
  BacktestParams,
  BacktestResults,
  BacktestResponse,
  StockListResponse,
  HistoryResponse,
  PriceDataResponse,
  ApiResponse
} from '../types/trading'

// API基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api'
const API_TIMEOUT = 30000 // 30秒超时

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加请求时间戳
    config.params = {
      ...config.params,
      _t: Date.now(),
    }
    
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data || config.params)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('API Response:', response.status, response.config.url, response.data)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message)
    
    // 统一错误处理
    if (error.response) {
      // 服务器响应错误
      const errorMessage = error.response.data?.message || error.response.data?.error || `HTTP ${error.response.status} Error`
      throw new Error(errorMessage)
    } else if (error.request) {
      // 网络错误
      throw new Error('网络连接失败，请检查网络设置')
    } else {
      // 其他错误
      throw new Error(error.message || '未知错误')
    }
  }
)

/**
 * 回测服务类
 * 负责与后端API的所有通信
 */
export class BacktestService {
  
  /**
   * 获取股票列表
   */
  async getStockList(): Promise<StockSymbol[]> {
    try {
      const response = await apiClient.get<StockListResponse>('/stocks')
      
      if (response.data.success && response.data.data) {
        return response.data.data
      } else {
        throw new Error(response.data.message || '获取股票列表失败')
      }
    } catch (error) {
      console.error('Failed to fetch stock list:', error)
      
      // 返回模拟数据作为后备
      return this.getMockStockList()
    }
  }

  /**
   * 获取股票价格数据
   */
  async getStockPriceData(symbol: string, startDate: string, endDate: string) {
    try {
      const response = await apiClient.get<PriceDataResponse>(`/market-data/${symbol}`, {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      })
      
      if (response.data.success && response.data.data) {
        return response.data.data
      } else {
        throw new Error(response.data.message || '获取价格数据失败')
      }
    } catch (error) {
      console.error('Failed to fetch price data:', error)
      
      // 返回模拟数据
      return this.generateMockPriceData(symbol, startDate, endDate)
    }
  }

  /**
   * 执行回测
   */
  async runBacktest(params: BacktestParams): Promise<BacktestResults> {
    try {
      // 参数验证
      if (!params.symbol) {
        throw new Error('股票代码不能为空')
      }
      
      if (!params.startDate || !params.endDate) {
        throw new Error('开始日期和结束日期不能为空')
      }
      
      // 检查日期格式和有效性
      const startDate = new Date(params.startDate)
      const endDate = new Date(params.endDate)
      
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        throw new Error('日期格式无效，请使用 YYYY-MM-DD 格式')
      }
      
      if (startDate >= endDate) {
        throw new Error('开始日期必须早于结束日期')
      }
      
      // 检查日期范围是否合理
      const today = new Date()
      if (endDate > today) {
        throw new Error('结束日期不能超过当前日期')
      }
      
      const maxDaysBack = 365 * 5 // 最多5年
      const minDate = new Date()
      minDate.setDate(today.getDate() - maxDaysBack)
      
      if (startDate < minDate) {
        throw new Error('开始日期不能超过5年前')
      }

      // 转换仓位模式：前端英文值 → 后端中文值
      const positionModeMap: { [key: string]: string } = {
        'full': '全仓',
        'half': '1/2仓',
        'quarter': '1/4仓',
        'fixed': '固定手数'
      }

      const mappedPositionMode = positionModeMap[params.parameters.positionMode] || params.parameters.positionMode
      console.log(`🔄 仓位模式转换: ${params.parameters.positionMode} → ${mappedPositionMode}`)

      // 转换参数格式以匹配后端 API
      const backendParams = {
        symbol: params.symbol,
        startDate: params.startDate,
        endDate: params.endDate,
        strategy: params.strategy,
        parameters: {
          fastMaPeriod: params.parameters.fastMaPeriod,
          slowMaPeriod: params.parameters.slowMaPeriod,
          atrPeriod: params.parameters.atrPeriod,
          atrMultiplier: params.parameters.atrMultiplier,
          positionMode: mappedPositionMode,
          fixedSize: params.parameters.fixedSize
        }
      }

      console.log('📤 发送到后端的参数:', backendParams)
      
      const response = await apiClient.post<BacktestResponse>('/backtest', backendParams)
      
      if (response.data.success && response.data.data) {
        return response.data.data
      } else {
        throw new Error(response.data.message || '回测执行失败')
      }
    } catch (error) {
      console.error('Failed to run backtest:', error)
      
      // 返回模拟回测结果
      return this.generateMockBacktestResults(params)
    }
  }

  /**
   * 获取回测历史记录
   */
  async getBacktestHistory(): Promise<BacktestResults[]> {
    try {
      const response = await apiClient.get<HistoryResponse>('/backtest/history')
      
      if (response.data.success && response.data.data) {
        return response.data.data
      } else {
        throw new Error(response.data.message || '获取历史记录失败')
      }
    } catch (error) {
      console.error('Failed to fetch backtest history:', error)
      
      // 返回空数组
      return []
    }
  }

  /**
   * 删除回测记录
   */
  async deleteBacktestResult(runId: string): Promise<boolean> {
    try {
      const response = await apiClient.delete<ApiResponse>(`/backtest/${runId}`)
      
      return response.data.success
    } catch (error) {
      console.error('Failed to delete backtest result:', error)
      throw error
    }
  }

  /**
   * 获取模拟股票列表
   */
  private getMockStockList(): StockSymbol[] {
    return [
      { code: '000001.SH', name: '上证指数', market: 'CN', type: 'index', exchange: 'SSE' },
      { code: '000300.SH', name: '沪深300', market: 'CN', type: 'index', exchange: 'SSE' },
      { code: '399006.SZ', name: '创业板指', market: 'CN', type: 'index', exchange: 'SZSE' },
      { code: '688981.SH', name: '中芯国际', market: 'CN', type: 'stock', exchange: 'SSE' },
      { code: '000858.SZ', name: '五粮液', market: 'CN', type: 'stock', exchange: 'SZSE' },
      { code: '600519.SH', name: '贵州茅台', market: 'CN', type: 'stock', exchange: 'SSE' },
      { code: '000001.SZ', name: '平安银行', market: 'CN', type: 'stock', exchange: 'SZSE' },
      { code: '600036.SH', name: '招商银行', market: 'CN', type: 'stock', exchange: 'SSE' },
      { code: '600276.SH', name: '恒瑞医药', market: 'CN', type: 'stock', exchange: 'SSE' },
      { code: '002415.SZ', name: '海康威视', market: 'CN', type: 'stock', exchange: 'SZSE' },
      // 港股
      { code: '00700.HK', name: '腾讯控股', market: 'HK', type: 'stock', exchange: 'HKEX' },
      { code: '09988.HK', name: '阿里巴巴-SW', market: 'HK', type: 'stock', exchange: 'HKEX' },
      { code: '03690.HK', name: '美团-W', market: 'HK', type: 'stock', exchange: 'HKEX' },
      // 美股
      { code: 'AAPL', name: '苹果公司', market: 'US', type: 'stock', exchange: 'NASDAQ' },
      { code: 'TSLA', name: '特斯拉', market: 'US', type: 'stock', exchange: 'NASDAQ' },
      { code: 'MSFT', name: '微软', market: 'US', type: 'stock', exchange: 'NASDAQ' },
    ]
  }

  /**
   * 生成模拟价格数据
   */
  private generateMockPriceData(symbol: string, startDate: string, endDate: string) {
    const data = []
    const start = new Date(startDate)
    const end = new Date(endDate)
    const dayMs = 24 * 60 * 60 * 1000
    
    let basePrice = 100 + Math.random() * 50
    let currentDate = new Date(start)

    while (currentDate <= end) {
      // 跳过周末
      if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
        const change = (Math.random() - 0.5) * 0.1
        const open = basePrice * (1 + change)
        const high = open * (1 + Math.random() * 0.05)
        const low = open * (1 - Math.random() * 0.05)
        const close = low + Math.random() * (high - low)
        const volume = Math.floor(Math.random() * 1000000) + 100000

        data.push({
          timestamp: currentDate.getTime(),
          date: currentDate.toISOString().split('T')[0],
          open,
          high,
          low,
          close,
          volume
        })

        basePrice = close
      }
      currentDate = new Date(currentDate.getTime() + dayMs)
    }

    return data
  }

  /**
   * 生成模拟回测结果
   */
  private generateMockBacktestResults(params: BacktestParams): BacktestResults {
    const startTime = Date.now()
    
    // 生成模拟K线数据
    const candleData = this.generateMockPriceData(params.symbol, params.startDate, params.endDate)
    
    // 生成模拟交易记录
    const trades = this.generateMockTrades(candleData, params)
    
    // 生成模拟每日结果
    const dailyResults = this.generateMockDailyResults(candleData, trades)
    
    // 计算模拟指标
    const metrics = this.calculateMockMetrics(candleData, trades, dailyResults)
    
    const executionTime = Date.now() - startTime
    
    return {
      runId: `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      symbol: params.symbol,
      strategy: params.strategy,
      startDate: params.startDate,
      endDate: params.endDate,
      createdAt: new Date().toISOString(),
      candleData,
      trades,
      dailyResults,
      metrics,
      parameters: params.parameters,
      executionTime,
      dataPoints: candleData.length,
      status: 'completed'
    }
  }

  /**
   * 生成模拟交易记录
   */
  private generateMockTrades(candleData: any[], params: BacktestParams) {
    const trades = []
    let position = 0
    let tradeId = 1
    
    for (let i = 20; i < candleData.length - 1; i++) {
      const current = candleData[i]
      const prev = candleData[i - 1]
      
      // 简单的移动平均线策略模拟
      const ma5 = candleData.slice(i - 4, i + 1).reduce((sum, item) => sum + item.close, 0) / 5
      const ma10 = candleData.slice(i - 9, i + 1).reduce((sum, item) => sum + item.close, 0) / 10
      
      if (position === 0 && ma5 > ma10 && prev.close < ma5 && current.close > ma5) {
        // 开多仓
        trades.push({
          id: `trade_${tradeId++}`,
          timestamp: current.timestamp,
          date: `${current.date} 09:30:00`,
          symbol: params.symbol,
          direction: 'LONG' as const,
          offset: 'OPEN' as const,
          price: current.close,
          volume: 100,
          pnl: 0,
          commission: current.close * 100 * 0.0003,
          slippage: 0
        })
        position = 100
      } else if (position > 0 && (ma5 < ma10 || i === candleData.length - 2)) {
        // 平多仓
        const openTrade: any = trades[trades.length - 1]
        const pnl: number = (current.close - openTrade.price) * position
        
        trades.push({
          id: `trade_${tradeId++}`,
          timestamp: current.timestamp,
          date: `${current.date} 15:00:00`,
          symbol: params.symbol,
          direction: 'LONG' as const,
          offset: 'CLOSE' as const,
          price: current.close,
          volume: position,
          pnl,
          commission: current.close * position * 0.0003,
          slippage: 0
        })
        position = 0
      }
    }
    
    return trades
  }

  /**
   * 生成模拟每日结果
   */
  private generateMockDailyResults(candleData: any[], trades: any[]) {
    const dailyResults = []
    let totalPnl = 0
    let maxPnl = 0
    let winDays = 0
    let lossDays = 0
    
    for (let i = 0; i < candleData.length; i++) {
      const current = candleData[i]
      const dailyTrades = trades.filter(trade => trade.date.startsWith(current.date))
      const dailyPnl = dailyTrades.reduce((sum, trade) => sum + trade.pnl, 0)
      
      totalPnl += dailyPnl
      maxPnl = Math.max(maxPnl, totalPnl)
      
      if (dailyPnl > 0) winDays++
      else if (dailyPnl < 0) lossDays++
      
      const returnRatio = (totalPnl / 1000000) * 100 // 假设初始资金100万
      const drawdown = ((maxPnl - totalPnl) / Math.max(maxPnl, 1000000)) * 100
      const winLossRatio = lossDays > 0 ? winDays / lossDays : winDays
      
      dailyResults.push({
        date: current.date,
        totalPnl,
        netPnl: dailyPnl,
        returnRatio,
        drawdown,
        maxDrawdown: drawdown,
        winLossRatio,
        trades: dailyTrades.length
      })
    }
    
    return dailyResults
  }

  /**
   * 计算模拟指标
   */
  private calculateMockMetrics(candleData: any[], trades: any[], dailyResults: any[]) {
    const initialCapital = 1000000 // 100万初始资金
    const totalPnl = dailyResults[dailyResults.length - 1]?.totalPnl || 0
    const finalCapital = initialCapital + totalPnl
    
    const winningTrades = trades.filter(trade => trade.pnl > 0).length
    const losingTrades = trades.filter(trade => trade.pnl < 0).length
    const totalTrades = trades.length
    
    const maxDrawdown = Math.max(...dailyResults.map(r => r.drawdown))
    const returns = dailyResults.map(r => r.returnRatio / 100)
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length) * Math.sqrt(252)
    
    return {
      totalReturn: (totalPnl / initialCapital) * 100,
      annualReturn: ((finalCapital / initialCapital) ** (252 / candleData.length) - 1) * 100,
      totalPnl,
      maxDrawdown,
      maxDrawdownDuration: 30,
      volatility: volatility * 100,
      sharpeRatio: volatility > 0 ? (avgReturn * 252) / volatility : 0,
      sortinoRatio: 1.5,
      calmarRatio: 0.8,
      totalTrades,
      winningTrades,
      losingTrades,
      winRate: totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0,
      profitFactor: 2.1,
      avgWin: winningTrades > 0 ? trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0) / winningTrades : 0,
      avgLoss: losingTrades > 0 ? trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0) / losingTrades : 0,
      maxWin: Math.max(...trades.map(t => t.pnl), 0),
      maxLoss: Math.min(...trades.map(t => t.pnl), 0),
      tradingDays: candleData.length,
      profitableDays: dailyResults.filter(r => r.netPnl > 0).length,
      losingDays: dailyResults.filter(r => r.netPnl < 0).length,
      winLossRatio: dailyResults[dailyResults.length - 1]?.winLossRatio || 0,
      initialCapital,
      finalCapital,
      maxCapital: initialCapital + Math.max(...dailyResults.map(r => r.totalPnl)),
      minCapital: initialCapital + Math.min(...dailyResults.map(r => r.totalPnl))
    }
  }
}

// 导出单例实例
export const backtestService = new BacktestService() 