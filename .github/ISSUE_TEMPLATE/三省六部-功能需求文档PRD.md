# 三省六部 · 功能需求文档（PRD）

> 目标：以下每个功能模块均按"数据结构 → 核心逻辑 → API接口 → 前端交互"拆解，可直接转化为代码实现。

---

## 一、让人上瘾的功能

---

### 1.1 奏折系统

#### 背景
任务完成后，系统自动生成一份结构化的"奏折"文档，作为该任务从下旨到完成的完整存档。解决"事情办完了但回头找不到过程和结论"的问题。

#### 数据结构

```json
{
  "id": "ZZ-20260224-003",
  "task_id": "JJC-20260224-003",
  "title": "关于用户注册系统开发事宜的回奏",
  "submitted_by": "尚书省",
  "submitted_at": "2026-02-24T18:30:00Z",
  "status": "已呈御览",
  "priority": "P1",
  "origin": {
    "type": "圣旨",
    "original_text": "给我设计一个用户注册系统，RESTful API，JWT鉴权",
    "issued_at": "2026-02-24T09:00:00Z"
  },
  "planning": {
    "agent": "zhongshu",
    "summary": "拆解为4个子任务：API设计、数据库建表、鉴权模块、测试用例",
    "sub_tasks": [
      {"id": "SUB-001", "title": "RESTful API 开发", "assigned_to": "bingbu"},
      {"id": "SUB-002", "title": "PostgreSQL 表结构设计", "assigned_to": "hubu"},
      {"id": "SUB-003", "title": "JWT 鉴权实现", "assigned_to": "bingbu"},
      {"id": "SUB-004", "title": "部署文档撰写", "assigned_to": "libu"}
    ]
  },
  "review": {
    "agent": "menxia",
    "result": "准奏",
    "notes": "方案完整，建议增加密码强度校验",
    "reviewed_at": "2026-02-24T09:15:00Z"
  },
  "execution": {
    "departments": [
      {
        "agent": "bingbu",
        "task": "API开发 + JWT鉴权",
        "status": "completed",
        "duration_minutes": 45,
        "tokens_used": 12800,
        "output_path": "/workspace-bingbu/outputs/user-auth-api/"
      },
      {
        "agent": "hubu",
        "task": "数据库表结构",
        "status": "completed",
        "duration_minutes": 15,
        "tokens_used": 3200,
        "output_path": "/workspace-hubu/outputs/db-schema.sql"
      },
      {
        "agent": "libu",
        "task": "部署文档",
        "status": "completed",
        "duration_minutes": 20,
        "tokens_used": 5600,
        "output_path": "/workspace-libu/outputs/deploy-guide.md"
      }
    ],
    "total_duration_minutes": 52,
    "total_tokens": 21600
  },
  "deliverables": [
    {"name": "API 源码", "path": "/outputs/user-auth-api/", "type": "code"},
    {"name": "数据库脚本", "path": "/outputs/db-schema.sql", "type": "sql"},
    {"name": "部署文档", "path": "/outputs/deploy-guide.md", "type": "doc"}
  ],
  "verdict": "各部办差妥当，产出齐备，呈请御览。",
  "pending_decisions": []
}
```

#### 存储位置
`data/memorials/ZZ-20260224-003.json`，同时在 `data/memorials_index.json` 中维护索引。

#### 核心逻辑

触发条件：任务状态流转到 `Done` 时，自动调用奏折生成。

```
输入：task_id
流程：
  1. 从 live_status.json 读取该任务完整信息
  2. 从各 agent session history 中提取该任务相关的所有消息
  3. 按时间线组装 origin → planning → review → execution 四段
  4. 计算汇总数据（总耗时、总token、参与部门）
  5. 生成奏折 JSON，写入 data/memorials/
  6. 更新 memorials_index.json
  7. 通过飞书推送摘要通知
输出：奏折 JSON 文件 + 飞书通知
```

#### 生成脚本
`scripts/generate_memorial.py`

```
参数：
  --task-id  STRING  必填，任务ID
  --format   STRING  可选，json（默认）| markdown | html

功能：
  - 读取 data/live_status.json 中对应任务
  - 遍历 ~/.openclaw/agents/*/sessions/ 目录，grep 任务ID 关联的 session 消息
  - 组装奏折结构
  - 写入 data/memorials/
```

#### API 接口

```
GET  /api/memorials                     # 奏折列表（支持分页、按日期/部门过滤）
GET  /api/memorials/:id                 # 单个奏折详情
GET  /api/memorials/:id/export?fmt=md   # 导出为 Markdown/HTML
POST /api/memorials/generate            # 手动触发生成 {"task_id": "JJC-xxx"}
```

#### 前端页面：奏折阁

看板新增 tab："📜 奏折阁"

布局：
- 左侧：奏折列表，按日期倒序，每条显示标题、来源部门、日期、状态标签
- 右侧：奏折详情，分为"圣旨原文"、"中书规划"、"门下审议"、"执行详情"、"产出清单"五个折叠段落
- 顶部：按日期范围筛选 + 按部门筛选 + 全文搜索
- 每份奏折右上角："导出 Markdown"按钮

