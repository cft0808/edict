export type StartGate = {
  run: () => Promise<void>
  reset: (attempt?: Promise<void>) => void
}

/**
 * Shares one in-flight startup attempt between callers.
 *
 * The gate deliberately clears itself after both success and failure. A later
 * request can therefore retry a failed launch, while concurrent requests do
 * not spawn multiple sidecars.
 */
export function createStartGate(start: () => Promise<void>): StartGate {
  let pending: Promise<void> | undefined

  return {
    run() {
      if (!pending) {
        let startAttempt: Promise<void>
        try {
          // Invoke the launcher immediately. The returned promise still
          // serializes callers, while synchronous launch setup failures are
          // converted into the same retryable promise lifecycle.
          startAttempt = Promise.resolve(start())
        } catch (reason) {
          startAttempt = Promise.reject(reason)
        }
        let gatedAttempt!: Promise<void>
        gatedAttempt = startAttempt.finally(() => {
          // A process-exit callback can reset the gate while this promise is
          // settling. Never clear a newer startup attempt in that case.
          if (pending === gatedAttempt) pending = undefined
        })
        pending = gatedAttempt
      }
      return pending
    },
    reset(attempt) {
      if (!attempt || pending === attempt) pending = undefined
    },
  }
}
