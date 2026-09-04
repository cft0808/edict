import { FormEvent, ReactNode, useCallback, useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  BookOpen,
  Bot,
  Brain,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Cloud,
  Command,
  Database,
  Gauge,
  Globe2,
  Hammer,
  History,
  Loader2,
  Menu,
  MessageSquareText,
  MoreHorizontal,
  Network,
  Pause,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Server,
  Settings2,
  ShieldCheck,
  Sparkles,
  Square,
  TerminalSquare,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Unplug,
  Wifi,
  WifiOff,
  X,
  Zap,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import ReferenceWorkspace, { MODULES, type ReferenceModule } from './components/ReferenceWorkspace'

type TaskStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | string

type Task = {
  id: string
  title: string
  status: TaskStatus
  created_at: string
  description?: string
  agent?: string
  thinking?: string
  network?: string
  updated_at?: string
}

type Status = {
  state: string
  taskCount: number
  tasks: Task[]
  transport: string
  activeCount?: number
  completedCount?: number
}

type Health = {
  ok: boolean
  service: string
  protocolVersion: string
  transport: string
}

type Provider = 'local' | 'legacy' | 'fastapi'
type ThinkingMode = 'fast' | 'balanced' | 'deep'
type NetworkPolicy = 'off' | 'ask' | 'on'

type McpServer = {
  id: string
  name: string
  url: string
  enabled?: boolean
}

type Settings = import('./types/domain').Settings

type SettingsResponse = { settings?: Partial<Settings>; available?: AvailableMetadata }

type AvailableMetadata = {
  agents?: Array<{ id: string; label?: string; description?: string }>
  skills?: Array<{ id: string; label?: string; description?: string; available?: boolean }>
  models?: Array<{ id: string; label?: string }>
}

type EventRecord = {
  id: string
  taskId?: string
  name: string
  label: string
  detail?: string
  timestamp: string
  kind: 'info' | 'success' | 'warning' | 'error'
}

type View = 'workbench' | 'execution' | 'settings' | 'reference'
type SettingsSection = 'runtime' | 'agents' | 'skills' | 'mcp' | 'connection'
type TaskFilter = 'all' | 'active' | 'completed' | 'failed'

const DEFAULT_SETTINGS: Settings = {
  backend: { provider: 'local', baseUrl: 'http://127.0.0.1:7891' },
  agent: { defaultAgent: 'general', allowedAgents: ['general'], model: 'auto' },
  thinking: { mode: 'balanced' },
  network: { policy: 'ask' },
  skills: { enabledSkillIds: [] },
  mcp: { enabled: false, servers: [] },
}

const DEFAULT_AVAILABLE: Required<AvailableMetadata> = {
  agents: [
    { id: 'general', label: '通用 Agent', description: '适合日常编排和综合任务' },
    { id: 'research', label: '研究 Agent', description: '适合资料梳理和事实核验' },
    { id: 'coding', label: '编码 Agent', description: '适合实现、调试和验证' },
  ],
  skills: [
    { id: 'planning', label: '任务规划', description: '把目标拆成可执行步骤', available: true },
    { id: 'code-review', label: '代码审查', description: '检查风险、回归和测试缺口', available: true },
    { id: 'doc-writer', label: '文档编写', description: '整理说明、报告和交付文档', available: true },
    { id: 'web-research', label: '联网检索', description: '需要联网策略开启后才能使用', available: false },
  ],
  models: [
    { id: 'auto', label: '自动选择' },
    { id: 'balanced', label: '平衡模型' },
    { id: 'fast', label: '快速模型' },
  ],
}

const STORAGE_KEY = 'edict.desktop.settings.v1'

const NAV_ITEMS: Array<{ id: View; label: string; hint: string; icon: LucideIcon }> = [
  { id: 'workbench', label: '工作台', hint: '任务总览', icon: Command },
  { id: 'execution', label: '执行中心', hint: '实时进程', icon: Activity },
  { id: 'settings', label: '设置', hint: '运行偏好', icon: Settings2 },
]

const SETTINGS_ITEMS: Array<{ id: SettingsSection; label: string; description: string; icon: LucideIcon }> = [
  { id: 'runtime', label: '执行偏好', description: '思考与联网', icon: Gauge },
  { id: 'agents', label: 'Agents', description: '角色与模型', icon: Bot },
  { id: 'skills', label: 'Skills', description: '能力开关', icon: Sparkles },
  { id: 'mcp', label: 'MCP', description: '工具服务器', icon: Network },
  { id: 'connection', label: '后端连接', description: 'Provider 与地址', icon: Server },
]

const statusLabel = (status: TaskStatus): string => {
  switch (status) {
    case 'queued': return '排队中'
    case 'running': return '执行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return status || '未知'
  }
}

const statusTone = (status: TaskStatus): string => {
  if (status === 'completed') return 'success'
  if (status === 'failed' || status === 'cancelled') return 'danger'
  if (status === 'running') return 'running'
  return 'queued'
}

const isActiveTask = (task: Task): boolean => task.status === 'queued' || task.status === 'running'

const formatTime = (value?: string): string => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const mergeSettings = (value: unknown): Settings => {
  const input = (value && typeof value === 'object' ? value : {}) as Partial<Settings>
  const backend = (input.backend ?? {}) as Partial<Settings['backend']>
  const agent = (input.agent ?? {}) as Partial<Settings['agent']>
  const thinking = (input.thinking ?? {}) as Partial<Settings['thinking']>
  const network = (input.network ?? {}) as Partial<Settings['network']>
  const skills = (input.skills ?? {}) as Partial<Settings['skills']>
  const mcp = (input.mcp ?? {}) as Partial<Settings['mcp']>
  const provider = backend.provider === 'legacy' || backend.provider === 'fastapi' ? backend.provider : DEFAULT_SETTINGS.backend.provider
  const mode = thinking.mode === 'fast' || thinking.mode === 'deep' ? thinking.mode : DEFAULT_SETTINGS.thinking.mode
  const policy = network.policy === 'off' || network.policy === 'on' ? network.policy : DEFAULT_SETTINGS.network.policy
  const allowedAgents = Array.isArray(agent.allowedAgents) ? agent.allowedAgents.filter((item): item is string => typeof item === 'string' && item.length > 0) : DEFAULT_SETTINGS.agent.allowedAgents
  const servers = Array.isArray(mcp.servers)
    ? mcp.servers
      .filter((item): item is McpServer => Boolean(item && typeof item === 'object'))
      .map((item, index) => ({
        id: typeof item.id === 'string' && item.id ? item.id : `server-${index + 1}`,
        name: typeof item.name === 'string' ? item.name : `MCP Server ${index + 1}`,
        url: typeof item.url === 'string' ? item.url : '',
        enabled: item.enabled !== false,
      }))
    : DEFAULT_SETTINGS.mcp.servers
  return {
    backend: {
      provider,
      baseUrl: typeof backend.baseUrl === 'string' && backend.baseUrl ? backend.baseUrl : DEFAULT_SETTINGS.backend.baseUrl,
    },
    agent: {
      defaultAgent: typeof agent.defaultAgent === 'string' && agent.defaultAgent ? agent.defaultAgent : DEFAULT_SETTINGS.agent.defaultAgent,
      allowedAgents: allowedAgents.length ? allowedAgents : DEFAULT_SETTINGS.agent.allowedAgents,
      model: typeof agent.model === 'string' && agent.model ? agent.model : DEFAULT_SETTINGS.agent.model,
    },
    thinking: { mode },
    network: { policy },
    skills: {
      enabledSkillIds: Array.isArray(skills.enabledSkillIds)
        ? skills.enabledSkillIds.filter((item): item is string => typeof item === 'string')
        : DEFAULT_SETTINGS.skills.enabledSkillIds,
    },
    mcp: { enabled: mcp.enabled === true, servers },
  }
}

const readStoredSettings = (): Settings => {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value ? mergeSettings(JSON.parse(value)) : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

const persistSettings = (settings: Settings): void => {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // Storage is optional in the Electron shell; sidecar remains the source of truth.
  }
}

const eventLabel = (name: string): { label: string; kind: EventRecord['kind'] } => {
  if (name.includes('error') || name.includes('failed')) return { label: '执行出现错误', kind: 'error' }
  if (name.includes('completed') || name.includes('succeeded')) return { label: '阶段已完成', kind: 'success' }
  if (name.includes('warning')) return { label: '需要注意', kind: 'warning' }
  if (name === 'task.created') return { label: '任务已创建', kind: 'info' }
  if (name.startsWith('execution.')) return { label: name.replace('execution.', '执行：'), kind: 'info' }
  return { label: name || '状态更新', kind: 'info' }
}

function StatusBadge({ status }: { status: TaskStatus }) {
  return <span className={`status-badge ${statusTone(status)}`}><span className="status-dot" />{statusLabel(status)}</span>
}

function EmptyState({ icon: Icon, title, detail, action }: { icon: LucideIcon; title: string; detail: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={22} /></div><h3>{title}</h3><p>{detail}</p>{action}</div>
}

function LoadingState({ label = '正在加载工作区' }: { label?: string }) {
  return <div className="loading-state"><Loader2 size={20} className="spin" /><span>{label}</span></div>
}

function App() {
  const [view, setView] = useState<View>('workbench')
  const [referenceModule, setReferenceModule] = useState<ReferenceModule>('edicts')
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('runtime')
  const [health, setHealth] = useState<Health | null>(null)
  const [status, setStatus] = useState<Status | null>(null)
  const [settings, setSettings] = useState<Settings>(() => readStoredSettings())
  const [available, setAvailable] = useState<AvailableMetadata>(DEFAULT_AVAILABLE)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [taskFilter, setTaskFilter] = useState<TaskFilter>('all')
  const [events, setEvents] = useState<EventRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsDirty, setSettingsDirty] = useState(false)
  const [settingsNotice, setSettingsNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const tasks = status?.tasks ?? []
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) ?? tasks[0] ?? null
  const activeTasks = tasks.filter(isActiveTask)
  const completedTasks = tasks.filter((task) => task.status === 'completed')
  const failedTasks = tasks.filter((task) => task.status === 'failed' || task.status === 'cancelled')
  const filteredTasks = tasks.filter((task) => {
    if (taskFilter === 'active') return isActiveTask(task)
    if (taskFilter === 'completed') return task.status === 'completed'
    if (taskFilter === 'failed') return task.status === 'failed' || task.status === 'cancelled'
    return true
  })

  const request = useCallback(async (command: string, payload?: unknown): Promise<unknown> => {
    if (!window.edictDesktop) throw new Error('桌面通信组件未能加载，请重新启动应用')
    return window.edictDesktop.request(command, payload)
  }, [])

  const applyStatus = useCallback((nextStatus: Status) => {
    const nextTasks = Array.isArray(nextStatus?.tasks) ? nextStatus.tasks : []
    setStatus({
      state: nextStatus?.state ?? 'ready',
      taskCount: nextStatus?.taskCount ?? nextTasks.length,
      tasks: nextTasks,
      transport: nextStatus?.transport ?? 'stdio-jsonl',
      activeCount: nextStatus?.activeCount,
      completedCount: nextStatus?.completedCount,
    })
    setSelectedTaskId((current) => current ?? nextTasks[0]?.id ?? null)
  }, [])

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setRefreshing(true)
    try {
      const [nextHealth, nextStatus] = await Promise.all([
        request('health') as Promise<Health>,
        request('status') as Promise<Status>,
      ])
      setHealth(nextHealth)
      applyStatus(nextStatus)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '无法连接 Python sidecar')
    } finally {
      setLoading(false)
      if (!quiet) setRefreshing(false)
    }
  }, [applyStatus, request])

  const loadSettings = useCallback(async () => {
    try {
      const result = await request('settings.get') as SettingsResponse | Settings
      const payload: SettingsResponse = result && typeof result === 'object' && 'settings' in result
        ? result as SettingsResponse
        : { settings: result as Partial<Settings> }
      if (payload.available) setAvailable({ ...DEFAULT_AVAILABLE, ...payload.available })
      if (payload.settings) {
        const normalized = mergeSettings(payload.settings)
        setSettings(normalized)
        persistSettings(normalized)
        setSettingsDirty(false)
      }
    } catch {
      // Older sidecars do not expose settings yet; localStorage keeps the controls useful.
    }
  }, [request])

  useEffect(() => {
    void Promise.all([refresh(true), loadSettings()])
    if (!window.edictDesktop) {
      setError('桌面通信组件未能加载，请重新启动应用')
      setLoading(false)
      return
    }
    return window.edictDesktop.onEvent((payload) => {
      if (!payload || typeof payload !== 'object') return
      const event = payload as Record<string, unknown>
      const name = typeof event.name === 'string' ? event.name : ''
      if (name === 'status') {
        applyStatus(event as unknown as Status)
        return
      }
      if (name === 'settings.updated' && event.settings) {
        const normalized = mergeSettings(event.settings)
        setSettings(normalized)
        persistSettings(normalized)
        setSettingsDirty(false)
        setSettingsNotice('设置已同步')
        return
      }
      const taskPayload = event.task && typeof event.task === 'object' ? event.task as Task : undefined
      if (name === 'task.created' && taskPayload) {
        setSelectedTaskId(taskPayload.id)
        setEvents((current) => current.some((item) => item.name === name && item.taskId === taskPayload.id)
          ? current
          : [makeEvent(name, taskPayload.id, '任务已创建', 'info'), ...current].slice(0, 80))
        return
      }
      const taskId = typeof event.taskId === 'string' ? event.taskId : taskPayload?.id
      if (name && (taskId || name.startsWith('execution.'))) {
        const detail = typeof event.detail === 'string' ? event.detail : typeof event.message === 'string' ? event.message : undefined
        setEvents((current) => [makeEvent(name, taskId, detail), ...current].slice(0, 80))
      }
    })
  }, [applyStatus, loadSettings, refresh])

  useEffect(() => {
    if (!selectedTaskId && tasks.length) setSelectedTaskId(tasks[0].id)
  }, [selectedTaskId, tasks])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const cleanTitle = title.trim()
    if (!cleanTitle || submitting) return
    setSubmitting(true)
    try {
      const result = await request('task.submit', {
        title: cleanTitle,
        description: description.trim() || undefined,
        agent: settings.agent.defaultAgent,
        thinking: settings.thinking.mode,
        network: settings.network.policy,
        skills: settings.skills.enabledSkillIds,
        mcp: settings.mcp.enabled,
      }) as { task?: Task }
      if (result?.task) {
        setSelectedTaskId(result.task.id)
      }
      setTitle('')
      setDescription('')
      setError(null)
      await refresh(true)
      setView('execution')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '任务提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  const updateSettings = (next: Settings) => {
    setSettings(next)
    setSettingsDirty(true)
    setSettingsNotice(null)
  }

  const saveSettings = async () => {
    setSettingsSaving(true)
    setSettingsNotice(null)
    persistSettings(settings)
    try {
      const result = await request('settings.update', { settings }) as SettingsResponse
      if (result?.settings) {
        const normalized = mergeSettings(result.settings)
        setSettings(normalized)
        persistSettings(normalized)
      }
      setSettingsDirty(false)
      setSettingsNotice('设置已保存')
    } catch {
      setSettingsDirty(false)
      setSettingsNotice('已保存到本机，sidecar 尚未提供设置接口')
    } finally {
      setSettingsSaving(false)
    }
  }

  const navTo = (nextView: View) => {
    setView(nextView)
    setMobileNavOpen(false)
  }

  const navToReference = (nextModule: ReferenceModule = referenceModule) => {
    setReferenceModule(nextModule)
    setView('reference')
    setMobileNavOpen(false)
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Command size={19} /></div>
          <div><strong>edict三省</strong><span>桌面控制台</span></div>
        </div>
        <div className="workspace-switcher"><span className="workspace-avatar">E</span><span><b>本地工作区</b><small>Desktop Alpha</small></span><ChevronRight size={15} /></div>
        <nav className="main-nav" aria-label="主导航">
           {NAV_ITEMS.map(({ id, label, hint, icon: Icon }) => (
             <button key={id} type="button" className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => navTo(id)} data-testid={`nav-${id}`}>
               <Icon size={18} /><span><b>{label}</b><small>{hint}</small></span>{id === 'execution' && activeTasks.length > 0 && <em>{activeTasks.length}</em>}
             </button>
           ))}
           <div className="nav-group-label">参考看板</div>
           <button type="button" className={`nav-item reference-nav-entry ${view === 'reference' ? 'active' : ''}`} onClick={() => navToReference()} data-testid="nav-reference"><BookOpenIcon /><span><b>参考工作区</b><small>十个 Legacy 模块</small></span><ChevronRight size={15} /></button>
            <div className={`nav-subitems ${view === 'reference' ? 'visible' : ''}`}>{MODULES.map(({ id, label }) => <button type="button" key={id} className={referenceModule === id ? 'active' : ''} onClick={() => navToReference(id)} data-testid={`nav-reference-${id}`}>{label}</button>)}</div>
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-footer">
          <div className={`connection-mini ${health?.ok ? 'online' : error ? 'offline' : ''}`}><span className="connection-dot" /><span>{health?.ok ? 'Sidecar 在线' : error ? '连接异常' : '正在连接'}</span><button type="button" className="icon-button tiny" title="刷新连接" aria-label="刷新连接" onClick={() => void refresh()}><RefreshCw size={13} className={refreshing ? 'spin' : ''} /></button></div>
          <small>协议 {health?.protocolVersion ?? '—'} · {status?.transport ?? 'stdio-jsonl'}</small>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <button type="button" className="mobile-menu icon-button" title="打开导航" aria-label="打开导航" onClick={() => setMobileNavOpen((value) => !value)}><Menu size={19} /></button>
           <div className="breadcrumb"><span>edict三省</span><ChevronRight size={14} /><strong>{view === 'settings' ? '设置' : view === 'execution' ? '执行中心' : view === 'reference' ? MODULES.find((item) => item.id === referenceModule)?.label : '工作台'}</strong></div>
          <div className="topbar-actions">
            <button type="button" className="search-trigger" title="搜索任务" onClick={() => document.getElementById('task-title')?.focus()}><Search size={16} /><span>搜索任务</span><kbd>⌘ K</kbd></button>
            <span className={`top-status ${health?.ok ? 'online' : error ? 'offline' : ''}`}><span className="connection-dot" />{health?.ok ? '运行正常' : error ? '需要检查' : '连接中'}</span>
            <button type="button" className="icon-button" title="刷新状态" aria-label="刷新状态" onClick={() => void refresh()}><RefreshCw size={17} className={refreshing ? 'spin' : ''} /></button>
          </div>
        </header>

        <main className="content">
          {error && <div className="alert-banner" role="alert"><AlertCircle size={17} /><span>{error}</span><button type="button" className="text-button" onClick={() => void refresh()}>重试</button><button type="button" className="icon-button tiny" title="关闭提示" aria-label="关闭提示" onClick={() => setError(null)}><X size={14} /></button></div>}
           {view === 'workbench' && <WorkbenchView loading={loading} status={status} tasks={filteredTasks} allTasks={tasks} activeTasks={activeTasks} completedTasks={completedTasks} failedTasks={failedTasks} selectedTaskId={selectedTask?.id ?? null} taskFilter={taskFilter} title={title} description={description} submitting={submitting} settings={settings} onTitleChange={setTitle} onDescriptionChange={setDescription} onSubmit={submit} onFilterChange={setTaskFilter} onSelectTask={(task) => { setSelectedTaskId(task.id); setView('execution') }} onOpenExecution={() => navTo('execution')} onOpenSettings={() => navTo('settings')} />}
           {view === 'execution' && <ExecutionView task={selectedTask} events={events} tasks={tasks} onBack={() => navTo('workbench')} onSelectTask={setSelectedTaskId} />}
           {view === 'settings' && <SettingsView section={settingsSection} settings={settings} available={available} dirty={settingsDirty} saving={settingsSaving} notice={settingsNotice} onSectionChange={setSettingsSection} onChange={updateSettings} onSave={() => void saveSettings()} />}
           {view === 'reference' && <ReferenceWorkspace module={referenceModule} settings={settings} onModuleChange={navToReference} />}
        </main>
      </div>
    </div>
  )
}

