import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// 获取根元素
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
)

// 渲染应用
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
) 