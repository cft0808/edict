import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import { randomUUID } from 'node:crypto'
import { existsSync } from 'node:fs'
import { createInterface } from 'node:readline'
import { join } from 'node:path'
import { createStartGate } from './start-gate.js'

export type SidecarProcess = {
  stdin: {
    writable: boolean
    write: (chunk: string, callback?: (error?: Error | null) => void) => boolean
    end: () => void
  }
  stdout: NodeJS.ReadableStream
  stderr: NodeJS.ReadableStream
  on: (event: 'error' | 'exit', listener: (...args: unknown[]) => void) => SidecarProcess
  once: (event: 'spawn' | 'error' | 'exit', listener: (...args: unknown[]) => void) => SidecarProcess
  kill: () => boolean
}

export type SpawnSidecar = (command: string, cwd: string, env: NodeJS.ProcessEnv) => Promise<SidecarProcess>

export type SidecarClientOptions = {
  sidecarDirectory: string
  configDirectory?: string
  pythonCandidates?: string[]
  spawnProcess?: SpawnSidecar
  fileExists?: (path: string) => boolean
  requestTimeoutMs?: number
  healthTimeoutMs?: number
  onEvent?: (payload: unknown) => void
  logger?: Pick<Console, 'error'>
}

type PendingRequest = {
  resolve: (payload: unknown) => void
  reject: (reason: Error) => void
  timer: ReturnType<typeof setTimeout>
}

type SidecarMessage = {
  type?: unknown
  request_id?: unknown
  payload?: unknown
}

const DEFAULT_PYTHON_CANDIDATES = [
  'python3.12',
  '/usr/local/bin/python3',
  '/opt/homebrew/bin/python3',
  '/Library/Frameworks/Python.framework/Versions/Current/bin/python3',
  'python3',
  '/usr/bin/python3',
]

export class SidecarLaunchError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'SidecarLaunchError'
  }
}

export class SidecarUnavailableError extends Error {
  constructor(message = 'Python sidecar 当前不可用') {
    super(message)
    this.name = 'SidecarUnavailableError'
  }
}

export class SidecarProcessError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'SidecarProcessError'
  }
}

function asError(reason: unknown, fallback = 'Python sidecar 启动失败'): Error {
  if (reason instanceof Error) return reason
  if (typeof reason === 'string' && reason) return new Error(reason)
  return new Error(fallback)
}

function defaultSpawnProcess(command: string, cwd: string, env: NodeJS.ProcessEnv): Promise<SidecarProcess> {
  return new Promise((resolve, reject) => {
    let settled = false
    let child: ChildProcessWithoutNullStreams
    try {
      child = spawn(command, ['-m', 'sidecar.main'], {
        cwd,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      })
    } catch (reason) {
      reject(reason)
      return
    }

    const process = child as unknown as SidecarProcess
    process.once('spawn', () => {
      if (settled) return
      settled = true
      resolve(process)
    })
    process.once('error', (reason) => {
      if (settled) return
      settled = true
      reject(reason)
    })
  })
}

export class SidecarClient {
  private process: SidecarProcess | undefined
  private startupAttempt: Promise<void> | undefined
  private lifecycleGeneration = 0
  private readonly startGate
  private readonly pending = new Map<string, PendingRequest>()
  private readonly options: SidecarClientOptions & { requestTimeoutMs: number; healthTimeoutMs: number }
  private readonly spawnProcess: SpawnSidecar
  private readonly fileExists: (path: string) => boolean
  private readonly logger: Pick<Console, 'error'>

  constructor(options: SidecarClientOptions) {
    this.options = {
      requestTimeoutMs: 5_000,
      healthTimeoutMs: 2_000,
      ...options,
    }
    this.spawnProcess = options.spawnProcess ?? defaultSpawnProcess
    this.fileExists = options.fileExists ?? existsSync
    this.logger = options.logger ?? console
    this.startGate = createStartGate(() => this.launch())
  }

  start(): Promise<void> {
    return this.ensureStarted()
  }

  async request(command: string, payload?: unknown): Promise<unknown> {
    await this.ensureStarted()
    return this.sendRequest(command, payload)
  }

  stop(): void {
    this.lifecycleGeneration += 1
    const startupAttempt = this.startupAttempt
    this.startupAttempt = undefined
    this.startGate.reset(startupAttempt)

    const child = this.process
    this.process = undefined
    this.rejectAll(new SidecarUnavailableError('Python sidecar 已停止'))
    if (child) this.terminate(child)
  }

  private ensureStarted(): Promise<void> {
    const child = this.process
    if (child?.stdin.writable) return Promise.resolve()
    if (child) {
      this.process = undefined
      this.rejectAll(new SidecarUnavailableError('Python sidecar 输入流不可写'))
      this.terminate(child)
    }

    const attempt = this.startGate.run()
    this.startupAttempt = attempt
    void attempt.then(
      () => this.clearStartupAttempt(attempt),
      () => this.clearStartupAttempt(attempt),
    )
    return attempt
  }

  private clearStartupAttempt(attempt: Promise<void>): void {
    if (this.startupAttempt === attempt) this.startupAttempt = undefined
  }

