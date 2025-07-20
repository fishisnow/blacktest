import styled, { createGlobalStyle, css } from 'styled-components'
import { futuTheme } from './theme'

export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    font-family: ${futuTheme.typography.fontFamily};
    font-size: ${futuTheme.typography.fontSize.sm};
    color: ${futuTheme.colors.textPrimary};
    background-color: ${futuTheme.colors.background};
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
  }

  #root {
    min-height: 100vh;
    width: 100%;
  }

  /* 滚动条样式 - 富途风格 */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: ${futuTheme.colors.backgroundSecondary};
  }

  ::-webkit-scrollbar-thumb {
    background: ${futuTheme.colors.border};
    border-radius: 4px;
    transition: background 0.2s ease;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${futuTheme.colors.textTertiary};
  }

  /* 选中文本样式 */
  ::selection {
    background-color: ${futuTheme.colors.futuBlue}40;
    color: ${futuTheme.colors.textPrimary};
  }

  /* 通用按钮样式 */
  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    outline: none;
    transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};
  }

  /* 输入框样式 */
  input, select, textarea {
    font-family: inherit;
    color: ${futuTheme.colors.textPrimary};
    background-color: ${futuTheme.colors.backgroundSecondary};
    border: 1px solid ${futuTheme.colors.border};
    outline: none;
    transition: border-color ${futuTheme.animation.duration} ${futuTheme.animation.easing};
  }

  input:focus, select:focus, textarea:focus {
    border-color: ${futuTheme.colors.futuBlue};
  }

  /* 链接样式 */
  a {
    color: ${futuTheme.colors.futuBlue};
    text-decoration: none;
    transition: color ${futuTheme.animation.duration} ${futuTheme.animation.easing};
  }

  a:hover {
    color: ${futuTheme.colors.buttonHover};
  }

  /* 表格样式 */
  table {
    border-collapse: collapse;
    width: 100%;
  }

  th, td {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid ${futuTheme.colors.border};
  }

  th {
    background-color: ${futuTheme.colors.tableHeader};
    font-weight: ${futuTheme.typography.fontWeight.medium};
    color: ${futuTheme.colors.textSecondary};
  }

  tr:hover {
    background-color: ${futuTheme.colors.tableRowHover};
  }

  /* 自定义富途组件样式类 */
  .futu-card {
    background-color: ${futuTheme.colors.cardBackground};
    border: 1px solid ${futuTheme.colors.border};
    border-radius: ${futuTheme.layout.borderRadius};
    padding: ${futuTheme.layout.padding};
    box-shadow: ${futuTheme.shadows.small};
  }

  .futu-panel {
    background-color: ${futuTheme.colors.panelBackground};
    border: 1px solid ${futuTheme.colors.border};
    border-radius: ${futuTheme.layout.borderRadius};
  }

  /* 金融数据颜色类 */
  .price-up {
    color: ${futuTheme.colors.futuGreen} !important;
  }

  .price-down {
    color: ${futuTheme.colors.futuRed} !important;
  }

  .price-neutral {
    color: ${futuTheme.colors.textSecondary} !important;
  }

  /* 响应式断点 */
  @media (max-width: 1920px) {
    html {
      font-size: 14px;
    }
  }

  @media (max-width: 1440px) {
    html {
      font-size: 13px;
    }
  }

  @media (max-width: 1200px) {
    html {
      font-size: 12px;
    }
  }

  /* 高分辨率显示器优化 */
  @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx) {
    * {
      -webkit-font-smoothing: subpixel-antialiased;
    }
  }
`

// 布局容器组件
export const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: ${futuTheme.colors.background};
`

export const MainContent = styled.div`
  display: flex;
  flex: 1;
  min-height: 0; /* 允许flex子项缩小 */
`

export const ContentArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: ${futuTheme.layout.margin};
  gap: ${futuTheme.layout.margin};
