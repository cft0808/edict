#!/usr/bin/env python3
"""
Review Gate — v1.2 评审门控脚本

在任务标记 Done 之前，检查是否已完成 Review。
如果没有 Review 记录，禁止标记 Done，并输出阻断原因。

用法：
  python3 scripts/review_gate.py check <task_id>
  python3 scripts/review_gate.py can_done <task_id>

返回：
  check: 输出 Review 状态
  can_done: 如果可以 Done 返回 0，否则返回 1 并输出原因
"""

import json
import sys
import os
from pathlib import Path

KANBAN_PATH = Path(__file__).parent.parent / "data" / "tasks_source.json"
MEMORY_DECISIONS = Path(__file__).parent.parent / "memory" / "decisions"

TOOL_NAME = "review_gate"


def read_kanban():
    """读取看板数据"""
    if not KANBAN_PATH.exists():
        return []
    with open(KANBAN_PATH) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []


def find_task(task_id):
    """找到指定任务"""
    tasks = read_kanban()
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None


def find_review_record(task_id):
    """查找 Review 记录"""
    # 查找 memory/decisions/ 中的 Review 记录
    if not MEMORY_DECISIONS.exists():
        return None
    
    # 格式：memory/decisions/review_<task_id>_<date>.md
    for f in MEMORY_DECISIONS.glob(f"review_*{task_id}*"):
        return f
    
    # 也检查 output 字段引用的 Review 记录
    return None


def check_review_for_task(task_id):
    """检查任务的 Review 状态"""
    task = find_task(task_id)
    if not task:
        return {
            "ok": False,
            "error": f"任务 {task_id} 不存在"
        }
    
    # 实现类任务需要 Review（简单任务可以豁免）
    title = task.get("title", "")
    state = task.get("state", "")
    
    # 判断是否需要 Review
    implement_keywords = [
        "实现", "开发", "写代码", "写脚本", "部署", "安装",
        "修改", "重构", "写", "做", "功能"
    ]
    needs_review = any(kw in title for kw in implement_keywords)
    
    if not needs_review:
        return {
            "ok": True,
            "needs_review": False,
            "can_done": True,
            "reason": "非实现类任务，不需要 Review"
        }
    
    # 查找 Review 记录
    review_file = find_review_record(task_id)
    
    # 也检查任务的 Reviewer 字段
    reviewers = task.get("reviewers", [])
    review_status = task.get("review_status", "")
    
    if review_file or reviewers or review_status == "passed":
        return {
            "ok": True,
            "needs_review": True,
            "can_done": True,
            "reason": "Review 已完成",
            "review_file": str(review_file) if review_file else None
        }
    
    return {
        "ok": True,
        "needs_review": True,
        "can_done": False,
        "reason": f"任务 {task_id} 是实现类，但还没有 Review 记录。\n请先完成 Review：\n1. QAEngineer 验收（功能/边界/bug）\n2. SecurityOfficer 验收（如果涉及安全）\nReview 完成后，在 memory/decisions/ 创建文件：review_{task_id}_<日期>.md",
        "task_title": title,
        "suggestion": "臣可以帮臣自动创建 Review 任务：python3 scripts/review_gate.py start_review <task_id>"
    }


def start_review(task_id):
    """创建 Review 子任务"""
    task = find_task(task_id)
    if not task:
        print(f"错误：任务 {task_id} 不存在", file=sys.stderr)
        sys.exit(1)
    
    title = task.get("title", "")
    print(f"开始 Review 流程...")
    print(f"任务：{title}")
    print(f"任务 ID：{task_id}")
    print()
    print("Review Checklist：")
    print("1. QAEngineer 验收：")
    print("   - [ ] 功能符合预期")
    print("   - [ ] 边界用例通过")
    print("   - [ ] 无阻断性 bug")
    print()
    print("2. SecurityOfficer 验收（如果涉及安全）：")
    print("   - [ ] 无安全漏洞")
    print("   - [ ] 无 credential 泄露")
    print("   - [ ] 权限合理")
    print()
    print("Review 完成后，在 memory/decisions/ 创建文件：")
    print(f"  review_{task_id}_YYYYMMDD.md")
    print("并更新看板：")
    print(f"  python3 scripts/kanban_update.py state {task_id} Done")


def cmd_check(task_id):
    """检查 Review 状态"""
    result = check_review_for_task(task_id)
    if not result["ok"]:
        print(f"错误：{result['error']}")
        sys.exit(1)
    
    print(f"任务：{result.get('task_title', task_id)}")
    print(f"需要 Review：{'是' if result['needs_review'] else '否'}")
    print(f"可以 Done：{'是' if result['can_done'] else '否'}")
    
    if not result["can_done"] and result.get("reason"):
        print()
        print(f"原因：{result['reason']}")
        if result.get("suggestion"):
            print(f"建议：{result['suggestion']}")


def cmd_can_done(task_id):
    """检查是否可以标记 Done"""
    result = check_review_for_task(task_id)
    if not result["ok"]:
        print(f"错误：{result['error']}", file=sys.stderr)
        sys.exit(1)
    
    if result["can_done"]:
        print(f"✓ 任务 {task_id} 可以标记 Done")
        sys.exit(0)
    else:
        print(f"✗ 任务 {task_id} 不能标记 Done", file=sys.stderr)
        print(f"原因：{result['reason']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "check" and len(sys.argv) >= 3:
        cmd_check(sys.argv[2])
    elif cmd == "can_done" and len(sys.argv) >= 3:
        cmd_can_done(sys.argv[2])
    elif cmd == "start_review" and len(sys.argv) >= 3:
        start_review(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(0)
