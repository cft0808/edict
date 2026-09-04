import { describe, expect, it, vi } from 'vitest'
import { createLegacyAdapter, normalizeBaseUrl } from './legacyAdapter'

describe('legacy adapter', () => {
  it('normalizes the configured endpoint and exposes explicit capabilities', () => {
    const adapter = createLegacyAdapter('  http://localhost:7891/// ')
    expect(adapter.baseUrl).toBe('http://localhost:7891')
    expect(adapter.capability('edicts').state).toBe('supported')
    expect(adapter.capability('tasks').state).toBe('unsupported')
    expect(normalizeBaseUrl('')).toBe('http://127.0.0.1:7891')
    expect(normalizeBaseUrl()).toBe('http://127.0.0.1:7891')
  })

  it('passes GET and POST through to the configured Legacy HTTP service', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_input, init) => {
      return new Response(JSON.stringify({ ok: true, method: init?.method ?? 'GET' }), { status: 200 })
    })
    const adapter = createLegacyAdapter('http://legacy.test/')

    await expect(adapter.get('/api/live-status', 'edicts')).resolves.toEqual({ ok: true, method: 'GET' })
    await expect(adapter.post('/api/create-task', { title: 'x' }, 'sessions')).resolves.toEqual({ ok: true, method: 'POST' })
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://legacy.test/api/create-task',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ title: 'x' }) }),
    )
    fetchMock.mockRestore()
  })

  it('reports unavailable Legacy service without inventing data', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('connection refused'))
    const adapter = createLegacyAdapter('http://legacy.test')

    await expect(adapter.get('/api/live-status', 'edicts')).rejects.toMatchObject({ code: 'network_error', retryable: true })
    vi.restoreAllMocks()
  })
})
