# ⚔️ SanSheng LiuBu · OpenClaw Multi-Agent Orchestration

<p align="center">
  <a href="README.md">中文</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#dashboard">Dashboard</a>
</p>

<p align="center">
  <img src="docs/screenshots/01-kanban-main.png" alt="SanSheng LiuBu Dashboard" width="100%">
</p>

**SanSheng LiuBu** (三省六部, Three Departments & Six Ministries) is a **multi-agent orchestration system** built on [OpenClaw](https://openclaw.ai), inspired by the ancient Chinese administrative system. Complex tasks flow through specialized AI agents in a structured, auditable pipeline — with a real-time dashboard for monitoring and control.

> User issues command → Planning (中书省) → Review (门下省) → Dispatch (尚书省) → Execution (六部) → Report back

## ✨ Features

- 🏛️ **9 specialized agents** with defined roles and communication permissions
- 📋 **Real-time Kanban** with state columns, department filters, and full-text search  
- 📊 **Work history** grouped by department with full audit trails
- ⏱️ **Timeline view** visualizing the complete task flow
- ⚙️ **Model configuration** — change any agent's LLM model from the dashboard, takes effect in ~5 seconds
- 🛠️ **Skills viewer** — see installed OpenClaw skills per department
- 💊 **Heartbeat monitoring** — live agent health with activity indicators
- 🔄 **Auto-refresh** with 15-second countdown

## 🚀 Quick Start

### Prerequisites

- [OpenClaw](https://openclaw.ai) installed and initialized
- Python 3.9+
- macOS / Linux

### Install

```bash
git clone https://github.com/cft0808/openclaw-sansheng-liubu.git
cd openclaw-sansheng-liubu
chmod +x install.sh
./install.sh
```

### Launch Dashboard

```bash
# Terminal 1: Data sync loop
bash scripts/run_loop.sh

# Terminal 2: Dashboard server
python3 dashboard/server.py

# Open browser
open http://127.0.0.1:7891
```

## 🏛️ Architecture

```
                    ┌─────────────────────────┐
                    │       User (皇上)         │
                    │  Feishu / Telegram / etc. │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    📜 Planning (中书省)   │
                    │  Receive → Plan → Break  │
                    └────────────┬────────────┘
                                 │ submit for review
                    ┌────────────▼────────────┐
                    │    🔍 Review (门下省)     │
                    │  Audit → Approve/Reject  │
                    └────────────┬────────────┘
                                 │ approved
                    ┌────────────▼────────────┐
                    │   📮 Dispatch (尚书省)    │
                    │  Assign → Collect → Report│
                    └──┬──────┬──────┬───┬────┘
           ┌───────────┘      │      │   └──────────┐
      ┌────▼────┐    ┌────────▼──┐  ┌▼────────┐  ┌──▼────┐
      │📝 Docs  │    │ 💰 Data   │  │⚔️ Code  │  │🔧 Ops │
      │ (礼部)  │    │  (户部)   │  │ (兵部)  │  │(工部) │
      └─────────┘    └───────────┘  └─────────┘  └───────┘
                          ⚖️ Compliance (刑部) — always watching
```

### Agent Roles

| Department | Agent ID | Role |
|-----------|----------|------|
| 📜 Planning (中书省) | `zhongshu` | Receive commands, plan tasks, generate execution plans |
| 🔍 Review (门下省) | `menxia` | Audit plans, quality control, approve/reject |
| 📮 Dispatch (尚书省) | `shangshu` | Assign tasks, coordinate departments, collect results |
| 📝 Documentation (礼部) | `libu` | Write docs, generate reports, define standards |
| 💰 Data/Resources (户部) | `hubu` | Data processing, resource generation, cost tracking |
| ⚔️ Engineering (兵部) | `bingbu` | Code implementation, algorithms, system checks |
| ⚖️ Compliance (刑部) | `xingbu` | Security audit, compliance checks, red-line enforcement |
| 🔧 Infrastructure (工部) | `gongbu` | CI/CD, deployment, automation tooling |

## 📋 Dashboard

| Tab | Description |
|-----|-------------|
| 📋 Kanban | Task cards by state with filter/search |
| 📰 Morning Briefing | Daily auto-fetched tech/finance news digest |
| 👥 Officials | Leaderboard with token usage & activity stats |
| ⚙️ Models | Per-agent LLM model configuration with live apply |
| 🛠️ Skills | Installed skills per agent workspace |

<details>
<summary>📸 Screenshots</summary>

**Kanban** — Task cards with heartbeat indicators, department filters, and full-text search.
![Kanban](docs/screenshots/01-kanban-main.png)

**Morning Briefing** — Auto-curated daily news across tech and business channels.
![Morning Briefing](docs/screenshots/02-morning-briefing.png)

**Task Detail** — Click any card to expand the full flow log from command to completion.
![Task Detail](docs/screenshots/03-task-detail.png)

**Model Config** — Switch any agent's LLM model; Gateway restarts automatically (~5s).
![Model Config](docs/screenshots/04-model-config.png)

**Skills Config** — See installed OpenClaw skills per department at a glance.
![Skills Config](docs/screenshots/05-skills-config.png)

**Officials Overview** — Merit leaderboard with token costs and session statistics.
![Officials Overview](docs/screenshots/06-official-overview.png)

</details>

## 📄 License

[MIT](LICENSE)