`

// 通用卡片组件
export const Card = styled.div<{ padding?: string; margin?: string; border?: boolean }>`
  background-color: ${futuTheme.colors.cardBackground};
  border: 1px solid ${({ border = true }) => border ? futuTheme.colors.border : 'transparent'};
  border-radius: ${futuTheme.layout.borderRadius};
  padding: ${({ padding = futuTheme.layout.padding }) => padding};
  margin: ${({ margin = '0' }) => margin};
  box-shadow: ${futuTheme.shadows.small};
  transition: box-shadow ${futuTheme.animation.duration} ${futuTheme.animation.easing};

  &:hover {
    box-shadow: ${futuTheme.shadows.medium};
  }
`

// 通用按钮组件
export const Button = styled.button<{ 
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
}>`
  padding: ${({ size = 'medium' }) => {
    switch (size) {
      case 'small': return '6px 12px'
      case 'large': return '12px 24px'
      default: return '8px 16px'
    }
  }};
  
  font-size: ${({ size = 'medium' }) => {
    switch (size) {
      case 'small': return futuTheme.typography.fontSize.xs
      case 'large': return futuTheme.typography.fontSize.md
      default: return futuTheme.typography.fontSize.sm
    }
  }};
  
  font-weight: ${futuTheme.typography.fontWeight.medium};
  border-radius: ${futuTheme.layout.borderRadius};
  cursor: pointer;
  border: 1px solid;
  transition: all ${futuTheme.animation.duration} ${futuTheme.animation.easing};
  white-space: nowrap;
  width: ${({ fullWidth }) => fullWidth ? '100%' : 'auto'};

  ${({ variant = 'primary' }) => {
    switch (variant) {
      case 'primary':
        return css`
          background-color: ${futuTheme.colors.futuBlue};
          border-color: ${futuTheme.colors.futuBlue};
          color: ${futuTheme.colors.textPrimary};
          
          &:hover:not(:disabled) {
            background-color: ${futuTheme.colors.buttonHover};
            border-color: ${futuTheme.colors.buttonHover};
          }
        `
      case 'secondary':
        return css`
          background-color: ${futuTheme.colors.buttonSecondary};
          border-color: ${futuTheme.colors.border};
          color: ${futuTheme.colors.textPrimary};
          
          &:hover:not(:disabled) {
            background-color: ${futuTheme.colors.backgroundTertiary};
            border-color: ${futuTheme.colors.textTertiary};
          }
        `
      case 'success':
        return css`
          background-color: ${futuTheme.colors.futuGreen};
          border-color: ${futuTheme.colors.futuGreen};
          color: ${futuTheme.colors.textPrimary};
          
          &:hover:not(:disabled) {
            opacity: 0.8;
          }
        `
      case 'warning':
        return css`
          background-color: ${futuTheme.colors.futuOrange};
          border-color: ${futuTheme.colors.futuOrange};
          color: ${futuTheme.colors.textPrimary};
          
          &:hover:not(:disabled) {
            opacity: 0.8;
          }
        `
      case 'error':
        return css`
          background-color: ${futuTheme.colors.futuRed};
          border-color: ${futuTheme.colors.futuRed};
          color: ${futuTheme.colors.textPrimary};
          
          &:hover:not(:disabled) {
            opacity: 0.8;
          }
        `
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:active:not(:disabled) {
    transform: translateY(1px);
  }
`

// 金融数据显示组件
export const PriceText = styled.span<{ value: number; compareValue?: number }>`
  font-weight: ${futuTheme.typography.fontWeight.medium};
  color: ${({ value, compareValue = 0 }) => {
    if (value > compareValue) return futuTheme.colors.futuGreen
    if (value < compareValue) return futuTheme.colors.futuRed
    return futuTheme.colors.textSecondary
  }};
`

// 加载状态组件
export const LoadingSpinner = styled.div`
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid ${futuTheme.colors.border};
  border-radius: 50%;
  border-top-color: ${futuTheme.colors.futuBlue};
  animation: spin 1s ease-in-out infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
` 