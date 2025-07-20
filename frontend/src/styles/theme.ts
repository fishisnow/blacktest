export const futuTheme = {
  colors: {
    // 主背景色 - 富途深色背景
    background: '#0D1117',
    backgroundSecondary: '#161B22',
    backgroundTertiary: '#21262D',
    
    // 边框和分割线
    border: '#30363D',
    borderSecondary: '#21262D',
    
    // 文字颜色
    textPrimary: '#F0F6FC',
    textSecondary: '#8B949E',
    textTertiary: '#6E7681',
    
    // 富途特色金融颜色
    futuGreen: '#00C853',      // 上涨/盈利
    futuRed: '#FF4444',        // 下跌/亏损
    futuBlue: '#1890FF',       // 主要操作
    futuOrange: '#FF9500',     // 警告/中性
    futuPurple: '#722ED1',     // 紫色指标
    
    // 状态颜色
    success: '#52C41A',
    warning: '#FAAD14',
    error: '#FF4D4F',
    info: '#1890FF',
    
    // 卡片和面板
    cardBackground: '#161B22',
    panelBackground: '#0D1117',
    
    // 按钮
    buttonPrimary: '#238636',
    buttonSecondary: '#21262D',
    buttonHover: '#2F81F7',
    
    // 表格
    tableHeader: '#21262D',
    tableRow: '#0D1117',
    tableRowHover: '#161B22',
    
    // 图表背景
    chartBackground: '#0D1117',
    gridColor: '#30363D',
    
    // 工具提示
    tooltipBackground: 'rgba(33, 38, 45, 0.95)',
    tooltipBorder: '#30363D',
  },
  
  // ECharts 主题配置
  echartsTheme: {
    backgroundColor: '#0D1117',
    textStyle: {
      color: '#F0F6FC',
      fontSize: 12,
    },
    title: {
      textStyle: {
        color: '#F0F6FC',
        fontSize: 16,
        fontWeight: 'bold',
      },
    },
    legend: {
      textStyle: {
        color: '#8B949E',
      },
    },
    grid: {
      borderColor: '#30363D',
    },
    categoryAxis: {
      axisLine: {
        lineStyle: {
          color: '#30363D',
        },
      },
      axisLabel: {
        color: '#8B949E',
      },
      splitLine: {
        lineStyle: {
          color: '#21262D',
        },
      },
    },
    valueAxis: {
      axisLine: {
        lineStyle: {
          color: '#30363D',
        },
      },
      axisLabel: {
        color: '#8B949E',
      },
      splitLine: {
        lineStyle: {
          color: '#21262D',
        },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(33, 38, 45, 0.95)',
      borderColor: '#30363D',
      textStyle: {
        color: '#F0F6FC',
      },
    },
    dataZoom: {
      backgroundColor: '#21262D',
      borderColor: '#30363D',
      textStyle: {
        color: '#8B949E',
      },
    },
  },
  
  // 布局尺寸
  layout: {
    headerHeight: '60px',
    sidebarWidth: '380px',  // 从320px增加到380px，为参数面板提供更多空间
    footerHeight: '300px',
    borderRadius: '6px',    // 从8px减少到6px，减少视觉噪音
    padding: '12px',        // 从16px减少到12px，节省空间
    margin: '6px',          // 从8px减少到6px，节省空间
  },
  
  // 动画
  animation: {
    duration: '0.2s',
    easing: 'ease-in-out',
  },
  
  // 字体
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontSize: {
      xs: '12px',
      sm: '14px',
      md: '16px',
      lg: '18px',
      xl: '20px',
      xxl: '24px',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  // 阴影
  shadows: {
    small: '0 1px 3px rgba(0, 0, 0, 0.3)',
    medium: '0 4px 6px rgba(0, 0, 0, 0.3)',
    large: '0 8px 15px rgba(0, 0, 0, 0.3)',
  },
  
  // Z-index层级
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
}

export type FutuTheme = typeof futuTheme

// K线图特殊颜色配置
export const candlestickColors = {
  up: {
    color: futuTheme.colors.futuGreen,
    borderColor: futuTheme.colors.futuGreen,
  },
  down: {
    color: futuTheme.colors.futuRed,
    borderColor: futuTheme.colors.futuRed,
  },
}

// 常用图表颜色序列
export const chartColorPalette = [
  futuTheme.colors.futuBlue,
  futuTheme.colors.futuGreen,
  futuTheme.colors.futuOrange,
  futuTheme.colors.futuPurple,
  futuTheme.colors.futuRed,
  '#FF6B9D',
  '#45B7D1',
  '#96CEB4',
  '#FFEAA7',
  '#DDA0DD',
] 