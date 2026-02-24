#!/usr/bin/env python3
"""
看板任务更新工具 - 供各省部 Agent 调用

用法:
  # 新建任务（收旨时）
  python3 kanban_update.py create JJC-20260223-012 "任务标题" Zhongshu 中书省 中书令

  # 更新状态
  python3 kanban_update.py state JJC-20260223-012 Menxia "规划方案已提交门下省"

  # 添加流转记录
  python3 kanban_update.py flow JJC-20260223-012 "中书省" "门下省" "规划方案提交审核"

  # 完成任务
  python3 kanban_update.py done JJC-20260223-012 "/path/to/output" "任务完成摘要"

  # 添加/更新子任务 todo
  python3 kanban_update.py todo JJC-20260223-012 1 "实现API接口" in-progress
  python3 kanban_update.py todo JJC-20260223-012 1 "" completed
"""
import json, pathlib, datetime, sys, subprocess

_BASE = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = _BASE / 'data' / 'tasks_source.json'
REFRESH_SCRIPT = _BASE / 'scripts' / 'refresh_live_data.py'

STATE_ORG_MAP = {
    'Zhongshu': '中书省', 'Menxia': '门下省', 'Assigned': '尚书省',
    'Doing': '执行中', 'Review': '尚书省', 'Done': '完成', 'Blocked': '阻塞',
}

def load():
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []

def save(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))
    # 触发刷新
    subprocess.run(['python3', str(REFRESH_SCRIPT)], capture_output=True)

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

def find_task(tasks, task_id):
    return next((t for t in tasks if t.get('id') == task_id), None)


def cmd_create(task_id, title, state, org, official, remark=None):
    """新建任务（收旨时立即调用）"""
    tasks = load()
    tasks = [t for t in tasks if t.get('id') != task_id]  # 去重
    flow_log = [{
        "at": now_iso(),
        "from": "皇上",
        "to": org,
        "remark": remark or f"下旨：{title}"
    }]
    tasks.insert(0, {
        "id": task_id,
        "title": title,
        "official": official,
        "org": org,
        "state": state,
        "now": f"{org}正在处理",
        "eta": "-",
        "block": "无",
        "output": "",
        "ac": "",
        "flow_log": flow_log,
        "updatedAt": now_iso()
    })
    save(tasks)
    print(f'[看板] ✅ 创建 {task_id} | {title[:30]} | state={state}')


def cmd_state(task_id, new_state, now_text=None):
    """更新任务状态"""
    tasks = load()
    t = find_task(tasks, task_id)
    if not t:
        print(f'[看板] ❌ 任务 {task_id} 不存在')
        return
    old_state = t['state']
    t['state'] = new_state
    if now_text:
        t['now'] = now_text
    t['updatedAt'] = now_iso()
    save(tasks)
    print(f'[看板] ✅ {task_id} 状态更新: {old_state} → {new_state}')


def cmd_flow(task_id, from_dept, to_dept, remark):
    """添加流转记录"""
    tasks = load()
    t = find_task(tasks, task_id)
    if not t:
        print(f'[看板] ❌ 任务 {task_id} 不存在')
        return
    if 'flow_log' not in t:
        t['flow_log'] = []
    t['flow_log'].append({
        "at": now_iso(),
        "from": from_dept,
        "to": to_dept,
        "remark": remark
    })
    t['now'] = remark[:60]
    t['updatedAt'] = now_iso()
    save(tasks)
    print(f'[看板] ✅ {task_id} 流转记录: {from_dept} → {to_dept}')


def cmd_done(task_id, output_path='', summary=''):
    """标记任务完成"""
    tasks = load()
    t = find_task(tasks, task_id)
    if not t:
        print(f'[看板] ❌ 任务 {task_id} 不存在')
        return
    t['state'] = 'Done'
    t['output'] = output_path
    t['now'] = summary or '任务已完成'
    if 'flow_log' not in t:
        t['flow_log'] = []
    t['flow_log'].append({
        "at": now_iso(),
        "from": t.get('org', '执行部门'),
        "to": "皇上",
        "remark": f"✅ 完成：{summary or '任务已完成'}"
    })
    t['updatedAt'] = now_iso()
    save(tasks)
    print(f'[看板] ✅ {task_id} 已完成')


def cmd_block(task_id, reason):
    """标记阻塞"""
    tasks = load()
    t = find_task(tasks, task_id)
    if not t:
        return
    t['state'] = 'Blocked'
    t['block'] = reason
    t['updatedAt'] = now_iso()
    save(tasks)
    print(f'[看板] ⚠️ {task_id} 已阻塞: {reason}')

def cmd_todo(task_id, todo_id, title, status='not-started'):
    """添加或更新子任务 todo

    status: not-started / in-progress / completed
    """
    tasks = load()
    t = find_task(tasks, task_id)
    if not t:
        print(f'[看板] ❌ 任务 {task_id} 不存在')
        return
    if 'todos' not in t:
        t['todos'] = []

    existing = next((td for td in t['todos'] if str(td.get('id')) == str(todo_id)), None)
    if existing:
        existing['status'] = status
        if title:
            existing['title'] = title
    else:
        t['todos'].append({
            'id': todo_id,
            'title': title,
            'status': status,
        })

    t['updatedAt'] = now_iso()
    save(tasks)

    done = sum(1 for td in t['todos'] if td.get('status') == 'completed')
    total = len(t['todos'])
    print(f'[看板] ✅ {task_id} todo [{done}/{total}]: {todo_id} → {status}')

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    cmd = args[0]
    if cmd == 'create' and len(args) >= 6:
        cmd_create(args[1], args[2], args[3], args[4], args[5], args[6] if len(args)>6 else None)
    elif cmd == 'state' and len(args) >= 3:
        cmd_state(args[1], args[2], args[3] if len(args)>3 else None)
    elif cmd == 'flow' and len(args) >= 5:
        cmd_flow(args[1], args[2], args[3], args[4])
    elif cmd == 'done' and len(args) >= 2:
        cmd_done(args[1], args[2] if len(args)>2 else '', args[3] if len(args)>3 else '')
    elif cmd == 'block' and len(args) >= 3:
        cmd_block(args[1], args[2])
    elif cmd == 'todo' and len(args) >= 4:
        cmd_todo(args[1], args[2], args[3] if len(args) > 3 else '', args[4] if len(args) > 4 else 'not-started')
    else:
        print(__doc__)