---

### 1.2 早朝 / 晚朝

#### 背景
每日定时自动生成运营简报推送给用户。早朝关注"今天该干什么"，晚朝关注"今天干了什么"。

#### 数据结构

```json
{
  "id": "CHAOBAO-20260224-AM",
  "type": "morning",
  "date": "2026-02-24",
  "generated_at": "2026-02-24T09:00:00Z",
  "sections": {
    "pending_tasks": [
      {"task_id": "JJC-xxx", "title": "...", "priority": "P1", "assigned_to": "bingbu", "eta": "..."}
    ],
    "overdue_tasks": [
      {"task_id": "JJC-yyy", "title": "...", "overdue_hours": 18, "assigned_to": "hubu"}
    ],
    "blocked_tasks": [
      {"task_id": "JJC-zzz", "title": "...", "block_reason": "等待外部API权限"}
    ],
    "agent_health": [
      {"agent_id": "shangshu", "status": "active", "last_heartbeat": "..."},
      {"agent_id": "bingbu", "status": "stale", "last_heartbeat": "...", "stale_minutes": 45}
    ],
    "resource_summary": {
      "total_tokens_yesterday": 85000,
      "top_consumer": {"agent_id": "bingbu", "tokens": 32000},
      "estimated_cost_usd": 1.28
    },
    "news_briefing": [
      {"title": "...", "source": "...", "summary": "...", "url": "..."}
    ]
  },
  "summary_text": "今日待办 5 件（P1: 2件），超期 1 件，阻塞 1 件。各部运转正常，兵部心跳略有延迟。"
}
```

晚朝结构相同，`type` 为 `evening`，`sections` 额外包含：

```json
{
  "completed_today": [
    {"task_id": "JJC-xxx", "title": "...", "completed_by": "libu", "duration_minutes": 30}
  ],
  "efficiency_stats": {
    "tasks_completed": 8,
    "avg_completion_minutes": 35,
    "rejection_count": 1,
    "rejection_reason": "户部报表缺少数据来源标注"
  },
  "token_breakdown": {
    "zhongshu": 4500,
    "menxia": 3200,
    "shangshu": 8900,
    "hubu": 12000,
    "libu": 8500,
    "bingbu": 32000,
    "xingbu": 2100,
    "gongbu": 1800
  }
}
```

#### 存储位置
`data/briefings/CHAOBAO-20260224-AM.json`

#### 核心逻辑

```
早朝（每天 09:00 触发）：
  1. 读取 live_status.json，筛选状态不为 Done 的所有任务
  2. 按优先级排序，标记超期任务（当前时间 > eta）
  3. 读取各 agent 心跳数据，判断健康状态
     - last_heartbeat < 10min → active（绿）
     - 10min ~ 30min → stale（黄）
     - > 30min → down（红）
  4. 统计昨日 token 消耗（从 agent session 日志或 billing 数据提取）
  5. （可选）调用新闻抓取 skill，获取今日科技/财经简报
  6. 组装 JSON，写入 data/briefings/
  7. 生成摘要文本，通过飞书推送

晚朝（每天 18:00 触发）：
  1. 读取今日所有状态变更为 Done 的任务
  2. 统计完成数、平均耗时、被驳回次数及原因
  3. 统计今日各 agent token 消耗明细
  4. 与昨日对比，计算效率变化趋势
  5. 组装 JSON，写入 data/briefings/
  6. 推送晚朝简报
```

#### 触发方式

OpenClaw cron 配置（写入 openclaw.json）：

```json
{
  "cron": {
    "jobs": [
      {
        "name": "morning-briefing",
        "schedule": "0 9 * * *",
        "tz": "Asia/Shanghai",
        "agentId": "shangshu",
        "message": "执行早朝巡检，生成今日简报并通过飞书呈报皇上"
      },
      {
        "name": "evening-briefing",
        "schedule": "0 18 * * *",
        "tz": "Asia/Shanghai",
        "agentId": "shangshu",
        "message": "执行晚朝总结，汇总今日各部完成情况和资源消耗，通过飞书呈报皇上"
      }
    ]
  }
}
```

生成脚本：`scripts/generate_briefing.py`

```
参数：
  --type     STRING  morning | evening
  --date     STRING  可选，默认今天 YYYY-MM-DD
  --push     BOOL    是否推送飞书，默认 true
```

#### API 接口

```
GET  /api/briefings                          # 简报列表（支持按日期、类型过滤）
GET  /api/briefings/:id                      # 单个简报详情
GET  /api/briefings/latest?type=morning      # 获取最近一条早朝/晚朝
POST /api/briefings/generate                 # 手动触发 {"type": "morning"}
```

#### 前端页面：朝报

看板新增 tab："🌅 朝报"

