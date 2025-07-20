import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { futuTheme } from '../../styles/theme'
import { Button } from '../../styles/GlobalStyle'
import { StockSymbol, BacktestStatus } from '../../types/trading'

// 导航栏容器
const NavContainer = styled.nav`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: ${futuTheme.layout.headerHeight};
  background-color: ${futuTheme.colors.backgroundSecondary};
  border-bottom: 1px solid ${futuTheme.colors.border};
  padding: 0 ${futuTheme.layout.padding};
  box-shadow: ${futuTheme.shadows.small};
  z-index: ${futuTheme.zIndex.fixed};
  position: relative;
`

// 左侧品牌区域
const BrandSection = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;
`

// 品牌标志
const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: ${futuTheme.typography.fontSize.lg};
  font-weight: ${futuTheme.typography.fontWeight.bold};
  color: ${futuTheme.colors.textPrimary};
  
  .icon {
    font-size: 24px;
    color: ${futuTheme.colors.futuBlue};
  }
`

// 导航菜单
const NavMenu = styled.div`
  display: flex;
  gap: 8px;
`

const NavItem = styled.button<{ active?: boolean }>`
  padding: 8px 16px;
  background: ${({ active }) => active ? futuTheme.colors.backgroundTertiary : 'transparent'};
  border: 1px solid ${({ active }) => active ? futuTheme.colors.border : 'transparent'};
  border-radius: ${futuTheme.layout.borderRadius};
  color: ${({ active }) => active ? futuTheme.colors.textPrimary : futuTheme.colors.textSecondary};
  font-size: ${futuTheme.typography.fontSize.sm};
  font-weight: ${({ active }) => active ? futuTheme.typography.fontWeight.medium : futuTheme.typography.fontWeight.normal};
  cursor: pointer;
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};
  white-space: nowrap;

  &:hover {
    background: ${futuTheme.colors.backgroundTertiary};
    border-color: ${futuTheme.colors.border};
    color: ${futuTheme.colors.textPrimary};
  }

  &:active {
    transform: translateY(1px);
  }
`

// 右侧状态区域
const StatusSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

// 股票信息显示
const StockInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: ${futuTheme.colors.backgroundTertiary};
  border: 1px solid ${futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  font-size: ${futuTheme.typography.fontSize.sm};
  
  .code {
    font-weight: ${futuTheme.typography.fontWeight.medium};
    color: ${futuTheme.colors.textPrimary};
  }
  
  .name {
    color: ${futuTheme.colors.textSecondary};
  }
  
  .market {
    background: ${futuTheme.colors.futuBlue};
    color: ${futuTheme.colors.textPrimary};
    padding: 2px 6px;
    border-radius: 4px;
    font-size: ${futuTheme.typography.fontSize.xs};
    font-weight: ${futuTheme.typography.fontWeight.medium};
  }
`

// 状态指示器
const StatusIndicator = styled.div<{ status: BacktestStatus }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: ${futuTheme.layout.borderRadius};
  font-size: ${futuTheme.typography.fontSize.sm};
  font-weight: ${futuTheme.typography.fontWeight.medium};
  background: ${({ status }) => {
    switch (status) {
      case 'running': return `${futuTheme.colors.futuBlue}20`
      case 'completed': return `${futuTheme.colors.futuGreen}20`
      case 'error': return `${futuTheme.colors.futuRed}20`
      default: return futuTheme.colors.backgroundTertiary
    }
  }};
  border: 1px solid ${({ status }) => {
    switch (status) {
      case 'running': return futuTheme.colors.futuBlue
      case 'completed': return futuTheme.colors.futuGreen
      case 'error': return futuTheme.colors.futuRed
      default: return futuTheme.colors.border
    }
  }};
  color: ${({ status }) => {
    switch (status) {
      case 'running': return futuTheme.colors.futuBlue
      case 'completed': return futuTheme.colors.futuGreen
      case 'error': return futuTheme.colors.futuRed
      default: return futuTheme.colors.textSecondary
    }
  }};

  .icon {
    animation: ${({ status }) => status === 'running' ? 'spin 1s linear infinite' : 'none'};
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`

// 工具栏
const Toolbar = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`

// 组件属性接口
interface TopNavigationProps {
  currentPage: 'backtest' | 'history'
  onPageChange: (page: 'backtest' | 'history') => void
  selectedSymbol: StockSymbol | null
  backtestStatus: BacktestStatus
}

export const TopNavigation: React.FC<TopNavigationProps> = ({
  currentPage,
  onPageChange,
  selectedSymbol,
  backtestStatus
}) => {
  const navigate = useNavigate()
  const location = useLocation()

  // 状态文本映射
  const getStatusText = (status: BacktestStatus) => {
    switch (status) {
      case 'running': return '运行中'
      case 'completed': return '已完成'
      case 'error': return '出错'
      default: return '就绪'
    }
  }

  // 状态图标映射
  const getStatusIcon = (status: BacktestStatus) => {
    switch (status) {
      case 'running': return '⚡'
      case 'completed': return '✅'
      case 'error': return '❌'
      default: return '⭕'
    }
  }

  // 页面导航处理
  const handlePageChange = (page: 'backtest' | 'history') => {
    onPageChange(page)
    navigate(page === 'backtest' ? '/' : '/history')
  }

  // 当前时间显示
  const getCurrentTime = () => {
    return new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <NavContainer>
      {/* 左侧品牌和导航 */}
      <BrandSection>
        <Logo>
          <span className="icon">📈</span>
          <span>富途回测系统</span>
        </Logo>
        
        <NavMenu>
          <NavItem 
            active={location.pathname === '/'}
            onClick={() => handlePageChange('backtest')}
          >
            🚀 回测执行
          </NavItem>
          <NavItem 
            active={location.pathname === '/history'}
            onClick={() => handlePageChange('history')}
          >
            📚 历史结果
          </NavItem>
        </NavMenu>
      </BrandSection>

      {/* 右侧状态信息 */}
      <StatusSection>
        {/* 当前选择的股票 */}
        {selectedSymbol && (
          <StockInfo>
            <span className="code">{selectedSymbol.code}</span>
            <span className="name">{selectedSymbol.name}</span>
            <span className="market">{selectedSymbol.market}</span>
          </StockInfo>
        )}

        {/* 回测状态 */}
        <StatusIndicator status={backtestStatus}>
          <span className="icon">{getStatusIcon(backtestStatus)}</span>
          <span>{getStatusText(backtestStatus)}</span>
        </StatusIndicator>

        {/* 工具栏 */}
        <Toolbar>
          <Button 
            variant="secondary" 
            size="small"
            title={`当前时间: ${getCurrentTime()}`}
          >
            🕐 {new Date().toLocaleTimeString('zh-CN', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </Button>
          
          <Button 
            variant="secondary" 
            size="small"
            onClick={() => window.location.reload()}
            title="刷新页面"
          >
            🔄
          </Button>
        </Toolbar>
      </StatusSection>
    </NavContainer>
  )
} 