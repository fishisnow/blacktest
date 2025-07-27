import React, { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import styled from 'styled-components'
import { DailyResult } from '../../types/trading'
import { futuTheme } from '../../styles/theme'
import { Card } from '../../styles/GlobalStyle'

const ChartCard = styled(Card)`
  width: 100%;
  height: 300px;
  padding: 16px;
  margin-bottom: 16px;
  background: ${futuTheme.colors.cardBackground};
`

const ChartTitle = styled.div`
  font-size: ${futuTheme.typography.fontSize.md};
  color: ${futuTheme.colors.textPrimary};
  margin-bottom: 12px;
  font-weight: 500;
`

const ChartContent = styled.div`
  flex: 1;
  min-height: 0;
  position: relative;
`

interface ChartProps {
  dailyResults: DailyResult[]
  symbol?: string
  loading?: boolean
  onZoomChange?: (start: number, end: number) => void
  zoomStart?: number
  zoomEnd?: number
  benchmarkData?: { date: string; benchmarkReturn: number }[]  // 添加标的涨幅数据
}

// 收益率图表组件
export const ReturnChart: React.FC<ChartProps> = ({ 
  dailyResults, 
  symbol, 
  loading,
  onZoomChange,
  zoomStart = 0,
  zoomEnd = 100,
  benchmarkData = []
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  // 初始化图表
  useEffect(() => {
    // 确保DOM元素存在
    if (!chartRef.current) return

    // 创建图表实例
    const chart = echarts.init(chartRef.current)
    chartInstance.current = chart

    // 监听窗口大小变化
    const handleResize = () => {
      chart.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartInstance.current = null
    }
  }, [])

  // 更新图表数据
  useEffect(() => {
    if (!chartInstance.current || !dailyResults.length) return

    const dates = dailyResults.map(item => item.date)
    const returnRatios = dailyResults.map(item => item.returnRatio)

    // 处理标的涨幅数据
    const benchmarkReturns = dates.map(date => {
      const benchmarkItem = benchmarkData.find(item => item.date === date)
      return benchmarkItem ? benchmarkItem.benchmarkReturn : null
    })

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '3%',
        containLabel: true
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          if (!params || !Array.isArray(params) || params.length === 0) {
            return '';
          }
          
          const date = params[0].axisValue;
          let result = `<div style="margin: 0px 0 0;line-height:1;">${date}</div>`;
          
          params.forEach((param: any) => {
            if (param.value !== null) {
              const color = param.color;
              const value = typeof param.value === 'number' ? param.value.toFixed(2) : '-';
              result += `
                <div style="margin: 10px 0 0;line-height:1;">
                  <div style="margin: 0px 0 0;line-height:1;">
                    <span style="display:inline-block;margin-right:4px;border-radius:50%;width:4px;height:4px;background-color:${color};"></span>
                    <span style="font-size:12px;color:#666;margin-right:8px;">${param.seriesName}:</span>
                    <span style="float:right;margin-left:20px;font-size:12px;color:#666;font-weight:900;">${value}%</span>
                  </div>
                </div>`;
            }
          });
          
          return result;
        },
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        borderColor: '#ccc',
        borderWidth: 1,
        padding: [5, 10],
        textStyle: {
          color: '#333'
        },
        extraCssText: 'box-shadow: 0 0 3px rgba(0, 0, 0, 0.3);'
      },
      legend: {
        data: ['策略收益率', `${symbol || '标的'} 涨幅`],
        top: 0,
        textStyle: {
          color: futuTheme.colors.textSecondary,
          fontSize: 10
        }
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { 
          lineStyle: { 
            color: futuTheme.colors.border,
            width: 1
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: false
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        name: '收益率(%)',
        nameTextStyle: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10,
          padding: [0, 30, 0, 0]
        },
        axisLine: { 
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: futuTheme.colors.border,
            width: 1,
            type: 'dashed',
            opacity: 0.2
          }
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10
        }
      },
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd,
          height: 20,
          bottom: 0,
          borderColor: futuTheme.colors.border,
          textStyle: { color: futuTheme.colors.textSecondary },
          handleStyle: {
            color: futuTheme.colors.futuBlue,
            borderColor: futuTheme.colors.border
          }
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd
        }
      ],
      series: [
        {
          name: '策略收益率',
          type: 'line',
          data: returnRatios,
          smooth: true,
          lineStyle: { width: 2, color: futuTheme.colors.futuBlue },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
              ]
            }
          }
        },
        {
          name: `${symbol || '标的'} 涨幅`,
          type: 'line',
          data: benchmarkReturns,
          smooth: true,
          lineStyle: { 
            width: 2, 
            color: futuTheme.colors.textSecondary,
            type: 'dashed'
          }
        }
      ]
    }

    chartInstance.current.setOption(option, true)

    // 添加缩放事件监听
    chartInstance.current.off('datazoom')
    chartInstance.current.on('datazoom', (params: any) => {
      if (onZoomChange) {
        onZoomChange(params.start, params.end)
      }
    })
  }, [dailyResults, symbol, benchmarkData, zoomStart, zoomEnd, onZoomChange])

  return (
    <ChartCard>
      <ChartTitle>策略收益率</ChartTitle>
      <div ref={chartRef} style={{ width: '100%', height: 'calc(100% - 40px)' }} />
    </ChartCard>
  )
}

