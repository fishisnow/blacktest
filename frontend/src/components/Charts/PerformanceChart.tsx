import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import styled from 'styled-components'
import { DailyResult } from '../../types/trading'
import { backtestService } from '../../services/BacktestService'

const ChartContainer = styled.div`
  width: 100%;
  height: 700px;
  background: #161B22;
  border: 1px solid #30363D;
  border-radius: 8px;
  overflow: hidden;
`

interface PerformanceChartProps {
  dailyResults: DailyResult[]
  symbol?: string
  startDate?: string
  endDate?: string
  loading?: boolean
}

interface BenchmarkData {
  date: string
  benchmarkReturn: number
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ 
  dailyResults, 
  symbol,
  startDate,
  endDate,
  loading = false 
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData[]>([])
  const [benchmarkLoading, setBenchmarkLoading] = useState(false)

  // 获取标的价格数据
  useEffect(() => {
    if (symbol && startDate && endDate && dailyResults.length > 0) {
      fetchBenchmarkData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, startDate, endDate, dailyResults])

  const fetchBenchmarkData = async () => {
    if (!symbol || !startDate || !endDate) return
    
    setBenchmarkLoading(true)
    try {
      const priceData = await backtestService.getStockPriceData(symbol, startDate, endDate)
      
      if (priceData && priceData.length > 0) {
        // 计算标的累计涨幅
        const initialPrice = priceData[0].close
        const benchmarkReturns: BenchmarkData[] = priceData.map(item => ({
          date: item.date,
          benchmarkReturn: ((item.close / initialPrice) - 1) * 100
        }))
        
        setBenchmarkData(benchmarkReturns)
      }
    } catch (error) {
      console.error('获取标的数据失败:', error)
      setBenchmarkData([])
    } finally {
      setBenchmarkLoading(false)
    }
  }

  useEffect(() => {
    if (!chartRef.current) return

    // 初始化图表
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, 'dark')
    }

    const chart = chartInstance.current

    if (loading || benchmarkLoading) {
      chart.showLoading({
        text: '加载中...',
        color: '#1890FF',
        textColor: '#F0F6FC',
        maskColor: 'rgba(13, 17, 23, 0.8)',
        zlevel: 0
      })
      return
    }

    chart.hideLoading()

    if (!dailyResults || dailyResults.length === 0) {
      chart.setOption({
        title: {
          text: '暂无性能数据',
          left: 'center',
          top: 'middle',
          textStyle: {
            color: '#8B949E',
            fontSize: 16
          }
        },
        backgroundColor: '#161B22'
      })
      return
    }

    // 准备数据
    const dates = dailyResults.map(item => item.date)
    const returnRatios = dailyResults.map(item => item.returnRatio)
    const drawdowns = dailyResults.map(item => -item.drawdown)
    const dailyPnl = dailyResults.map(item => item.netPnl)
    const winLossRatios = dailyResults.map(item => item.winLossRatio)

    // 匹配标的数据
    let matchedBenchmarkReturns: number[] = []
    if (benchmarkData.length > 0) {
      matchedBenchmarkReturns = dates.map(date => {
        const benchmark = benchmarkData.find(b => b.date === date)
        return benchmark ? benchmark.benchmarkReturn : null
      }).filter(val => val !== null) as number[]
      
      // 如果数据长度不匹配，使用插值或截取
      if (matchedBenchmarkReturns.length !== dates.length) {
        matchedBenchmarkReturns = dates.map((date, index) => {
          const benchmark = benchmarkData.find(b => b.date === date)
          if (benchmark) {
            return benchmark.benchmarkReturn
          }
          // 前向填充
          if (index > 0 && matchedBenchmarkReturns[index - 1] !== undefined) {
            return matchedBenchmarkReturns[index - 1]
          }
          return 0
        })
      }
    }

    // 构建图例数据
    const legendData = ['策略收益率', '回撤']
    if (matchedBenchmarkReturns.length > 0) {
      legendData.splice(1, 0, `${symbol} 涨幅`)
    }
    legendData.push('每日盈亏', '盈亏天数比')

    // 配置图表选项
    const option: echarts.EChartsOption = {
      backgroundColor: '#161B22',
      title: {
        text: '策略性能分析',
        left: 'left',
        textStyle: {
          color: '#F0F6FC',
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: {
            color: '#30363D'
          }
        },
        backgroundColor: 'rgba(33, 38, 45, 0.95)',
        borderColor: '#30363D',
        textStyle: {
          color: '#F0F6FC'
        },
        formatter: function(params: any) {
          let html = `<div style="font-size: 12px;">
            <div style="margin-bottom: 8px; font-weight: bold;">${params[0].axisValue}</div>`
          
          params.forEach((param: any) => {
            const color = param.color
            const value = param.value
            let formattedValue = value
            
            if (param.seriesName.includes('收益率') || param.seriesName.includes('涨幅') || param.seriesName === '回撤') {
              formattedValue = `${value.toFixed(2)}%`
            } else if (param.seriesName === '每日盈亏') {
              formattedValue = value.toLocaleString('zh-CN', { 
                minimumFractionDigits: 0,
                maximumFractionDigits: 0 
              })
            } else if (param.seriesName === '盈亏天数比') {
              formattedValue = value.toFixed(2)
            }
            
            html += `<div style="margin: 4px 0;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${color}; border-radius: 50%; margin-right: 8px;"></span>
              <span style="color: #F0F6FC;">${param.seriesName}:</span>
              <span style="color: ${color}; font-weight: bold; margin-left: 8px;">${formattedValue}</span>
            </div>`
          })
          
          html += '</div>'
          return html
        }
      },
      legend: {
        data: legendData,
        top: 35,
        left: 'center',
        itemGap: 20,
        textStyle: {
          color: '#8B949E',
          fontSize: 12
        },
        icon: 'circle'
      },
      grid: [
        {
          left: '5%',
          right: '5%',
          top: '12%',
          height: '35%',
          containLabel: true
        },
        {
          left: '5%',
          right: '5%',
          top: '52%',
          height: '18%',
          containLabel: true
        },
        {
          left: '5%',
          right: '5%',
          top: '75%',
          bottom: '12%',
          containLabel: true
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          axisPointer: {
            type: 'shadow'
          },
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            color: '#8B949E',
            fontSize: 11,
            interval: Math.max(0, Math.floor(dates.length / 12)),
            formatter: function(value: string) {
              const date = new Date(value)
              if (dates.length > 180) {
                // 超过半年数据，只显示月份
                return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
              } else if (dates.length > 60) {
                // 超过2个月数据，显示月-日
                return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
              } else {
                // 短期数据，显示完整日期
                return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
              }
            },
            rotate: dates.length > 120 ? 45 : 0
          },
          splitLine: {
            show: false
          }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            show: false
          },
          splitLine: {
            show: false
          }
        },
        {
          type: 'category',
          gridIndex: 2,
          data: dates,
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            color: '#8B949E',
            fontSize: 11,
            interval: Math.max(0, Math.floor(dates.length / 8)),
            formatter: function(value: string) {
              const date = new Date(value)
              if (dates.length > 180) {
                return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
              } else if (dates.length > 60) {
                return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
              } else {
                return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
              }
            },
            rotate: dates.length > 120 ? 45 : 0
          },
          splitLine: {
            show: false
          }
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '收益率 (%)',
          nameTextStyle: {
            color: '#8B949E'
          },
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            color: '#8B949E',
            formatter: '{value}%'
          },
          splitLine: {
            lineStyle: {
              color: '#30363D',
              type: 'dashed'
            }
          }
        },
        {
          type: 'value',
          gridIndex: 1,
          name: '每日盈亏',
          nameTextStyle: {
            color: '#8B949E'
          },
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            color: '#8B949E',
            formatter: function(value: number) {
              return value.toLocaleString('zh-CN', { 
                notation: 'compact',
                compactDisplay: 'short'
              })
            }
          },
          splitLine: {
            lineStyle: {
              color: '#30363D',
              type: 'dashed'
            }
          }
        },
        {
          type: 'value',
          gridIndex: 2,
          name: '盈亏天数比',
          nameTextStyle: {
            color: '#8B949E'
          },
          axisLine: {
            lineStyle: {
              color: '#30363D'
            }
          },
          axisLabel: {
            color: '#8B949E',
            formatter: '{value}'
          },
          splitLine: {
            lineStyle: {
              color: '#30363D',
              type: 'dashed'
            }
          }
        }
      ],
      series: (() => {
        const seriesData: any[] = [
          {
            name: '策略收益率',
            type: 'line',
            data: returnRatios,
            smooth: true,
            lineStyle: {
              width: 3,
              color: '#00D4AA'
            },
            itemStyle: {
              color: '#00D4AA'
            },
            symbol: 'none',
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(0, 212, 170, 0.25)' },
                  { offset: 1, color: 'rgba(0, 212, 170, 0.03)' }
                ]
              }
            }
          }
        ]

        // 添加标的涨幅曲线（如果有数据）
        if (matchedBenchmarkReturns.length > 0) {
                     seriesData.push({
            name: `${symbol} 涨幅`,
            type: 'line',
            data: matchedBenchmarkReturns,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#40A9FF',
              type: 'dashed'
            },
            itemStyle: {
              color: '#40A9FF'
            },
            symbol: 'none'
          })
        }

        // 添加其他系列
        seriesData.push(
          {
            name: '回撤',
            type: 'line',
            data: drawdowns,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#FF6B6B'
            },
            itemStyle: {
              color: '#FF6B6B'
            },
            symbol: 'none',
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(255, 107, 107, 0.2)' },
                  { offset: 1, color: 'rgba(255, 107, 107, 0.03)' }
                ]
              }
            }
          },
          {
            name: '每日盈亏',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: dailyPnl.map(value => ({
              value,
              itemStyle: {
                color: value >= 0 ? '#00D4AA' : '#FF6B6B',
                opacity: 0.8
              }
            })),
            barWidth: '50%'
          },
          {
            name: '盈亏天数比',
            type: 'line',
            xAxisIndex: 2,
            yAxisIndex: 2,
            data: winLossRatios,
            smooth: true,
            lineStyle: {
              width: 2,
              color: '#FFA940'
            },
            itemStyle: {
              color: '#FFA940'
            },
            symbol: 'circle',
            symbolSize: 3,
            markLine: {
              data: [
                {
                  yAxis: 1,
                  lineStyle: {
                    color: '#FFA940',
                    type: 'dashed',
                    opacity: 0.6
                  },
                  label: {
                    formatter: '平衡线 (1.0)',
                    color: '#8B949E',
                    fontSize: 10
                  }
                }
              ]
            }
          }
        )

        return seriesData
      })(),
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1, 2],
          start: Math.max(0, 100 - (100 / dailyResults.length) * Math.min(120, dailyResults.length)),
          end: 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true
        },
        {
          type: 'slider',
          xAxisIndex: [0, 1, 2],
          start: Math.max(0, 100 - (100 / dailyResults.length) * Math.min(120, dailyResults.length)),
          end: 100,
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
      ]
    }

    chart.setOption(option, true)

    // 处理窗口大小变化
    const handleResize = () => {
      chart.resize()
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dailyResults, benchmarkData, loading, benchmarkLoading])

  // 清理图表实例
  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose()
        chartInstance.current = null
      }
    }
  }, [])

  return <ChartContainer ref={chartRef} />
} 