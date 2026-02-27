"""tests for scripts/kanban_update.py"""
import json, pathlib, sys

# Ensure scripts/ is importable
SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import kanban_update as kb


def test_create_and_get(tmp_path):
    """kanban create + get round-trip."""
    tasks_file = tmp_path / 'tasks_source.json'
    tasks_file.write_text('[]')

    # Patch TASKS_FILE
    original = kb.TASKS_FILE
    kb.TASKS_FILE = tasks_file
    try:
        kb.cmd_create('TEST-001', '测试任务创建和查询功能验证', 'Inbox', '工部', '工部尚书')
        tasks = json.loads(tasks_file.read_text())
        assert any(t.get('id') == 'TEST-001' for t in tasks)
        t = next(t for t in tasks if t['id'] == 'TEST-001')
        assert t['title'] == '测试任务创建和查询功能验证'
        assert t['state'] == 'Inbox'
        assert t['org'] == '工部'
    finally:
        kb.TASKS_FILE = original


def test_move_state(tmp_path):
    """kanban move changes task state."""
    tasks_file = tmp_path / 'tasks_source.json'
    tasks_file.write_text(json.dumps([
        {'id': 'T-1', 'title': 'test', 'state': 'Inbox'}
    ]))

    original = kb.TASKS_FILE
    kb.TASKS_FILE = tasks_file
    try:
        kb.cmd_state('T-1', 'Doing')
        tasks = json.loads(tasks_file.read_text())
        assert tasks[0]['state'] == 'Doing'
    finally:
        kb.TASKS_FILE = original


def test_block_and_unblock(tmp_path):
    """kanban block/unblock round-trip."""
    tasks_file = tmp_path / 'tasks_source.json'
    tasks_file.write_text(json.dumps([
        {'id': 'T-2', 'title': 'blocker test', 'state': 'Doing'}
    ]))

    original = kb.TASKS_FILE
    kb.TASKS_FILE = tasks_file
    try:
        kb.cmd_block('T-2', '等待依赖')
        tasks = json.loads(tasks_file.read_text())
        assert tasks[0]['state'] == 'Blocked'
        assert tasks[0]['block'] == '等待依赖'
    finally:
        kb.TASKS_FILE = original