// 每日盈亏图表组件
export const PnLChart: React.FC<ChartProps> = ({ 
  dailyResults, 
  loading,
  onZoomChange,
  zoomStart = 0,
  zoomEnd = 100
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  // 初始化图表
  useEffect(() => {
    // 确保DOM元素存在
    if (!chartRef.current) return

    // 创建图表实例
    const chart = echarts.init(chartRef.current)
    chartInstance.current = chart

    // 监听窗口大小变化
    const handleResize = () => {
      chart.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartInstance.current = null
    }
  }, [])

  // 更新图表数据
  useEffect(() => {
    if (!chartInstance.current || !dailyResults.length) return

    const dates = dailyResults.map(item => item.date)
    const pnls = dailyResults.map(item => item.netPnl)

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '3%',
        containLabel: true
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const date = params[0].axisValue
          const value = params[0].value
          return `${date}<br/>盈亏: ${value.toFixed(2)}`
        }
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { 
          lineStyle: { 
            color: futuTheme.colors.border,
            width: 1
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: false
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        name: '盈亏',
        nameTextStyle: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10,
          padding: [0, 30, 0, 0]  // 调整名称位置
        },
        axisLine: { 
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: futuTheme.colors.border,
            width: 1,
            type: 'dashed',
            opacity: 0.2
          }
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10,
          formatter: (value: number) => {
            if (Math.abs(value) >= 10000) {
              return (value / 10000).toFixed(0) + 'w'
            }
            return value.toFixed(0)
          }
        }
      },
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd,
          height: 20,
          bottom: 0,
          borderColor: futuTheme.colors.border,
          textStyle: { color: futuTheme.colors.textSecondary },
          handleStyle: {
            color: futuTheme.colors.futuBlue,
            borderColor: futuTheme.colors.border
          }
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd
        }
      ],
      series: [{
        data: pnls,
        type: 'bar',
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? futuTheme.colors.futuRed : futuTheme.colors.futuGreen
          }
        }
      }]
    }

    chartInstance.current.setOption(option, true)

    // 添加缩放事件监听
    chartInstance.current.off('datazoom')
    chartInstance.current.on('datazoom', (params: any) => {
      if (onZoomChange) {
        onZoomChange(params.start, params.end)
      }
    })
  }, [dailyResults, zoomStart, zoomEnd, onZoomChange])

  return (
    <ChartCard>
      <ChartTitle>每日盈亏</ChartTitle>
      <div ref={chartRef} style={{ width: '100%', height: 'calc(100% - 40px)' }} />
    </ChartCard>
  )
}

// 最大回撤图表组件
export const DrawdownChart: React.FC<ChartProps> = ({ 
  dailyResults, 
  loading,
  onZoomChange,
  zoomStart = 0,
  zoomEnd = 100
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  // 初始化图表
  useEffect(() => {
    // 确保DOM元素存在
    if (!chartRef.current) return

    // 创建图表实例
    const chart = echarts.init(chartRef.current)
    chartInstance.current = chart

    // 监听窗口大小变化
    const handleResize = () => {
      chart.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartInstance.current = null
    }
  }, [])

  // 更新图表数据
  useEffect(() => {
    if (!chartInstance.current || !dailyResults.length) return

    const dates = dailyResults.map(item => item.date)
    const drawdowns = dailyResults.map(item => -item.drawdown)

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '3%',
        containLabel: true
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const date = params[0].axisValue
          const value = params[0].value
          return `${date}<br/>回撤: ${(-value).toFixed(2)}%`
        }
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { 
          lineStyle: { 
            color: futuTheme.colors.border,
            width: 1
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: false
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        name: '回撤(%)',
        nameTextStyle: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10,
          padding: [0, 30, 0, 0]  // 调整名称位置
        },
        axisLine: { 
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: futuTheme.colors.border,
            width: 1,
            type: 'dashed',
            opacity: 0.2
          }
        },
        axisLabel: { 
          color: futuTheme.colors.textSecondary,
          fontSize: 10,
          formatter: (value: number) => (-value).toFixed(1) + '%'
        }
      },
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd,
          height: 20,
          bottom: 0,
          borderColor: futuTheme.colors.border,
          textStyle: { color: futuTheme.colors.textSecondary },
          handleStyle: {
            color: futuTheme.colors.futuBlue,
            borderColor: futuTheme.colors.border
          }
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: zoomStart,
          end: zoomEnd
        }
      ],
      series: [{
        data: drawdowns,
        type: 'line',
        smooth: true,
        lineStyle: { width: 2, color: futuTheme.colors.futuRed },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 77, 79, 0.3)' },
              { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
            ]
          }
        }
      }]
    }

    chartInstance.current.setOption(option, true)

    // 添加缩放事件监听
    chartInstance.current.off('datazoom')
    chartInstance.current.on('datazoom', (params: any) => {
      if (onZoomChange) {
        onZoomChange(params.start, params.end)
      }
    })
  }, [dailyResults, zoomStart, zoomEnd, onZoomChange])

  return (
    <ChartCard>
      <ChartTitle>最大回撤</ChartTitle>
      <div ref={chartRef} style={{ width: '100%', height: 'calc(100% - 40px)' }} />
    </ChartCard>
  )
} 