  private async launch(): Promise<void> {
    const generation = this.lifecycleGeneration
    const entry = join(this.options.sidecarDirectory, 'sidecar', 'main.py')
    if (!this.fileExists(entry)) {
      throw new SidecarLaunchError(`Python sidecar 文件缺失：${this.options.sidecarDirectory}`)
    }

    const configured = this.options.pythonCandidates ?? []
    const candidates = (configured.length ? configured : [process.env.EDICT_PYTHON, ...DEFAULT_PYTHON_CANDIDATES])
      .filter((value, index, values): value is string => Boolean(value) && values.indexOf(value) === index)
    const failures: string[] = []

    for (const command of candidates) {
      if (generation !== this.lifecycleGeneration) throw new SidecarLaunchError('Python sidecar 启动已取消')
      let child: SidecarProcess | undefined
      try {
        child = await this.spawnProcess(command, this.options.sidecarDirectory, {
          ...process.env,
          ...(this.options.configDirectory ? { EDICT_CONFIG_DIR: this.options.configDirectory } : {}),
        })
        if (generation !== this.lifecycleGeneration) throw new SidecarLaunchError('Python sidecar 启动已取消')
        this.process = child
        this.attach(child)
        await this.sendRequest('health', undefined, this.options.healthTimeoutMs)
        return
      } catch (reason) {
        const error = asError(reason)
        failures.push(`${command}: ${error.message}`)
        if (error instanceof SidecarLaunchError && error.message === 'Python sidecar 启动已取消') throw error
        if (child && this.process === child) {
          this.process = undefined
          this.rejectAll(error)
        }
        if (child) {
          this.terminate(child)
          await this.waitForExit(child)
        }
      }
    }

    throw new SidecarLaunchError(`无法启动 Python sidecar。尝试结果：${failures.join('; ') || '没有可用 Python 解释器'}`)
  }

  private sendRequest(command: string, payload?: unknown, timeoutMs = this.options.requestTimeoutMs): Promise<unknown> {
    const child = this.process
    if (!child?.stdin.writable) return Promise.reject(new SidecarUnavailableError('Python sidecar 进程不存在或输入流不可写'))

    const requestId = randomUUID()
    const serialized = `${JSON.stringify({ requestId, command, payload })}\n`
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(requestId)
        reject(new Error(`sidecar 请求超时：${command}`))
      }, timeoutMs)
      this.pending.set(requestId, { resolve, reject, timer })

      const onWrite = (reason?: Error | null) => {
        if (!reason) return
        const pending = this.pending.get(requestId)
        if (!pending) return
        this.pending.delete(requestId)
        clearTimeout(pending.timer)
        pending.reject(asError(reason, `sidecar 写入失败：${command}`))
      }

      try {
        child.stdin.write(serialized, onWrite)
      } catch (reason) {
        onWrite(asError(reason, `sidecar 写入失败：${command}`))
      }
    })
  }

  private attach(child: SidecarProcess): void {
    child.on('error', (reason) => this.handleProcessFailure(child, new SidecarProcessError(asError(reason, 'Python sidecar 进程错误').message)))
    child.on('exit', (code) => this.handleProcessFailure(child, new SidecarProcessError(`Python sidecar 已退出（code ${code ?? 'unknown'}）`)))
    child.stderr.on('data', (data) => this.logger.error(`[sidecar] ${String(data)}`))
    createInterface({ input: child.stdout }).on('line', (line) => this.handleLine(line))
  }

  private handleProcessFailure(child: SidecarProcess, reason: Error): void {
    if (this.process !== child) return
    this.process = undefined
    this.startGate.reset(this.startupAttempt)
    this.rejectAll(reason)
  }

  private handleLine(line: string): void {
    let message: SidecarMessage
    try {
      message = JSON.parse(line) as SidecarMessage
    } catch (reason) {
      this.logger.error('无法解析 sidecar JSONL 消息', reason)
      return
    }

    const requestId = typeof message.request_id === 'string' ? message.request_id : undefined
    if (message.type === 'response' && requestId) {
      const pending = this.pending.get(requestId)
      if (!pending) return
      this.pending.delete(requestId)
      clearTimeout(pending.timer)
      pending.resolve(message.payload)
      return
    }
    if (message.type === 'error' && requestId) {
      const pending = this.pending.get(requestId)
      if (!pending) return
      this.pending.delete(requestId)
      clearTimeout(pending.timer)
      const payload = message.payload
      const detail = payload && typeof payload === 'object' && 'message' in payload && typeof payload.message === 'string'
        ? payload.message
        : JSON.stringify(payload)
      pending.reject(new Error(detail))
      return
    }
    if (message.type === 'event') this.options.onEvent?.(message.payload)
  }

  private rejectAll(reason: Error): void {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer)
      pending.reject(reason)
    }
    this.pending.clear()
  }

  private terminate(child: SidecarProcess): void {
    try {
      child.stdin.end()
    } catch {
      // The process may have already closed its input stream.
    }
    try {
      child.kill()
    } catch {
      // The process may have already exited.
    }
  }

  private waitForExit(child: SidecarProcess): Promise<void> {
    return new Promise((resolve) => {
      let settled = false
      const finish = () => {
        if (settled) return
        settled = true
        resolve()
      }
      child.once('exit', finish)
      setTimeout(finish, 250)
    })
  }
}
