import { describe, expect, it, vi } from 'vitest'
import { createStartGate } from './start-gate.js'

describe('createStartGate', () => {
  it('shares concurrent startup and permits a later retry after failure', async () => {
    let attempts = 0
    let rejectFirst: ((reason: Error) => void) | undefined
    const start = vi.fn(() => {
      attempts += 1
      if (attempts === 1) {
        return new Promise<void>((_resolve, reject) => {
          rejectFirst = reject
        })
      }
      return Promise.resolve()
    })
    const gate = createStartGate(start)

    const first = gate.run()
    const concurrent = gate.run()
    await Promise.resolve()
    expect(first).toBe(concurrent)
    expect(start).toHaveBeenCalledTimes(1)

    rejectFirst?.(new Error('first launch failed'))
    await expect(first).rejects.toThrow('first launch failed')

    await gate.run()
    expect(start).toHaveBeenCalledTimes(2)
  })

  it('does not start again while the process is already healthy', async () => {
    const start = vi.fn(() => Promise.resolve())
    const gate = createStartGate(start)

    await Promise.all([gate.run(), gate.run(), gate.run()])
    expect(start).toHaveBeenCalledTimes(1)
  })

  it('does not let an old attempt clear a newer retry', async () => {
    let releaseFirst: (() => void) | undefined
    let releaseSecond: (() => void) | undefined
    const start = vi.fn()
      .mockImplementationOnce(() => new Promise<void>((resolve) => { releaseFirst = resolve }))
      .mockImplementationOnce(() => new Promise<void>((resolve) => { releaseSecond = resolve }))
    const gate = createStartGate(start)

    const first = gate.run()
    gate.reset(first)
    const second = gate.run()
    await Promise.resolve()
    expect(start).toHaveBeenCalledTimes(2)
    expect(first).not.toBe(second)

    releaseFirst?.()
    await first
    expect(gate.run()).toBe(second)

    releaseSecond?.()
    await second
  })
})