布局：
- 顶部：日期选择器（日历形式），选中某天显示当日早朝+晚朝
- 早朝卡片：左侧待办列表（P0/P1 红色高亮，超期任务闪烁），右侧 agent 健康状态网格
- 晚朝卡片：左侧完成列表，右侧 token 消耗饼图 + 效率趋势折线图（最近7天）
- 底部：摘要文本区域，可一键复制

---

### 1.3 功过簿

#### 背景
为每个 agent 维护一份持续更新的绩效档案，用于评估各部门效率、成本、质量，并支持自动化的模型升降级。

#### 数据结构

每个 agent 一个文件：`data/performance/bingbu.json`

```json
{
  "agent_id": "bingbu",
  "agent_name": "兵部",
  "stats": {
    "total_tasks": 156,
    "completed": 148,
    "rejected_by_menxia": 6,
    "blocked": 2,
    "completion_rate": 0.949,
    "avg_completion_minutes": 38.5,
    "total_tokens_used": 2450000,
    "avg_tokens_per_task": 16554
  },
  "monthly_trend": [
    {
      "month": "2026-01",
      "tasks_completed": 62,
      "avg_minutes": 42.1,
      "tokens_used": 980000,
      "rejection_rate": 0.048,
      "model": "claude-sonnet-4-5"
    },
    {
      "month": "2026-02",
      "tasks_completed": 86,
      "avg_minutes": 35.8,
      "tokens_used": 1470000,
      "rejection_rate": 0.035,
      "model": "claude-sonnet-4-5"
    }
  ],
  "rejection_log": [
    {
      "task_id": "JJC-xxx",
      "date": "2026-02-15",
      "reason": "代码缺少错误处理",
      "resolved": true,
      "retry_count": 1
    }
  ],
  "current_model": "claude-sonnet-4-5",
  "model_history": [
    {"model": "claude-haiku-4-5", "from": "2026-01-01", "to": "2026-01-15", "reason": "初始配置"},
    {"model": "claude-sonnet-4-5", "from": "2026-01-15", "to": null, "reason": "任务复杂度提升，手动升级"}
  ],
  "auto_scaling_rules": {
    "upgrade_trigger": "rejection_rate > 0.1 连续3天",
    "downgrade_trigger": "avg_tokens_per_task < 5000 连续7天 且 rejection_rate < 0.02",
    "enabled": false
  }
}
```

#### 核心逻辑

```
更新时机：每次任务状态变更时触发增量更新

流程：
  1. 监听 live_status.json 变更（run_loop.sh 每15秒同步时顺带执行）
  2. 对比上次快照，提取新的状态变更事件
  3. 更新对应 agent 的 stats 字段：
     - 完成 → completed + 1，累加 duration 和 tokens
     - 驳回 → rejected_by_menxia + 1，写入 rejection_log
     - 阻塞 → blocked + 1
  4. 重算 completion_rate、avg_completion_minutes、avg_tokens_per_task
  5. 每月1号自动归档上月数据到 monthly_trend
  6. 写回 data/performance/<agent_id>.json

自动升降级逻辑（可选，默认关闭）：
  if auto_scaling_rules.enabled:
    if 最近3天 rejection_rate > 0.1:
      升级模型（如 haiku → sonnet → opus）
      记录到 model_history
      写入 pending_model_changes.json 等待下次同步应用
    if 最近7天 avg_tokens < 5000 且 rejection_rate < 0.02:
      降级模型
      记录到 model_history
```

#### 更新脚本
`scripts/update_performance.py`

```
参数：
  --agent-id   STRING  可选，不填则更新全部
  --rebuild    BOOL    可选，从历史数据完整重建
```

#### API 接口

```
GET  /api/performance                        # 全部 agent 绩效概览
GET  /api/performance/:agent_id              # 单个 agent 详情
GET  /api/performance/:agent_id/trend        # 月度趋势数据（用于画图）
GET  /api/performance/ranking                # 排行榜（按完成率、效率、成本排序）
POST /api/performance/auto-scaling           # 开关自动升降级 {"agent_id": "bingbu", "enabled": true}
```

#### 前端页面：功过簿

看板新增 tab："📊 功过簿"

布局：
- 顶部：全局排行榜卡片，按完成率排名，展示前三名带🥇🥈🥉图标
- 中部：各 agent 绩效卡片网格（3列），每张卡片展示：
  - agent 名称 + 当前模型标签
  - 完成率圆环图
  - 本月完成数 / 平均耗时 / token 消耗三个数字
  - 被驳回次数（红色标注）
  - 点击展开详情
- 详情面板：
  - 月度趋势折线图（完成数、耗时、token 三条线）
  - 驳回记录列表（可展开查看原因和修复情况）
  - 模型变更历史时间线
  - 自动升降级开关 + 规则配置

---

## 二、让人离不开的功能

---

### 2.1 御批模式

#### 背景
高风险、高成本、涉及对外操作的任务不应全自动执行。御批模式在流程中插入人工审批节点，用户通过飞书"准"或"驳"即可控制流程继续或回退。

