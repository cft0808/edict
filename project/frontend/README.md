# edict三省 Desktop Frontend

Electron 主进程启动 Python sidecar，并通过 `stdin/stdout` JSONL 转发请求和事件；渲染进程不直接访问 Node 或 sidecar。

## 兼容基线

- macOS 13 Ventura 及以上；同时输出 Apple Silicon（`arm64`）和 Intel（`x64`）DMG。
- Node.js 20 LTS 或更高版本。
- Python 3.12（开发时可用 `EDICT_PYTHON` 临时指定其他可用解释器）。
- 一期不包含代码签名、公证或自动发布。未签名应用首次打开可能需要在系统设置中明确允许。

## 开发

```bash
cp .env.example .env
npm ci
npm run dev
```

Vite 仅在开发时绑定 `127.0.0.1:1517`。sidecar 不监听任何 TCP/HTTP 端口。

如本机没有 `python3.12`，可执行 `EDICT_PYTHON=python3 npm run dev` 临时指定解释器。

## 质量验证

```bash
npm run verify
python3 -m unittest discover -s ../backend/tests -v
```

`verify` 依次执行 TypeScript 类型检查、Vitest 和生产构建。

## 本地 macOS 打包（不签名、不公证、不发布）

```bash
npm ci
npm run package:mac   # 仅生成未签名 .app 目录，便于本机冒烟
npm run dist:mac      # 生成 arm64/x64 DMG 到 release/
```

`electron-builder` 仅打包桌面端渲染层、Electron 主进程与 Python sidecar 源码。目标机仍需提供兼容的 Python 3.12 解释器；一期尚未内嵌 Python 运行时。
