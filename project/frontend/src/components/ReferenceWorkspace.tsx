import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BookOpen,
  Bot,
  Check,
  ChevronRight,
  CircleHelp,
  FileText,
  Gauge,
  Loader2,
  MessageSquareText,
  Newspaper,
  Play,
  Plus,
  RefreshCw,
  Save,
  Send,
  Settings2,
  Sparkles,
  Users,
  X,
  Zap,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { createLegacyAdapter, LEGACY_BASE, normalizeBaseUrl } from '../adapters/legacyAdapter'
import type {
  AgentInfo,
  AgentsStatusData,
  Capability,
  OfficialsData,
  MorningBrief,
  Task,
} from '../types/domain'
import type { Settings } from '../types/domain'

export type ReferenceModule =
  | 'edicts'
  | 'court'
  | 'monitor'
  | 'officials'
  | 'models'
  | 'skills'
  | 'sessions'
  | 'memorials'
  | 'templates'
  | 'morning'

type ReferenceWorkspaceProps = {
  module: ReferenceModule
  settings: Settings
  onModuleChange: (module: ReferenceModule) => void
}

type LegacyResponse = Record<string, unknown>

type ModelConfig = {
  agents: AgentInfo[]
  knownModels?: Array<{ id: string; label?: string; provider?: string }>
  dispatchChannel?: string
}

type SkillConfig = ModelConfig

type MorningConfig = {
  categories: string[]
  keywords: string[]
  custom_feeds: Array<{ name: string; url: string; category: string }>
  feishu_webhook: string
}

type LegacyTask = Task & {
  state?: string
  org?: string
  now?: string
  block?: string
  archived?: boolean
  flow_log?: Array<{ at?: string; from?: string; to?: string; remark?: string }>
  output?: string
}

const MODULES: Array<{ id: ReferenceModule; label: string; description: string; icon: LucideIcon }> = [
  { id: 'edicts', label: '旨意看板', description: '全局任务与流转', icon: FileText },
  { id: 'court', label: '朝堂议政', description: '多官员协同讨论', icon: MessageSquareText },
  { id: 'monitor', label: '省部调度', description: '在线状态与值守', icon: Activity },
  { id: 'officials', label: '官员总览', description: '角色、绩效与成本', icon: Users },
  { id: 'models', label: '模型配置', description: '角色模型与渠道', icon: Bot },
  { id: 'skills', label: '技能配置', description: '本地与远程技能', icon: Sparkles },
  { id: 'sessions', label: '小任务', description: '快速下达任务', icon: Zap },
  { id: 'memorials', label: '奏折阁', description: '完成任务归档', icon: BookOpen },
  { id: 'templates', label: '旨库', description: '模板化下旨', icon: FileText },
  { id: 'morning', label: '天下要闻', description: '简报与订阅配置', icon: Newspaper },
]

const MODULE_META = Object.fromEntries(MODULES.map((item) => [item.id, item])) as Record<ReferenceModule, typeof MODULES[number]>

const TEMPLATE_LIBRARY = [
  { id: 'release', icon: '🚀', name: '发布准备', description: '整理发布清单并检查风险', department: '工部', command: '请完成 {project} 的发布准备，重点检查 {focus}。' },
  { id: 'research', icon: '🔎', name: '专题调研', description: '对指定主题形成结构化调研', department: '中书省', command: '请调研 {topic}，输出结论、证据和待办。' },
  { id: 'incident', icon: '🚨', name: '故障复盘', description: '梳理故障影响、根因与修复计划', department: '门下省', command: '请复盘 {incident}，并给出 {owner} 的修复计划。' },
]

const DEFAULT_CONFIG: MorningConfig = {
  categories: ['政治', '军事', '经济', 'AI大模型'],
  keywords: [] as string[],
  custom_feeds: [] as Array<{ name: string; url: string; category: string }>,
  feishu_webhook: '',
}

function getEnvBaseUrl(): string {
  const candidate = import.meta.env.VITE_LEGACY_API_URL || import.meta.env.VITE_API_URL
  return typeof candidate === 'string' && candidate.trim() ? candidate : LEGACY_BASE
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : []
}

function asText(value: unknown, fallback = '—'): string {
  return typeof value === 'string' && value ? value : fallback
}

