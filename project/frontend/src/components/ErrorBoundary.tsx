import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[Edict renderer]', error, info.componentStack)
  }

  private recover = (): void => {
    this.setState({ error: null })
  }

  render(): ReactNode {
    if (!this.state.error) return this.props.children
    return (
      <main className="fatal-error-screen" role="alert">
        <div className="fatal-error-card">
          <div className="fatal-error-icon"><AlertTriangle size={24} /></div>
          <p className="eyebrow">RENDERER ERROR</p>
          <h1>页面暂时无法显示</h1>
          <p>渲染器遇到未处理异常，桌面壳仍在运行。可以先重试当前页面；若持续发生，请重新启动应用。</p>
          <code>{this.state.error.message || '未知渲染错误'}</code>
          <button type="button" className="primary-button" onClick={this.recover}><RefreshCw size={16} />重试页面</button>
        </div>
      </main>
    )
  }
}