function makeEvent(name: string, taskId?: string, detail?: string, explicitKind?: EventRecord['kind']): EventRecord {
  const descriptor = eventLabel(name)
  return { id: `${name}-${taskId ?? 'global'}-${Date.now()}-${Math.random()}`, taskId, name, label: detail || descriptor.label, detail: detail && detail !== descriptor.label ? detail : undefined, timestamp: new Date().toISOString(), kind: explicitKind ?? descriptor.kind }
}

type WorkbenchProps = {
  loading: boolean
  status: Status | null
  tasks: Task[]
  allTasks: Task[]
  activeTasks: Task[]
  completedTasks: Task[]
  failedTasks: Task[]
  selectedTaskId: string | null
  taskFilter: TaskFilter
  title: string
  description: string
  submitting: boolean
  settings: Settings
  onTitleChange: (value: string) => void
  onDescriptionChange: (value: string) => void
  onSubmit: (event: FormEvent) => void
  onFilterChange: (filter: TaskFilter) => void
  onSelectTask: (task: Task) => void
  onOpenExecution: () => void
  onOpenSettings: () => void
}

function WorkbenchView({ loading, status, tasks, allTasks, activeTasks, completedTasks, failedTasks, selectedTaskId, taskFilter, title, description, submitting, settings, onTitleChange, onDescriptionChange, onSubmit, onFilterChange, onSelectTask, onOpenExecution, onOpenSettings }: WorkbenchProps) {
  return <div className="page-stack">
    <section className="page-heading"><div><p className="eyebrow">CONTROL ROOM</p><h1>工作台</h1><p className="page-subtitle">把任务交给合适的 Agent，并持续看见执行进度。</p></div><div className="heading-actions"><span className="sync-label"><Wifi size={14} /> {status?.state === 'ready' ? '状态已同步' : '等待同步'}</span><button type="button" className="secondary-button" onClick={onOpenExecution}><Activity size={16} />执行中心</button></div></section>

    <section className="dispatch-panel panel"><div className="dispatch-copy"><div className="section-kicker"><Zap size={15} />新的任务</div><h2>下达一项任务</h2><p>从一个清晰的目标开始，执行过程会在执行中心持续更新。</p><div className="config-pills"><span><Bot size={13} />{settings.agent.defaultAgent}</span><span><Brain size={13} />{settings.thinking.mode === 'balanced' ? '平衡思考' : settings.thinking.mode === 'fast' ? '快速思考' : '深度思考'}</span><span><Globe2 size={13} />{settings.network.policy === 'off' ? '离线' : settings.network.policy === 'ask' ? '按需联网' : '允许联网'}</span></div><button type="button" className="link-button" onClick={onOpenSettings}>调整执行偏好 <ChevronRight size={14} /></button></div><form className="dispatch-form" onSubmit={onSubmit}><label htmlFor="task-title">任务标题</label><input id="task-title" value={title} onChange={(event) => onTitleChange(event.target.value)} placeholder="例如：整理一期发布清单" autoComplete="off" /><label htmlFor="task-description">补充说明 <span>可选</span></label><textarea id="task-description" value={description} onChange={(event) => onDescriptionChange(event.target.value)} placeholder="输入验收标准、上下文或希望的输出" rows={3} /><button type="submit" className="primary-button dispatch-submit" disabled={!title.trim() || submitting} data-testid="task-submit">{submitting ? <><Loader2 size={16} className="spin" />提交中</> : <><Play size={16} fill="currentColor" />开始执行</>}</button></form></section>

    <section className="metric-grid"><Metric icon={Activity} label="进行中" value={activeTasks.length} tone="blue" detail={activeTasks.length ? '需要关注' : '暂无运行任务'} /><Metric icon={CheckCircle2} label="已完成" value={completedTasks.length} tone="green" detail="本地任务记录" /><Metric icon={AlertCircle} label="异常" value={failedTasks.length} tone="orange" detail={failedTasks.length ? '需要复盘' : '运行平稳'} /><Metric icon={Bot} label="默认 Agent" value={settings.agent.defaultAgent} tone="purple" detail={settings.agent.model === 'auto' ? '自动选择模型' : settings.agent.model} compact /></section>

    <section className="panel task-panel"><div className="panel-header"><div><div className="section-kicker"><TerminalSquare size={15} />任务</div><h2>最近任务</h2></div><div className="panel-header-actions"><div className="segmented compact" role="tablist" aria-label="任务筛选">{([['all', '全部'], ['active', '进行中'], ['completed', '已完成'], ['failed', '异常']] as const).map(([value, label]) => <button type="button" key={value} className={taskFilter === value ? 'selected' : ''} onClick={() => onFilterChange(value)}>{label}{value === 'all' ? ` ${allTasks.length}` : value === 'active' ? ` ${activeTasks.length}` : value === 'completed' ? ` ${completedTasks.length}` : ` ${failedTasks.length}`}</button>)}</div></div></div>{loading ? <LoadingState label="正在加载任务" /> : tasks.length ? <div className="task-list">{tasks.map((task) => <TaskRow key={task.id} task={task} selected={task.id === selectedTaskId} onClick={() => onSelectTask(task)} />)}</div> : <EmptyState icon={MessageSquareText} title={taskFilter === 'all' ? '还没有任务' : '没有匹配任务'} detail={taskFilter === 'all' ? '提交第一项任务后，它会出现在这里。' : '切换筛选查看其他任务。'} />}</section>
  </div>
}

