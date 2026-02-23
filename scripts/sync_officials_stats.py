#!/usr/bin/env python3
"""同步各官员统计数据 → data/officials_stats.json
包括：Token消耗、任务功绩、会话状态、估算费用
"""
import json, pathlib, datetime, re

BASE = pathlib.Path('/Users/bingsen/clawd/junjichu-v2')
DATA = BASE / 'data'
AGENTS_ROOT = pathlib.Path('/Users/bingsen/.openclaw/agents')
OPENCLAW_CFG = pathlib.Path('/Users/bingsen/.openclaw/openclaw.json')

# 模型定价（每1M token，美元）
MODEL_PRICING = {
    'anthropic/claude-sonnet-4-6':  {'in': 3.0,   'out': 15.0},
    'anthropic/claude-opus-4-5':    {'in': 15.0,  'out': 75.0},
    'anthropic/claude-haiku-3-5':   {'in': 0.8,   'out': 4.0},
    'openai/gpt-4o':                {'in': 2.5,   'out': 10.0},
    'openai/gpt-4o-mini':           {'in': 0.15,  'out': 0.6},
    'openai-codex/gpt-5.3-codex':   {'in': 3.0,   'out': 15.0},
    'google/gemini-2.0-flash':      {'in': 0.075, 'out': 0.3},
    'google/gemini-2.5-pro':        {'in': 1.25,  'out': 10.0},
}

OFFICIALS = [
    {'id': 'zhongshu', 'label': '中书省', 'role': '中书令',   'emoji': '📜', 'rank': '正一品'},
    {'id': 'menxia',   'label': '门下省', 'role': '侍中',     'emoji': '🔍', 'rank': '正一品'},
    {'id': 'shangshu', 'label': '尚书省', 'role': '尚书令',   'emoji': '📮', 'rank': '正一品'},
    {'id': 'libu',     'label': '礼部',   'role': '礼部尚书', 'emoji': '📝', 'rank': '正二品'},
    {'id': 'hubu',     'label': '户部',   'role': '户部尚书', 'emoji': '💰', 'rank': '正二品'},
    {'id': 'bingbu',   'label': '兵部',   'role': '兵部尚书', 'emoji': '⚔️', 'rank': '正二品'},
    {'id': 'xingbu',   'label': '刑部',   'role': '刑部尚书', 'emoji': '⚖️', 'rank': '正二品'},
    {'id': 'gongbu',   'label': '工部',   'role': '工部尚书', 'emoji': '🔧', 'rank': '正二品'},
]

def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def get_agent_model(agent_id):
    """从 openclaw.json 获取 agent 当前使用的模型"""
    cfg = read_json(OPENCLAW_CFG, {})
    agents_list = cfg.get('agents', {}).get('list', [])
    default_model = cfg.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', 'unknown')
    for ag in agents_list:
        if ag.get('id') == agent_id:
            return ag.get('model', default_model)
    return default_model


def scan_sessions(agent_id):
    """扫描 agent 的 session 文件，汇总 token 使用"""
    sessions_dir = AGENTS_ROOT / agent_id / 'sessions'
    if not sessions_dir.exists():
        return {'sessions': 0, 'tokens_in': 0, 'tokens_out': 0, 'tokens_total': 0, 'last_active': None, 'messages': 0}

    total_in = 0
    total_out = 0
    total_total = 0
    total_cost = 0.0
    session_count = 0
    last_active = None
    msg_count = 0

    for session_file in sorted(sessions_dir.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True):
        session_count += 1
        mtime = datetime.datetime.fromtimestamp(session_file.stat().st_mtime)
        if last_active is None or mtime > last_active:
            last_active = mtime

        # 读取 session jsonl 文件（每行一条记录）
        try:
            lines = session_file.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
            for line in lines[-500:]:  # 最多读最后500行
                try:
                    entry = json.loads(line)
                    entry_type = entry.get('type', '')
                    # OpenClaw session 格式: type=message, message.usage
                    if entry_type == 'message':
                        msg = entry.get('message', {})
                        usage = msg.get('usage', {})
                        if usage:
                            total_in += usage.get('input', 0) or 0
                            total_out += usage.get('output', 0) or 0
                            cost = usage.get('cost', {})
                            total_cost += cost.get('total', 0) or 0
                        if msg.get('role') in ('assistant', 'user'):
                            msg_count += 1
                except Exception:
                    pass
        except Exception:
            pass

        # 最多扫描最近20个session节省时间
        if session_count >= 20:
            break

    return {
        'sessions': session_count,
        'tokens_in': total_in,
        'tokens_out': total_out,
        'tokens_total': total_in + total_out,
        'cost_actual': round(total_cost, 6),
        'last_active': last_active.strftime('%Y-%m-%d %H:%M:%S') if last_active else None,
        'messages': msg_count,
    }


