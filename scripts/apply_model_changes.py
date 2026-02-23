#!/usr/bin/env python3
"""应用 data/pending_model_changes.json → openclaw.json，并重启 Gateway"""
import json, pathlib, subprocess, datetime, shutil

BASE = pathlib.Path(__file__).parent.parent
DATA = BASE / 'data'
OPENCLAW_CFG = pathlib.Path.home() / '.openclaw' / 'openclaw.json'
PENDING = DATA / 'pending_model_changes.json'
CHANGE_LOG = DATA / 'model_change_log.json'


def rj(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def wj(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    if not PENDING.exists():
        return
    pending = rj(PENDING, [])
    if not pending:
        return

    cfg = rj(OPENCLAW_CFG, {})
    agents_list = cfg.get('agents', {}).get('list', [])
    default_model = cfg.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', '')

    applied, errors = [], []
    for change in pending:
        ag_id = change.get('agentId', '').strip()
        new_model = change.get('model', '').strip()
        if not ag_id or not new_model:
            errors.append({'change': change, 'error': 'missing fields'})
            continue
        found = False
        for ag in agents_list:
            if ag.get('id') == ag_id:
                old = ag.get('model', default_model)
                if new_model == default_model:
                    ag.pop('model', None)
                else:
                    ag['model'] = new_model
                applied.append({'at': datetime.datetime.now().isoformat(), 'agentId': ag_id, 'oldModel': old, 'newModel': new_model})
                found = True
                break
        if not found:
            errors.append({'change': change, 'error': f'agent {ag_id} not found'})

    if applied:
        bak = OPENCLAW_CFG.parent / f'openclaw.json.bak.model-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}'
        shutil.copy2(OPENCLAW_CFG, bak)
        cfg['agents']['list'] = agents_list
        wj(OPENCLAW_CFG, cfg)

        log = rj(CHANGE_LOG, [])
        log.extend(applied)
        if len(log) > 200:
            log = log[-200:]
        wj(CHANGE_LOG, log)

        for e in applied:
            print(f'[model_change] {e["agentId"]}: {e["oldModel"]} → {e["newModel"]}')

        restart_ok = False
        try:
            r = subprocess.run(['openclaw', 'gateway', 'restart'], capture_output=True, text=True, timeout=30)
            restart_ok = r.returncode == 0
            print(f'[gateway restart] rc={r.returncode}')
        except Exception as e:
            print(f'[gateway restart error] {e}')

        PENDING.write_text('[]')
        wj(DATA / 'last_model_change_result.json', {
            'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'applied': applied, 'errors': errors, 'gatewayRestarted': restart_ok,
        })
    else:
        PENDING.write_text('[]')


if __name__ == '__main__':
    main()
