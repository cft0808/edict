# 快速上手指南

## 1. 安装 OpenClaw

```bash
# macOS
brew install openclaw
# 或下载安装包: https://openclaw.ai/download
```

## 2. 克隆并安装

```bash
git clone https://github.com/cft0808/openclaw-sansheng-liubu.git
cd openclaw-sansheng-liubu
./install.sh
```

## 3. 配置消息渠道

在 OpenClaw 中配置你的消息渠道（Feishu/Telegram/Signal），
并将 `zhongshu` Agent 设为接收旨意的入口。

参考 OpenClaw 文档：https://docs.openclaw.ai/channels

## 4. 启动服务

```bash
# 数据刷新（后台运行）
bash scripts/run_loop.sh &

# 看板服务器
python3 dashboard/server.py
```

## 5. 发送第一道旨意

向中书省发送任务：

```
请帮我用 Python 写一个文本分类器：
1. 使用 scikit-learn
2. 支持多分类
3. 输出混淆矩阵
4. 写完整的文档
```

## 6. 查看执行过程

打开看板 http://127.0.0.1:7891，切换到"任务看板"，
观察任务在各个状态之间流转。

## 故障排查

**看板显示"服务器未启动"**
→ 确认 `python3 dashboard/server.py` 正在运行

**Agent 不响应**
→ 检查 `openclaw gateway status`，必要时 `openclaw gateway restart`

**数据不更新**
→ 检查 `run_loop.sh` 是否在运行，查看日志：`tail -f /tmp/sansheng_liubu_refresh.log`
