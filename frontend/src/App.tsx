import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { GlobalStyle, AppContainer, MainContent, ContentArea } from './styles/GlobalStyle'
import { TopNavigation } from './components/Navigation/TopNavigation'
import { ParameterPanel } from './components/Panels/ParameterPanel'
import { ChartArea } from './components/Charts/ChartArea'
import { MetricsPanel } from './components/Panels/MetricsPanel'
import { TradeTable } from './components/Tables/TradeTable'
import { HistoryPage } from './pages/HistoryPage'
import { BacktestService } from './services/BacktestService'
import { 
  BacktestParams, 
  BacktestResults, 
  StockSymbol,
  BacktestStatus 
} from './types/trading'

const App: React.FC = () => {
  // 应用状态管理
  const [currentPage, setCurrentPage] = useState<'backtest' | 'history'>('backtest')
  const [selectedSymbol, setSelectedSymbol] = useState<StockSymbol | null>(null)
  // 获取默认日期
  const getDefaultDates = () => {
    const end = new Date()
    const start = new Date()
    start.setFullYear(end.getFullYear() - 1) // 默认1年
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    }
  }

  const defaultDates = getDefaultDates()

  const [backtestParams, setBacktestParams] = useState<BacktestParams>({
    symbol: '',
    startDate: defaultDates.start,
    endDate: defaultDates.end,
    strategy: 'TrendFollowingStrategy',
    parameters: {
      fastMaPeriod: 10,
      slowMaPeriod: 30,
      atrPeriod: 14,
      atrMultiplier: 2.0,
      positionMode: 'full',
      fixedSize: 1
    }
  })
  
  const [backtestResults, setBacktestResults] = useState<BacktestResults | null>(null)
  const [backtestStatus, setBacktestStatus] = useState<BacktestStatus>('idle')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 回测服务实例
  const backtestService = useMemo(() => new BacktestService(), [])

  // 获取股票列表
  const [stockList, setStockList] = useState<StockSymbol[]>([])

  // 加载股票列表
  const loadStockList = useCallback(async () => {
    try {
      const stocks = await backtestService.getStockList()
      setStockList(stocks)
      if (stocks.length > 0 && !selectedSymbol) {
        setSelectedSymbol(stocks[0])
        setBacktestParams(prev => ({
          ...prev,
          symbol: stocks[0].code
        }))
      }
    } catch (err) {
      setError('加载股票列表失败')
      console.error('Failed to load stock list:', err)
    }
  }, [backtestService, selectedSymbol])

  useEffect(() => {
    loadStockList()
  }, [loadStockList])



  // 执行回测
  const handleRunBacktest = async () => {
    if (!selectedSymbol) {
      setError('请选择股票')
      return
    }

    // 最终参数验证
    const finalParams = {
      ...backtestParams,
      symbol: selectedSymbol.code,
      startDate: backtestParams.startDate || defaultDates.start,
      endDate: backtestParams.endDate || defaultDates.end
    }

    try {
      setLoading(true)
      setError(null)
      setBacktestStatus('running')
      
      const results = await backtestService.runBacktest(finalParams)
      
      setBacktestResults(results)
      setBacktestStatus('completed')
    } catch (err) {
      setError(err instanceof Error ? err.message : '回测执行失败')
      setBacktestStatus('error')
      console.error('Backtest failed:', err)
    } finally {
      setLoading(false)
    }
  }

  // 清除结果
  const handleClearResults = () => {
    setBacktestResults(null)
    setBacktestStatus('idle')
    setError(null)
  }

  // 参数变更处理
  const handleParameterChange = useCallback((newParams: Partial<BacktestParams>) => {
    setBacktestParams(prev => {
      const updated = { ...prev, ...newParams }
      
      // 确保日期参数不为空
      if (newParams.startDate === '' || (!updated.startDate && !newParams.startDate)) {
        updated.startDate = defaultDates.start
      }
      if (newParams.endDate === '' || (!updated.endDate && !newParams.endDate)) {
        updated.endDate = defaultDates.end
      }
      
      return updated
    })
  }, [defaultDates])

  // 股票选择处理
  const handleSymbolChange = (symbol: StockSymbol) => {
    setSelectedSymbol(symbol)
    setBacktestParams(prev => ({
      ...prev,
      symbol: symbol.code
    }))
  }

  return (
    <Router>
      <AppContainer>
        <GlobalStyle />
        
        {/* 顶部导航栏 */}
        <TopNavigation 
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          selectedSymbol={selectedSymbol}
          backtestStatus={backtestStatus}
        />

        {/* 主要内容区 */}
        <MainContent>
          <Routes>
            {/* 回测页面 */}
            <Route path="/" element={
              <>
                {/* 左侧参数设置面板 */}
                <ParameterPanel
                  stockList={stockList}
                  selectedSymbol={selectedSymbol}
                  backtestParams={backtestParams}
                  loading={loading}
                  onSymbolChange={handleSymbolChange}
                  onParameterChange={handleParameterChange}
                  onRunBacktest={handleRunBacktest}
                  onClearResults={handleClearResults}
                />

                {/* 右侧主要内容区 */}
                <ContentArea>
                  {/* 图表区域 */}
                  <ChartArea 
                    selectedSymbol={selectedSymbol}
                    backtestParams={backtestParams}
                    backtestResults={backtestResults}
                    loading={loading}
                    error={error}
                  />

                  {/* 底部区域：指标和交易明细 */}
                  {backtestResults && (
                    <>
                      {/* 回测指标 */}
                      <MetricsPanel 
                        metrics={backtestResults?.metrics || null}
                      />

                      {/* 交易明细 */}
                      <TradeTable 
                        trades={backtestResults.trades}
                        loading={loading}
                      />
                    </>
                  )}

                  {/* 错误显示 */}
                  {error && !loading && (
                    <div style={{
                      padding: '20px',
                      textAlign: 'center',
                      color: '#FF4444',
                      background: 'rgba(255, 68, 68, 0.1)',
                      borderRadius: '8px',
                      border: '1px solid rgba(255, 68, 68, 0.3)'
                    }}>
                      {error}
                    </div>
                  )}

                  {/* 空状态显示 */}
                  {!backtestResults && !loading && !error && (
                    <div style={{
                      flex: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                      gap: '16px',
                      color: '#8B949E',
                      fontSize: '16px'
                    }}>
                      <div>📈</div>
                      <div>选择股票和参数，开始回测分析</div>
                    </div>
                  )}
                </ContentArea>
              </>
            } />

            {/* 历史记录页面 */}
            <Route path="/history" element={
              <ContentArea>
                <HistoryPage />
              </ContentArea>
            } />
          </Routes>
        </MainContent>
      </AppContainer>
    </Router>
  )
}

export default App 