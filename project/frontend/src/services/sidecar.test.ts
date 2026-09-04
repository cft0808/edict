import { describe, expect, it } from 'vitest'
import {
  nextSidecarRequestState,
  shouldStartSidecar,
  sidecarStartFailure,
} from './sidecar'

describe('sidecar retry lifecycle helpers', () => {
  it('only starts from idle or failed states', () => {
    expect(shouldStartSidecar('idle')).toBe(true)
    expect(shouldStartSidecar('failed')).toBe(true)
    expect(shouldStartSidecar('starting')).toBe(false)
    expect(shouldStartSidecar('ready')).toBe(false)
  })

  it('moves an exited process to a retryable failed state', () => {
    expect(nextSidecarRequestState('idle', 'request')).toBe('starting')
    expect(nextSidecarRequestState('starting', 'started')).toBe('ready')
    expect(nextSidecarRequestState('ready', 'exited')).toBe('failed')
    expect(nextSidecarRequestState('failed', 'request')).toBe('starting')
  })

  it('normalizes non-Error launch failures', () => {
    expect(sidecarStartFailure('boom').message).toBe('boom')
    expect(sidecarStartFailure(new Error('bad')).message).toBe('bad')
    expect(sidecarStartFailure({ code: 'EFAIL' }).message).toBe('Python sidecar 启动失败')
  })
})
