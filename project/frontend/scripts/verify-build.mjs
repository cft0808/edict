import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = process.cwd()
const indexPath = resolve(root, 'dist-renderer/index.html')
const preloadPath = resolve(root, 'dist-electron/preload.cjs')

if (!existsSync(indexPath)) throw new Error('Renderer build is missing index.html')
if (!existsSync(preloadPath)) throw new Error('Electron preload must be emitted as preload.cjs')

const html = readFileSync(indexPath, 'utf8')
if (/\b(?:src|href)="\//.test(html)) {
  throw new Error('Renderer build contains absolute asset paths that fail under file://')
}

console.log('Packaged renderer paths and preload format verified')
