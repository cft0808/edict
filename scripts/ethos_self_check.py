#!/usr/bin/env python3
"""
ETHOS Self-Check — v1.2 ETHOS 自查脚本

在臣执行 exec 写操作前，检查是否已完成 ETHOS 要求的步骤。

用法：
  python3 scripts/ethos_self_check.py before_exec <task_id> "<command>"
  python3 scripts/ethos_self_check.py check_task <task_id>

返回：
  0 = 可以执行
  1 = 禁止执行（ETHOS 未满足）
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

KANBAN_PATH = Path(__file__).parent.parent / "data" / "tasks_source.json"
MEMORY_DECISIONS = Path(__file__).parent.parent / "memory" / "decisions"


def read_kanban():
    if not KANBAN_PATH.exists():
        return []
    with open(KANBAN_PATH) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def find_task(task_id):
    for t in read_kanban():
        if t.get("id") == task_id:
            return t
    return None


def is_write_operation(command):
    """判断是否是写操作"""
    if not command:
        return False
    
    command = str(command)
    write_indicators = [
        " > ", " >> ", " | tee ", " 2>", "2>&1",
        "cat >", "python3 -c", "open(",
        "mv ", "cp ", "rm ",  # 文件操作
        "write(", "edit(", "append(",
        "mkdir ", "touch ",
    ]
    return any(ind in command for ind in write_indicators)


def check_search_before_building(task_id):
    """检查是否已完成 GitHub 搜索"""
    task = find_task(task_id)
    if not task:
        return {"done": False, "reason": f"任务 {task_id} 不存在"}
    
    # 检查任务备注或 output 中是否有 GitHub 搜索记录
    notes = task.get("notes", "") or task.get("description", "") or ""
    
    # 简化判断：检查 notes 中是否有 github 或 search 关键词
    has_search = any(kw in notes.lower() for kw in ["github", "search", "搜索", "竞品", "alternatives"])
    
    return {
        "done": has_search,
        "notes_preview": notes[:100] if notes else ""
    }


def check_boil_the_lake(task_id):
    """检查是否有 Boil the Lake 标注"""
    task = find_task(task_id)
    if not task:
        return {"done": False, "reason": f"任务 {task_id} 不存在"}
    
    notes = task.get("notes", "") or ""
    
    # 检查是否有完整实现/简化实现标注
    has_boil = any(kw in notes for kw in ["完整实现", "简化实现", "Boil the Lake", "ETHOS"])
    
    return {"done": has_boil, "notes_preview": notes[:100] if notes else ""}


def check_review_gate(task_id):
    """检查 Review 是否完成"""
    task = find_task(task_id)
    if not task:
        return {"done": False, "reason": f"任务 {task_id} 不存在"}
    
    # 检查 review_status
    review_status = task.get("review_status", "")
    if review_status == "passed":
        return {"done": True}
    
    # 检查是否有 Review 记录文件
    review_keywords = [
        f"review_{task_id}",
        f"review-{task_id}",
    ]
    
    if MEMORY_DECISIONS.exists():
        for f in MEMORY_DECISIONS.glob("*"):
            if any(kw in f.name for kw in review_keywords):
                return {"done": True, "file": str(f)}
    
    return {"done": False}


def before_exec_check(task_id, command):
    """在 exec 前的检查"""
    if not is_write_operation(command):
        # 非写操作，直接放行
        return {
            "allowed": True,
            "reason": "非写操作，直接放行"
        }
    
    print(f"[ETHOS] 检查 exec 写操作...")
    print(f"[ETHOS] 任务：{task_id}")
    print(f"[ETHOS] 命令：{command[:80]}...")
    print()
    
    # 1. 检查 Research 是否完成（如果任务被 Research 阻塞）
    task = find_task(task_id)
    if task:
        blocked_by = task.get("blockedBy", [])
        if blocked_by:
            for bid in blocked_by:
                blocker = find_task(bid)
                if blocker and blocker.get("state") != "Done":
                    return {
                        "allowed": False,
                        "reason": f"Research 任务 {bid} 未完成，禁止写操作。\n请先完成 Research，再执行写操作。\n提示：python3 scripts/review_gate.py check {bid}"
                    }
        
        # 检查 state
        if task.get("state") == "Researching":
            return {
                "allowed": False,
                "reason": f"任务 {task_id} 还在 Research 阶段，禁止写操作。\n请先完成 Research，再执行写操作。"
            }
    
    # 2. 检查 Search Before Building
    print("[ETHOS] 检查 Search Before Building...")
    search = check_search_before_building(task_id)
    if not search["done"]:
        print(f"[ETHOS] ⚠️ 警告：未检测到 GitHub 搜索记录")
        print(f"[ETHOS] 建议：在任务备注里记录 GitHub 搜索结果")
        print()
    
    # 3. 检查 Boil the Lake
    print("[ETHOS] 检查 Boil the Lake...")
    boil = check_boil_the_lake(task_id)
    if not boil["done"]:
        print(f"[ETHOS] ⚠️ 警告：未检测到实现选择标注（完整/简化）")
        print(f"[ETHOS] 建议：在任务备注里标注是完整实现还是简化实现")
        print()
    
    # 4. 检查 Review（只有任务 state 是 Done 之前才检查）
    if task and task.get("state") not in ["Done", "Researching"]:
        print("[ETHOS] 检查 Review Gate...")
        review = check_review_gate(task_id)
        if not review["done"]:
            print(f"[ETHOS] ⚠️ 警告：任务没有 Review 记录")
            print(f"[ETHOS] 提示：python3 scripts/review_gate.py check {task_id}")
            print()
    
    print(f"[ETHOS] ✓ 允许执行（但建议先完成以上检查项）")
    return {
        "allowed": True,
        "warnings": {
            "search": not search["done"],
            "boil": not boil["done"]
        }
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "before_exec" and len(sys.argv) >= 4:
        task_id = sys.argv[2]
        command = sys.argv[3]
        result = before_exec_check(task_id, command)
        
        if not result["allowed"]:
            print(f"\n[ETHOS] ✗ 禁止执行")
            print(f"[ETHOS] 原因：{result['reason']}")
            sys.exit(1)
        else:
            if result.get("warnings", {}).get("search") or result.get("warnings", {}).get("boil"):
                sys.exit(0)  # 有警告但允许执行
            else:
                sys.exit(0)
    
    elif cmd == "check_task" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        task = find_task(task_id)
        if not task:
            print(f"错误：任务 {task_id} 不存在")
            sys.exit(1)
        
        print(f"任务：{task.get('title', task_id)}")
        print(f"状态：{task.get('state', 'unknown')}")
        print()
        
        search = check_search_before_building(task_id)
        print(f"Search Before Building：{'✓' if search['done'] else '✗'}")
        
        boil = check_boil_the_lake(task_id)
        print(f"Boil the Lake：{'✓' if boil['done'] else '✗'}")
        
        review = check_review_gate(task_id)
        print(f"Review Gate：{'✓' if review['done'] else '✗'}")
        
        sys.exit(0)
    
    else:
        print(__doc__)
        sys.exit(0)
