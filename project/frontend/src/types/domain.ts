export type ProviderId = 'local' | 'legacy' | 'fastapi'

export type TaskStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | string

export type RuntimeState = 'starting' | 'ready' | 'unavailable' | 'stopped' | 'timeout'

export type CapabilityId =
  | 'tasks'
  | 'settings'
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

export type CapabilityState = 'supported' | 'unsupported' | 'degraded'

export type Capability = {
  id: CapabilityId
  state: CapabilityState
  label: string
  detail: string
}

export type Health = {
  ok: boolean
  service?: string
  protocolVersion?: string
  transport?: string
  capabilities?: Capability[]
}

export type RuntimeStatus = {
  state: RuntimeState
  detail?: string
  python?: string
  pid?: number
  transport?: string
  restartable?: boolean
}

export type Task = {
  id: string
  title: string
  status: TaskStatus
  created_at: string
  description?: string
  agent?: string
  thinking?: string
  network?: string
  skills?: string[]
  mcp?: boolean
  phase?: string
  progress?: number
  updated_at?: string
  state?: string
  org?: string
  now?: string
  eta?: string
  block?: string
  archived?: boolean
  heartbeat?: { status: string; label: string }
  todos?: Array<{ id: string | number; title: string; status: string; detail?: string }>
  review_round?: number
  flow_log?: Array<{ at: string; from: string; to: string; remark: string }>
  output?: string
  sourceMeta?: Record<string, unknown>
}

export type StatusPayload = {
  state: string
  taskCount: number
  tasks: Task[]
  transport?: string
  activeCount?: number
  completedCount?: number
}

export type Settings = {
  backend: { provider: ProviderId; baseUrl: string }
  agent: { defaultAgent: string; allowedAgents: string[]; model: string }
  thinking: { mode: 'fast' | 'balanced' | 'deep' }
  network: { policy: 'off' | 'ask' | 'on' }
  skills: { enabledSkillIds: string[] }
  mcp: { enabled: boolean; servers: McpServer[] }
}

export type McpServer = { id: string; name: string; url: string; enabled?: boolean }

export type AvailableMetadata = {
  agents: Array<{ id: string; label?: string; description?: string }>
  skills: Array<{ id: string; label?: string; description?: string; available?: boolean }>
  models: Array<{ id: string; label?: string; provider?: string }>
}

export type AgentInfo = {
  id: string
  label: string
  emoji?: string
  role?: string
  model?: string
  skills?: Array<{ name: string; description: string; path?: string }>
}

export type AgentConfig = { agents: AgentInfo[]; knownModels?: AvailableMetadata['models']; dispatchChannel?: string }

export type OfficialInfo = {
  id: string
  label: string
  emoji: string
  role: string
  rank: string
  model?: string
  status?: string
  tasks_done?: number
  tasks_active?: number
  cost_cny?: number
  sessions?: number
  messages?: number
  merit_score?: number
  heartbeat?: { status: string; label: string }
  participated_edicts?: Array<{ id: string; title: string; state: string }>
}

export type OfficialsData = {
  officials: OfficialInfo[]
  totals?: { tasks_done: number; cost_cny: number }
  top_official?: string
}

export type AgentsStatusData = {
  ok: boolean
  gateway?: { alive: boolean; probe: boolean; status: string }
  agents: Array<{ id: string; label: string; emoji: string; role: string; status: string; statusLabel: string; lastActive?: string }>
  checkedAt?: string
}

export type MorningBrief = {
  date?: string
  generated_at?: string
  categories: Record<string, Array<{ title: string; summary?: string; desc?: string; link: string; source: string; pub_date?: string }>>
}

export type SubConfig = {
  categories: Array<{ name: string; enabled: boolean }>
  keywords: string[]
  custom_feeds: Array<{ name: string; url: string; category: string }>
  feishu_webhook: string
}

export type DomainSnapshot = {
  status: StatusPayload | null
  health: Health | null
  runtime: RuntimeStatus
  settings: Settings
  available: AvailableMetadata
  agentConfig: AgentConfig | null
  officials: OfficialsData | null
  agentsStatus: AgentsStatusData | null
  morning: MorningBrief | null
  morningConfig: SubConfig | null
}

export type ProviderResult<T> = {
  value: T
  source: ProviderId
  capability: Capability
}

export class ProviderError extends Error {
  readonly code: string
  readonly capability: CapabilityId
  readonly retryable: boolean

  constructor(message: string, options: { code?: string; capability?: CapabilityId; retryable?: boolean } = {}) {
    super(message)
    this.name = 'ProviderError'
    this.code = options.code ?? 'provider_error'
    this.capability = options.capability ?? 'tasks'
    this.retryable = options.retryable ?? false
  }
}
