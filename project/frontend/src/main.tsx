import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import './styles.css'

const root = document.getElementById('root')

if (!root) {
  document.body.innerHTML = '<main class="fatal-error-screen"><div class="fatal-error-card"><h1>edict三省无法初始化</h1><p>找不到 renderer 根节点，请重新安装或重新启动应用。</p></div></main>'
} else {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <ErrorBoundary><App /></ErrorBoundary>
    </React.StrictMode>,
  )
}