def get_task_stats(agent_id, org_label, tasks):
    """从 tasks 数据统计功绩"""
    done = [t for t in tasks if t.get('state') == 'Done' and t.get('org') == org_label]
    active = [t for t in tasks if t.get('state') in ('Doing', 'Review', 'Assigned') and t.get('org') == org_label]
    # 流转日志中涉及该部门的条目
    fl_count = 0
    for t in tasks:
        for fl in t.get('flow_log', []):
            if fl.get('from') == org_label or fl.get('to') == org_label:
                fl_count += 1
    return {
        'tasks_done': len(done),
        'tasks_active': len(active),
        'flow_participations': fl_count,
    }


def calc_cost(tokens_in, tokens_out, model):
    pricing = MODEL_PRICING.get(model, {'in': 3.0, 'out': 15.0})
    cost = (tokens_in / 1_000_000 * pricing['in']) + (tokens_out / 1_000_000 * pricing['out'])
    return round(cost, 6)


def get_heartbeat_from_live(agent_id, live_tasks):
    """从 live_status 获取 agent 心跳"""
    for t in live_tasks:
        src = t.get('sourceMeta', {})
        if src.get('agentId') == agent_id and t.get('heartbeat'):
            return t['heartbeat']
    return {'status': 'idle', 'label': '⚪ 待命', 'ageSec': None}


def main():
    tasks = read_json(DATA / 'tasks_source.json', [])
    live = read_json(DATA / 'live_status.json', {})
    live_tasks = live.get('tasks', [])

    result = []
    for off in OFFICIALS:
        agent_id = off['id']
        model = get_agent_model(agent_id)
        session_stats = scan_sessions(agent_id)
        task_stats = get_task_stats(agent_id, off['label'], tasks)
        hb = get_heartbeat_from_live(agent_id, live_tasks)
        # 优先使用实际计费，fallback 按定价估算
        cost_actual = session_stats.get('cost_actual', 0)
        cost_usd = cost_actual if cost_actual > 0 else calc_cost(session_stats['tokens_in'], session_stats['tokens_out'], model)

        result.append({
            **off,
            'model': model,
            'model_short': model.split('/')[-1] if '/' in model else model,
            'sessions': session_stats['sessions'],
            'tokens_in': session_stats['tokens_in'],
            'tokens_out': session_stats['tokens_out'],
            'tokens_total': session_stats['tokens_in'] + session_stats['tokens_out'],
            'messages': session_stats['messages'],
            'cost_usd': round(cost_usd, 4),
            'cost_cny': round(cost_usd * 7.25, 2),
            'last_active': session_stats['last_active'],
            'heartbeat': hb,
            'tasks_done': task_stats['tasks_done'],
            'tasks_active': task_stats['tasks_active'],
            'flow_participations': task_stats['flow_participations'],
            # merit score: 功绩分（简单加权）
            'merit_score': task_stats['tasks_done'] * 10 + task_stats['flow_participations'] * 2 + min(session_stats['sessions'] * 1, 20),
        })

    # 按功绩排名
    result.sort(key=lambda x: x['merit_score'], reverse=True)
    for i, r in enumerate(result):
        r['merit_rank'] = i + 1

    payload = {
        'generatedAt': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'officials': result,
        'totals': {
            'tokens_total': sum(r['tokens_total'] for r in result),
            'cost_usd': round(sum(r['cost_usd'] for r in result), 4),
            'cost_cny': round(sum(r['cost_cny'] for r in result), 2),
            'tasks_done': sum(r['tasks_done'] for r in result),
        }
    }

    (DATA / 'officials_stats.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )
    print(f'[officials_stats] synced {len(result)} officials, total_cost=${payload["totals"]["cost_usd"]}')


if __name__ == '__main__':
    main()