#### 数据结构

审批请求：`data/approvals/pending/<approval_id>.json`

```json
{
  "id": "AP-20260224-001",
  "task_id": "JJC-20260224-005",
  "type": "execution_approval",
  "trigger_rule": "estimated_cost_usd > 5.0",
  "requested_by": "menxia",
  "requested_at": "2026-02-24T10:30:00Z",
  "expires_at": "2026-02-24T22:30:00Z",
  "status": "pending",
  "context": {
    "task_title": "抓取竞品网站全量产品数据并生成分析报告",
    "plan_summary": "兵部爬取3个站点约5000页 → 户部数据清洗分析 → 礼部生成报告",
    "estimated_cost_usd": 8.50,
    "estimated_duration_minutes": 120,
    "risk_flags": ["对外网络请求", "大量token消耗", "可能触发反爬"]
  },
  "options": {
    "approve": "准奏，按计划执行",
    "reject": "驳回，需附理由",
    "modify": "准奏但需调整，需附修改意见"
  },
  "decision": null,
  "decision_at": null,
  "decision_note": null
}
```

审批规则配置：`data/approval_rules.json`

```json
{
  "rules": [
    {
      "id": "rule-cost",
      "name": "高成本任务",
      "condition": "estimated_cost_usd > 5.0",
      "action": "require_approval",
      "description": "预估成本超过 $5 的任务需要御批"
    },
    {
      "id": "rule-external",
      "name": "对外操作",
      "condition": "has_tag('external_api') || has_tag('send_email') || has_tag('publish')",
      "action": "require_approval",
      "description": "涉及对外请求、发邮件、发布内容的任务需要御批"
    },
    {
      "id": "rule-irreversible",
      "name": "不可逆操作",
      "condition": "has_tag('delete') || has_tag('deploy_production')",
      "action": "require_approval",
      "description": "删除数据、生产部署等不可逆操作需要御批"
    },
    {
      "id": "rule-multi-dept",
      "name": "跨三部门以上协作",
      "condition": "departments_count >= 3",
      "action": "require_approval",
      "description": "涉及3个及以上部门的复杂任务需要御批"
    }
  ],
  "default_timeout_hours": 12,
  "auto_reject_on_timeout": false,
  "notify_channel": "feishu"
}
```

#### 核心逻辑

```
触发节点：门下省审核通过后、尚书省派发之前

流程：
  1. 门下省审核通过，将方案提交给尚书省
  2. 尚书省收到方案后，先运行规则引擎：
     for rule in approval_rules:
       if evaluate(rule.condition, task_context):
         创建审批请求 → 写入 data/approvals/pending/
         通过飞书推送审批卡片给用户
         任务状态标记为 "待御批"
         return  # 暂停流程
  3. 如果没有规则触发，正常派发执行

飞书审批卡片内容：
  标题：📜 御批 | {task_title}
  正文：
    触发规则：{trigger_rule_name}
    中书方案摘要：{plan_summary}
    预估成本：${estimated_cost_usd}
    预估耗时：{estimated_duration_minutes} 分钟
    风险提示：{risk_flags}
  按钮：
    [准奏] → 用户点击后回复 "准"
    [驳回] → 弹出输入框要求填写理由

用户回复处理：
  "准" / "准奏" / "approve" → 
    更新 approval status = "approved"
    任务状态从 "待御批" → "Assigned"
    尚书省继续派发
  "驳" / "驳回" + 理由 →
    更新 approval status = "rejected"
    任务状态从 "待御批" → "Menxia"（退回门下省重新审议）
    理由写入 decision_note
  "改" / "准但改" + 修改意见 →
    更新 approval status = "approved_with_changes"
    修改意见写入 decision_note
    尚书省根据修改意见调整方案后派发

超时处理：
  if current_time > expires_at:
    if auto_reject_on_timeout:
      自动驳回
    else:
      再次推送提醒
```

#### 脚本
- `scripts/check_approval_rules.py` — 规则引擎，输入 task context，输出是否需要审批
- `scripts/process_approval.py` — 处理用户审批决定，更新状态，触发后续流程

#### API 接口

```
GET    /api/approvals                          # 审批列表（pending / approved / rejected）
GET    /api/approvals/:id                      # 单个审批详情
POST   /api/approvals/:id/decide               # 提交决定 {"decision": "approve|reject|modify", "note": "..."}
GET    /api/approval-rules                     # 获取规则列表
PUT    /api/approval-rules/:rule_id            # 修改规则
POST   /api/approval-rules                     # 新增规则
DELETE /api/approval-rules/:rule_id            # 删除规则
```

#### 前端交互

看板任务卡片上：
- 状态为"待御批"的卡片增加金色边框 + ⏳ 图标
- 点击展开后显示审批详情 + "准奏" / "驳回" 按钮（从看板也能直接操作，不只依赖飞书）
- 已审批的卡片显示审批结果标签：✅ 已准奏 / ❌ 已驳回 / ✏️ 准奏（附修改意见）

