import { PassThrough } from 'node:stream'
import { describe, expect, it, vi } from 'vitest'
import { SidecarClient, type SidecarProcess, type SpawnSidecar } from './sidecar-client.js'

type FakeProcess = SidecarProcess & {
  stdout: PassThrough
  stderr: PassThrough
  exit: (code?: number | null) => void
  fail: (reason: Error) => void
  requests: () => Array<Record<string, unknown>>
  respond: (index: number, payload: unknown) => void
}

function createFakeProcess(): FakeProcess {
  const stdout = new PassThrough()
  const stderr = new PassThrough()
  const listeners = new Map<string, Array<(...args: unknown[]) => void>>()
  const writes: Array<Record<string, unknown>> = []
  let writable = true
  const emit = (event: string, ...args: unknown[]) => {
    for (const listener of listeners.get(event) ?? []) listener(...args)
  }
  const process = {
    stdin: {
      get writable() { return writable },
      write(chunk: string, callback?: (error?: Error | null) => void) {
        writes.push(JSON.parse(chunk) as Record<string, unknown>)
        callback?.(null)
        return true
      },
      end() { writable = false },
    },
    stdout,
    stderr,
    on(event: string, listener: (...args: unknown[]) => void) {
      listeners.set(event, [...(listeners.get(event) ?? []), listener])
      return process
    },
    once(event: string, listener: (...args: unknown[]) => void) {
      const onceListener = (...args: unknown[]) => {
        const current = listeners.get(event) ?? []
        listeners.set(event, current.filter((item) => item !== onceListener))
        listener(...args)
      }
      return process.on(event as 'error' | 'exit', onceListener)
    },
    kill() {
      writable = false
      return true
    },
    exit(code?: number | null) {
      writable = false
      emit('exit', code ?? 0)
    },
    fail(reason: Error) {
      writable = false
      emit('error', reason)
    },
    requests: () => writes,
    respond(index: number, payload: unknown) {
      const requestId = writes[index]?.requestId
      stdout.write(`${JSON.stringify({ type: 'response', request_id: requestId, payload })}\n`)
    },
  } as FakeProcess
  return process
}

function createClient(spawnProcess: SpawnSidecar) {
  return new SidecarClient({
    sidecarDirectory: '/sidecar-root',
    pythonCandidates: ['python-test'],
    fileExists: () => true,
    spawnProcess,
    healthTimeoutMs: 1_000,
    requestTimeoutMs: 1_000,
    logger: { error: vi.fn() },
  })
}

describe('SidecarClient', () => {
  it('launches once for concurrent requests and completes the health handshake', async () => {
    const process = createFakeProcess()
    const spawnProcess = vi.fn(async () => process)
    const client = createClient(spawnProcess)

    const first = client.start()
    const second = client.request('status')
    await vi.waitFor(() => expect(process.requests()).toHaveLength(1))
    process.respond(0, { ok: true })
    await vi.waitFor(() => expect(process.requests()).toHaveLength(2))
    process.respond(1, { state: 'ready' })

    await expect(first).resolves.toBeUndefined()
    await expect(second).resolves.toEqual({ state: 'ready' })
    expect(spawnProcess).toHaveBeenCalledTimes(1)
    client.stop()
  })

  it('reports missing sidecar files without attempting to spawn', async () => {
    const spawnProcess = vi.fn<SpawnSidecar>()
    const client = new SidecarClient({
      sidecarDirectory: '/missing',
      pythonCandidates: ['python-test'],
      fileExists: () => false,
      spawnProcess,
    })

    await expect(client.start()).rejects.toThrow('文件缺失')
    expect(spawnProcess).not.toHaveBeenCalled()
  })

  it('retries a failed first launch after the start gate is cleared', async () => {
    const process = createFakeProcess()
    const spawnProcess = vi.fn<SpawnSidecar>()
      .mockRejectedValueOnce(new Error('spawn failed'))
      .mockImplementationOnce(async () => process)
    const client = createClient(spawnProcess)

    await expect(client.start()).rejects.toThrow('spawn failed')
    const retry = client.start()
    await vi.waitFor(() => expect(process.requests()).toHaveLength(1))
    process.respond(0, { ok: true })
    await expect(retry).resolves.toBeUndefined()
    expect(spawnProcess).toHaveBeenCalledTimes(2)
    client.stop()
  })

  it('rejects pending requests on exit and starts a fresh process on the next request', async () => {
    const firstProcess = createFakeProcess()
    const secondProcess = createFakeProcess()
    const spawnProcess = vi.fn<SpawnSidecar>()
      .mockImplementationOnce(async () => firstProcess)
      .mockImplementationOnce(async () => secondProcess)
    const client = createClient(spawnProcess)

    const firstStart = client.start()
    await vi.waitFor(() => expect(firstProcess.requests()).toHaveLength(1))
    firstProcess.respond(0, { ok: true })
    await firstStart

    const pending = client.request('status')
    await vi.waitFor(() => expect(firstProcess.requests()).toHaveLength(2))
    firstProcess.exit(17)
    await expect(pending).rejects.toThrow('已退出')

    const retry = client.request('status')
    await vi.waitFor(() => expect(secondProcess.requests()).toHaveLength(1))
    secondProcess.respond(0, { ok: true })
    await vi.waitFor(() => expect(secondProcess.requests()).toHaveLength(2))
    secondProcess.respond(1, { state: 'ready-again' })
    await expect(retry).resolves.toEqual({ state: 'ready-again' })
    expect(spawnProcess).toHaveBeenCalledTimes(2)
    client.stop()
  })

  it('does not leave startup or pending requests alive after stop', async () => {
    const firstProcess = createFakeProcess()
    const secondProcess = createFakeProcess()
    const spawnProcess = vi.fn<SpawnSidecar>()
      .mockImplementationOnce(async () => firstProcess)
      .mockImplementationOnce(async () => secondProcess)
    const client = createClient(spawnProcess)
    const start = client.start()
    client.stop()
    await expect(start).rejects.toThrow('启动已取消')

    const nextStart = client.start()
    await vi.waitFor(() => expect(secondProcess.requests()).toHaveLength(1))
    secondProcess.respond(0, { ok: true })
    await nextStart
    const pending = client.request('status')
    await vi.waitFor(() => expect(secondProcess.requests()).toHaveLength(2))
    client.stop()
    await expect(pending).rejects.toThrow('已停止')
  })
})
