# 远程 Skills 快速入门

## 5 分钟体验

### 1. 启动服务器

```bash
# 确保你在项目根目录
python3 dashboard/server.py
# 输出: 三省六部看板启动 → http://127.0.0.1:7891
```

### 2. 添加默认 Skill（CLI）

```bash
# 为门下省添加 MiniMax CLI skill
python3 scripts/skill_manager.py add-remote \
  --agent menxia \
  --name mmx_cli \
  --source https://raw.githubusercontent.com/MiniMax-AI/cli/main/skill/SKILL.md \
  --description "MiniMax 多模态 CLI 技能"

# 输出:
# ⏳ 正在从 https://raw.githubusercontent.com/... 下载...
# ✅ 技能 mmx_cli 已添加到 menxia
#    路径: /Users/xxx/.openclaw/workspace-menxia/skills/mmx_cli/SKILL.md
#    大小: 14655 字节
```

### 3. 列出所有远程 Skills

```bash
python3 scripts/skill_manager.py list-remote

# 输出:
# 📋 共 1 个远程 skills：
# 
# Agent       | Skill 名称           | 描述                           | 添加时间
# ------------|----------------------|--------------------------------|----------
# menxia      | mmx_cli              | MiniMax 多模态 CLI 技能         | 2026-03-02
```

### 4. 查看 API 响应

```bash
curl http://localhost:7891/api/remote-skills-list | jq .

# 输出:
# {
#   "ok": true,
#   "remoteSkills": [
#     {
#       "skillName": "mmx_cli",
#       "agentId": "menxia",
#       "sourceUrl": "https://raw.githubusercontent.com/...",
#       "description": "MiniMax 多模态 CLI 技能",
#       "localPath": "/Users/xxx/.openclaw/workspace-menxia/skills/mmx_cli/SKILL.md",
#       "addedAt": "2026-03-02T14:30:00Z",
#       "lastUpdated": "2026-03-02T14:30:00Z",
#       "status": "valid"
#     }
#   ],
#   "count": 1,
#   "listedAt": "2026-03-02T14:35:00Z"
# }
```

---

## 常见操作

### 一键导入默认 skills

```bash
python3 scripts/skill_manager.py import-official-hub \
  --agents menxia,shangshu
```

这会为指定 agent 添加默认可用的 `mmx_cli` skill。旧的 `openclaw-ai/skills-hub` 仓库当前不可用，因此不再作为默认官方源。

如果你维护自己的 Skills Hub，可以通过环境变量或本地配置指定：

```bash
export OPENCLAW_SKILLS_HUB_BASE=https://your-hub/raw-base
# 或
echo "https://your-hub/raw-base" > ~/.openclaw/skills-hub-url
```

### 更新某个 Skill 到最新版本

```bash
python3 scripts/skill_manager.py update-remote \
  --agent menxia \
  --name mmx_cli

# 输出:
# ⏳ 正在从 https://raw.githubusercontent.com/... 下载...
# ✅ 技能 mmx_cli 已添加到 menxia
# ✅ 技能已更新
#    路径: /Users/xxx/.openclaw/workspace-menxia/skills/mmx_cli/SKILL.md
#    大小: 14655 字节
```

### 移除某个 Skill

```bash
python3 scripts/skill_manager.py remove-remote \
  --agent menxia \
  --name mmx_cli

# 输出:
# ✅ 技能 mmx_cli 已从 menxia 移除
```

---

## 看板 UI 操作

### 在看板中添加 Remote Skill

1. 打开 http://localhost:7891
2. 进入 🔧 **技能配置** 面板
3. 点击 **➕ 添加远程 Skill** 按钮
4. 填写表单：
   - **Agent**: 从下拉列表选择（如 menxia）
   - **Skill 名称**: 输入内部 ID 如 `mmx_cli`
   - **远程 URL**: 粘贴 GitHub URL 如 `https://raw.githubusercontent.com/MiniMax-AI/cli/main/skill/SKILL.md`
   - **中文描述**: 可选，如 `MiniMax 多模态 CLI 技能`
5. 点击 **导入** 按钮
6. 等待 1-2 秒，看到 ✅ 成功提示

### 管理已添加的 Skills

在看板 → 🔧 技能配置 → **远程 Skills** 标签页：

