import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { futuTheme } from '../../styles/theme'
import { Card, Button } from '../../styles/GlobalStyle'
import { StockSymbol, BacktestParams, StrategyParams } from '../../types/trading'

// 面板容器
const PanelContainer = styled.div`
  width: ${futuTheme.layout.sidebarWidth};
  background-color: ${futuTheme.colors.backgroundSecondary};
  border-right: 1px solid ${futuTheme.colors.border};
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  min-width: 360px;               // 添加最小宽度限制
  max-width: 420px;               // 添加最大宽度限制
  
  /* 响应式适配 */
  @media (max-width: 1600px) {
    width: 360px;
  }
  
  @media (max-width: 1400px) {
    width: 340px;
  }
  
  @media (max-width: 1200px) {
    width: 320px;
  }
`

// 面板内容
const PanelContent = styled.div`
  padding: 12px;                  // 从${futuTheme.layout.padding}减少到12px
  display: flex;
  flex-direction: column;
  gap: 12px;                      // 从${futuTheme.layout.margin}减少到12px
`

// 区块标题
const SectionTitle = styled.h3`
  font-size: ${futuTheme.typography.fontSize.md};
  font-weight: ${futuTheme.typography.fontWeight.semibold};
  color: ${futuTheme.colors.textPrimary};
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  
  .icon {
    color: ${futuTheme.colors.futuBlue};
  }
`

// 表单组
const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

// 标签
const Label = styled.label`
  font-size: ${futuTheme.typography.fontSize.sm};
  font-weight: ${futuTheme.typography.fontWeight.medium};
  color: ${futuTheme.colors.textSecondary};
  display: flex;
  align-items: center;
  gap: 8px;
`

