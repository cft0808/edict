import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    // 与 dashboard/server.py 的 DIST 一致，避免 build 到 edict/frontend/dist 后看板仍加载旧 bundle
    outDir: '../../dashboard/dist',
    emptyOutDir: true,
  },
})