设置页新增"审批规则"管理面板：
- 规则列表，每条可编辑条件和描述
- 开关"超时自动驳回"
- 设置默认超时时长

---

### 2.2 国史馆（经验沉淀知识库）

#### 背景
每次踩坑、规则调整、门下省驳回的原因，自动沉淀为结构化的经验记录。Agent 处理新任务时可检索历史案例，避免重复犯错。

#### 数据结构

单条经验：`data/history_records/<record_id>.json`

```json
{
  "id": "GS-20260224-001",
  "type": "rejection_lesson",
  "source_task_id": "JJC-20260220-012",
  "created_at": "2026-02-20T15:00:00Z",
  "department": "hubu",
  "tags": ["数据分析", "数据来源", "驳回"],
  "title": "数据报表必须标注数据来源和提取时间",
  "trigger": "门下省驳回户部报表，原因：缺少数据来源说明",
  "lesson": "所有数据分析产出必须在报表末尾附上：数据来源、提取时间、筛选条件、数据范围。",
  "resolution": "户部 SOUL.md 输出标准中增加「附上数据来源和处理方法说明」条款。",
  "applied_to": ["hubu"],
  "auto_rule": {
    "when": "department == 'hubu' && task_type == 'data_analysis'",
    "inject_prompt": "注意：所有数据分析报表必须在末尾标注数据来源、提取时间、筛选条件。参见国史馆记录 GS-20260224-001。"
  },
  "referenced_count": 5,
  "last_referenced_at": "2026-02-24T11:00:00Z"
}
```

索引文件：`data/history_records/index.json`

```json
{
  "records": [
    {"id": "GS-20260224-001", "tags": ["数据分析", "驳回"], "department": "hubu", "title": "..."}
  ],
  "tag_counts": {"数据分析": 12, "驳回": 8, "安全": 5, "代码规范": 15},
  "total": 45
}
```

#### 核心逻辑

```
自动沉淀触发点：

1. 门下省驳回时：
   - 提取驳回原因
   - 生成 type="rejection_lesson" 记录
   - 提取关键词作为 tags
   - 生成 auto_rule（下次同类型任务时自动注入提示）

2. 任务阻塞解除时：
   - 提取阻塞原因和解决方案
   - 生成 type="block_resolution" 记录

3. 用户手动标记时：
   - 用户在飞书发送 "记档：{内容}" 
   - 生成 type="manual_note" 记录

4. 规则变更时：
   - SOUL.md 或 AGENTS.md 修改
   - 审批规则变更
   - 生成 type="rule_change" 记录

经验检索与注入：
  当 agent 收到新任务时：
  1. 提取任务关键词和 department
  2. 检索 index.json，匹配 tags 和 department
  3. 找到相关记录后，将 auto_rule.inject_prompt 拼接到 agent 的本次 context 中
  4. 更新 referenced_count 和 last_referenced_at
```

#### 检索脚本
`scripts/search_history.py`

```
参数：
  --query      STRING  搜索关键词
  --department STRING  按部门过滤
  --tags       STRING  按标签过滤（逗号分隔）
  --limit      INT     返回条数，默认5

输出：匹配的记录列表（按相关度 + 最近引用排序）
```

#### 注入脚本
`scripts/inject_history_context.py`

```
参数：
  --agent-id     STRING  目标 agent
  --task-context STRING  当前任务描述

功能：
  1. 从 task-context 提取关键词
  2. 检索匹配的国史馆记录
  3. 将 inject_prompt 内容格式化为 context 片段
  4. 输出可拼接到 agent prompt 的文本
```

#### API 接口

```
GET    /api/history                             # 记录列表（支持分页、标签、部门过滤）
GET    /api/history/:id                         # 单条记录详情
POST   /api/history                             # 手动新增记录
PUT    /api/history/:id                         # 编辑记录
DELETE /api/history/:id                         # 删除记录
GET    /api/history/search?q=数据来源&dept=hubu  # 全文检索
GET    /api/history/tags                         # 标签云数据
```

#### 前端页面：国史馆

看板新增 tab："📚 国史馆"

布局：
- 顶部：搜索栏 + 标签云（点击标签过滤）+ 部门筛选下拉
- 主体：记录卡片列表，每张卡片显示：
  - 类型图标（🔄 驳回教训 / 🚧 阻塞经验 / 📝 手动记录 / ⚙️ 规则变更）
  - 标题 + 标签
  - lesson 摘要（截断显示，展开看全文）
  - 被引用次数
  - 关联部门
- 点击展开：完整内容 + 关联任务链接 + auto_rule 展示 + 编辑按钮
- 右下角：浮动按钮 "+ 新增记录"

---

### 2.3 急递铺（紧急通道）

#### 背景
用户发送带特定前缀的指令时，任务跳过中书规划和门下审核，直接由尚书省派发执行。适用于紧急的小任务。事后自动标记为"未经审议"，列入待补审清单。

#### 数据结构

急递任务在标准任务结构上增加字段：

