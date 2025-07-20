import React, { useState, useMemo } from 'react'
import styled from 'styled-components'
import { TradeRecord } from '../../types/trading'

// 样式组件
const TableContainer = styled.div`
  background: #161B22;
  border: 1px solid #30363D;
  border-radius: 6px;             // 从8px减少到6px
  overflow: hidden;
  margin-bottom: 8px;             // 从24px减少到8px
  max-height: 600px;              // 增加最大高度到600px，确保表格可见
  display: flex;
  flex-direction: column;
  min-height: 200px;              // 添加最小高度，确保表格至少显示
`

const TableHeader = styled.div`
  background: #21262D;
  padding: 10px 12px;             // 从16px减少到10px 12px
  border-bottom: 1px solid #30363D;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;                 // 防止头部被压缩
`

const TableTitle = styled.h3`
  margin: 0;
  color: #F0F6FC;
  font-size: 14px;                // 从16px减少到14px
  font-weight: 600;
`

const TableControls = styled.div`
  display: flex;
  gap: 8px;                       // 从12px减少到8px
  align-items: center;
`

const PageSizeSelect = styled.select`
  background: #0D1117;
  border: 1px solid #30363D;
  color: #F0F6FC;
  padding: 3px 6px;               // 从4px 8px减少到3px 6px
  border-radius: 4px;
  font-size: 11px;                // 从12px减少到11px
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;                // 添加整体字体大小
`

const TableHead = styled.thead`
  background: #21262D;
  position: sticky;               // 添加粘性定位
  top: 0;
  z-index: 1;
`

const TableBody = styled.tbody`
  overflow-y: auto;               // 添加滚动
  flex: 1;
`

const TableRow = styled.tr`
  border-bottom: 1px solid #30363D;
  
  &:hover {
    background: #0D1117;
  }
  
  &:last-child {
    border-bottom: none;
  }
`

const TableHeaderCell = styled.th`
  padding: 8px 12px;              // 从12px 16px减少到8px 12px
  text-align: left;
  color: #8B949E;
  font-weight: 500;
  font-size: 11px;                // 从12px减少到11px
  text-transform: uppercase;
  border-bottom: 1px solid #30363D;
`

const TableCell = styled.td`
  padding: 6px 12px;              // 从12px 16px减少到6px 12px
  color: #F0F6FC;
  font-size: 11px;                // 从13px减少到11px
  vertical-align: middle;
  white-space: nowrap;            // 防止文本换行
`

const DirectionBadge = styled.span<{ direction: string }>`
  padding: 2px 6px;               // 从4px 8px减少到2px 6px
  border-radius: 3px;             // 从4px减少到3px
  font-size: 10px;                // 从11px减少到10px
  font-weight: 600;
  text-transform: uppercase;
  background: ${props => props.direction === 'LONG' ? '#1B5E20' : '#B71C1C'};
  color: ${props => props.direction === 'LONG' ? '#4CAF50' : '#F44336'};
`

const OffsetBadge = styled.span<{ offset: string }>`
  padding: 2px 6px;               // 从4px 8px减少到2px 6px
  border-radius: 3px;             // 从4px减少到3px
  font-size: 10px;                // 从11px减少到10px
  font-weight: 600;
  text-transform: uppercase;
  background: ${props => props.offset === 'OPEN' ? '#1A237E' : '#E65100'};
  color: ${props => props.offset === 'OPEN' ? '#3F51B5' : '#FF9800'};
`

const PnlCell = styled(TableCell)<{ pnl: number }>`
  color: ${props => 
    props.pnl > 0 ? '#52C41A' :
    props.pnl < 0 ? '#FF4D4F' :
    '#F0F6FC'
  };
  font-weight: 600;
`

const PaginationContainer = styled.div`
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #30363D;
  background: #0D1117;
`

const PaginationInfo = styled.div`
  color: #8B949E;
  font-size: 12px;
`

const PaginationControls = styled.div`
  display: flex;
  gap: 8px;
`

const PaginationButton = styled.button<{ disabled?: boolean }>`
  padding: 6px 12px;
  background: ${props => props.disabled ? '#21262D' : '#0D1117'};
  border: 1px solid #30363D;
  color: ${props => props.disabled ? '#6E7681' : '#F0F6FC'};
  border-radius: 4px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-size: 12px;
  
  &:hover:not(:disabled) {
    background: #161B22;
  }
`

const EmptyState = styled.div`
  padding: 48px 24px;
  text-align: center;
  color: #8B949E;
`

const StatsContainer = styled.div`
  display: flex;
  gap: 24px;
  align-items: center;
  font-size: 12px;
  color: #8B949E;
`

const StatItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;
`

const StatLabel = styled.span`
  color: #6E7681;
`

const StatValue = styled.span<{ positive?: boolean; negative?: boolean }>`
  color: ${props => 
    props.positive ? '#52C41A' :
    props.negative ? '#FF4D4F' :
    '#F0F6FC'
  };
  font-weight: 600;
