# 📸 截图说明

看板截图用于 README 和文档展示。请启动看板后按以下顺序截图并放置到本目录。

## 截图清单

| 文件名 | 内容 | 对应面板 |
|--------|------|---------|
| `01-kanban-main.png` | 旨意看板总览 | 📋 旨意看板 |
| `02-monitor.png` | 省部调度 | 🔭 省部调度 |
| `03-task-detail.png` | 任务流转详情（点击任务卡片展开） | 📋 旨意看板 → 详情 |
| `04-model-config.png` | 模型配置面板 | ⚙️ 模型配置 |
| `05-skills-config.png` | 技能配置面板 | 🛠️ 技能配置 |
| `06-official-overview.png` | 官员总览（12 位 Agent） | 👥 官员总览 |
| `07-sessions.png` | 小任务 / 会话 | 💬 小任务 |
| `08-memorials.png` | 奏折阁 | 📜 奏折阁 |
| `09-templates.png` | 旨库（圣旨模板） | 📜 旨库 |
| `10-morning-briefing.png` | 天下要闻 | 📰 天下要闻 |
| `11-ceremony.png` | 上朝仪式动画 | 开场动画 |

## 自动截图

```bash
# 确保看板服务器正在运行
python3 dashboard/server.py &

# 自动截取全部 11 张截图
python3 scripts/take_screenshots.py

# 录制 demo GIF（需要 ffmpeg）
python3 scripts/record_demo.py
```

## 建议

- 使用 **1920×1080** 或 **2560×1440** 分辨率
- 确保看板有足够的数据（至少 5+ 任务）
- 深色主题截图效果最佳
- 截图前刷新数据确保最新状态
