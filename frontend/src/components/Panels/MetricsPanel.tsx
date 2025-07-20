import React from 'react'
import styled from 'styled-components'
import { BacktestMetrics } from '../../types/trading'

// 样式组件
const MetricsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); // 从200px减少到180px
  gap: 8px;                       // 从16px减少到8px
  margin-bottom: 12px;            // 调整为12px，给表格更多间距
  padding: 8px 0;                 // 添加轻微的垂直内边距
  max-height: 120px;              // 限制指标面板最大高度
  overflow: hidden;               // 防止指标面板过高
  
  /* 响应式优化 */
  @media (max-width: 1600px) {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 6px;
  }
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 4px;
  }
`

const MetricCard = styled.div`
  background: #161B22;
  border: 1px solid #30363D;
  border-radius: 6px;             // 从8px减少到6px
  padding: 10px;                  // 从16px减少到10px
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);  // 减少阴影
  transition: box-shadow 0.2s ease;
  min-height: 60px;               // 设置最小高度，保持一致性

  &:hover {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);  // 减少hover阴影
  }
`

const MetricLabel = styled.div`
  font-size: 11px;                // 从12px减少到11px
  color: #8B949E;
  margin-bottom: 2px;             // 从4px减少到2px
  font-weight: 500;
  line-height: 1.2;
`

const MetricValue = styled.div<{ positive?: boolean; negative?: boolean }>`
  font-size: 16px;                // 从20px减少到16px
  font-weight: 600;
  color: ${props => 
    props.positive ? '#52C41A' :
    props.negative ? '#FF4D4F' :
    '#F0F6FC'
  };
  line-height: 1.2;
`

const MetricDescription = styled.div`
  font-size: 10px;                // 从11px减少到10px
  color: #6E7681;
  margin-top: 2px;                // 从4px减少到2px
  line-height: 1.2;               // 从1.3减少到1.2
  display: -webkit-box;
  -webkit-line-clamp: 2;          // 限制为最多2行
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
`

interface MetricsPanelProps {
  metrics: BacktestMetrics | null
  loading?: boolean
}

interface MetricInfo {
  label: string
  value: string | number
  description: string
  positive?: boolean
  negative?: boolean
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics, loading = false }) => {
  if (loading) {
    return (
      <MetricsContainer>
        {Array.from({ length: 12 }).map((_, index) => (
          <MetricCard key={index}>
            <MetricLabel>加载中...</MetricLabel>
            <MetricValue>--</MetricValue>
          </MetricCard>
        ))}
      </MetricsContainer>
    )
  }

  if (!metrics) {
    return (
      <MetricsContainer>
        <MetricCard>
          <MetricLabel>状态</MetricLabel>
          <MetricValue>暂无数据</MetricValue>
          <MetricDescription>请先执行回测以查看指标</MetricDescription>
        </MetricCard>
      </MetricsContainer>
    )
  }

  const formatPercentage = (value: number) => `${value.toFixed(2)}%`
  const formatNumber = (value: number) => value.toLocaleString()
  const formatDecimal = (value: number) => value.toFixed(2)

  const metricsData: MetricInfo[] = [
    {
      label: '总收益率',
      value: formatPercentage(metrics.totalReturn),
      description: '策略期间的总体收益表现',
      positive: metrics.totalReturn > 0,
      negative: metrics.totalReturn < 0
    },
    {
      label: '年化收益率',
      value: formatPercentage(metrics.annualReturn),
      description: '将策略收益换算为年化表现',
      positive: metrics.annualReturn > 0,
      negative: metrics.annualReturn < 0
    },
    {
      label: '最大回撤',
      value: formatPercentage(Math.abs(metrics.maxDrawdown)),
      description: '从最高点到最低点的最大损失',
      negative: true
    },
    {
      label: '夏普比率',
      value: formatDecimal(metrics.sharpeRatio),
      description: '风险调整后的收益指标，越高越好',
      positive: metrics.sharpeRatio > 1,
      negative: metrics.sharpeRatio < 0
    },
    {
      label: '波动率',
      value: formatPercentage(metrics.volatility),
      description: '策略收益的年化标准差'
    },
    {
      label: '胜率',
      value: formatPercentage(metrics.winRate),
      description: '盈利交易占总交易数量的比例',
      positive: metrics.winRate > 50
    },
    {
      label: '盈利因子',
      value: formatDecimal(metrics.profitFactor),
      description: '总盈利与总亏损的比值',
      positive: metrics.profitFactor > 1,
      negative: metrics.profitFactor < 1
    },
    {
      label: '总交易次数',
      value: formatNumber(metrics.totalTrades),
      description: '策略期间的总交易笔数'
    },
    {
      label: '平均盈利',
      value: formatNumber(metrics.avgWin),
      description: '每笔盈利交易的平均金额',
      positive: metrics.avgWin > 0
    },
    {
      label: '平均亏损',
      value: formatNumber(Math.abs(metrics.avgLoss)),
      description: '每笔亏损交易的平均金额',
      negative: true
    },
    {
      label: '最大单笔盈利',
      value: formatNumber(metrics.maxWin),
      description: '单笔交易的最大盈利金额',
      positive: metrics.maxWin > 0
    },
    {
      label: '最大单笔亏损',
      value: formatNumber(Math.abs(metrics.maxLoss)),
      description: '单笔交易的最大亏损金额',
      negative: true
    }
  ]

  return (
    <MetricsContainer>
      {metricsData.map((metric, index) => (
        <MetricCard key={index}>
          <MetricLabel>{metric.label}</MetricLabel>
          <MetricValue 
            positive={metric.positive} 
            negative={metric.negative}
          >
            {metric.value}
          </MetricValue>
          <MetricDescription>{metric.description}</MetricDescription>
        </MetricCard>
      ))}
    </MetricsContainer>
  )
} 