function Metric({ icon: Icon, label, value, tone, detail, compact = false }: { icon: LucideIcon; label: string; value: number | string; tone: string; detail: string; compact?: boolean }) {
  return <div className={`metric panel ${tone}`}><div className="metric-icon"><Icon size={17} /></div><div className="metric-body"><span>{label}</span><strong className={compact ? 'small-value' : ''}>{value}</strong><small>{detail}</small></div><MoreHorizontal size={16} className="metric-menu" /></div>
}

function TaskRow({ task, selected, onClick }: { task: Task; selected: boolean; onClick: () => void }) {
  return <button type="button" className={`task-row ${selected ? 'selected' : ''}`} onClick={onClick} data-testid={`task-card-${task.id}`}><div className={`task-leading ${statusTone(task.status)}`}><span>{task.status === 'completed' ? <Check size={16} /> : task.status === 'failed' || task.status === 'cancelled' ? <AlertCircle size={16} /> : task.status === 'running' ? <Loader2 size={16} className="spin" /> : <ClockIcon size={16} />}</span></div><div className="task-main"><strong>{task.title}</strong><span>{task.description || '暂无描述'}</span><div className="task-meta"><StatusBadge status={task.status} /><span>{task.agent || 'general'}</span><span>{formatTime(task.updated_at || task.created_at)}</span></div></div><ChevronRight size={17} className="task-chevron" /></button>
}

