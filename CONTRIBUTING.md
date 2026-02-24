# Contributing to 三省六部

感谢你对本项目的兴趣！以下是贡献指南。

## 如何贡献

### 报告 Bug

请使用 [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) 模板提交 Issue，包含：
- OpenClaw 版本
- 操作系统
- 复现步骤
- 期望行为 vs 实际行为

### 提交功能建议

使用 [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) 模板。

### 提交 Pull Request

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/my-feature`
3. 提交改动：`git commit -m 'feat: add my feature'`
4. 推送：`git push origin feature/my-feature`
5. 创建 Pull Request

### Commit 格式

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式
refactor: 代码重构
test: 测试
chore: 杂项维护
```

## 开发环境

```bash
git clone https://github.com/cft0808/edict.git
cd edict
./install.sh

# 启动开发服务器
python3 dashboard/server.py --port 7892
```

## 常见贡献方向

- 🌐 **新语言支持**：英文/日文 README
- 🎨 **看板 UI 改进**：新视图、更好的响应式设计
- 🤖 **新 Agent 角色**：适合特定场景的专职 Agent
- 📦 **Skills 扩展**：各部门专用技能包
- 🔗 **集成扩展**：对接 Notion/Jira/Linear 等工具

## 行为准则

请保持友善和建设性。我们欢迎所有人参与贡献。
