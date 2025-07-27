import React, { useEffect, useRef, useState, useCallback } from 'react'
import * as echarts from 'echarts'
import styled from 'styled-components'
import { futuTheme, candlestickColors } from '../../styles/theme'
import { StockSymbol, BacktestResults, CandleData, TradeRecord } from '../../types/trading'
import { backtestService } from '../../services/BacktestService'

// 图表容器
const ChartContainer = styled.div`
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
  display: flex;
  flex-direction: column;
`

const ChartContent = styled.div`
  flex: 1;
  min-height: 0;
  position: relative;
`

// 图表控制面板
const ChartControls = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 8px;
  z-index: 10;
`

const ControlButton = styled.button<{ active?: boolean }>`
  padding: 4px 8px;
  background: ${({ active }) => active ? futuTheme.colors.futuBlue : futuTheme.colors.backgroundTertiary};
  border: 1px solid ${({ active }) => active ? futuTheme.colors.futuBlue : futuTheme.colors.border};
  border-radius: 4px;
  color: ${({ active }) => active ? futuTheme.colors.textPrimary : futuTheme.colors.textSecondary};
  font-size: ${futuTheme.typography.fontSize.xs};
  cursor: pointer;
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:hover {
    background: ${futuTheme.colors.futuBlue};
    color: ${futuTheme.colors.textPrimary};
  }