function ClockIcon({ size }: { size: number }) { return <History size={size} /> }

function BookOpenIcon() { return <BookOpen size={18} /> }

function ExecutionView({ task, events, tasks, onBack, onSelectTask }: { task: Task | null; events: EventRecord[]; tasks: Task[]; onBack: () => void; onSelectTask: (id: string) => void }) {
  const taskEvents = events.filter((event) => !event.taskId || event.taskId === task?.id)
  const stage = task?.status === 'completed' ? 3 : task?.status === 'running' ? 1 : task?.status === 'failed' || task?.status === 'cancelled' ? 1 : 0
  const stageItems = [{ label: '接收', icon: MessageSquareText }, { label: '执行', icon: Hammer }, { label: '校验', icon: ShieldCheck }, { label: '完成', icon: CheckCircle2 }]
  return <div className="page-stack"><section className="page-heading execution-heading"><div><button type="button" className="back-button" onClick={onBack}><ChevronRight size={15} className="back-chevron" />返回工作台</button><p className="eyebrow">LIVE RUN</p><h1>执行中心</h1><p className="page-subtitle">每一步都留在时间线上，当前状态不会被藏起来。</p></div><div className="heading-actions"><span className="live-chip"><span />LIVE</span>{task && <StatusBadge status={task.status} />}</div></section>{!task ? <section className="panel"><EmptyState icon={Activity} title="暂无执行中的任务" detail="从工作台提交一项任务，执行过程会显示在这里。" action={<button type="button" className="primary-button" onClick={onBack}><Plus size={16} />创建任务</button>} /></section> : <><section className="panel run-overview"><div className="run-title"><div className={`run-icon ${statusTone(task.status)}`}><Bot size={20} /></div><div><span className="task-id">TASK {task.id.slice(0, 8).toUpperCase()}</span><h2>{task.title}</h2><p>{task.description || '暂无任务描述'}</p></div></div><div className="run-actions"><button type="button" className="secondary-button" disabled title="当前 sidecar 尚未暴露暂停命令"><Pause size={15} />暂停</button><button type="button" className="danger-button" disabled title="当前 sidecar 尚未暴露取消命令"><Square size={14} fill="currentColor" />取消</button></div></section><section className="stage-rail panel">{stageItems.map(({ label, icon: Icon }, index) => <div key={label} className={`stage ${index < stage ? 'done' : index === stage ? 'current' : ''}`}><div className="stage-icon">{index < stage ? <Check size={15} /> : <Icon size={15} />}</div><span>{label}</span>{index < stageItems.length - 1 && <div className="stage-line" />}</div>)}</section><div className="execution-grid"><section className="panel timeline-panel"><div className="panel-header"><div><div className="section-kicker"><Activity size={15} />实时动态</div><h2>执行时间线</h2></div><span className="muted-count">{taskEvents.length} 条记录</span></div>{taskEvents.length ? <div className="timeline">{taskEvents.map((event) => <TimelineItem key={event.id} event={event} />)}</div> : <EmptyState icon={Loader2} title="等待执行事件" detail="任务已进入 sidecar，运行时事件接入后会持续更新。" />}</section><aside className="execution-sidebar"><section className="panel run-summary"><div className="panel-header"><div><div className="section-kicker"><Database size={15} />运行信息</div><h2>当前配置</h2></div></div><dl><div><dt>Agent</dt><dd>{task.agent || 'general'}</dd></div><div><dt>思考模式</dt><dd>{task.thinking || 'balanced'}</dd></div><div><dt>联网策略</dt><dd>{task.network || 'ask'}</dd></div><div><dt>创建时间</dt><dd>{formatTime(task.created_at)}</dd></div></dl></section><section className="panel queue-panel"><div className="panel-header"><div><div className="section-kicker"><History size={15} />任务队列</div><h2>其他任务</h2></div></div>{tasks.length > 1 ? <div className="queue-list">{tasks.filter((item) => item.id !== task.id).slice(0, 5).map((item) => <button type="button" key={item.id} onClick={() => onSelectTask(item.id)}><span className={`queue-dot ${statusTone(item.status)}`} /><span>{item.title}</span><StatusBadge status={item.status} /></button>)}</div> : <p className="panel-note">暂无其他任务</p>}</section></aside></div></>}</div>
}

