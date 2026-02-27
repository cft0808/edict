# 🤝 参与贡献

<p align="center">
  <strong>三省六部欢迎各路英雄好汉 ⚔️</strong><br>
  <sub>无论是修一个 typo 还是设计一个新的 Agent 角色，我们都万分感谢</sub>
</p>

---

## 📋 贡献方式

### 🐛 报告 Bug

请使用 [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) 模板提交 Issue，包含：
- OpenClaw 版本（`openclaw --version`）
- Python 版本（`python3 --version`）
- 操作系统
- 复现步骤（越详细越好）
- 期望行为 vs 实际行为
- 截图（如果涉及看板 UI）

### 💡 功能建议

使用 [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) 模板。

我们推荐用"旨意"的格式来描述你的需求 —— 就像给皇上写奏折一样 😄

### 🔧 提交 Pull Request

```bash
# 1. Fork 本仓库
# 2. 克隆你的 Fork
git clone https://github.com/<your-username>/edict.git
cd edict

# 3. 创建功能分支
git checkout -b feat/my-awesome-feature

# 4. 开发 & 测试
python3 dashboard/server.py  # 启动看板验证

# 5. 提交
git add .
git commit -m "feat: 添加了一个很酷的功能"

# 6. 推送 & 创建 PR
git push origin feat/my-awesome-feature
```

---

## 🏗️ 开发环境

### 前置条件
- [OpenClaw](https://openclaw.ai) 已安装
- Python 3.9+
- macOS / Linux

### 本地启动

```bash
# 安装
./install.sh

# 启动数据刷新（后台运行）
bash scripts/run_loop.sh &

# 启动看板服务器（开发端口）
python3 dashboard/server.py --port 7892

# 打开浏览器
open http://127.0.0.1:7892
```

### 项目结构速览

| 目录/文件 | 说明 | 改动频率 |
|----------|------|---------|
| `dashboard/dashboard.html` | 看板前端（单文件，~2500 行） | 🔥 高 |
| `dashboard/server.py` | API 服务器（stdlib，~1200 行） | 🔥 高 |
| `agents/*/SOUL.md` | 12 个 Agent 人格模板 | 🔶 中 |
| `scripts/kanban_update.py` | 看板 CLI + 数据清洗（~300 行） | 🔶 中 |
| `scripts/*.py` | 数据同步 / 自动化脚本 | 🔶 中 |
| `tests/test_e2e_kanban.py` | E2E 看板测试（17 断言） | 🔶 中 |
| `install.sh` | 安装脚本 | 🟢 低 |

---

## 📝 Commit 规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat:     ✨ 新功能
fix:      🐛 修复 Bug
docs:     📝 文档更新
style:    🎨 代码格式（不影响逻辑）
refactor: ♻️ 代码重构
perf:     ⚡ 性能优化
test:     ✅ 测试
chore:    🔧 杂项维护
ci:       👷 CI/CD 配置
```

示例：
```
feat: 添加奏折导出为 PDF 功能
fix: 修复模型切换后 Gateway 未重启的问题
docs: 更新 README 截图
```

---

## 🎯 特别欢迎的贡献方向

### 🎨 看板 UI
- 深色/浅色主题切换
- 响应式布局优化
- 动画效果增强
- 可访问性（a11y）改进

### 🤖 新 Agent 角色
- 适合特定行业/场景的专职 Agent
- 新的 SOUL.md 人格模板
- Agent 间协作模式创新

### 📦 Skills 生态
- 各部门专用技能包
- MCP 集成技能
- 数据处理 / 代码分析 / 文档生成专项技能

### 🔗 第三方集成
- Notion / Jira / Linear 同步
- GitHub Issues / PR 联动
- Slack / Discord 消息渠道
- Webhook 扩展

### 🌐 国际化
- 日文 / 韩文 / 西班牙文翻译
- 看板 UI 多语言支持

### 📱 移动端
- 响应式适配
- PWA 支持
- 移动端操作优化

---

## 🧪 测试

```bash
# 编译检查
python3 -m py_compile dashboard/server.py
python3 -m py_compile scripts/kanban_update.py

# E2E 看板测试（9 场景 17 断言）
python3 tests/test_e2e_kanban.py

# 验证数据同步
python3 scripts/refresh_live_data.py
python3 scripts/sync_agent_config.py

# 启动服务器验证 API
python3 dashboard/server.py &
curl -s http://localhost:7891/api/live-status | python3 -m json.tool | head -20
```

---

## 📏 代码风格

- **Python**: PEP 8，使用 pathlib 处理路径
- **HTML/CSS/JS**: 单文件，CSS 变量命名以 `--` 开头，JS 函数名使用 camelCase
- **Markdown**: 标题使用 `#`，列表使用 `-`，代码块标注语言

---

## 🙏 行为准则

- 保持友善和建设性
- 尊重不同的观点和经验
- 接受建设性的批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

**我们对骚扰行为零容忍。**

---

## 📬 联系方式

- GitHub Issues: [提交问题](https://github.com/cft0808/edict/issues)
- GitHub Discussions: [社区讨论](https://github.com/cft0808/edict/discussions)

---

<p align="center">
  <sub>感谢每一位贡献者，你们是三省六部的基石 ⚔️</sub>
</p>
