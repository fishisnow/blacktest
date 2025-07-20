import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { BacktestResults } from '../types/trading'
import { backtestService } from '../services/BacktestService'

const PageContainer = styled.div`
  padding: 24px;
  background: #0D1117;
  min-height: 100vh;
`

const PageTitle = styled.h1`
  margin: 0 0 24px 0;
  color: #F0F6FC;
  font-size: 24px;
  font-weight: 600;
`

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #8B949E;
  font-size: 16px;
`

const HistoryCard = styled.div`
  background: #161B22;
  border: 1px solid #30363D;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: border-color 0.2s ease;

  &:hover {
    border-color: #1890FF;
  }
`

const CardTitle = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #F0F6FC;
  margin-bottom: 8px;
`

const CardInfo = styled.div`
  font-size: 14px;
  color: #8B949E;
  margin-bottom: 4px;
`

const MetricValue = styled.span<{ positive?: boolean; negative?: boolean }>`
  color: ${props => 
    props.positive ? '#52C41A' :
    props.negative ? '#FF4D4F' :
    '#F0F6FC'
  };
  font-weight: 600;
`

export const HistoryPage: React.FC = () => {
  const [historyResults, setHistoryResults] = useState<BacktestResults[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true)
        const results = await backtestService.getBacktestHistory()
        setHistoryResults(results)
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取历史记录失败')
      } finally {
        setLoading(false)
      }
    }

    loadHistory()
  }, [])

  if (loading) {
    return (
      <PageContainer>
        <PageTitle>回测历史记录</PageTitle>
        <LoadingState>加载中...</LoadingState>
      </PageContainer>
    )
  }

  if (error) {
    return (
      <PageContainer>
        <PageTitle>回测历史记录</PageTitle>
        <div style={{ color: '#FF4D4F', textAlign: 'center', padding: '48px' }}>
          {error}
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageTitle>回测历史记录</PageTitle>
      
      {historyResults.length === 0 ? (
        <div style={{ color: '#8B949E', textAlign: 'center', padding: '48px' }}>
          暂无历史记录
        </div>
      ) : (
        historyResults.map((result) => (
          <HistoryCard key={result.runId}>
            <CardTitle>{result.symbol} - {result.strategy}</CardTitle>
            <CardInfo>时间范围: {result.startDate} ~ {result.endDate}</CardInfo>
            <CardInfo>创建时间: {new Date(result.createdAt).toLocaleString()}</CardInfo>
            <CardInfo>
              总收益率: <MetricValue 
                positive={result.metrics.totalReturn > 0}
                negative={result.metrics.totalReturn < 0}
              >
                {result.metrics.totalReturn.toFixed(2)}%
              </MetricValue>
              {' | '}
              最大回撤: <MetricValue negative>
                {Math.abs(result.metrics.maxDrawdown).toFixed(2)}%
              </MetricValue>
              {' | '}
              夏普比率: <MetricValue>
                {result.metrics.sharpeRatio.toFixed(2)}
              </MetricValue>
            </CardInfo>
          </HistoryCard>
        ))
      )}
    </PageContainer>
  )
} 