function TimelineItem({ event }: { event: EventRecord }) {
  return <div className={`timeline-item ${event.kind}`}><div className="timeline-marker"><span /></div><div className="timeline-content"><div className="timeline-top"><strong>{event.label}</strong><time>{formatTime(event.timestamp)}</time></div>{event.detail && <p>{event.detail}</p>}<small>{event.name}</small></div></div>
}

type SettingsProps = {
  section: SettingsSection
  settings: Settings
  available: AvailableMetadata
  dirty: boolean
  saving: boolean
  notice: string | null
  onSectionChange: (section: SettingsSection) => void
  onChange: (settings: Settings) => void
  onSave: () => void
}

function SettingsView({ section, settings, available, dirty, saving, notice, onSectionChange, onChange, onSave }: SettingsProps) {
  return <div className="page-stack"><section className="page-heading"><div><p className="eyebrow">WORKSPACE SETTINGS</p><h1>设置</h1><p className="page-subtitle">把 Agent、思考模式、联网策略和工具能力放在一个可见的地方。</p></div><div className="heading-actions"><span className={`save-state ${dirty ? 'dirty' : ''}`}>{dirty ? '有未保存更改' : notice || '已同步'}</span><button type="button" className="primary-button" onClick={onSave} disabled={!dirty || saving} data-testid="settings-save">{saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}{saving ? '保存中' : '保存设置'}</button></div></section><div className="settings-layout"><aside className="settings-nav panel">{SETTINGS_ITEMS.map(({ id, label, description, icon: Icon }) => <button type="button" key={id} className={section === id ? 'active' : ''} onClick={() => onSectionChange(id)}><Icon size={17} /><span><b>{label}</b><small>{description}</small></span><ChevronRight size={15} /></button>)}</aside><section className="settings-content">{section === 'runtime' && <RuntimeSettings settings={settings} onChange={onChange} />}{section === 'agents' && <AgentSettings settings={settings} available={available} onChange={onChange} />}{section === 'skills' && <SkillSettings settings={settings} available={available} onChange={onChange} />}{section === 'mcp' && <McpSettings settings={settings} onChange={onChange} />}{section === 'connection' && <ConnectionSettings settings={settings} onChange={onChange} />}</section></div></div>
}