`

interface TradeTableProps {
  trades: TradeRecord[]
  loading?: boolean
}

export const TradeTable: React.FC<TradeTableProps> = ({ trades, loading = false }) => {
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 计算分页数据
  const { paginatedTrades, totalPages, startIndex, endIndex, stats } = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    const end = start + pageSize
    const paginated = trades.slice(start, end)
    const total = Math.ceil(trades.length / pageSize)
    
    // 计算统计数据
    const profitTrades = trades.filter(t => t.pnl > 0).length
    const lossTrades = trades.filter(t => t.pnl < 0).length
    const totalPnl = trades.reduce((sum, t) => sum + t.pnl, 0)
    const winRate = trades.length > 0 ? (profitTrades / trades.length) * 100 : 0
    
    return {
      paginatedTrades: paginated,
      totalPages: total,
      startIndex: start + 1,
      endIndex: Math.min(end, trades.length),
      stats: {
        profitTrades,
        lossTrades,
        totalPnl,
        winRate
      }
    }
  }, [trades, currentPage, pageSize])

  const formatDateTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const formatNumber = (num: number, decimals = 2) => {
    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })
  }

  if (loading) {
    return (
      <TableContainer>
        <TableHeader>
          <TableTitle>交易记录</TableTitle>
        </TableHeader>
        <EmptyState>
          <div>加载中...</div>
        </EmptyState>
      </TableContainer>
    )
  }

  if (trades.length === 0) {
    return (
      <TableContainer>
        <TableHeader>
          <TableTitle>交易记录</TableTitle>
        </TableHeader>
        <EmptyState>
          <div>暂无交易记录</div>
          <div style={{ marginTop: '8px', fontSize: '11px' }}>
            执行回测后将显示详细的交易记录
          </div>
        </EmptyState>
      </TableContainer>
    )
  }

  return (
    <TableContainer>
      <TableHeader>
        <TableTitle>交易记录</TableTitle>
        <TableControls>
          <StatsContainer>
            <StatItem>
              <StatLabel>盈利交易</StatLabel>
              <StatValue positive>{stats.profitTrades}</StatValue>
            </StatItem>
            <StatItem>
              <StatLabel>亏损交易</StatLabel>
              <StatValue negative>{stats.lossTrades}</StatValue>
            </StatItem>
            <StatItem>
              <StatLabel>胜率</StatLabel>
              <StatValue positive={stats.winRate > 50}>
                {stats.winRate.toFixed(1)}%
              </StatValue>
            </StatItem>
            <StatItem>
              <StatLabel>总盈亏</StatLabel>
              <StatValue 
                positive={stats.totalPnl > 0} 
                negative={stats.totalPnl < 0}
              >
                {formatNumber(stats.totalPnl)}
              </StatValue>
            </StatItem>
          </StatsContainer>
          <label style={{ color: '#8B949E', fontSize: '12px' }}>
            每页:
            <PageSizeSelect 
              value={pageSize} 
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setCurrentPage(1)
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </PageSizeSelect>
          </label>
        </TableControls>
      </TableHeader>
      
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>时间</TableHeaderCell>
            <TableHeaderCell>股票代码</TableHeaderCell>
            <TableHeaderCell>方向</TableHeaderCell>
            <TableHeaderCell>开平</TableHeaderCell>
            <TableHeaderCell>价格</TableHeaderCell>
            <TableHeaderCell>数量</TableHeaderCell>
            <TableHeaderCell>盈亏</TableHeaderCell>
            <TableHeaderCell>手续费</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {paginatedTrades.map((trade) => (
            <TableRow key={trade.id}>
              <TableCell>{formatDateTime(trade.date)}</TableCell>
              <TableCell>{trade.symbol}</TableCell>
              <TableCell>
                <DirectionBadge direction={trade.direction}>
                  {trade.direction === 'LONG' ? '做多' : '做空'}
                </DirectionBadge>
              </TableCell>
              <TableCell>
                <OffsetBadge offset={trade.offset}>
                  {trade.offset === 'OPEN' ? '开仓' : '平仓'}
                </OffsetBadge>
              </TableCell>
              <TableCell>{formatNumber(trade.price)}</TableCell>
              <TableCell>{trade.volume.toLocaleString()}</TableCell>
              <PnlCell pnl={trade.pnl}>
                {trade.pnl >= 0 ? '+' : ''}{formatNumber(trade.pnl)}
              </PnlCell>
              <TableCell>{formatNumber(trade.commission)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      {totalPages > 1 && (
        <PaginationContainer>
          <PaginationInfo>
            显示第 {startIndex}-{endIndex} 条，共 {trades.length} 条记录
          </PaginationInfo>
          <PaginationControls>
            <PaginationButton 
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(1)}
            >
              首页
            </PaginationButton>
            <PaginationButton 
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              上一页
            </PaginationButton>
            <span style={{ color: '#F0F6FC', fontSize: '12px', padding: '0 12px' }}>
              {currentPage} / {totalPages}
            </span>
            <PaginationButton 
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              下一页
            </PaginationButton>
            <PaginationButton 
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(totalPages)}
            >
              末页
            </PaginationButton>
          </PaginationControls>
        </PaginationContainer>
      )}
    </TableContainer>
  )
} 