function formatDate(value?: string): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function normalizeMorningConfig(value: unknown): MorningConfig {
  const raw = value && typeof value === 'object' ? value as Record<string, unknown> : {}
  const categories = asArray<unknown>(raw.categories).filter((item): item is string => typeof item === 'string')
  const keywords = asArray<unknown>(raw.keywords).filter((item): item is string => typeof item === 'string')
  const customFeeds = asArray<unknown>(raw.custom_feeds).filter((item): item is { name: string; url: string; category: string } => {
    if (!item || typeof item !== 'object') return false
    const feed = item as Record<string, unknown>
    return typeof feed.name === 'string' && typeof feed.url === 'string' && typeof feed.category === 'string'
  })
  return {
    categories: categories.length ? categories : [...DEFAULT_CONFIG.categories],
    keywords,
    custom_feeds: customFeeds,
    feishu_webhook: typeof raw.feishu_webhook === 'string' ? raw.feishu_webhook : '',
  }
}

function normalizeTasks(payload: unknown): LegacyTask[] {
  const body = payload && typeof payload === 'object' ? payload as LegacyResponse : {}
  return asArray<LegacyTask>(body.tasks ?? payload).filter((task) => task && typeof task === 'object' && typeof task.id === 'string')
}

function ReferenceEmpty({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return <div className="reference-empty"><CircleHelp size={22} /><strong>{title}</strong><p>{detail}</p>{action}</div>
}

function ReferenceWorkspace({ module, settings, onModuleChange }: ReferenceWorkspaceProps) {
  const [refreshKey, setRefreshKey] = useState(0)
  const [probe, setProbe] = useState<'idle' | 'loading' | 'connected' | 'error'>('idle')
  const [probeMessage, setProbeMessage] = useState('尚未探测 Legacy 服务')
  const legacyBaseUrl = settings.backend.provider === 'legacy' ? settings.backend.baseUrl : getEnvBaseUrl()
  const adapter = useMemo(() => createLegacyAdapter(legacyBaseUrl), [legacyBaseUrl])
  const capability = adapter.capability(module)

  const probeLegacy = useCallback(async () => {
    setProbe('loading')
    try {
      await adapter.get('/healthz', module)
      setProbe('connected')
      setProbeMessage(`已连接 ${adapter.baseUrl}`)
    } catch (reason) {
      setProbe('error')
      setProbeMessage(reason instanceof Error ? reason.message : 'Legacy 服务不可用')
    }
  }, [adapter, module])

  useEffect(() => {
    setProbe('idle')
    setProbeMessage(`尚未探测 Legacy 服务（${adapter.baseUrl}）`)
  }, [adapter.baseUrl, module])

  const renderModule = () => {
    const props = { adapter, capability, refreshKey, onChanged: () => setRefreshKey((value) => value + 1) }
    switch (module) {
      case 'edicts': return <EdictsModule {...props} />
      case 'court': return <CourtModule {...props} />
      case 'monitor': return <MonitorModule {...props} />
      case 'officials': return <OfficialsModule {...props} />
      case 'models': return <ModelsModule {...props} />
      case 'skills': return <SkillsModule {...props} />
      case 'sessions': return <SessionsModule {...props} />
      case 'memorials': return <MemorialsModule {...props} />
      case 'templates': return <TemplatesModule {...props} />
      case 'morning': return <MorningModule {...props} />
    }
  }

  return <div className="reference-workspace">
    <section className="reference-heading">
      <div>
        <p className="eyebrow">LEGACY REFERENCE WORKSPACE</p>
        <h1>{MODULE_META[module].label}</h1>
        <p className="page-subtitle">{MODULE_META[module].description} · 通过可注入 HTTP adapter 连接原看板能力。</p>
      </div>
      <div className="reference-connection">
        <span className={`reference-status ${probe}`}>{probe === 'connected' ? '● 已连接' : probe === 'error' ? '● 未连接' : probe === 'loading' ? '◌ 探测中' : '○ 未探测'}</span>
        <code>{normalizeBaseUrl(adapter.baseUrl)}</code>
        <button type="button" className="secondary-button" onClick={() => void probeLegacy()} disabled={probe === 'loading'}><RefreshCw size={15} className={probe === 'loading' ? 'spin' : ''} />探测 Legacy</button>
      </div>
    </section>
    <div className="reference-layout">
      <aside className="reference-nav panel" aria-label="参考模块导航">
        <div className="reference-nav-label">参考模块</div>
        {MODULES.map(({ id, label, description, icon: Icon }) => <button type="button" key={id} className={module === id ? 'active' : ''} onClick={() => onModuleChange(id)} data-testid={`reference-nav-${id}`}><Icon size={16} /><span><b>{label}</b><small>{description}</small></span><ChevronRight size={14} /></button>)}
      </aside>
      <section className="reference-content">
        {capability.state !== 'supported' ? <ReferenceEmpty title={`${capability.label}暂未接入`} detail={capability.detail} /> : <>{probe === 'error' && <div className="reference-error" role="alert"><X size={16} /><span>{probeMessage}</span><button type="button" className="text-button" onClick={() => void probeLegacy()}>重试连接</button></div>}{probe === 'idle' && <div className="reference-hint"><CircleHelp size={15} /><span>{probeMessage}。未连接时不会显示伪造数据，模块请求失败会提供重试。</span></div>}{renderModule()}</>}
      </section>
    </div>
  </div>
}

type ModuleProps = { adapter: ReturnType<typeof createLegacyAdapter>; capability: Capability; refreshKey: number; onChanged: () => void }

function ModuleFrame({ title, description, loading, error, children, onRetry }: { title: string; description: string; loading: boolean; error: string | null; children: ReactNode; onRetry: () => void }) {
  return <div className="reference-module"><div className="module-toolbar"><div><h2>{title}</h2><p>{description}</p></div>{loading && <span className="module-loading"><Loader2 size={15} className="spin" />加载中</span>}</div>{error ? <ReferenceEmpty title="Legacy 数据未加载" detail={error} action={<button type="button" className="secondary-button" onClick={onRetry}><RefreshCw size={15} />重试</button>} /> : children}</div>
}

function useLegacyData<T>(loader: () => Promise<T>, refreshKey: number) {
  const [value, setValue] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try { setValue(await loader()) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Legacy 请求失败') } finally { setLoading(false) }
  }, [loader])
  useEffect(() => { void load() }, [load, refreshKey])
  return { value, loading, error, reload: load }
}

