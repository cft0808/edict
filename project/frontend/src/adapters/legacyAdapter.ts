import type { Capability, CapabilityId, ProviderId } from '../types/domain'
import { ProviderError } from '../types/domain'

export const LEGACY_BASE = 'http://127.0.0.1:7891'

export function normalizeBaseUrl(value?: string): string {
  return (value?.trim() || LEGACY_BASE).replace(/\/+$/, '')
}

export function legacyCapability(id: CapabilityId, state: 'supported' | 'unsupported' | 'degraded', detail: string): Capability {
  const labels: Record<CapabilityId, string> = {
    tasks: '任务提交', settings: '设置', edicts: '旨意看板', court: '朝堂议政', monitor: '省部调度', officials: '官员总览', models: '模型配置', skills: '技能配置', sessions: '小任务', memorials: '奏折阁', templates: '旨库', morning: '天下要闻',
  }
  return { id, state, label: labels[id], detail }
}

export async function requestLegacy<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 8_000)
  try {
    const response = await fetch(`${normalizeBaseUrl(baseUrl)}${path}`, { ...init, signal: controller.signal, cache: 'no-store' })
    if (!response.ok) throw new ProviderError(`Legacy 服务返回 HTTP ${response.status}`, { code: `http_${response.status}`, retryable: response.status >= 500 })
    return await response.json() as T
  } catch (reason) {
    if (reason instanceof ProviderError) throw reason
    if (reason instanceof DOMException && reason.name === 'AbortError') throw new ProviderError('Legacy 请求超时（7891）', { code: 'timeout', retryable: true })
    throw new ProviderError('无法连接 Legacy 兼容入口（7891）', { code: 'network_error', retryable: true })
  } finally {
    clearTimeout(timer)
  }
}

export type LegacyAdapter = {
  provider: ProviderId
  baseUrl: string
  capability(id: CapabilityId): Capability
  get<T>(path: string, capability: CapabilityId): Promise<T>
  post<T>(path: string, body: unknown, capability: CapabilityId): Promise<T>
}

export function createLegacyAdapter(baseUrl: string): LegacyAdapter {
  const normalized = normalizeBaseUrl(baseUrl)
  const supported = new Set<CapabilityId>(['edicts', 'court', 'monitor', 'officials', 'models', 'skills', 'sessions', 'memorials', 'templates', 'morning'])
  return {
    provider: 'legacy',
    baseUrl: normalized,
    capability(id) {
      return supported.has(id)
        ? legacyCapability(id, 'supported', `通过现有 Legacy HTTP 入口 ${normalized} 提供`)
        : legacyCapability(id, 'unsupported', 'Legacy 入口未提供该能力')
    },
    get<T>(path: string, capability: CapabilityId) {
      if (!supported.has(capability)) return Promise.reject(new ProviderError(`${capability} 尚未接入 Legacy provider`, { code: 'unsupported_capability', capability }))
      return requestLegacy<T>(normalized, path)
    },
    post<T>(path: string, body: unknown, capability: CapabilityId) {
      if (!supported.has(capability)) return Promise.reject(new ProviderError(`${capability} 尚未接入 Legacy provider`, { code: 'unsupported_capability', capability }))
      return requestLegacy<T>(normalized, path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    },
  }
}
