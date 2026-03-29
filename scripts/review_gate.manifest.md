# review_gate.py — 评审门控

## 概述
v1.2 Review Gate 的命令行工具。在任务标记 Done 前检查是否已完成 Review。

## 核心功能
- `check <task_id>`：检查任务的 Review 状态
- `can_done <task_id>`：检查是否可以标记 Done（返回 exit code）
- `start_review <task_id>`：输出 Review 流程指引

## 核心逻辑
```
实现类任务（标题含：实现/开发/部署/写/功能）→ 必须 Review
非实现类任务 → 可以直接 Done
```

## 依赖
- `data/tasks_source.json`（看板）
- `memory/decisions/`（Review 记录文件）

## 使用场景
臣在标记任务 Done 前，先调用：
```bash
python3 scripts/review_gate.py can_done JJC-20260330-XXX
if [ $? -eq 0 ]; then
    python3 scripts/kanban_update.py done JJC-20260330-XXX ...
fi
```

## 错误处理
- 任务不存在 → exit 1，输出具体原因
- 需要 Review 但没有记录 → exit 1，输出 Review 流程指引
- 不需要 Review → exit 0

## 版本
v1.0 — 2026-03-30
