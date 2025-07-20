import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import styled from 'styled-components'
import { futuTheme, candlestickColors } from '../../styles/theme'
import { StockSymbol, BacktestResults, CandleData, TradeRecord } from '../../types/trading'

// 图表容器
const ChartContainer = styled.div`
  width: 100%;
  height: 100%;
  min-height: 400px;
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
}

export const KLineChart: React.FC<KLineChartProps> = ({
  symbol,
  dateRange,
  backtestResults,
  height = 400
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showVolume, setShowVolume] = useState(true)
  const [showMA, setShowMA] = useState(true)
  const [showTrades, setShowTrades] = useState(true)

  // 模拟K线数据生成（实际应用中应从API获取）
  const generateMockData = (startDate: string, endDate: string, symbol: string): CandleData[] => {
    const data: CandleData[] = []
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
  const prepareChartData = () => {
    if (!symbol || !dateRange[0] || !dateRange[1]) {
      return null
    }

    let candleData: CandleData[]
    
    // 使用回测结果中的K线数据，如果没有则生成模拟数据
    if (backtestResults && backtestResults.candleData && backtestResults.candleData.length > 0) {
      candleData = backtestResults.candleData
    } else {
      candleData = generateMockData(dateRange[0], dateRange[1], symbol.code)
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
  }

  // 准备交易标记数据
  const prepareTradeMarks = (chartData: any) => {
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
  }

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

    const chartData = prepareChartData()
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
      chartInstance.current.setOption(emptyOption)
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
          height: showVolume ? '60%' : '75%'
        },
        {
          left: '60px',
          right: '60px',
          height: '15%',
          bottom: '60px'
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
          start: 70,
          end: 100
        },
        {
          type: 'slider',
          xAxisIndex: [0, 1],
          bottom: 10,
          height: 20,
          borderColor: futuTheme.colors.border,
          fillerColor: futuTheme.colors.futuBlue + '20',
          selectedDataBackground: {
            lineStyle: {
              color: futuTheme.colors.futuBlue
            },
            areaStyle: {
              color: futuTheme.colors.futuBlue + '20'
            }
          },
          textStyle: {
            color: futuTheme.colors.textSecondary,
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
            color: candlestickColors.up.color,
            color0: candlestickColors.down.color,
            borderColor: candlestickColors.up.borderColor,
            borderColor0: candlestickColors.down.borderColor,
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
                  futuTheme.colors.futuGreen + '60' : 
                  futuTheme.colors.futuRed + '60'
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

    chartInstance.current.setOption(option, true)

    // 自适应大小
    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [symbol, dateRange, backtestResults, showVolume, showMA, showTrades])

  return (
    <ChartContainer>
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
      
      <div 
        ref={chartRef} 
        style={{ 
          width: '100%', 
          height: `${height}px`,
          minHeight: '400px'
        }} 
      />
    </ChartContainer>
  )
} 