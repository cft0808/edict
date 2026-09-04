/// <reference types="vite/client" />

interface Window {
  edictDesktop?: {
    request(command: string, payload?: unknown): Promise<unknown>
    onEvent(listener: (payload: unknown) => void): () => void
    runtime?: {
      getStatus(): Promise<unknown>
      restart(): Promise<unknown>
    }
  }
}

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_LEGACY_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
