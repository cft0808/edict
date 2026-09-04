import { app, BrowserWindow, ipcMain } from 'electron'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { SidecarClient } from './sidecar-client.js'

const currentDirectory = dirname(fileURLToPath(import.meta.url))
const isDevelopment = Boolean(process.env.VITE_DEV_SERVER_URL)

function getSidecarDirectory(): string {
  if (isDevelopment) return join(currentDirectory, '..', '..', 'backend')
  return join(process.resourcesPath, 'backend')
}

let sidecar: SidecarClient | undefined
let activeWindow: BrowserWindow | undefined

function createWindow(): BrowserWindow {
  const window = new BrowserWindow({
    title: 'edict三省',
    width: 1120,
    height: 760,
    minWidth: 880,
    minHeight: 620,
    backgroundColor: '#0b1020',
    webPreferences: {
      preload: join(currentDirectory, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  if (isDevelopment) {
    void window.loadURL(process.env.VITE_DEV_SERVER_URL!)
  } else {
    void window.loadFile(join(currentDirectory, '..', 'dist-renderer', 'index.html'))
  }
  return window
}

app.whenReady().then(() => {
  sidecar = new SidecarClient({
    sidecarDirectory: getSidecarDirectory(),
    // Keep user settings outside the packaged app so they survive upgrades.
    configDirectory: app.getPath('userData'),
    onEvent: (payload) => {
      if (activeWindow && !activeWindow.isDestroyed()) activeWindow.webContents.send('sidecar:event', payload)
    },
  })
  ipcMain.handle('sidecar:request', (_event, command: string, payload?: unknown) => {
    if (!sidecar) throw new Error('Python sidecar 尚未初始化')
    return sidecar.request(command, payload)
  })
  const window = createWindow()
  activeWindow = window
  void sidecar.start().catch((reason) => console.error('Unable to start sidecar', reason))
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      const nextWindow = createWindow()
      activeWindow = nextWindow
      void sidecar?.start().catch((reason) => console.error('Unable to start sidecar', reason))
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => sidecar?.stop())