```json
{
  "id": "JJC-20260224-URGENT-001",
  "title": "修复线上登录接口500错误",
  "is_urgent": true,
  "urgent_reason": "线上故障",
  "skipped_stages": ["zhongshu_planning", "menxia_review"],
  "post_review_status": "pending",
  "post_review_result": null,
  "post_review_at": null
}
```

#### 核心逻辑

```
触发方式：
  用户消息以以下前缀开头时触发急递模式：
  - "急递：" / "急递:" / "加急：" / "加急:"
  - "urgent:" / "URGENT:"
  - "八百里加急："

识别流程：
  1. 飞书消息到达 zhongshu agent
  2. zhongshu 检测到急递前缀
  3. 跳过规划阶段，直接将任务转发给 shangshu
  4. shangshu 跳过门下省审核，直接判断目标部门并派发
  5. 任务状态直接进入 "Doing"，标记 is_urgent = true
  6. 在看板上显示 🔴 急递标签
  7. 任务完成后，自动进入"待补审"队列

补审流程：
  每日晚朝时，shangshu 检查所有 post_review_status == "pending" 的急递任务
  将补审清单推送给用户："今日有 N 件急递未经审议，是否需要门下省补审？"
  用户回复 "补审" → 送 menxia 走标准审核流程
  用户回复 "免审" → post_review_status = "waived"
```

#### 配置文件
`data/urgent_config.json`

```json
{
  "enabled": true,
  "prefixes": ["急递：", "急递:", "加急：", "加急:", "urgent:", "八百里加急："],
  "max_urgent_per_day": 10,
  "auto_post_review": true,
  "notify_on_trigger": true
}
```

#### API 接口

```
GET  /api/urgent/pending-review       # 待补审的急递任务列表
POST /api/urgent/:task_id/review      # 提交补审 {"action": "review|waive"}
GET  /api/urgent/config               # 获取急递配置
PUT  /api/urgent/config               # 修改急递配置
GET  /api/urgent/stats                # 急递使用统计（今日/本周/本月）
```

#### 前端交互

- 急递任务卡片：红色左边框 + 🔴"急递"标签 + "未经审议"灰色角标
- 看板顶部：如有待补审任务，显示横幅提醒："📮 有 N 件急递待补审"
- 点击横幅展开补审列表，可逐条"补审"或"免审"

---

## 三、让人愿意传播的功能

---

### 3.1 圣旨模板库

#### 背景
提供预设的常用场景模板，用户选模板、填参数、一键下旨。降低使用门槛，同时展示系统能力。

#### 数据结构

模板定义：`data/templates/<template_id>.json`

```json
{
  "id": "tpl-weekly-report",
  "name": "周报生成",
  "icon": "📝",
  "category": "日常办公",
  "description": "基于本周工作记录和看板数据，自动生成周报",
  "popularity": 89,
  "parameters": [
    {
      "key": "date_range",
      "label": "报告周期",
      "type": "date_range",
      "default": "本周",
      "required": true
    },
    {
      "key": "focus_areas",
      "label": "重点关注",
      "type": "multi_select",
      "options": ["项目进展", "风险事项", "下周计划", "资源消耗"],
      "default": ["项目进展", "下周计划"],
      "required": false
    },
    {
      "key": "format",
      "label": "输出格式",
      "type": "single_select",
      "options": ["Markdown", "飞书文档", "邮件正文"],
      "default": "Markdown",
      "required": true
    },
    {
      "key": "extra_notes",
      "label": "补充说明",
      "type": "text",
      "placeholder": "需要额外包含的内容或特别说明",
      "required": false
    }
  ],
  "generated_command": "生成{{date_range}}的周报，重点覆盖{{focus_areas}}，输出为{{format}}格式。{{extra_notes}}",
  "involved_departments": ["hubu", "libu"],
  "estimated_duration_minutes": 10,
  "estimated_cost_usd": 0.5
}
```

模板索引：`data/templates/index.json`

```json
{
  "categories": [
    {
      "name": "日常办公",
      "icon": "💼",
      "templates": ["tpl-weekly-report", "tpl-meeting-notes", "tpl-daily-standup"]
    },
    {
      "name": "数据分析",
      "icon": "📊",
      "templates": ["tpl-competitor-analysis", "tpl-sales-report", "tpl-user-growth"]
    },
    {
      "name": "工程开发",
      "icon": "⚙️",
      "templates": ["tpl-code-review", "tpl-api-design", "tpl-deploy-checklist"]
    },
    {
      "name": "内容创作",
      "icon": "✍️",
      "templates": ["tpl-blog-post", "tpl-product-copy", "tpl-email-campaign"]
    }
  ]
}
```

预置模板清单：

