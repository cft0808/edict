import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { App } from './App'

/**
 * The desktop renderer must still produce a useful first frame while the
 * sidecar is starting (or unavailable). These checks intentionally use SSR so
 * they run in Vitest's default Node environment without a browser dependency.
 */
describe('desktop first-frame contract', () => {
  it('renders a non-empty shell with primary navigation and settings entry', () => {
    const html = renderToStaticMarkup(<App />)

    expect(html.length).toBeGreaterThan(200)
    expect(html).toContain('data-testid="nav-workbench"')
    expect(html).toContain('data-testid="nav-execution"')
    expect(html).toContain('data-testid="nav-settings"')
    expect(html).toContain('data-testid="nav-reference"')
    expect(html).toContain('data-testid="nav-reference-edicts"')
    expect(html).toContain('data-testid="nav-reference-morning"')
    expect(html).toContain('旨意看板')
    expect(html).toContain('朝堂议政')
    expect(html).toContain('省部调度')
    expect(html).toContain('官员总览')
    expect(html).toContain('模型配置')
    expect(html).toContain('技能配置')
    expect(html).toContain('小任务')
    expect(html).toContain('奏折阁')
    expect(html).toContain('旨库')
    expect(html).toContain('天下要闻')
    expect(html).toContain('edict三省')
    expect(html).not.toContain('undefined')
  })

  it('keeps the task submission affordance in the initial frame', () => {
    const html = renderToStaticMarkup(<App />)

    expect(html).toContain('data-testid="task-submit"')
    expect(html).toMatch(/<input[^>]+(task|title)/i)
  })
})