function EdictsModule({ adapter, refreshKey, onChanged }: ModuleProps) {
  const load = useCallback(() => adapter.get<LegacyResponse>('/api/live-status', 'edicts'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const [filter, setFilter] = useState<'active' | 'archived' | 'all'>('active')
  const tasks = useMemo(() => normalizeTasks(value).filter((task) => filter === 'all' || (filter === 'archived' ? task.archived : !task.archived)), [value, filter])
  const archiveAll = async () => { try { await adapter.post('/api/archive-task', { archiveAllDone: true }, 'edicts'); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '归档失败') } }
  return <ModuleFrame title="旨意看板" description="查看任务状态、部门流转和归档情况。" loading={loading} error={error} onRetry={() => void reload()}><div className="reference-actions"><div className="segmented compact">{(['active', 'archived', 'all'] as const).map((item) => <button type="button" key={item} className={filter === item ? 'selected' : ''} onClick={() => setFilter(item)}>{item === 'active' ? '活跃' : item === 'archived' ? '归档' : '全部'}</button>)}</div><button type="button" className="secondary-button" onClick={() => void archiveAll()}><BookOpen size={15} />归档已完成</button><span className="muted-count">{tasks.length} 道旨意</span></div><div className="reference-card-grid">{tasks.length ? tasks.map((task) => <TaskCard key={task.id} task={task} />) : <ReferenceEmpty title="暂无旨意" detail="Legacy 已连接，但当前筛选没有任务记录。" />}</div></ModuleFrame>
}

function TaskCard({ task }: { task: LegacyTask }) {
  const state = task.state || task.status || '未知'
  return <article className="reference-card"><div className="reference-card-top"><span className="reference-id">{task.id}</span><span className={`reference-tag ${state.toLowerCase()}`}>{state}</span></div><h3>{task.title || '无标题'}</h3><p>{task.now || task.description || '暂无当前进展'}</p><div className="reference-card-meta"><span>{task.org || task.agent || '未分派'}</span><span>{formatDate(task.updated_at || task.created_at)}</span></div></article>
}

function CourtModule({ adapter, refreshKey, onChanged }: ModuleProps) {
  const load = useCallback(() => adapter.get<LegacyResponse>('/api/court-discuss/officials', 'court'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const officials = asArray<{ id: string; name?: string; label?: string; emoji?: string; role?: string }>((value as LegacyResponse | null)?.officials)
  const [topic, setTopic] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [session, setSession] = useState<LegacyResponse | null>(null)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const start = async (event: FormEvent) => { event.preventDefault(); if (!topic.trim() || selected.length < 2 || submitting) return; setSubmitting(true); try { const result = await adapter.post<LegacyResponse>('/api/court-discuss/start', { topic: topic.trim(), officials: selected }, 'court'); setSession(result); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '议政启动失败') } finally { setSubmitting(false) } }
  const advance = async () => { if (!session?.session_id || !message.trim()) return; setSubmitting(true); try { const result = await adapter.post<LegacyResponse>('/api/court-discuss/advance', { sessionId: session.session_id, userMessage: message.trim() }, 'court'); setSession((current) => ({ ...(current || {}), ...result, messages: [...asArray(current?.messages), ...asArray(result.new_messages)] })); setMessage('') } catch (reason) { window.alert(reason instanceof Error ? reason.message : '议政推进失败') } finally { setSubmitting(false) } }
  if (session) return <ModuleFrame title="朝堂议政进行中" description={asText(session.topic, topic)} loading={false} error={null} onRetry={() => {}}><div className="court-session"><div className="court-session-head"><span>第 {asText(session.round, '1')} 轮</span><button type="button" className="secondary-button" onClick={() => setSession(null)}><X size={15} />结束本地视图</button></div><div className="court-messages">{asArray<LegacyResponse>(session.messages).map((item, index) => <div className={`court-message ${item.type === 'emperor' ? 'emperor' : ''}`} key={`${String(item.timestamp)}-${index}`}><b>{asText(item.official_name ?? item.name ?? item.type, '朝堂')}</b><p>{asText(item.content)}</p></div>)}{!asArray(session.messages).length && <ReferenceEmpty title="等待首轮议政结果" detail="点击发送观点，推动 Legacy 会话继续运行。" />}</div><div className="inline-form"><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="陛下可补充观点或追问" onKeyDown={(event) => { if (event.key === 'Enter') void advance() }} /><button type="button" className="primary-button" onClick={() => void advance()} disabled={!message.trim() || submitting}><Send size={15} />发送</button></div></div></ModuleFrame>
  return <ModuleFrame title="朝堂议政" description="选择至少两位官员，启动真实 Legacy 议政会话。" loading={loading} error={error} onRetry={() => void reload()}><form className="reference-form" onSubmit={start}><label>议题<input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="例如：讨论本期发布风险" /></label><div><span className="field-label">参朝官员（已选 {selected.length}/8）</span><div className="official-picker">{officials.length ? officials.map((official) => <button type="button" key={official.id} className={selected.includes(official.id) ? 'selected' : ''} onClick={() => setSelected((current) => current.includes(official.id) ? current.filter((id) => id !== official.id) : current.length < 8 ? [...current, official.id] : current)}><span>{official.emoji || '👤'}</span><b>{official.label || official.name || official.id}</b>{selected.includes(official.id) && <Check size={14} />}</button>) : <ReferenceEmpty title="没有官员资料" detail="Legacy 返回为空，无法伪造参朝人员。" />}</div></div><button type="submit" className="primary-button" disabled={!topic.trim() || selected.length < 2 || submitting}><Play size={15} />{submitting ? '启动中' : '开始议政'}</button></form></ModuleFrame>
}

function MonitorModule({ adapter, refreshKey }: ModuleProps) {
  const load = useCallback(() => adapter.get<AgentsStatusData>('/api/agents-status', 'monitor'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const data = value
  return <ModuleFrame title="省部调度" description="查看 Gateway 与各部门 Agent 的在线状态。" loading={loading} error={error} onRetry={() => void reload()}>{data ? <><div className="status-summary"><div><span>Gateway</span><strong>{data.gateway?.status || '未知'}</strong></div><div><span>在线 Agent</span><strong>{asArray<{ status?: string }>(data.agents).filter((agent) => agent.status === 'running').length}</strong></div><div><span>检查时间</span><strong>{formatDate(data.checkedAt)}</strong></div></div><div className="agent-status-grid">{asArray<{ id: string; label: string; emoji: string; role: string; status: string; statusLabel: string }>(data.agents).map((agent) => <article className="agent-status-card" key={agent.id}><span className={`status-dot-large ${agent.status}`} /><span className="agent-emoji">{agent.emoji}</span><b>{agent.label}</b><small>{agent.role}</small><span>{agent.statusLabel || agent.status}</span></article>)}</div></> : <ReferenceEmpty title="没有调度数据" detail="Legacy 已连接，但没有返回 Agent 状态。" />}</ModuleFrame>
}

function OfficialsModule({ adapter, refreshKey }: ModuleProps) {
  const load = useCallback(() => adapter.get<OfficialsData>('/api/officials-stats', 'officials'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  return <ModuleFrame title="官员总览" description="按角色查看 Agent 绩效、活跃任务与成本。" loading={loading} error={error} onRetry={() => void reload()}>{value ? <><div className="status-summary"><div><span>完成任务</span><strong>{value.totals?.tasks_done ?? 0}</strong></div><div><span>累计成本</span><strong>¥{(value.totals?.cost_cny ?? 0).toFixed(2)}</strong></div><div><span>首席官员</span><strong>{value.top_official || '—'}</strong></div></div><div className="official-table"><div className="table-head"><span>官员</span><span>模型</span><span>进行中</span><span>已完成</span><span>功绩</span></div>{asArray<{ id: string; label: string; emoji: string; role: string; rank: string; model?: string; tasks_active?: number; tasks_done?: number; merit_score?: number }>(value.officials).map((official) => <div className="table-row" key={official.id}><span><b>{official.emoji} {official.label}</b><small>{official.role} · {official.rank}</small></span><span>{official.model || '—'}</span><span>{official.tasks_active ?? 0}</span><span>{official.tasks_done ?? 0}</span><span>{official.merit_score ?? 0}</span></div>)}</div></> : <ReferenceEmpty title="暂无官员数据" detail="Legacy 已连接，但当前没有官员统计。" />}</ModuleFrame>
}

function ModelsModule({ adapter, refreshKey, onChanged }: ModuleProps) {
  const load = useCallback(() => adapter.get<ModelConfig>('/api/agent-config', 'models'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const [selected, setSelected] = useState<Record<string, string>>({})
  useEffect(() => { if (value) setSelected(Object.fromEntries(value.agents.map((agent) => [agent.id, agent.model || '']))) }, [value])
  const apply = async (agent: AgentInfo) => { try { await adapter.post('/api/set-model', { agentId: agent.id, model: selected[agent.id] }, 'models'); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '模型保存失败') } }
  const models = value?.knownModels || []
  return <ModuleFrame title="模型配置" description="为每个官员选择模型并提交到 Legacy 配置。" loading={loading} error={error} onRetry={() => void reload()}>{value ? <div className="config-grid">{value.agents.map((agent) => <article className="config-card" key={agent.id}><div className="config-card-title"><span>{agent.emoji || '🤖'}</span><div><b>{agent.label}</b><small>{agent.id} · {agent.role || '—'}</small></div></div><p>当前：{agent.model || '未配置'}</p><select value={selected[agent.id] || ''} onChange={(event) => setSelected((current) => ({ ...current, [agent.id]: event.target.value }))}><option value="">选择模型</option>{models.map((model) => <option value={model.id} key={model.id}>{model.label || model.id}{model.provider ? ` · ${model.provider}` : ''}</option>)}</select><button type="button" className="secondary-button" onClick={() => void apply(agent)} disabled={!selected[agent.id] || selected[agent.id] === agent.model}><Save size={15} />应用</button></article>)}</div> : <ReferenceEmpty title="暂无模型配置" detail="Legacy 已连接，但没有返回 Agent 配置。" />}</ModuleFrame>
}

function SkillsModule({ adapter, refreshKey, onChanged }: ModuleProps) {
  const load = useCallback(() => adapter.get<SkillConfig>('/api/agent-config', 'skills'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const [agentId, setAgentId] = useState('')
  const [skillName, setSkillName] = useState('')
  const [description, setDescription] = useState('')
  const [tab, setTab] = useState<'local' | 'remote'>('local')
  const [remote, setRemote] = useState<LegacyResponse[]>([])
  const loadRemote = useCallback(async () => { try { const result = await adapter.get<LegacyResponse>('/api/remote-skills-list', 'skills'); setRemote(asArray<LegacyResponse>(result.remoteSkills)) } catch (reason) { window.alert(reason instanceof Error ? reason.message : '远程技能加载失败') } }, [adapter])
  const addSkill = async (event: FormEvent) => { event.preventDefault(); if (!agentId || !skillName.trim()) return; try { await adapter.post('/api/add-skill', { agentId, skillName: skillName.trim(), description: description.trim() }, 'skills'); setSkillName(''); setDescription(''); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '技能添加失败') } }
  useEffect(() => { if (value?.agents[0] && !agentId) setAgentId(value.agents[0].id) }, [value, agentId])
  useEffect(() => { if (tab === 'remote') void loadRemote() }, [tab, loadRemote])
  const agents = asArray<AgentInfo>(value?.agents)
  return <ModuleFrame title="技能配置" description="查看本地技能，并通过真实接口添加远程技能。" loading={loading} error={error} onRetry={() => void reload()}><div className="tab-bar"><button type="button" className={tab === 'local' ? 'selected' : ''} onClick={() => setTab('local')}>本地技能</button><button type="button" className={tab === 'remote' ? 'selected' : ''} onClick={() => setTab('remote')}>远程技能</button></div>{tab === 'local' ? <div className="config-grid">{agents.map((agent) => <article className="config-card" key={agent.id}><div className="config-card-title"><span>{agent.emoji || '✨'}</span><div><b>{agent.label}</b><small>{agent.id}</small></div></div><div className="skill-list">{asArray<{ name: string; description?: string }>(agent.skills).length ? asArray<{ name: string; description?: string }>(agent.skills).map((skill) => <span className="skill-chip" key={skill.name}>📦 {skill.name}<small>{skill.description || '无描述'}</small></span>) : <span className="muted-count">暂无 Skills</span>}</div></article>)}</div> : <><div className="reference-actions"><button type="button" className="secondary-button" onClick={() => void loadRemote()}><RefreshCw size={15} />刷新远程技能</button><span className="muted-count">{remote.length} 个远程技能</span></div><div className="reference-card-grid">{remote.length ? remote.map((skill, index) => <article className="reference-card" key={`${String(skill.agentId)}-${String(skill.skillName)}-${index}`}><h3>{String(skill.skillName)}</h3><p>{String(skill.description || skill.sourceUrl || '无描述')}</p><span className="reference-tag">{String(skill.agentId)}</span></article>) : <ReferenceEmpty title="暂无远程技能" detail="Legacy 已连接，但没有返回远程技能记录。" />}</div></>}<form className="inline-form skill-add-form" onSubmit={addSkill}><select value={agentId} onChange={(event) => setAgentId(event.target.value)}><option value="">目标 Agent</option>{agents.map((agent) => <option value={agent.id} key={agent.id}>{agent.label} ({agent.id})</option>)}</select><input value={skillName} onChange={(event) => setSkillName(event.target.value)} placeholder="技能名称" /><input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="描述（可选）" /><button type="submit" className="primary-button" disabled={!agentId || !skillName.trim()}><Plus size={15} />添加本地技能</button></form></ModuleFrame>
}

function SessionsModule({ adapter, onChanged }: ModuleProps) {
  const [title, setTitle] = useState('')
  const [org, setOrg] = useState('中书省')
  const [submitting, setSubmitting] = useState(false)
  const create = async (event: FormEvent) => { event.preventDefault(); if (!title.trim() || submitting) return; setSubmitting(true); try { await adapter.post('/api/create-task', { title: title.trim(), org }, 'sessions'); setTitle(''); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '小任务提交失败') } finally { setSubmitting(false) } }
  return <ModuleFrame title="小任务" description="不依赖模板，直接创建一条真实 Legacy 任务。" loading={false} error={null} onRetry={() => {}}><form className="reference-form narrow" onSubmit={create}><label>任务标题<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="例如：整理本周风险清单" /></label><label>负责部门<select value={org} onChange={(event) => setOrg(event.target.value)}><option>中书省</option><option>门下省</option><option>工部</option><option>户部</option><option>兵部</option><option>刑部</option><option>礼部</option></select></label><button type="submit" className="primary-button" disabled={!title.trim() || submitting}><Send size={15} />{submitting ? '提交中' : '下达小任务'}</button></form><div className="reference-hint"><Zap size={15} />提交成功后可从「旨意看板」查看 Legacy 任务流转。</div></ModuleFrame>
}

function MemorialsModule({ adapter, refreshKey }: ModuleProps) {
  const load = useCallback(() => adapter.get<LegacyResponse>('/api/live-status', 'memorials'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const tasks = normalizeTasks(value).filter((task) => ['Done', 'Cancelled', 'completed', 'cancelled'].includes(task.state || task.status))
  const [detail, setDetail] = useState<LegacyTask | null>(null)
  const copy = async (task: LegacyTask) => { const text = `# 奏折 · ${task.title}\n\n- 任务编号：${task.id}\n- 状态：${task.state || task.status}\n- 负责部门：${task.org || '—'}\n`; try { await navigator.clipboard.writeText(text); window.alert('奏折摘要已复制') } catch { window.alert('当前环境不允许复制') } }
  const flowLog = asArray<{ from?: string; to?: string; remark?: string; at?: string }>(detail?.flow_log)
  return <ModuleFrame title="奏折阁" description="浏览已完成或已取消任务，并复制可审阅的奏折摘要。" loading={loading} error={error} onRetry={() => void reload()}><div className="reference-card-grid">{tasks.length ? tasks.map((task) => <button type="button" className="reference-card memorial-card" key={task.id} onClick={() => setDetail(task)}><div className="reference-card-top"><span className="reference-id">📜 {task.id}</span><span className="reference-tag">{task.state || task.status}</span></div><h3>{task.title || task.id}</h3><p>{task.org || '—'} · {task.flow_log?.length || 0} 步流转</p></button>) : <ReferenceEmpty title="暂无奏折" detail="Legacy 已连接，任务完成后这里会出现奏折。" />}</div>{detail && <div className="reference-modal-backdrop" onClick={() => setDetail(null)}><div className="reference-modal" onClick={(event) => event.stopPropagation()}><button type="button" className="icon-button" onClick={() => setDetail(null)} aria-label="关闭详情"><X size={16} /></button><p className="eyebrow">MEMORIAL</p><h2>{detail.title || detail.id}</h2><p>{detail.now || detail.description || '暂无说明'}</p><div className="flow-list">{flowLog.map((flow, index) => <div key={index}><b>{flow.from || '—'} → {flow.to || '—'}</b><span>{flow.remark || '—'} · {formatDate(flow.at)}</span></div>)}</div><button type="button" className="secondary-button" onClick={() => void copy(detail)}><BookOpen size={15} />复制奏折摘要</button></div></div>}</ModuleFrame>
}

function TemplatesModule({ adapter, onChanged }: ModuleProps) {
  const [template, setTemplate] = useState<typeof TEMPLATE_LIBRARY[number] | null>(null)
  const [values, setValues] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState('')
  const templateFields: Record<string, string[]> = { release: ['project', 'focus'], research: ['topic'], incident: ['incident', 'owner'] }
  const build = () => { if (!template) return ''; return template.command.replace(/\{(\w+)\}/g, (_match, key: string) => values[key] || `{${key}}`) }
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!template) return; const title = build(); if (title.includes('{')) { window.alert('请先填写模板参数'); return } try { await adapter.post('/api/create-task', { title, org: '中书省', targetDept: template.department, templateId: template.id, params: values }, 'templates'); setTemplate(null); setPreview(''); onChanged() } catch (reason) { window.alert(reason instanceof Error ? reason.message : '下旨失败') } }
  return <ModuleFrame title="旨库" description="使用模板生成真实任务，支持预览后再下旨。" loading={false} error={null} onRetry={() => {}}><div className="reference-card-grid">{TEMPLATE_LIBRARY.map((item) => <article className="reference-card" key={item.id}><div className="reference-card-top"><span className="template-icon">{item.icon}</span><span className="reference-tag">{item.department}</span></div><h3>{item.name}</h3><p>{item.description}</p><button type="button" className="primary-button" onClick={() => { setTemplate(item); setValues({}); setPreview('') }}><FileText size={15} />使用模板</button></article>)}</div>{template && <div className="reference-modal-backdrop" onClick={() => setTemplate(null)}><div className="reference-modal" onClick={(event) => event.stopPropagation()}><button type="button" className="icon-button" onClick={() => setTemplate(null)} aria-label="关闭模板"><X size={16} /></button><p className="eyebrow">TEMPLATE</p><h2>{template.icon} {template.name}</h2><form className="reference-form" onSubmit={submit}>{templateFields[template.id].map((field, index) => <label key={field}>{index === 0 ? '项目 / 主题' : '补充要求'}<input value={values[field] || ''} onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))} placeholder="必填" /></label>)}{preview && <pre className="template-preview">{preview}</pre>}<div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setPreview(build())}><CircleHelp size={15} />预览旨意</button><button type="submit" className="primary-button"><Send size={15} />下旨</button></div></form></div></div>}</ModuleFrame>
}

function MorningModule({ adapter, refreshKey, onChanged }: ModuleProps) {
  const load = useCallback(() => adapter.get<MorningBrief>('/api/morning-brief', 'morning'), [adapter])
  const { value, loading, error, reload } = useLegacyData(load, refreshKey)
  const [config, setConfig] = useState<MorningConfig>(DEFAULT_CONFIG)
  const [keyword, setKeyword] = useState('')
  const [configOpen, setConfigOpen] = useState(false)
  useEffect(() => {
    if (value && typeof value === 'object' && 'config' in value) setConfig(normalizeMorningConfig(value.config))
  }, [value])
  const saveConfig = async () => { try { await adapter.post('/api/morning-config', config, 'morning'); onChanged(); setConfigOpen(false) } catch (reason) { window.alert(reason instanceof Error ? reason.message : '订阅配置保存失败') } }
  const refresh = async () => { try { await adapter.post('/api/morning-brief/refresh', {}, 'morning'); window.alert('采集已触发，请稍后刷新') } catch (reason) { window.alert(reason instanceof Error ? reason.message : '要闻采集失败') } }
  return <ModuleFrame title="天下要闻" description="查看 Legacy 简报，并调整分类与关注关键词。" loading={loading} error={error} onRetry={() => void reload()}><div className="reference-actions"><button type="button" className="secondary-button" onClick={() => setConfigOpen((open) => !open)}><Settings2 size={15} />订阅配置</button><button type="button" className="primary-button" onClick={() => void refresh()}><RefreshCw size={15} />立即采集</button><span className="muted-count">{value ? `${Object.values(value.categories || {}).flat().length} 条` : '—'}</span></div>{configOpen && <div className="config-panel"><div className="category-toggles">{DEFAULT_CONFIG.categories.map((category) => <button type="button" key={category} className={config.categories.includes(category) ? 'selected' : ''} onClick={() => setConfig((current) => ({ ...current, categories: current.categories.includes(category) ? current.categories.filter((item) => item !== category) : [...current.categories, category] }))}>{category}<Check size={14} /></button>)}</div><div className="inline-form"><input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="新增关注关键词" onKeyDown={(event) => { if (event.key === 'Enter' && keyword.trim()) { setConfig((current) => ({ ...current, keywords: [...new Set([...current.keywords, keyword.trim()])] })); setKeyword('') } }} /><button type="button" className="secondary-button" onClick={() => { if (keyword.trim()) { setConfig((current) => ({ ...current, keywords: [...new Set([...current.keywords, keyword.trim()])] })); setKeyword('') } }}><Plus size={15} />添加</button></div><div className="chip-list">{config.keywords.map((item) => <button type="button" className="skill-chip" key={item} onClick={() => setConfig((current) => ({ ...current, keywords: current.keywords.filter((keywordItem) => keywordItem !== item) }))}>{item} <X size={12} /></button>)}</div><button type="button" className="primary-button" onClick={() => void saveConfig()}><Save size={15} />保存配置</button></div>}{value ? <div className="news-grid">{Object.entries(value.categories || {}).filter(([category]) => config.categories.includes(category) || !configOpen).map(([category, items]) => <section className="news-section" key={category}><h3><Newspaper size={16} />{category}<span>{asArray(items).length}</span></h3>{asArray<LegacyResponse>(items).map((item, index) => <article className="news-item" key={index}><b>{asText(item.title)}</b><p>{asText(item.summary ?? item.desc, '暂无摘要')}</p><small>{asText(item.source, '未知来源')} · {formatDate(asText(item.pub_date, ''))}</small></article>)}</section>)}</div> : <ReferenceEmpty title="暂无天下要闻" detail="Legacy 已连接，但没有返回简报内容。" />}</ModuleFrame>
}

export { MODULES, ReferenceWorkspace }
export default ReferenceWorkspace
