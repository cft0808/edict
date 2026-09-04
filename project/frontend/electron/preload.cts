import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('edictDesktop', {
  request: (command: string, payload?: unknown) => ipcRenderer.invoke('sidecar:request', command, payload),
  onEvent: (listener: (payload: unknown) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, payload: unknown) => listener(payload)
    ipcRenderer.on('sidecar:event', handler)
    return () => ipcRenderer.removeListener('sidecar:event', handler)
  },
})