| ID | 名称 | 涉及部门 | 说明 |
|----|------|---------|------|
| tpl-weekly-report | 周报生成 | 户部+礼部 | 基于看板数据生成周报 |
| tpl-meeting-notes | 会议纪要整理 | 礼部 | 输入会议录音/要点，输出结构化纪要 |
| tpl-competitor-analysis | 竞品分析 | 兵部+户部+礼部 | 爬取+分析+报告 |
| tpl-code-review | 代码审查 | 兵部+刑部 | 代码+安全双重审查 |
| tpl-api-design | API 设计 | 中书+兵部 | 需求→设计→实现 |
| tpl-deploy-checklist | 上线检查单 | 兵部+工部+刑部 | 安全检查+部署+验证 |
| tpl-blog-post | 博客文章 | 礼部 | 给定主题生成文章 |
| tpl-email-campaign | 邮件模板 | 礼部 | 批量邮件文案 |
| tpl-sales-report | 销售数据报告 | 户部+礼部 | 数据分析+报告 |
| tpl-daily-standup | 每日站会摘要 | 尚书省 | 汇总各部今日进展 |

#### 核心逻辑

```
使用流程：
  1. 用户在看板选择模板
  2. 填写参数表单
  3. 点击"下旨"
  4. 前端将 generated_command 模板填充参数后，调用 API
  5. API 将填充后的命令通过 session 发送给 zhongshu agent
  6. 后续走标准三省六部流程

飞书快捷方式：
  用户在飞书发送 "/模板 周报" 或 "/tpl weekly"
  zhongshu 回复模板参数表单（飞书卡片消息形式）
  用户填写后确认，触发执行
```

#### API 接口

```
GET  /api/templates                         # 模板列表（按分类）
GET  /api/templates/:id                     # 模板详情（含参数定义）
POST /api/templates/:id/execute             # 填充参数并下旨 {"params": {"date_range": "2026-02-17~2026-02-23", ...}}
POST /api/templates                         # 用户自建模板
PUT  /api/templates/:id                     # 编辑模板
GET  /api/templates/popular                 # 热门模板排行
```

#### 前端页面：圣旨模板库

看板新增 tab："📜 旨库"

布局：
- 顶部：搜索栏 + 分类标签（日常办公 / 数据分析 / 工程开发 / 内容创作）
- 主体：模板卡片网格（每行3张），每张卡片显示：
  - icon + 名称
  - 描述（一行）
  - 涉及部门标签
  - 预估耗时和成本
  - 使用次数
  - "下旨"按钮
- 点击"下旨"：弹出参数填写模态框，底部"确认下旨"按钮
- 底部："+自建模板"入口

---

### 3.2 年度大考（复盘报告）

#### 背景
定期自动生成阶段性复盘报告，包含工作量统计、效率趋势、成本分析、常见问题汇总。带图表，可导出分享。

#### 数据结构

```json
{
  "id": "EXAM-2026-W08",
  "type": "weekly",
  "period": {"from": "2026-02-17", "to": "2026-02-23"},
  "generated_at": "2026-02-24T00:00:00Z",
  "summary": {
    "total_tasks": 47,
    "completed": 42,
    "rejected": 3,
    "blocked": 2,
    "completion_rate": 0.894,
    "avg_completion_minutes": 33.5,
    "total_tokens": 680000,
    "total_cost_usd": 10.88
  },
  "department_breakdown": [
    {"dept": "bingbu", "tasks": 18, "tokens": 290000, "avg_minutes": 42, "rejection_rate": 0.056},
    {"dept": "libu", "tasks": 12, "tokens": 150000, "avg_minutes": 25, "rejection_rate": 0.0},
    {"dept": "hubu", "tasks": 8, "tokens": 128000, "avg_minutes": 30, "rejection_rate": 0.125}
  ],
  "efficiency_trend": {
    "labels": ["W04", "W05", "W06", "W07", "W08"],
    "tasks_completed": [28, 31, 35, 40, 42],
    "avg_minutes": [45, 42, 40, 38, 33.5],
    "cost_usd": [7.2, 8.1, 9.0, 9.8, 10.88]
  },
  "top_rejections": [
    {"reason": "缺少数据来源标注", "count": 2, "department": "hubu"},
    {"reason": "代码缺少错误处理", "count": 1, "department": "bingbu"}
  ],
  "highlights": [
    "兵部平均完成时间较上周缩短 12%",
    "户部驳回率从 15% 降至 12.5%",
    "本周首次使用急递通道 2 次"
  ],
  "model_cost_breakdown": {
    "claude-opus-4-6": {"tokens": 120000, "cost_usd": 4.80},
    "claude-sonnet-4-5": {"tokens": 480000, "cost_usd": 5.76},
    "claude-haiku-4-5": {"tokens": 80000, "cost_usd": 0.32}
  }
}
```

#### 核心逻辑

```
生成周期：
  - 周报：每周日 23:59 自动生成
  - 月报：每月最后一天 23:59 自动生成

流程：
  1. 读取该周期内所有任务数据（从 memorials + live_status）
  2. 读取各 agent performance 数据
  3. 计算汇总指标
  4. 与上一周期对比，计算趋势
  5. 提取驳回原因 Top N
  6. 生成亮点/问题自动摘要（可调 LLM 生成 highlights）
  7. 写入 data/exams/
  8. 推送飞书通知
```

