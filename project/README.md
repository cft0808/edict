# Edict 桌面端工程

- `frontend/`：Electron 主进程、预加载桥接与 React + TypeScript + Vite 渲染进程。
- `backend/`：Python 3.12 sidecar，使用 stdin/stdout JSONL 协议，不启动 HTTP 服务。

## 一期交付与运行说明

- 支持基线：macOS 13 Ventura 及以上，构建 `arm64` 与 `x64` 未签名 DMG。
- 开发端口：Vite 仅绑定 `127.0.0.1:1517`；sidecar 无网络端口。
- 安全边界：Electron 使用 `contextIsolation`、关闭 `nodeIntegration` 并启用 renderer sandbox。
- 不包含：代码签名、公证、自动更新、发布与远程部署。

从 `project/frontend` 执行：

```bash
cp .env.example .env
npm ci
npm run verify
python3 -m unittest discover -s ../backend/tests -v
npm run package:mac
```

产物位于 `project/frontend/release/`。当前包携带 Python sidecar 源码，运行设备需已安装 Python 3.12；该依赖会在二期内嵌运行时时消除。