function RuntimeSettings({ settings, onChange }: { settings: Settings; onChange: (settings: Settings) => void }) {
  const thinkingOptions: Array<{ value: ThinkingMode; label: string; detail: string; icon: LucideIcon }> = [{ value: 'fast', label: '快速', detail: '优先响应速度', icon: Zap }, { value: 'balanced', label: '平衡', detail: '速度与质量兼顾', icon: Gauge }, { value: 'deep', label: '深度', detail: '适合复杂任务', icon: Brain }]
  const networkOptions: Array<{ value: NetworkPolicy; label: string; detail: string; icon: LucideIcon }> = [{ value: 'off', label: '关闭', detail: '全程离线', icon: WifiOff }, { value: 'ask', label: '按需询问', detail: '使用前提示', icon: ShieldCheck }, { value: 'on', label: '允许', detail: '由执行器决定', icon: Globe2 }]
  return <SettingsSection title="执行偏好" description="这些选项会随任务提交传递给执行层。"><SettingGroup title="思考模式" description="实际效果取决于当前 Agent 和模型是否支持。"><div className="option-grid three">{thinkingOptions.map(({ value, label, detail, icon: Icon }) => <button type="button" key={value} className={`option-card ${settings.thinking.mode === value ? 'selected' : ''}`} onClick={() => onChange({ ...settings, thinking: { mode: value } })}><Icon size={18} /><b>{label}</b><span>{detail}</span>{settings.thinking.mode === value && <Check size={15} className="option-check" />}</button>)}</div></SettingGroup><SettingGroup title="联网策略" description="联网开关是执行策略，不等于安全沙箱。"><div className="option-grid three">{networkOptions.map(({ value, label, detail, icon: Icon }) => <button type="button" key={value} className={`option-card ${settings.network.policy === value ? 'selected' : ''}`} onClick={() => onChange({ ...settings, network: { policy: value } })}><Icon size={18} /><b>{label}</b><span>{detail}</span>{settings.network.policy === value && <Check size={15} className="option-check" />}</button>)}</div></SettingGroup><SettingGroup title="任务提交时携带"><div className="readonly-chips"><span><Bot size={14} />{settings.agent.defaultAgent}</span><span><Brain size={14} />{settings.thinking.mode}</span><span><Globe2 size={14} />{settings.network.policy}</span><span><Sparkles size={14} />{settings.skills.enabledSkillIds.length} 项 Skill</span></div></SettingGroup></SettingsSection>
}