- **查看**: 点击 Skill 名称查看 SKILL.md 内容
- **更新**: 点击 🔄 重新从源 URL 下载最新版本
- **删除**: 点击 ✕ 移除本地副本
- **复制 URL**: 快速分享给他人

---

## 创建自己的 Skill 库

### 目录结构

```
my-skills-hub/
├── code_review/
│   └── SKILL.md          # 代码审查能力
├── api_design/
│   └── SKILL.md          # API 设计审查
├── data_analysis/
│   └── SKILL.md          # 数据分析
└── README.md
```

### SKILL.md 模板

```markdown
---
name: my_custom_skill
description: 简短描述
version: 1.0.0
tags: [tag1, tag2]
---

# Skill 完整名称

详细描述...

## 输入

说明接收什么参数

## 处理流程

具体步骤...

## 输出规范

输出格式说明
```

### 上传到 GitHub

```bash
git init
git add .
git commit -m "Initial commit: my-skills-hub"
git remote add origin https://github.com/yourname/my-skills-hub
git push -u origin main
```

### 导入自己的 Skill

```bash
python3 scripts/skill_manager.py add-remote \
  --agent zhongshu \
  --name my_skill \
  --source https://raw.githubusercontent.com/yourname/my-skills-hub/main/my_skill/SKILL.md \
  --description "我的定制技能"
```

---

## API 完整参考

### POST /api/add-remote-skill

添加远程 skill。

**请求：**
```bash
curl -X POST http://localhost:7891/api/add-remote-skill \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "zhongshu",
    "skillName": "code_review",
    "sourceUrl": "https://raw.githubusercontent.com/...",
    "description": "代码审查"
  }'
```

**响应 (200):**
```json
{
  "ok": true,
  "message": "技能 code_review 已从远程源添加到 zhongshu",
  "skillName": "code_review",
  "agentId": "zhongshu",
  "source": "https://raw.githubusercontent.com/...",
  "localPath": "/Users/xxx/.openclaw/workspace-zhongshu/skills/code_review/SKILL.md",
  "size": 2048,
  "addedAt": "2026-03-02T14:30:00Z"
}
```

### GET /api/remote-skills-list

列出所有远程 skills。

```bash
curl http://localhost:7891/api/remote-skills-list
```

**响应:**
```json
{
  "ok": true,
  "remoteSkills": [
    {
      "skillName": "mmx_cli",
      "agentId": "menxia",
      "sourceUrl": "https://raw.githubusercontent.com/...",
      "description": "MiniMax 多模态 CLI 技能",
      "localPath": "/Users/xxx/.openclaw/workspace-menxia/skills/mmx_cli/SKILL.md",
      "addedAt": "2026-03-02T14:30:00Z",
      "lastUpdated": "2026-03-02T14:30:00Z",
      "status": "valid"
    }
  ],
  "count": 1,
  "listedAt": "2026-03-02T14:35:00Z"
}
```

### POST /api/update-remote-skill

更新远程 skill 为最新版本。

```bash
curl -X POST http://localhost:7891/api/update-remote-skill \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "zhongshu",
    "skillName": "code_review"
  }'
```

### DELETE /api/remove-remote-skill

移除远程 skill。

```bash
curl -X POST http://localhost:7891/api/remove-remote-skill \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "zhongshu",
    "skillName": "code_review"
  }'
```

---

## 故障排查

### Q: 下载失败，提示 "Connection timeout"

**A:** 检查网络连接和 URL 有效性

```bash
curl -I https://raw.githubusercontent.com/...
# 应该返回 HTTP/1.1 200 OK
```

### Q: 文件格式无效

**A:** 确保 SKILL.md 以 YAML frontmatter 开头

```markdown
---
name: skill_name
description: 描述
---

# 正文开始...
```

### Q: 导入后看不到 Skill

**A:** 刷新看板或检查 Agent 是否配置正确

```bash
# 检查 Agent 是否存在
python3 scripts/skill_manager.py list-remote

# 检查本地文件
ls -la ~/.openclaw/workspace-zhongshu/skills/
```

---

## 更多信息

- 📚 [完整指南](remote-skills-guide.md)
- 🏛️ [架构文档](task-dispatch-architecture.md)
- 🤝 [项目贡献](../CONTRIBUTING.md)
