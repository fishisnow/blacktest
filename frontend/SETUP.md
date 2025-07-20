# 富途风格回测系统 - 快速设置指南

## 🚀 一键快速启动

### 前提条件
- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 快速运行命令

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装所有依赖
npm install

# 3. 启动开发服务器
npm start
```

访问 http://localhost:3000 即可查看应用！

## 📦 依赖安装详情

如果遇到安装问题，可以分步骤安装：

### 核心依赖
```bash
# React 相关
npm install react@18.2.0 react-dom@18.2.0

# TypeScript 相关
npm install typescript@4.9.5
npm install @types/react@18.2.42 @types/react-dom@18.2.17 @types/node@16.18.68

# 路由
npm install react-router-dom@6.20.1

# 样式相关
npm install styled-components@6.1.6
npm install @types/styled-components@5.1.34

# 图表相关
npm install echarts@5.4.3 echarts-for-react@3.0.2

# HTTP 客户端
npm install axios@1.6.2

# UI 组件库
npm install antd@5.12.8

# 日期处理
npm install dayjs@1.11.10

# React Scripts
npm install react-scripts@5.0.1
```

### 开发依赖
```bash
# 测试相关
npm install --save-dev @testing-library/jest-dom@5.17.0
npm install --save-dev @testing-library/react@13.4.0
npm install --save-dev @testing-library/user-event@14.5.2
npm install --save-dev @types/jest@27.5.2

# 工具
npm install --save-dev web-vitals@2.1.4
```

## 🛠 开发环境配置

### 1. 环境变量设置

创建 `.env` 文件（在 frontend/ 目录下）：

```bash
# API 后端地址
REACT_APP_API_URL=http://localhost:8000/api

# 应用环境
REACT_APP_ENV=development

# 是否启用调试模式
REACT_APP_DEBUG=true

# 应用版本
REACT_APP_VERSION=1.0.0
```

### 2. VSCode 配置（推荐）

创建 `.vscode/settings.json`：

```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "emmet.includeLanguages": {
    "typescript": "html"
  }
}
```

### 3. 代码格式化配置

创建 `.prettierrc`：

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

## 🎯 功能验证清单

启动应用后，检查以下功能是否正常：

### 基础功能
- [ ] 页面正常加载，显示富途暗黑主题
- [ ] 顶部导航栏显示正常
- [ ] 左侧参数设置面板可展开收起
- [ ] 股票搜索功能工作正常

### 图表功能
- [ ] K线图正常显示
- [ ] 图表支持缩放和平移
- [ ] 十字准线和tooltip正常工作
- [ ] 移动平均线可切换显示

### 回测功能
- [ ] 参数设置面板交互正常
- [ ] 回测按钮可点击
- [ ] 模拟回测结果正常显示
- [ ] 收益曲线图正常绘制

### 响应式设计
- [ ] 不同屏幕尺寸下布局正常
- [ ] 高分辨率显示器显示清晰
- [ ] 移动端基本可用

## 🔧 常见问题解决

### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :3000

# 使用其他端口启动
PORT=3001 npm start
```

### 2. 依赖版本冲突
```bash
# 清除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 3. TypeScript 编译错误
```bash
# 检查 TypeScript 配置
npx tsc --noEmit

# 重启 TypeScript 服务
# 在 VSCode 中：Ctrl+Shift+P -> "TypeScript: Restart TS Server"
```

### 4. ECharts 图表不显示
- 检查浏览器控制台是否有 JavaScript 错误
- 确认容器尺寸设置正确
- 检查数据格式是否符合 ECharts 要求

### 5. 样式显示异常
```bash
# 清除浏览器缓存
# Chrome: Ctrl+Shift+Delete

# 检查样式文件是否正确加载
# 浏览器开发者工具 -> Network 面板
```

## 📁 项目结构说明

```
frontend/
├── public/                 # 静态资源
│   ├── index.html         # HTML 模板
│   └── favicon.ico        # 网站图标
├── src/
│   ├── components/        # React 组件
│   │   ├── Charts/       # 图表组件
│   │   ├── Navigation/   # 导航组件
│   │   ├── Panels/       # 面板组件
│   │   └── Tables/       # 表格组件
│   ├── pages/            # 页面组件
│   ├── services/         # API 服务
│   ├── styles/           # 样式和主题
│   ├── types/            # TypeScript 类型
│   ├── utils/            # 工具函数
│   ├── App.tsx           # 主应用组件
│   └── index.tsx         # 应用入口
├── package.json          # 项目配置
├── tsconfig.json        # TypeScript 配置
└── README.md            # 项目文档
```

## 🔗 相关命令

```bash
# 开发相关
npm start              # 启动开发服务器
npm run build          # 构建生产版本
npm test               # 运行测试
npm run eject          # 弹出 CRA 配置（不可逆）

# 代码检查
npm run lint           # ESLint 检查（需要配置）
npm run format         # Prettier 格式化（需要配置）

# 依赖相关
npm install            # 安装依赖
npm update             # 更新依赖
npm audit              # 安全审计
npm audit fix          # 修复安全问题
```

## 🚦 下一步

1. **连接后端**：修改 `src/services/BacktestService.ts` 中的 API 地址
2. **数据对接**：根据实际后端接口调整数据格式
3. **功能扩展**：添加更多策略类型和指标
4. **性能优化**：使用 React.memo、useMemo 等优化性能
5. **测试编写**：添加单元测试和集成测试

## 💡 开发建议

- 使用 React DevTools 浏览器扩展进行调试
- 充分利用 TypeScript 的类型检查
- 遵循 React Hooks 最佳实践
- 保持组件的单一职责原则
- 合理使用 styled-components 的主题功能

---

如果遇到问题，请检查：
1. Node.js 版本是否符合要求
2. 依赖是否完全安装
3. 浏览器控制台是否有错误信息
4. 网络连接是否正常

**享受开发过程！** 🎉 