function AgentSettings({ settings, available, onChange }: { settings: Settings; available: AvailableMetadata; onChange: (settings: Settings) => void }) {
  const agents = available.agents?.length ? available.agents : DEFAULT_AVAILABLE.agents
  const models = available.models?.length ? available.models : DEFAULT_AVAILABLE.models
  const toggleAgent = (id: string) => {
    const current = settings.agent.allowedAgents
    const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    onChange({ ...settings, agent: { ...settings.agent, allowedAgents: next.length ? next : [id] } })
  }
  return <SettingsSection title="Agents 与模型" description="选择默认角色，并限制任务可以调用的 Agent。"><SettingGroup title="默认 Agent" description="新任务会使用这个角色作为入口。"><div className="agent-list">{agents.map((agent) => <button type="button" key={agent.id} className={`agent-option ${settings.agent.defaultAgent === agent.id ? 'selected' : ''}`} onClick={() => onChange({ ...settings, agent: { ...settings.agent, defaultAgent: agent.id, allowedAgents: settings.agent.allowedAgents.includes(agent.id) ? settings.agent.allowedAgents : [...settings.agent.allowedAgents, agent.id] } })}><span className="agent-avatar"><Bot size={16} /></span><span><b>{agent.label || agent.id}</b><small>{agent.description || agent.id}</small></span>{settings.agent.defaultAgent === agent.id && <CheckCircle2 size={17} />}</button>)}</div></SettingGroup><SettingGroup title="允许调用的 Agent" description="关闭的角色不会参与后续编排。"><div className="check-list">{agents.map((agent) => <label className="check-row" key={agent.id}><input type="checkbox" checked={settings.agent.allowedAgents.includes(agent.id)} onChange={() => toggleAgent(agent.id)} /><span className="fake-check"><Check size={13} /></span><span><b>{agent.label || agent.id}</b><small>{agent.id}</small></span></label>)}</div></SettingGroup><SettingGroup title="默认模型"><div className="field-row"><label htmlFor="model-select">模型</label><select id="model-select" value={settings.agent.model} onChange={(event) => onChange({ ...settings, agent: { ...settings.agent, model: event.target.value } })}>{models.map((model) => <option value={model.id} key={model.id}>{model.label || model.id}</option>)}</select></div><p className="availability-note"><CircleHelp size={14} />模型清单由执行后端提供，当前桌面端只保存选择。</p></SettingGroup></SettingsSection>
}

