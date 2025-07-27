import React, { useState } from 'react'
import styled from 'styled-components'
import { futuTheme } from '../../styles/theme'
import { Card } from '../../styles/GlobalStyle'
import { KLineChart } from './KLineChart'
import { ReturnChart, PnLChart, DrawdownChart } from './PerformanceChart'
import { StockSymbol, BacktestParams, BacktestResults } from '../../types/trading'

// 图表区域容器
const ChartContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 16px;
  min-height: 100%;
`

// 图表头部
const ChartHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  margin-bottom: 12px;
`

const ChartTitle = styled.h3`
  font-size: ${futuTheme.typography.fontSize.lg};
  font-weight: ${futuTheme.typography.fontWeight.semibold};
  color: ${futuTheme.colors.textPrimary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;

  .icon {
    color: ${futuTheme.colors.futuBlue};
  }
`

// 图表内容区域
const ChartsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
`

// 主图表区域 (K线图)
const MainChartArea = styled(Card)`
  width: 100%;
  height: 600px;
  padding: 16px;
  margin-bottom: 16px;
  background: ${futuTheme.colors.cardBackground};
`

// 副图表区域 (收益曲线)
const SubChartArea = styled(Card)`
  width: 100%;
  height: 400px;
  padding: 16px;
  margin-bottom: 16px;
`

// 加载状态容器
const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  height: 300px;
  color: ${futuTheme.colors.textSecondary};

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid ${futuTheme.colors.border};
    border-top: 3px solid ${futuTheme.colors.futuBlue};
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`

// 错误状态容器
const ErrorContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  height: 300px;
  color: ${futuTheme.colors.futuRed};
  text-align: center;

  .icon {
    font-size: 48px;
    opacity: 0.7;
  }
`

// 空状态容器
const EmptyContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  height: 300px;
  color: ${futuTheme.colors.textTertiary};
  
  .icon {
    font-size: 48px;
    opacity: 0.7;
  }
`

// 组件属性接口
interface ChartAreaProps {
  selectedSymbol: StockSymbol | null
  backtestParams: BacktestParams
  backtestResults: BacktestResults | null
  loading: boolean
  error: string | null
}

export const ChartArea: React.FC<ChartAreaProps> = ({
  selectedSymbol,
  backtestParams,
  backtestResults,
  loading,
  error
}) => {
  // 添加缩放状态
  const [zoomRange, setZoomRange] = useState({ start: 70, end: 100 })

  // 处理缩放变化
  const handleZoomChange = (start: number, end: number) => {
    setZoomRange({ start, end })
  }

  // 获取图表标题
  const getChartTitle = () => {
    if (selectedSymbol) {
      return `${selectedSymbol.code} - ${selectedSymbol.name}`
    }
    return '股票走势分析'
  }

  // 渲染加载状态
  if (loading) {
    return (
      <ChartContainer>
        <ChartHeader>
          <ChartTitle>
            <span className="icon">📊</span>
            {getChartTitle()}
          </ChartTitle>
        </ChartHeader>
        <ChartsWrapper>
          <MainChartArea>
            <LoadingContainer>
              <div className="spinner"></div>
              <div>正在加载图表数据...</div>
            </LoadingContainer>
          </MainChartArea>
        </ChartsWrapper>
      </ChartContainer>
    )
  }

  // 渲染错误状态
  if (error) {
    return (
      <ChartContainer>
        <ChartHeader>
          <ChartTitle>
            <span className="icon">📊</span>
            {getChartTitle()}
          </ChartTitle>
        </ChartHeader>
        <ChartsWrapper>
          <MainChartArea>
            <ErrorContainer>
              <div className="icon">❌</div>
              <div>{error}</div>
              <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
                请检查网络连接或刷新页面重试
              </div>
            </ErrorContainer>
          </MainChartArea>
        </ChartsWrapper>
      </ChartContainer>
    )
  }

  // 渲染空状态
  if (!selectedSymbol && !backtestResults) {
    return (
      <ChartContainer>
        <ChartHeader>
          <ChartTitle>
            <span className="icon">📊</span>
            图表分析
          </ChartTitle>
        </ChartHeader>
        
        <ChartsWrapper>
          <MainChartArea>
            <EmptyContainer>
              <div className="icon">📈</div>
              <div>请选择股票开始分析</div>
              <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
                选择股票和设置参数后，点击开始回测查看结果
              </div>
            </EmptyContainer>
          </MainChartArea>
        </ChartsWrapper>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer>
      {/* 图表头部 */}
      <ChartHeader>
        <ChartTitle>
          <span className="icon">📊</span>
          {getChartTitle()}
        </ChartTitle>
      </ChartHeader>

      {/* 图表内容 */}
      <ChartsWrapper>
        {/* K线图 */}
        <MainChartArea>
          <KLineChart
            symbol={selectedSymbol}
            dateRange={[backtestParams.startDate, backtestParams.endDate]}
            backtestResults={backtestResults}
            height={550}
            onZoomChange={handleZoomChange}
            zoomStart={zoomRange.start}
            zoomEnd={zoomRange.end}
          />
        </MainChartArea>

        {/* 收益率图表 */}
        {backtestResults && (
          <ReturnChart
            dailyResults={backtestResults.dailyResults}
            symbol={selectedSymbol?.code}
            loading={loading}
            onZoomChange={handleZoomChange}
            zoomStart={zoomRange.start}
            zoomEnd={zoomRange.end}
            benchmarkData={backtestResults.candleData?.map(item => ({
              date: item.date,
              benchmarkReturn: ((item.close / backtestResults.candleData[0].close) - 1) * 100
            }))}
          />
        )}

        {/* 每日盈亏图表 */}
        {backtestResults && (
          <PnLChart
            dailyResults={backtestResults.dailyResults}
            loading={loading}
            onZoomChange={handleZoomChange}
            zoomStart={zoomRange.start}
            zoomEnd={zoomRange.end}
          />
        )}

        {/* 最大回撤图表 */}
        {backtestResults && (
          <DrawdownChart
            dailyResults={backtestResults.dailyResults}
            loading={loading}
            onZoomChange={handleZoomChange}
            zoomStart={zoomRange.start}
            zoomEnd={zoomRange.end}
          />
        )}

        {/* 空状态显示 */}
        {!backtestResults && (
          <Card>
            <EmptyContainer>
              <div className="icon">📊</div>
              <div>暂无回测结果</div>
              <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
                请先运行回测以查看分析结果
              </div>
            </EmptyContainer>
          </Card>
        )}
      </ChartsWrapper>
    </ChartContainer>
  )
} 