#### 生成脚本
`scripts/generate_exam_report.py`

```
参数：
  --type    STRING  weekly | monthly
  --period  STRING  可选，如 "2026-W08" 或 "2026-02"，默认最近一个周期
  --export  STRING  可选，json（默认）| markdown | html
```

#### API 接口

```
GET  /api/exams                              # 报告列表
GET  /api/exams/:id                          # 单个报告详情
GET  /api/exams/:id/export?fmt=html          # 导出
POST /api/exams/generate                     # 手动触发 {"type": "weekly"}
```

#### 前端页面：大考

看板新增 tab："🏆 大考"

布局：
- 顶部：周期切换（周报 / 月报）+ 时间选择器
- 核心指标卡片行：完成数、完成率、平均耗时、总成本，每个指标带上/下箭头表示趋势
- 部门工作量柱状图（横向，按 tasks 数排序）
- 效率趋势折线图（最近5个周期，三条线：完成数/耗时/成本）
- 模型成本饼图
- 常见驳回原因排行
- 亮点列表（绿色标注）
- 底部："导出报告"按钮（Markdown / HTML）+ "分享到飞书"按钮

---

### 3.3 上朝仪式感

#### 背景
每日首次打开看板时展示"开朝"动画，增强使用粘性和仪式感。

#### 数据结构

用户当日状态存储在 localStorage：

```json
{
  "last_court_open": "2026-02-24",
  "court_opened_today": true,
  "court_preference": {
    "animation_enabled": true,
    "sound_enabled": false,
    "duration_seconds": 3
  }
}
```

#### 核心逻辑

```
前端逻辑（纯 JavaScript，无后端依赖）：

页面加载时：
  1. 读取 localStorage 中 last_court_open
  2. if last_court_open != 今天日期:
     显示开朝动画
     更新 last_court_open = 今天
     更新 court_opened_today = true
  3. else:
     跳过动画，直接显示看板

开朝动画内容：
  - 全屏遮罩，深色半透明背景
  - 中央显示文字动画（逐字显现）：
    第一行（大字）："早朝开始"
    第二行（小字）："各部听旨"
    第三行（数据）："今日待办 {N} 件 · 超期 {M} 件"
  - 底部：今日日期 + 农历日期（调用公开API或本地计算）
  - 动画持续3秒后自动消失，或点击任意处跳过
  - 可选：播放一声清脆的钟声（默认关闭）

退朝动画（可选）：
  当用户关闭浏览器标签页时（beforeunload 事件不可靠，改为在设置中提供手动"退朝"按钮）
  点击"退朝"按钮：
  - 显示："退朝 · 今日完成 {N} 件旨意"
  - 持续2秒后页面关闭
```

#### 前端实现要点

```
技术要求：
  - 纯 CSS 动画 + JavaScript，不引入额外依赖
  - 开朝数据（待办数、超期数）从已加载的 live_status.json 中提取
  - 设置页面增加"仪式感"配置区域：
    - 开关：开朝动画 on/off
    - 开关：音效 on/off
    - 滑块：动画时长 2-5 秒
  - 农历日期：使用 lunar-javascript 库或内嵌简易农历算法
  - 动画风格：参考中式水墨风，字体使用思源宋体（Noto Serif SC）

CSS 动画规格：
  - 背景：#1a1a2e，opacity 0 → 0.95，duration 0.5s
  - 文字："早朝开始"，font-size 48px，逐字 fadeIn，每字间隔 200ms
  - "各部听旨"，font-size 24px，整行 fadeIn，delay 1.2s
  - 数据行，font-size 16px，fadeIn，delay 1.8s
  - 2.5s 后整体 fadeOut，duration 0.5s
```

---

## 四、优先级排序与开发建议

### Phase 1（核心，1-2周）
1. **御批模式** — 解决信任问题，用户敢用
2. **奏折系统** — 解决追溯问题，用户放心
3. **急递铺** — 解决灵活性问题，用户不嫌烦

### Phase 2（粘性，2-3周）
4. **早朝/晚朝** — 让用户养成每天看一眼的习惯
5. **功过簿** — 让用户看到系统在进步
6. **国史馆** — 让系统越用越聪明

### Phase 3（传播，1-2周）
7. **圣旨模板库** — 降低新用户门槛
8. **年度大考** — 给用户社交传播的素材
9. **上朝仪式感** — 最简单但最有记忆点的功能

---

## 五、新增看板 Tab 总览

改造后的看板顶部导航：

```
🏠 总览 | 📋 旨意看板 | 📜 奏折阁 | 🌅 朝报 | 📊 功过簿 | 📚 国史馆 | 📜 旨库 | 🏆 大考 | ⚙️ 设置
```

设置页面新增：
- 审批规则管理（御批模式）
- 急递通道配置
- 仪式感配置（开朝动画/音效）
- 自动升降级规则（功过簿）
