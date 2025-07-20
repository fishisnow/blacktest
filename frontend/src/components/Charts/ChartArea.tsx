import React, { useState } from 'react'
import styled from 'styled-components'
import { futuTheme } from '../../styles/theme'
import { Card } from '../../styles/GlobalStyle'
import { KLineChart } from './KLineChart'
import { PerformanceChart } from './PerformanceChart'
import { StockSymbol, BacktestParams, BacktestResults } from '../../types/trading'

// 图表区域容器
const ChartContainer = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 8px;                       // 调整为8px，更好的视觉间距
  min-height: 0;
  height: 100%;                   // 确保占满可用高度
  overflow: hidden;               // 防止图表区域内容溢出
`

// 图表头部
const ChartHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
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

// 图表切换按钮组
const ChartTabs = styled.div`
  display: flex;
  gap: 8px;
`

const TabButton = styled.button<{ active?: boolean }>`
  padding: 6px 12px;
  background: ${({ active }) => active ? futuTheme.colors.futuBlue : futuTheme.colors.backgroundTertiary};
  border: 1px solid ${({ active }) => active ? futuTheme.colors.futuBlue : futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  color: ${({ active }) => active ? futuTheme.colors.textPrimary : futuTheme.colors.textSecondary};
  font-size: ${futuTheme.typography.fontSize.sm};
  font-weight: ${({ active }) => active ? futuTheme.typography.fontWeight.medium : futuTheme.typography.fontWeight.normal};
  cursor: pointer;
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:hover {
    background: ${({ active }) => active ? futuTheme.colors.futuBlue : futuTheme.colors.backgroundSecondary};
    border-color: ${futuTheme.colors.futuBlue};
    color: ${futuTheme.colors.textPrimary};
  }
`

// 图表内容区域
const ChartContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
`

// 主图表区域 (K线图)
const MainChartArea = styled(Card)`
  flex: 2.5;                      // 调整为2.5，比之前的3更平衡
  min-height: 400px;              // 恢复为400px
  padding: 10px;                  // 调整为10px，平衡空间利用
  position: relative;
`

// 副图表区域 (收益曲线)
const SubChartArea = styled(Card)`
  flex: 1;                        // 保持flex: 1
  min-height: 280px;              // 调整为280px，给收益曲线更多空间
  padding: 10px;                  // 调整为10px，保持一致
  margin-top: 8px;                // 调整为8px，适当间距
  position: relative;
`

// 加载状态
const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: ${futuTheme.colors.textSecondary};
  font-size: ${futuTheme.typography.fontSize.md};
  flex-direction: column;
  gap: 16px;

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

// 错误状态
const ErrorContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: ${futuTheme.colors.futuRed};
  font-size: ${futuTheme.typography.fontSize.md};
  flex-direction: column;
  gap: 16px;
  text-align: center;

  .icon {
    font-size: 48px;
    opacity: 0.7;
  }
`

// 空状态
const EmptyContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: ${futuTheme.colors.textTertiary};
  font-size: ${futuTheme.typography.fontSize.md};
  flex-direction: column;
  gap: 16px;
  text-align: center;

  .icon {
    font-size: 48px;
    opacity: 0.7;
  }
`

// 图表类型定义
type ChartType = 'kline' | 'performance'

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
  const [chartType, setChartType] = useState<ChartType>('kline')

  // 图表标题获取
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
        
        <MainChartArea>
          <LoadingContainer>
            <div className="spinner"></div>
            <div>正在加载图表数据...</div>
          </LoadingContainer>
        </MainChartArea>
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
        
        <MainChartArea>
          <ErrorContainer>
            <div className="icon">❌</div>
            <div>{error}</div>
            <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
              请检查网络连接或刷新页面重试
            </div>
          </ErrorContainer>
        </MainChartArea>
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
        
        <MainChartArea>
          <EmptyContainer>
            <div className="icon">📈</div>
            <div>请选择股票开始分析</div>
            <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
              选择股票和设置参数后，点击开始回测查看结果
            </div>
          </EmptyContainer>
        </MainChartArea>
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
        
        <ChartTabs>
          <TabButton 
            active={chartType === 'kline'}
            onClick={() => setChartType('kline')}
          >
            📈 K线图
          </TabButton>
          <TabButton 
            active={chartType === 'performance'}
            onClick={() => setChartType('performance')}
          >
            📊 收益曲线
          </TabButton>
        </ChartTabs>
      </ChartHeader>

      {/* 图表内容 */}
      <ChartContent>
        {/* K线图单独显示 */}
        {chartType === 'kline' && (
          <MainChartArea>
            <KLineChart
              symbol={selectedSymbol}
              dateRange={[backtestParams.startDate, backtestParams.endDate]}
              backtestResults={backtestResults}
            />
          </MainChartArea>
        )}

        {/* 收益曲线单独显示 */}
        {chartType === 'performance' && backtestResults && (
          <MainChartArea>
            <PerformanceChart
              dailyResults={backtestResults.dailyResults || []}
              symbol={selectedSymbol?.code}
              startDate={backtestParams.startDate}
              endDate={backtestParams.endDate}
            />
          </MainChartArea>
        )}



        {/* 只有K线图，没有回测结果时的提示 */}
        {chartType === 'performance' && !backtestResults && (
          <MainChartArea>
            <EmptyContainer>
              <div className="icon">📊</div>
              <div>暂无回测结果</div>
              <div style={{ fontSize: futuTheme.typography.fontSize.sm, opacity: 0.7 }}>
                请先运行回测以查看收益曲线
              </div>
            </EmptyContainer>
          </MainChartArea>
        )}
      </ChartContent>
    </ChartContainer>
  )
} 