`

// 组件属性接口
interface KLineChartProps {
  symbol: StockSymbol | null
  dateRange: [string, string]
  backtestResults?: BacktestResults | null
  height?: number
  onZoomChange?: (start: number, end: number) => void
  zoomStart?: number
  zoomEnd?: number
}

export const KLineChart: React.FC<KLineChartProps> = ({
  symbol,
  dateRange,
  backtestResults,
  height = 400,
  onZoomChange,
  zoomStart = 70,
  zoomEnd = 100
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showVolume, setShowVolume] = useState(true)
  const [showMA, setShowMA] = useState(true)
  const [showTrades, setShowTrades] = useState(true)

  // 计算移动平均线
  const calculateMA = (data: CandleData[], period: number): number[] => {
    const ma: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        ma.push(NaN)
      } else {
        let sum = 0
        for (let j = 0; j < period; j++) {
          sum += data[i - j].close
        }
        ma.push(sum / period)
      }
    }
    return ma
  }

  // 准备图表数据
  const prepareChartData = useCallback(async () => {
    if (!symbol || !dateRange[0] || !dateRange[1]) {
      return null
    }

    let candleData: CandleData[]
    
    // 使用回测结果中的K线数据，如果没有则从API获取数据
    if (backtestResults && backtestResults.candleData && backtestResults.candleData.length > 0) {
      candleData = backtestResults.candleData
    } else {
      try {
        candleData = await backtestService.getStockPriceData(symbol.code, dateRange[0], dateRange[1])
      } catch (error) {
        console.error('获取K线数据失败:', error)
        return null
      }
    }

    if (candleData.length === 0) {
      return null
    }

    // 准备ECharts数据格式
    const dates = candleData.map(item => item.date)
    const values = candleData.map(item => [item.open, item.close, item.low, item.high])
    const volumes = candleData.map(item => item.volume)
    
    // 计算移动平均线
    const ma5 = calculateMA(candleData, 5)
    const ma10 = calculateMA(candleData, 10)
    const ma20 = calculateMA(candleData, 20)

    return {
      dates,
      values,
      volumes,
      ma5,
      ma10,
      ma20,
      candleData
    }
  }, [symbol, dateRange, backtestResults])

  // 准备交易标记数据
  const prepareTradeMarks = useCallback((chartData: any) => {
    if (!backtestResults || !backtestResults.trades || !showTrades) {
      return []
    }

    const tradeMarks: any[] = []
    
    backtestResults.trades.forEach((trade: TradeRecord) => {
      const tradeDate = trade.date.split(' ')[0] // 获取日期部分
      const dateIndex = chartData.dates.indexOf(tradeDate)
      
      if (dateIndex !== -1) {
        const isLong = trade.direction === 'LONG'
        const isOpen = trade.offset === 'OPEN'
        
        tradeMarks.push({
          name: `${trade.direction} ${trade.offset}`,
          coord: [dateIndex, trade.price],
          symbol: isOpen ? 'triangle' : 'circle',
          symbolSize: 8,
          itemStyle: {
            color: isLong ? 
              (isOpen ? futuTheme.colors.futuGreen : futuTheme.colors.futuGreen + '80') :
              (isOpen ? futuTheme.colors.futuRed : futuTheme.colors.futuRed + '80')
          },
          label: {
            show: false
          }
        })
      }
    })

    return tradeMarks
  }, [backtestResults, showTrades])

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current) return

    // 销毁已存在的图表实例
    if (chartInstance.current) {
      chartInstance.current.dispose()
    }

    // 创建新的图表实例
    chartInstance.current = echarts.init(chartRef.current, 'dark')

    // 注册富途主题
    echarts.registerTheme('futu', {
      backgroundColor: futuTheme.colors.chartBackground,
      textStyle: {
        color: futuTheme.colors.textPrimary
      }
    })

    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose()
      }
    }
  }, [])

  // 更新图表数据
  useEffect(() => {
    if (!chartInstance.current) return

    const updateChart = async () => {
      const chartData = await prepareChartData()
      if (!chartData) {
        // 显示空数据状态
        const emptyOption = {
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: {
              color: futuTheme.colors.textTertiary,
              fontSize: 16
            }
          }
        }
        chartInstance.current?.setOption(emptyOption)
        return
      }

      const tradeMarks = prepareTradeMarks(chartData)

      // 构建图表配置
      const option = {
        backgroundColor: futuTheme.colors.chartBackground,
        animation: true,
        animationDuration: 300,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            lineStyle: {
              color: futuTheme.colors.futuBlue,
              width: 1,
              opacity: 0.8
            }
          },
          backgroundColor: futuTheme.colors.tooltipBackground,
          borderColor: futuTheme.colors.tooltipBorder,
          borderWidth: 1,
          textStyle: {
            color: futuTheme.colors.textPrimary,
            fontSize: 12
          },
          formatter: (params: any) => {
            if (!params || params.length === 0) return ''
            
            const dataIndex = params[0].dataIndex
            const date = chartData.dates[dataIndex]
            const candleValue = chartData.values[dataIndex]
            const volume = chartData.volumes[dataIndex]
            
            if (!candleValue) return ''
            
            const [open, close, low, high] = candleValue
            const change = ((close - open) / open * 100).toFixed(2)
            const changeColor = close >= open ? futuTheme.colors.futuGreen : futuTheme.colors.futuRed
            
            return `
              <div style="padding: 8px;">
                <div style="font-weight: bold; margin-bottom: 8px;">${symbol?.code} ${date}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px;">
                  <div>开盘: <span style="color: ${futuTheme.colors.textPrimary}">${open.toFixed(2)}</span></div>
                  <div>收盘: <span style="color: ${changeColor}">${close.toFixed(2)}</span></div>
                  <div>最高: <span style="color: ${futuTheme.colors.futuGreen}">${high.toFixed(2)}</span></div>
                  <div>最低: <span style="color: ${futuTheme.colors.futuRed}">${low.toFixed(2)}</span></div>
                  <div>涨跌: <span style="color: ${changeColor}">${change}%</span></div>
                  <div>成交量: <span style="color: ${futuTheme.colors.textSecondary}">${(volume / 10000).toFixed(1)}万</span></div>
                </div>
              </div>
            `
          }
        },
        grid: [
          {
            left: '60px',
            right: '60px',
            top: '60px',
            height: showVolume ? '65%' : '80%'
          },
          {
            left: '60px',
            right: '60px',
            height: '25%',
            bottom: '30px'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: chartData.dates,
            boundaryGap: false,
            axisLine: {
              lineStyle: {
                color: futuTheme.colors.border
              }
            },
            axisLabel: {
              color: futuTheme.colors.textSecondary,
              fontSize: 11
            },
            splitLine: {
              show: false
            }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: chartData.dates,
            boundaryGap: false,
            axisLine: {
              lineStyle: {
                color: futuTheme.colors.border
              }
            },
            axisLabel: {
              color: futuTheme.colors.textSecondary,
              fontSize: 11
            },
            splitLine: {
              show: false
            }
          }
        ],
        yAxis: [
          {
            scale: true,
            axisLine: {
              lineStyle: {
                color: futuTheme.colors.border
              }
            },
            axisLabel: {
              color: futuTheme.colors.textSecondary,
              fontSize: 11,
              formatter: (value: number) => value.toFixed(2)
            },
            splitLine: {
              lineStyle: {
                color: futuTheme.colors.gridColor,
                opacity: 0.3
              }
            }
          },
          {
            scale: true,
            gridIndex: 1,
            axisLine: {
              lineStyle: {
                color: futuTheme.colors.border
              }
            },
            axisLabel: {
              color: futuTheme.colors.textSecondary,
              fontSize: 11,
              formatter: (value: number) => (value / 10000).toFixed(0) + 'w'
            },
            splitLine: {
              lineStyle: {
                color: futuTheme.colors.gridColor,
                opacity: 0.3
              }
            }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: zoomStart,
            end: zoomEnd,
            zoomOnMouseWheel: true,
            moveOnMouseMove: true
          },
          {
            type: 'slider',
            xAxisIndex: [0, 1],
            start: zoomStart,
            end: zoomEnd,
            height: 20,
            bottom: 15,
            fillerColor: 'rgba(0, 212, 170, 0.15)',
            borderColor: '#30363D',
            handleStyle: {
              color: '#00D4AA',
              borderColor: '#30363D'
            },
            dataBackground: {
              lineStyle: {
                color: '#30363D'
              },
              areaStyle: {
                color: 'rgba(0, 212, 170, 0.1)'
              }
            },
            textStyle: {
              color: '#8B949E',
              fontSize: 10
            }
          }
        ],
        series: [
          // K线图
          {
            type: 'candlestick',
            data: chartData.values,
            itemStyle: {
              // 修改颜色逻辑：收盘价大于等于开盘价为上涨，使用红色
              color: candlestickColors.down.color,     // 空心部分颜色
              color0: candlestickColors.up.color,      // 实心部分颜色
              borderColor: candlestickColors.down.borderColor,     // 上涨边框为红色
              borderColor0: candlestickColors.up.borderColor,      // 下跌边框为绿色
              borderWidth: 1
            },
            markPoint: {
              data: tradeMarks,
              symbol: 'circle',
              symbolSize: 6
            }
          },
          // 移动平均线
          ...(showMA ? [
            {
              name: 'MA5',
              type: 'line',
              data: chartData.ma5,
              smooth: true,
              lineStyle: {
                width: 1,
                color: futuTheme.colors.futuBlue
              },
              showSymbol: false
            },
            {
              name: 'MA10',
              type: 'line',
              data: chartData.ma10,
              smooth: true,
              lineStyle: {
                width: 1,
                color: futuTheme.colors.futuOrange
              },
              showSymbol: false
            },
            {
              name: 'MA20',
              type: 'line',
              data: chartData.ma20,
              smooth: true,
              lineStyle: {
                width: 1,
                color: futuTheme.colors.futuPurple
              },
              showSymbol: false
            }
          ] : []),
          // 成交量
          ...(showVolume ? [
            {
              type: 'bar',
              xAxisIndex: 1,
              yAxisIndex: 1,
              data: chartData.volumes,
              itemStyle: {
                color: (params: any) => {
                  const candleValue = chartData.values[params.dataIndex]
                  if (!candleValue) return futuTheme.colors.textTertiary
                  const [open, close] = candleValue
                  return close >= open ? 
                    futuTheme.colors.futuRed + '60' :   // 上涨成交量为红色
                    futuTheme.colors.futuGreen + '60'   // 下跌成交量为绿色
                }
              }
            }
          ] : [])
        ],
        legend: showMA ? {
          data: ['MA5', 'MA10', 'MA20'],
          top: 10,
          left: 10,
          textStyle: {
            color: futuTheme.colors.textSecondary,
            fontSize: 11
          },
          itemWidth: 12,
          itemHeight: 8
        } : undefined
      }

      chartInstance.current?.setOption(option, true)

      // 添加缩放事件监听
      chartInstance.current?.on('datazoom', (params: any) => {
        if (onZoomChange) {
          onZoomChange(params.batch?.[0]?.start ?? params.start, params.batch?.[0]?.end ?? params.end)
        }
      })

      // 处理窗口大小变化
      const handleResize = () => {
        chartInstance.current?.resize()
      }

      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
      }
    }

    updateChart()
  }, [symbol, dateRange, backtestResults, showVolume, showMA, showTrades, prepareChartData, prepareTradeMarks, onZoomChange, zoomStart, zoomEnd])

  return (
    <ChartContainer>
      <ChartContent ref={chartRef} />
      <ChartControls>
        <ControlButton 
          active={showMA}
          onClick={() => setShowMA(!showMA)}
        >
          MA
        </ControlButton>
        <ControlButton 
          active={showVolume}
          onClick={() => setShowVolume(!showVolume)}
        >
          成交量
        </ControlButton>
        <ControlButton 
          active={showTrades}
          onClick={() => setShowTrades(!showTrades)}
        >
          交易点
        </ControlButton>
      </ChartControls>
    </ChartContainer>
  )
} 