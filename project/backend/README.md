# Edict Python Sidecar

## 兼容基线

- macOS 13+；推荐 Python 3.12。
- 不监听 TCP/HTTP 端口，仅通过 stdin/stdout JSONL 与 Electron 通信。
- 一期桌面包携带 sidecar 源码，目标机需要可用的 Python 3.12 解释器。

运行入口：

```bash
python3.12 -m sidecar.main
```

协议为每行一个 JSON 对象。输入 `health`、`status`、`task.submit` 请求，输出对应响应和状态流事件；日志仅写 stderr，stdout 保持 JSONL 干净。

验证：

```bash
python3 -m unittest discover -s tests -v
```
