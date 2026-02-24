# ⚔️ 三省六部 · OpenClaw Multi-Agent Orchestration

<p align="center">
  <img src="docs/screenshots/01-kanban-main.png" alt="三省六部看板总览" width="100%">
</p>

<p align="center">
  <a href="README_EN.md">English</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#架构">架构</a> ·
  <a href="#看板功能">看板功能</a> ·
  <a href="#配置">配置</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Required-blue?style=flat-square" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Agents-9-purple?style=flat-square" alt="Agents">
</p>

---

**三省六部**是一套基于 [OpenClaw](https://openclaw.ai) 的**多 Agent 协同编排系统**，借鉴中国古代三省六部制的分权协作思想，将复杂任务在多个专职 AI Agent 之间流转执行，并通过实时看板统一监控和管理。

> 皇上一道旨意 → 中书省规划 → 门下省审议 → 尚书省派发 → 六部执行 → 回奏

---

## 🤔 为什么是三省六部？

> **"与其让一个 AI 全做错，不如让 9 个专职 AI 互相制衡。"**

大多数多 Agent 框架让 Agent 直接执行任务——**三省六部**引入了古代中国朝廷的分权制衡智慧：

| 特性 | 三省六部 | CrewAI | MetaGPT | AutoGen |
|------|:-------:|:------:|:-------:|:-------:|
| 内建审议/否决机制（门下省） | ✅ | ❌ | ❌ | ❌ |
| 实时 Kanban 监控看板 | ✅ | ❌ | ❌ | ❌ |
| 流转日志追溯（谁做了什么） | ✅ | ⚠️ | ⚠️ | ❌ |
| 官员心跳健康监控 | ✅ | ❌ | ❌ | ❌ |
| 模型配置热更新（无需重启） | ✅ | ❌ | ❌ | ❌ |
| 通过 IM 下达自然语言指令 | ✅ | ❌ | ❌ | ❌ |

**核心创新：门下省（Reviewer Agent）** — 所有执行计划必须经过独立的审议 Agent 审核，可封驳退回，让 AI 决策更可靠。

---

## ✨ 特性

| 功能 | 说明 |
|------|------|
| 🏛️ **9 个专职 Agent** | 中书省·门下省·尚书省 + 户·礼·兵·刑·工 六部 |
| 📋 **实时看板** | Kanban 看板，按状态/省部过滤，支持全文搜索 |
| 📊 **工作记录** | 按部门分组的完成历史，含完整流转日志 |
| ⏱️ **时间线视图** | 全局事件时间线，可视化任务流转过程 |
| ⚙️ **模型配置** | 直接从看板修改各 Agent 使用的 LLM 模型，实时生效 |
| 🛠️ **技能配置** | 查看各 Agent 已安装的 Skills |
| 💊 **心跳监控** | Agent 健康状态实时显示（活跃/停滞/告警） |
| 🔄 **自动刷新** | 每15秒数据自动同步，倒计时显示 |

## 🖼️ 看板截图

### 旨意看板
任务以卡片形式展示，支持按省/部过滤、全文搜索，心跳徽章实时显示 Agent 状态。

![旨意看板](docs/screenshots/01-kanban-main.png)

<details>
<summary>展开查看更多截图</summary>

### 早朝简报
每日自动抓取科技/财经资讯，汇总展示。

![早朝简报](docs/screenshots/02-morning-briefing.png)

### 任务流转详情
点击任意任务卡片，展开完整流转日志，追踪从下旨到回奏的每一步。

![任务流转详情](docs/screenshots/03-task-detail.png)

### 模型配置
一键切换各省/部 Agent 使用的 LLM 模型，更改后自动重启 Gateway（约5秒生效）。

![模型配置](docs/screenshots/04-model-config.png)

### 技能配置
展示各省/部已安装的 OpenClaw Skills，一览各 Agent 的能力边界。

![技能配置](docs/screenshots/05-skills-config.png)

### 官员总览
功绩排行榜 + 各官员 Token 消耗、活跃状态、完成旨意数全面统计。

![官员总览](docs/screenshots/06-official-overview.png)

</details>

---

## 🚀 快速开始

### 前置条件

- [OpenClaw](https://openclaw.ai) 已安装并完成初始化
- Python 3.9+
- macOS / Linux

### 一键安装

```bash
git clone https://github.com/cft0808/openclaw-sansheng-liubu.git
cd openclaw-sansheng-liubu
chmod +x install.sh
./install.sh
```

安装脚本会自动完成：
1. ✅ 创建 9 个 Agent Workspace（`~/.openclaw/workspace-*`）
2. ✅ 写入各省部的 SOUL.md（角色人格）
3. ✅ 在 `openclaw.json` 中注册 Agent 及权限矩阵
4. ✅ 初始化数据目录
5. ✅ 执行首次数据同步
6. ✅ 重启 Gateway 使配置生效

### 启动看板

```bash
# 终端 1：启动数据刷新循环（每15秒同步一次）
bash scripts/run_loop.sh

# 终端 2：启动看板服务器
python3 dashboard/server.py

# 打开浏览器
open http://127.0.0.1:7891
```

---

## 🏛️ 架构

```
                         ┌─────────────────────────────┐
                         │         皇上（用户）          │
                         │   通过 Feishu / Telegram 下旨  │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │        📜 中书省              │
                         │   接旨 → 规划 → 拆解任务      │
                         └──────────────┬──────────────┘
                                        │ 提交审核
                         ┌──────────────▼──────────────┐
                         │        🔍 门下省              │
                         │   审议方案 → 准奏 / 封驳      │
                         └──────────────┬──────────────┘
                                        │ 准奏
                         ┌──────────────▼──────────────┐
                         │        📮 尚书省              │
                         │   派发任务 → 汇总结果 → 回奏  │
                         └───────┬──────────────┬───────┘
                    ┌────────────┼──────────────┼────────────┐
                    │            │              │            │
          ┌─────────▼──┐ ┌──────▼─────┐ ┌─────▼──────┐ ┌──▼──────┐
          │  📝 礼部   │ │  💰 户部   │ │  ⚔️ 兵部   │ │ 🔧 工部 │
          │  文档/规范  │ │  数据/资源  │ │  工程实现  │ │ 基础设施 │
          └────────────┘ └────────────┘ └────────────┘ └─────────┘
                              ⚖️ 刑部（合规审计，随时介入）
```

### 各省部职责

| 部门 | Agent ID | 职责 |
|------|----------|------|
| 📜 中书省 | `zhongshu` | 接旨、规划任务、生成执行方案 |
| 🔍 门下省 | `menxia` | 审议方案、把关质量、准奏/封驳 |
| 📮 尚书省 | `shangshu` | 派发任务、协调六部、汇总回奏 |
| 📝 礼部 | `libu` | 文档撰写、报告生成、规范制定 |
| 💰 户部 | `hubu` | 数据处理、资源生成、成本核算 |
| ⚔️ 兵部 | `bingbu` | 代码实现、算法开发、系统巡检 |
| ⚖️ 刑部 | `xingbu` | 安全审计、合规检查、红线管控 |
| 🔧 工部 | `gongbu` | CI/CD、基础设施、自动化工具 |

### 权限矩阵（能发消息给谁）

| From → To | 中书 | 门下 | 尚书 | 户 | 礼 | 兵 | 刑 | 工 |
|-----------|:----:|:----:|:----:|:--:|:--:|:--:|:--:|:--:|
| 中书省 | — | ✅ | ✅ | | | | | |
| 门下省 | ✅ | — | ✅ | | | | | |
| 尚书省 | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| 六部 | | | ✅ | | | | | |

---

## 📋 看板功能

### 🏠 总览
- **流程管线**：可视化各状态的任务数量
- **任务分布图**：按省/部和状态的横向条形图
- **Agent 健康卡**：实时显示各 Agent 心跳状态与当前模型

### 📋 任务看板
- **Kanban 列视图**：Inbox / 中书规划 / 门下审议 / 已派发 / 执行中 / 待审查 / 已完成 / 阻塞
- **省部过滤**：一键只看某个省或部的任务
- **全文搜索**：跨任务ID/标题/官员/省部
- **心跳徽章**：绿色=活跃，黄色=可能停滞，红色闪烁=已停滞
- **详情抽屉**：点击任务卡片，侧边展开完整信息+活动日志

### 📊 工作记录
- 按省/部分组展示所有已完成任务
- 点击展开流转日志（完整的流转链路）
- 产出物验收状态

### ⏱️ 时间线
- 全局事件时间线，按时间倒序排列
- 彩色节点标注来源省/部
- 展示完整流转链路

### ⚙️ 模型配置
- 展示每个 Agent 当前使用的 LLM 模型
- 下拉选择新模型后点击"应用更改"
- **自动**写入 `openclaw.json` 并重启 Gateway（约5秒生效）
- 变更记录永久存档

### 🛠️ 技能配置
- 展示各省/部已安装的 OpenClaw Skills
- 技能名称与描述一览

---

## ⚙️ 配置

### 任务状态流转

```
Inbox → Zhongshu → Menxia → Assigned → Doing → Review → Done
                                                        ↗
                                              Blocked ──
```

### 自定义 Agent

在 `agents/<id>/SOUL.md` 中修改 Agent 的人格、职责和输出格式。

### 添加新的六部成员

1. 在 `agents/` 下新建目录，添加 `SOUL.md`
2. 在 `install.sh` 的 `AGENTS` 数组中添加新 ID
3. 在 `scripts/sync_agent_config.py` 的 `ID_LABEL` 中添加元信息
4. 重新运行 `./install.sh`

### 数据目录结构

```
data/
├── live_status.json          # 实时看板数据（每15秒更新）
├── agent_config.json         # Agent 配置（模型、Skills）
├── tasks_source.json         # 手动任务数据源
├── pending_model_changes.json # 待执行的模型变更
├── model_change_log.json     # 模型变更历史
└── sync_status.json          # 同步状态
```

---

## 📁 项目结构

```
openclaw-sansheng-liubu/
├── README.md                  # 本文件
├── README_EN.md               # English docs
├── LICENSE                    # MIT License
├── CONTRIBUTING.md            # 贡献指南
├── install.sh                 # 一键安装脚本
├── agents/                    # Agent 配置模板
│   ├── zhongshu/SOUL.md       # 中书省人格
│   ├── menxia/SOUL.md         # 门下省人格
│   ├── shangshu/SOUL.md       # 尚书省人格
│   └── [hubu|libu|bingbu|xingbu|gongbu]/SOUL.md
├── dashboard/
│   ├── dashboard.html         # 看板前端（单文件，无依赖）
│   └── server.py              # 本地 API 服务器（Python标准库）
├── scripts/
│   ├── sync_from_openclaw_runtime.py  # 从 OpenClaw 会话同步任务
│   ├── sync_agent_config.py           # 同步 Agent 配置
│   ├── apply_model_changes.py         # 应用模型变更
│   ├── refresh_live_data.py           # 生成 live_status.json
│   └── run_loop.sh                    # 自动刷新循环（每15秒）
├── docs/
│   ├── getting-started.md     # 详细上手指南
│   ├── architecture.md        # 架构深度解析
│   ├── configuration.md       # 配置参考
│   └── screenshots/           # 截图
└── data/                      # 运行时数据（gitignored）
    └── .gitkeep
```

---

## 🔧 使用方法

### 向 AI 下旨

通过你配置的消息渠道（Feishu/Telegram/Signal）发送消息给 `zhongshu` Agent：

```
给我设计一个用户注册系统，要求：
1. RESTful API（FastAPI）
2. PostgreSQL 数据库
3. JWT 鉴权
4. 完整测试用例
5. 部署文档
```

中书省会自动：
1. 回复确认收旨
2. 规划子任务分配给各部门
3. 发给门下省审核
4. 审核通过后由尚书省统一派发
5. 各部并行/串行执行
6. 汇总结果回奏

### 手动创建任务

直接编辑 `data/tasks_source.json`：

```json
[
  {
    "id": "JJC-20240101-001",
    "title": "任务标题",
    "official": "兵部尚书",
    "org": "兵部",
    "state": "Doing",
    "now": "当前进展描述",
    "eta": "2024-01-02 18:00",
    "block": "无",
    "output": "/path/to/output",
    "ac": "验收标准"
  }
]
```

---

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

- 🐛 [提交 Bug](https://github.com/cft0808/openclaw-sansheng-liubu/issues/new?template=bug_report.md)
- 💡 [功能建议](https://github.com/cft0808/openclaw-sansheng-liubu/issues/new?template=feature_request.md)
- 🔧 [提交 PR](https://github.com/cft0808/openclaw-sansheng-liubu/pulls)

---

## 📄 License

[MIT](LICENSE) · 由 [OpenClaw](https://openclaw.ai) 社区构建

---

<p align="center">
  <sub>⚔️ 以古制御新技，以智慧驾驭 AI</sub>
</p>