function SkillSettings({ settings, available, onChange }: { settings: Settings; available: AvailableMetadata; onChange: (settings: Settings) => void }) {
  const skills = available.skills?.length ? available.skills : DEFAULT_AVAILABLE.skills
  const toggleSkill = (id: string) => {
    const enabled = settings.skills.enabledSkillIds.includes(id)
    onChange({ ...settings, skills: { enabledSkillIds: enabled ? settings.skills.enabledSkillIds.filter((item) => item !== id) : [...settings.skills.enabledSkillIds, id] } })
  }
  return <SettingsSection title="Skills" description="为任务选择可用能力。未接入运行时的 Skill 会标注为待接入。"><div className="skill-grid">{skills.map((skill) => { const enabled = settings.skills.enabledSkillIds.includes(skill.id); const availableNow = skill.available !== false; return <div className={`skill-card ${enabled ? 'enabled' : ''}`} key={skill.id}><div className="skill-card-top"><span className="skill-icon"><Sparkles size={16} /></span><span className={`availability ${availableNow ? 'available' : 'pending'}`}>{availableNow ? '可用' : '待接入'}</span></div><h3>{skill.label || skill.id}</h3><p>{skill.description || skill.id}</p><button type="button" className={`toggle-button ${enabled ? 'on' : ''}`} onClick={() => toggleSkill(skill.id)} disabled={!availableNow} aria-label={`${enabled ? '关闭' : '启用'} ${skill.label || skill.id}`}>{enabled ? <ToggleRight size={23} /> : <ToggleLeft size={23} />}<span>{enabled ? '已启用' : availableNow ? '未启用' : '不可用'}</span></button></div> })}</div><div className="notice-strip"><Unplug size={15} /><span>桌面 Alpha 当前只保存 Skill 选择，真实加载由后续执行 Provider 接入。</span></div></SettingsSection>
}

function McpSettings({ settings, onChange }: { settings: Settings; onChange: (settings: Settings) => void }) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const addServer = () => {
    if (!name.trim() || !url.trim()) return
    const server: McpServer = { id: `server-${Date.now()}`, name: name.trim(), url: url.trim(), enabled: true }
    onChange({ ...settings, mcp: { ...settings.mcp, servers: [...settings.mcp.servers, server] } })
    setName('')
    setUrl('')
  }
  const removeServer = (id: string) => onChange({ ...settings, mcp: { ...settings.mcp, servers: settings.mcp.servers.filter((server) => server.id !== id) } })
  return <SettingsSection title="MCP 工具服务器" description="记录可用的 MCP 连接；当前桌面 sidecar 尚未启动 MCP 运行时。"><div className="setting-banner"><div className="banner-icon"><Network size={17} /></div><div><strong>MCP 运行时未接入</strong><p>你可以先保存服务器配置，接入 Provider 后再启用。</p></div><button type="button" className={`switch ${settings.mcp.enabled ? 'on' : ''}`} onClick={() => onChange({ ...settings, mcp: { ...settings.mcp, enabled: !settings.mcp.enabled } })} aria-label="切换 MCP"><span /></button></div><SettingGroup title="已配置服务器" description="地址只保存在本地设置文件中。">{settings.mcp.servers.length ? <div className="server-list">{settings.mcp.servers.map((server) => <div className="server-row" key={server.id}><span className="server-icon"><Server size={16} /></span><span><b>{server.name}</b><small>{server.url}</small></span><span className={`availability ${server.enabled !== false ? 'pending' : ''}`}>{server.enabled !== false ? '待接入' : '已停用'}</span><button type="button" className="icon-button danger-icon" title="移除服务器" aria-label={`移除 ${server.name}`} onClick={() => removeServer(server.id)}><Trash2 size={15} /></button></div>)}</div> : <p className="panel-note">尚未配置 MCP 服务器</p>}</SettingGroup><SettingGroup title="添加服务器"><div className="add-server-form"><input value={name} onChange={(event) => setName(event.target.value)} placeholder="名称" aria-label="服务器名称" /><input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="http://127.0.0.1:3000/mcp" aria-label="服务器地址" /><button type="button" className="secondary-button" onClick={addServer} disabled={!name.trim() || !url.trim()}><Plus size={15} />添加</button></div></SettingGroup></SettingsSection>
}

function ConnectionSettings({ settings, onChange }: { settings: Settings; onChange: (settings: Settings) => void }) {
  return <SettingsSection title="后端连接" description="选择桌面控制平面，并检查当前连接地址。"><SettingGroup title="Control Plane Provider" description="Phase 1 默认使用本地 sidecar。"><div className="provider-grid">{([{ value: 'local', label: '本地 Sidecar', detail: 'stdio JSONL', icon: TerminalSquare }, { value: 'legacy', label: 'Legacy 看板', detail: 'HTTP API · 待接入', icon: Cloud }, { value: 'fastapi', label: 'FastAPI 服务', detail: 'WebSocket · 待接入', icon: Server }] as const).map(({ value, label, detail, icon: Icon }) => <button type="button" key={value} className={`provider-card ${settings.backend.provider === value ? 'selected' : ''}`} onClick={() => onChange({ ...settings, backend: { ...settings.backend, provider: value } })}><Icon size={18} /><b>{label}</b><span>{detail}</span>{settings.backend.provider === value && <Check size={15} className="option-check" />}</button>)}</div></SettingGroup><SettingGroup title="服务地址"><div className="field-row"><label htmlFor="base-url">Base URL</label><input id="base-url" value={settings.backend.baseUrl} onChange={(event) => onChange({ ...settings, backend: { ...settings.backend, baseUrl: event.target.value } })} disabled={settings.backend.provider === 'local'} /><span className="field-state"><Wifi size={14} />本地 sidecar 通过 IPC 连接</span></div></SettingGroup><div className="connection-detail"><div><span className="detail-icon"><ShieldCheck size={16} /></span><span><b>安全边界</b><small>联网策略不会改变 Electron 沙箱或操作系统权限。</small></span></div><div><span className="detail-icon"><RotateCcw size={16} /></span><span><b>切换 Provider</b><small>Legacy 和 FastAPI 适配器将在后续阶段启用。</small></span></div></div></SettingsSection>
}

function SettingsSection({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <div className="settings-section"><div className="settings-section-heading"><h2>{title}</h2><p>{description}</p></div>{children}</div>
}

function SettingGroup({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return <section className="setting-group"><div className="setting-group-heading"><h3>{title}</h3>{description && <p>{description}</p>}</div>{children}</section>
}

export { App }
