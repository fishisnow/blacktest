import styled, { createGlobalStyle, css } from 'styled-components'
import { futuTheme } from './theme'

export const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  body {
    background: ${futuTheme.colors.background};
    color: ${futuTheme.colors.textPrimary};
    font-family: ${futuTheme.typography.fontFamily};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow: hidden;
  }

  button {
    font-family: ${futuTheme.typography.fontFamily};
  }
`

export const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
`

export const MainContent = styled.main`
  display: flex;
  flex: 1;
  min-height: 0;
  padding: 16px;
  gap: 16px;
  height: calc(100vh - ${futuTheme.layout.headerHeight});
  overflow: hidden;
`

export const ContentArea = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 16px;
  overflow-y: auto;
  padding-right: 16px;
  height: 100%;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: ${futuTheme.colors.backgroundSecondary};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${futuTheme.colors.border};
    border-radius: 4px;
    
    &:hover {
      background: ${futuTheme.colors.borderSecondary};
    }
  }
`

export const Card = styled.div`
  background: ${futuTheme.colors.cardBackground};
  border: 1px solid ${futuTheme.colors.border};
  border-radius: ${futuTheme.layout.borderRadius};
  overflow: hidden;
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