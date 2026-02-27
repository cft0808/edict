#!/usr/bin/env python3
"""端到端测试 kanban_update.py 的清洗+创建+流转全流程"""
import sys, os, json, pathlib

# 切换到 scripts 目录（file_lock 依赖）
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.insert(0, '.')

from kanban_update import (
    _sanitize_title, _sanitize_remark, _is_valid_task_title,
    cmd_create, cmd_flow, cmd_state, cmd_done, load, TASKS_FILE
)

# 备份原始数据
backup = TASKS_FILE.read_text()
passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}: {detail}")
        failed += 1

def get_task(tid):
    return next((x for x in load() if x['id'] == tid), None)

try:
    print("========== 端到端测试 ==========\n")

    # TEST 1: 脏标题(含文件路径+Conversation)应被清洗后创建
    print("--- TEST 1: 脏标题清洗后创建 ---")
    cmd_create('JJC-TEST-E2E-01',
        '全面审查/Users/bingsen/clawd/openclaw-sansheng-liubu/这个项目\nConversation info (xxx)',
        'Zhongshu', '中书省', '中书令',
        '下旨（自动预建）：全面审查/Users/bingsen/clawd/项目')
    t = get_task('JJC-TEST-E2E-01')
    check("任务已创建", t is not None)
    if t:
        check("标题无路径", '/Users' not in t['title'], t['title'])
        check("标题无Conversation", 'Conversation' not in t['title'], t['title'])
        check("remark无自动预建", '自动预建' not in t['flow_log'][0]['remark'], t['flow_log'][0]['remark'])
        check("remark无路径", '/Users' not in t['flow_log'][0]['remark'], t['flow_log'][0]['remark'])
        print(f"  -> 清洗后标题: {t['title']}")
        print(f"  -> 清洗后remark: {t['flow_log'][0]['remark']}")
    print()

    # TEST 2: 纯文件路径标题被拒绝
    print("--- TEST 2: 纯路径标题拒绝 ---")
    cmd_create('JJC-TEST-E2E-02', '/Users/bingsen/clawd/openclaw-sansheng-liubu/', 'Zhongshu', '中书省', '中书令')
    check("路径标题被拒绝", get_task('JJC-TEST-E2E-02') is None)
    print()

    # TEST 3: 正常标题正常创建
    print("--- TEST 3: 正常标题创建 ---")
    cmd_create('JJC-TEST-E2E-03', '调研工业数据分析大模型应用方案', 'Zhongshu', '中书省', '中书令', '太子整理旨意')
    t = get_task('JJC-TEST-E2E-03')
    check("正常任务已创建", t is not None)
    if t:
        check("标题完整保留", t['title'] == '调研工业数据分析大模型应用方案', t['title'])
    print()

    # TEST 4: flow remark 清洗
    print("--- TEST 4: flow remark 清洗 ---")
    cmd_flow('JJC-TEST-E2E-03', '太子', '中书省', '旨意传达：审查/Users/bingsen/clawd/xxx项目 Conversation blah')
    t = get_task('JJC-TEST-E2E-03')
    if t:
        last_flow = t['flow_log'][-1]
        check("remark无路径", '/Users' not in last_flow['remark'], last_flow['remark'])
        check("remark无Conversation", 'Conversation' not in last_flow['remark'], last_flow['remark'])
        print(f"  -> 清洗后remark: {last_flow['remark']}")
    print()

    # TEST 5: 太短标题拒绝
    print("--- TEST 5: 短标题拒绝 ---")
    cmd_create('JJC-TEST-E2E-05', '好的', 'Zhongshu', '中书省', '中书令')
    check("短标题被拒绝", get_task('JJC-TEST-E2E-05') is None)
    print()

    # TEST 6: 传旨前缀剥离
    print("--- TEST 6: 传旨前缀剥离 ---")
    cmd_create('JJC-TEST-E2E-06', '传旨：帮我写技术博客文章关于智能体架构', 'Zhongshu', '中书省', '中书令')
    t = get_task('JJC-TEST-E2E-06')
    check("任务已创建", t is not None)
    if t:
        check("前缀已剥离", not t['title'].startswith('传旨'), t['title'])
        print(f"  -> 标题: {t['title']}")
    print()

    # TEST 7: state 更新 + org 自动联动
    print("--- TEST 7: state 更新 ---")
    cmd_state('JJC-TEST-E2E-03', 'Menxia', '方案提交门下省审议')
    t = get_task('JJC-TEST-E2E-03')
    if t:
        check("state=Menxia", t['state'] == 'Menxia', t['state'])
        check("org=门下省", t['org'] == '门下省', t['org'])
    print()

    # TEST 8: done 完成
    print("--- TEST 8: done 完成 ---")
    cmd_done('JJC-TEST-E2E-03', '/tmp/output.md', '任务已完成')
    t = get_task('JJC-TEST-E2E-03')
    if t:
        check("state=Done", t['state'] == 'Done', t['state'])
    print()

    # TEST 9: 已完成任务不可覆盖
    print("--- TEST 9: Done任务拒绝覆盖 ---")
    cmd_create('JJC-TEST-E2E-03', '试图覆盖已完成的任务标题', 'Zhongshu', '中书省', '中书令')
    t = get_task('JJC-TEST-E2E-03')
    if t:
        check("仍为Done", t['state'] == 'Done', t['state'])
    print()

    # 汇总
    total = passed + failed
    print(f"========== 结果: {passed}/{total} 通过 {'✅' if failed == 0 else '❌'} ==========")

finally:
    # 恢复原始数据
    TASKS_FILE.write_text(backup)
    # 清理测试任务
    tasks = json.loads(TASKS_FILE.read_text())
    tasks = [t for t in tasks if not t.get('id', '').startswith('JJC-TEST-')]
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))
    print("\n(测试数据已清理)")

sys.exit(0 if failed == 0 else 1)