// 输入框组件
const Input = styled.input`
  padding: 10px 12px;
  border: 1px solid ${futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  background-color: ${futuTheme.colors.backgroundTertiary};
  color: ${futuTheme.colors.textPrimary};
  font-size: ${futuTheme.typography.fontSize.sm};
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:focus {
    border-color: ${futuTheme.colors.futuBlue};
    box-shadow: 0 0 0 2px ${futuTheme.colors.futuBlue}20;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

// 选择框组件
const Select = styled.select`
  padding: 10px 12px;
  border: 1px solid ${futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  background-color: ${futuTheme.colors.backgroundTertiary};
  color: ${futuTheme.colors.textPrimary};
  font-size: ${futuTheme.typography.fontSize.sm};
  cursor: pointer;
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:focus {
    border-color: ${futuTheme.colors.futuBlue};
    box-shadow: 0 0 0 2px ${futuTheme.colors.futuBlue}20;
  }

  option {
    background-color: ${futuTheme.colors.backgroundTertiary};
    color: ${futuTheme.colors.textPrimary};
  }
`

// 滑块容器
const SliderContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const SliderWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`

const Slider = styled.input`
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: ${futuTheme.colors.border};
  outline: none;
  -webkit-appearance: none;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: ${futuTheme.colors.futuBlue};
    cursor: pointer;
    border: 2px solid ${futuTheme.colors.background};
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  &::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: ${futuTheme.colors.futuBlue};
    cursor: pointer;
    border: 2px solid ${futuTheme.colors.background};
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
`

const SliderValue = styled.span`
  min-width: 40px;
  text-align: center;
  font-weight: ${futuTheme.typography.fontWeight.medium};
  color: ${futuTheme.colors.futuBlue};
  background: ${futuTheme.colors.backgroundTertiary};
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid ${futuTheme.colors.border};
  font-size: ${futuTheme.typography.fontSize.xs};
`

// 股票搜索容器
const StockSearchContainer = styled.div`
  position: relative;
`

const StockSearchInput = styled(Input)`
  padding-right: 40px;
`

const StockSearchIcon = styled.div`
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: ${futuTheme.colors.textTertiary};
  pointer-events: none;
`

// 股票列表
const StockList = styled.div`
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid ${futuTheme.colors.border};
  border-top: none;
  border-radius: 0 0 ${futuTheme.layout.borderRadius} ${futuTheme.layout.borderRadius};
  background: ${futuTheme.colors.backgroundTertiary};
  position: absolute;
  width: 100%;
  z-index: ${futuTheme.zIndex.dropdown};
`

const StockItem = styled.div`
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid ${futuTheme.colors.border};
  transition: background-color ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:hover {
    background-color: ${futuTheme.colors.backgroundSecondary};
  }

  &:last-child {
    border-bottom: none;
  }

  .code {
    font-weight: ${futuTheme.typography.fontWeight.medium};
    color: ${futuTheme.colors.textPrimary};
  }

  .name {
    font-size: ${futuTheme.typography.fontSize.xs};
    color: ${futuTheme.colors.textSecondary};
    margin-top: 2px;
  }

  .market {
    display: inline-block;
    background: ${futuTheme.colors.futuBlue};
    color: ${futuTheme.colors.textPrimary};
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 10px;
    margin-left: 8px;
  }
`

// 日期范围选择器
const DateRangeContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
`

const DateInput = styled(Input).attrs({ type: 'date' })`
  font-family: inherit;
  color-scheme: dark;
`

// 操作按钮区域
const ActionButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid ${futuTheme.colors.border};
`

// 参数摘要
const ParameterSummary = styled.div`
  background: ${futuTheme.colors.backgroundTertiary};
  border: 1px solid ${futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  padding: 12px;
  font-size: ${futuTheme.typography.fontSize.xs};
  color: ${futuTheme.colors.textSecondary};
  
  .summary-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .value {
    color: ${futuTheme.colors.textPrimary};
    font-weight: ${futuTheme.typography.fontWeight.medium};
  }
`

// 组件属性接口
interface ParameterPanelProps {
  stockList: StockSymbol[]
  selectedSymbol: StockSymbol | null
  backtestParams: BacktestParams
  loading: boolean
  onSymbolChange: (symbol: StockSymbol) => void
  onParameterChange: (params: Partial<BacktestParams>) => void
  onRunBacktest: () => void
  onClearResults: () => void
}

export const ParameterPanel: React.FC<ParameterPanelProps> = ({
  stockList,
  selectedSymbol,
  backtestParams,
  loading,
  onSymbolChange,
  onParameterChange,
  onRunBacktest,
  onClearResults
}) => {
  const [stockSearchTerm, setStockSearchTerm] = useState('')
  const [showStockList, setShowStockList] = useState(false)
  const [filteredStocks, setFilteredStocks] = useState<StockSymbol[]>([])

  // 过滤股票列表
  useEffect(() => {
    if (stockSearchTerm) {
      const filtered = stockList.filter(stock => 
        stock.code.toLowerCase().includes(stockSearchTerm.toLowerCase()) ||
        stock.name.toLowerCase().includes(stockSearchTerm.toLowerCase())
      )
      setFilteredStocks(filtered)
    } else {
      setFilteredStocks(stockList.slice(0, 20)) // 默认显示前20个
    }
  }, [stockSearchTerm, stockList])

  // 确保日期参数不为空
  useEffect(() => {
    const defaultDates = getDefaultDates()
    if (!backtestParams.startDate || !backtestParams.endDate) {
      onParameterChange({
        startDate: backtestParams.startDate || defaultDates.start,
        endDate: backtestParams.endDate || defaultDates.end
      })
    }
  }, [backtestParams.startDate, backtestParams.endDate, onParameterChange])

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

  // 参数更新处理
  const handleParameterUpdate = (key: keyof StrategyParams, value: any) => {
    onParameterChange({
      parameters: {
        ...backtestParams.parameters,
        [key]: value
      }
    })
  }

  // 股票选择处理
  const handleStockSelect = (stock: StockSymbol) => {
    onSymbolChange(stock)
    setStockSearchTerm(stock.code)
    setShowStockList(false)
  }

  return (
    <PanelContainer>
      <PanelContent>
        {/* 股票选择 */}
        <Card>
          <SectionTitle>
            <span className="icon">🎯</span>
            股票选择
          </SectionTitle>
          
          <FormGroup>
            <Label>股票代码</Label>
            <StockSearchContainer>
              <StockSearchInput
                placeholder="搜索股票代码或名称..."
                value={stockSearchTerm}
                onChange={(e) => {
                  setStockSearchTerm(e.target.value)
                  setShowStockList(true)
                }}
                onFocus={() => setShowStockList(true)}
                onBlur={() => setTimeout(() => setShowStockList(false), 200)}
              />
              <StockSearchIcon>🔍</StockSearchIcon>
              
              {showStockList && filteredStocks.length > 0 && (
                <StockList>
                  {filteredStocks.map((stock) => (
                    <StockItem 
                      key={stock.code}
                      onClick={() => handleStockSelect(stock)}
                    >
                      <div className="code">
                        {stock.code}
                        <span className="market">{stock.market}</span>
                      </div>
                      <div className="name">{stock.name}</div>
                    </StockItem>
                  ))}
                </StockList>
              )}
            </StockSearchContainer>
          </FormGroup>
        </Card>

        {/* 时间范围 */}
        <Card>
          <SectionTitle>
            <span className="icon">📅</span>
            时间范围
          </SectionTitle>
          
          <FormGroup>
            <Label>回测区间</Label>
            <DateRangeContainer>
              <DateInput
                value={backtestParams.startDate || defaultDates.start}
                onChange={(e) => {
                  const value = e.target.value || defaultDates.start
                  onParameterChange({ startDate: value })
                }}
                placeholder="开始日期"
                required
              />
              <DateInput
                value={backtestParams.endDate || defaultDates.end}
                onChange={(e) => {
                  const value = e.target.value || defaultDates.end
                  onParameterChange({ endDate: value })
                }}
                placeholder="结束日期"
                required
              />
            </DateRangeContainer>
          </FormGroup>
        </Card>

        {/* 策略参数 */}
        <Card>
          <SectionTitle>
            <span className="icon">⚙️</span>
            策略参数
          </SectionTitle>
          
          <FormGroup>
            <Label>移动平均线</Label>
            <SliderContainer>
              <SliderWrapper>
                <span style={{ fontSize: '12px', color: futuTheme.colors.textTertiary }}>快线:</span>
                <Slider
                  type="range"
                  min="5"
                  max="20"
                  value={backtestParams.parameters.fastMaPeriod}
                  onChange={(e) => handleParameterUpdate('fastMaPeriod', parseInt(e.target.value))}
                />
                <SliderValue>{backtestParams.parameters.fastMaPeriod}</SliderValue>
              </SliderWrapper>
              
              <SliderWrapper>
                <span style={{ fontSize: '12px', color: futuTheme.colors.textTertiary }}>慢线:</span>
                <Slider
                  type="range"
                  min="20"
                  max="60"
                  value={backtestParams.parameters.slowMaPeriod}
                  onChange={(e) => handleParameterUpdate('slowMaPeriod', parseInt(e.target.value))}
                />
                <SliderValue>{backtestParams.parameters.slowMaPeriod}</SliderValue>
              </SliderWrapper>
            </SliderContainer>
          </FormGroup>

          <FormGroup>
            <Label>ATR 参数</Label>
            <SliderContainer>
              <SliderWrapper>
                <span style={{ fontSize: '12px', color: futuTheme.colors.textTertiary }}>周期:</span>
                <Slider
                  type="range"
                  min="10"
                  max="30"
                  value={backtestParams.parameters.atrPeriod}
                  onChange={(e) => handleParameterUpdate('atrPeriod', parseInt(e.target.value))}
                />
                <SliderValue>{backtestParams.parameters.atrPeriod}</SliderValue>
              </SliderWrapper>
              
              <SliderWrapper>
                <span style={{ fontSize: '12px', color: futuTheme.colors.textTertiary }}>倍数:</span>
                <Slider
                  type="range"
                  min="1"
                  max="4"
                  step="0.1"
                  value={backtestParams.parameters.atrMultiplier}
                  onChange={(e) => handleParameterUpdate('atrMultiplier', parseFloat(e.target.value))}
                />
                <SliderValue>{backtestParams.parameters.atrMultiplier}</SliderValue>
              </SliderWrapper>
            </SliderContainer>
          </FormGroup>

          <FormGroup>
            <Label>仓位管理</Label>
            <Select
              value={backtestParams.parameters.positionMode}
              onChange={(e) => handleParameterUpdate('positionMode', e.target.value)}
            >
              <option value="full">全仓</option>
              <option value="half">半仓</option>
              <option value="quarter">1/4仓</option>
              <option value="fixed">固定手数</option>
            </Select>
            
            {backtestParams.parameters.positionMode === 'fixed' && (
              <Input
                type="number"
                min="1"
                max="100"
                value={backtestParams.parameters.fixedSize}
                onChange={(e) => handleParameterUpdate('fixedSize', parseInt(e.target.value))}
                placeholder="输入固定手数"
              />
            )}
          </FormGroup>
        </Card>

        {/* 参数摘要 */}
        <Card>
          <SectionTitle>
            <span className="icon">📋</span>
            参数摘要
          </SectionTitle>
          
          <ParameterSummary>
            <div className="summary-item">
              <span>股票:</span>
              <span className="value">{selectedSymbol?.code || '未选择'}</span>
            </div>
            <div className="summary-item">
              <span>快/慢均线:</span>
              <span className="value">{backtestParams.parameters.fastMaPeriod}/{backtestParams.parameters.slowMaPeriod}</span>
            </div>
            <div className="summary-item">
              <span>ATR:</span>
              <span className="value">{backtestParams.parameters.atrPeriod}期 {backtestParams.parameters.atrMultiplier}倍</span>
            </div>
            <div className="summary-item">
              <span>仓位:</span>
              <span className="value">{
                backtestParams.parameters.positionMode === 'full' ? '全仓' :
                backtestParams.parameters.positionMode === 'half' ? '半仓' :
                backtestParams.parameters.positionMode === 'quarter' ? '1/4仓' :
                `${backtestParams.parameters.fixedSize}手`
              }</span>
            </div>
            <div className="summary-item">
              <span>回测天数:</span>
              <span className="value">
                {backtestParams.startDate && backtestParams.endDate
                  ? Math.ceil((new Date(backtestParams.endDate).getTime() - new Date(backtestParams.startDate).getTime()) / (1000 * 60 * 60 * 24))
                  : '未设置'
                }天
              </span>
            </div>
          </ParameterSummary>
        </Card>

        {/* 操作按钮 */}
        <ActionButtons>
          <Button
            variant="primary"
            size="large"
            fullWidth
            disabled={loading || !selectedSymbol}
            onClick={onRunBacktest}
          >
            {loading ? '🔄 运行中...' : '🚀 开始回测'}
          </Button>
          
          <Button
            variant="secondary"
            size="medium"
            fullWidth
            onClick={onClearResults}
          >
            🗑️ 清除结果
          </Button>
        </ActionButtons>
      </PanelContent>
    </PanelContainer>
  )
} 