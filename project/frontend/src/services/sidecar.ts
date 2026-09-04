import type { Health, RuntimeStatus, StatusPayload } from '../types/domain'

export type DesktopBridge = NonNullable<Window['edictDesktop']>

export const REQUEST_TIMEOUT_MS = 8_000

export type SidecarRequestState = 'idle' | 'starting' | 'ready' | 'failed'

/** Pure lifecycle helpers shared with the Electron-side retry tests. */
export function shouldStartSidecar(state: SidecarRequestState): boolean {
  return state === 'idle' || state === 'failed'
}

export function sidecarStartFailure(reason: unknown): Error {
  if (reason instanceof Error) return reason
  return new Error(typeof reason === 'string' ? reason : 'Python sidecar 启动失败')
}

export function nextSidecarRequestState(
  state: SidecarRequestState,
  transition: 'request' | 'started' | 'failed' | 'exited',
): SidecarRequestState {
  if (transition === 'request') return shouldStartSidecar(state) ? 'starting' : state
  if (transition === 'started') return 'ready'
  if (transition === 'failed' || transition === 'exited') return 'failed'
  return state
}

export function getDesktopBridge(): DesktopBridge | null {
  return typeof window !== 'undefined' && window.edictDesktop ? window.edictDesktop : null
}

export function describeBridgeError(reason: unknown): string {
  if (reason instanceof Error && reason.message) return reason.message
  return typeof reason === 'string' ? reason : '桌面通信组件暂时不可用'
}

export async function requestSidecar<T>(command: string, payload?: unknown, timeoutMs = REQUEST_TIMEOUT_MS): Promise<T> {
  const bridge = getDesktopBridge()
  if (!bridge) throw new Error('桌面通信组件未能加载，请重新启动应用')

  let timer: ReturnType<typeof setTimeout> | undefined
  try {
    const request = bridge.request(command, payload)
    const timeout = new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new Error(`sidecar 请求超时：${command}`)), timeoutMs)
    })
    return await Promise.race([request as Promise<T>, timeout])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

export async function requestSidecarWithRetry<T>(command: string, payload?: unknown, options: { attempts?: number; timeoutMs?: number } = {}): Promise<T> {
  const attempts = Math.max(1, options.attempts ?? 2)
  let lastError: unknown
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await requestSidecar<T>(command, payload, options.timeoutMs)
    } catch (reason) {
      lastError = reason
      if (attempt + 1 < attempts) await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)))
    }
  }
  throw lastError instanceof Error ? lastError : new Error(describeBridgeError(lastError))
}

export async function readHealth(): Promise<Health> {
  return requestSidecarWithRetry<Health>('health', undefined, { attempts: 2, timeoutMs: 3_000 })
}

export async function readStatus(): Promise<StatusPayload> {
  return requestSidecarWithRetry<StatusPayload>('status', undefined, { attempts: 2 })
}

export async function readRuntime(): Promise<RuntimeStatus> {
  const bridge = getDesktopBridge()
  if (!bridge?.runtime) return { state: 'starting', detail: '当前 preload 未提供运行时状态' }
  return requestSidecarWithRetry<RuntimeStatus>('runtime.status', undefined, { attempts: 1, timeoutMs: 3_000 })
}

export function subscribeSidecarEvents(listener: (payload: unknown) => void): () => void {
  return getDesktopBridge()?.onEvent(listener) ?? (() => undefined)
}
