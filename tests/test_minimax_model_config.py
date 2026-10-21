"""Offline coverage for MiniMax choices and the configured request boundary."""
import importlib.util
import json
import re
import urllib.request
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODELS = ['MiniMax-M3.1-Flash', 'MiniMax-M3']


def load_module(relative_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_catalog_sync_preserves_configured_models(tmp_path, monkeypatch):
    sync = load_module('scripts/sync_agent_config.py', monkeypatch)
    saved = 'minimax/MiniMax-M2.7'
    custom = 'minimax/custom-model'
    cfg = {
        'agents': {
            'defaults': {'model': {'primary': saved}, 'models': {custom: {}}},
            'list': [{'id': 'taizi', 'model': custom}],
        },
        'providers': {'custom': {'models': ['custom/explicit-model']}},
    }
    cfg_path = tmp_path / 'openclaw.json'
    cfg_path.write_text(json.dumps(cfg))
    monkeypatch.setattr(sync, 'OPENCLAW_CFG', cfg_path)
    monkeypatch.setattr(sync, 'DATA', tmp_path / 'data')
    monkeypatch.setattr(sync, 'deploy_soul_files', lambda: None)
    monkeypatch.setattr(sync, 'sync_scripts_to_workspaces', lambda: None)
    sync.main()

    output = json.loads((tmp_path / 'data' / 'agent_config.json').read_text())
    builtin = [m['id'] for m in sync.KNOWN_MODELS if m['provider'] == 'MiniMax']
    assert builtin == ['minimax/' + model for model in MODELS]
    ids = [m['id'] for m in output['knownModels']]
    assert len(ids) == len(set(ids))
    assert saved in ids and custom in ids and 'custom/explicit-model' in ids
    assert output['defaultModel'] == saved
    assert next(a for a in output['agents'] if a['id'] == 'taizi')['model'] == custom
    assert json.loads(cfg_path.read_text()) == cfg


@pytest.mark.parametrize('relative_path', [
    'dashboard/dashboard.html',
    'edict/frontend/src/components/ModelConfig.tsx',
])
def test_ui_fallbacks_match_minimax_catalog(relative_path):
    source = (ROOT / relative_path).read_text()
    fallback = source.split('const FALLBACK_MODELS', 1)[1].split('];', 1)[0]
    assert re.findall(r"id:\s*'minimax/([^']+)'", fallback) == MODELS


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


@pytest.mark.parametrize('host', ['api.minimax.io', 'api.minimaxi.com'])
@pytest.mark.parametrize('api_type,base_path,request_path', [
    ('openai-completions', '/v1', '/v1/chat/completions'),
    ('anthropic-messages', '/anthropic', '/anthropic/v1/messages'),
])
@pytest.mark.parametrize('model', MODELS + ['MiniMax-M2.7', 'custom-model'])
def test_configured_model_reaches_http_unchanged(
    tmp_path, monkeypatch, host, api_type, base_path, request_path, model,
):
    court = load_module('dashboard/court_discuss.py', monkeypatch)
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.delenv('OPENCLAW_LLM_API_KEY', raising=False)
    config_dir = tmp_path / '.openclaw'
    config_dir.mkdir()
    (config_dir / 'openclaw.json').write_text(json.dumps({
        'models': {'providers': {'minimax': {
            'api': api_type, 'baseUrl': 'https://' + host + base_path,
            'apiKey': 'offline-placeholder', 'models': [{'id': model}],
        }}},
    }))
    captured = []

    def capture(request, timeout):
        captured.append(request)
        if api_type == 'anthropic-messages':
            return Response({'content': [{'type': 'text', 'text': 'ok'}]})
        return Response({'choices': [{'message': {'content': 'ok'}}]})

    monkeypatch.setattr(urllib.request, 'urlopen', capture)
    assert court._llm_complete('system', 'user', max_tokens=2048) == 'ok'
    assert len(captured) == 1
    request = captured[0]
    assert request.full_url == 'https://' + host + request_path
    assert request.method == 'POST'
    payload = json.loads(request.data)
    assert payload['model'] == model
    assert payload['max_tokens'] == 2048
    assert payload['messages'][-1] == {'role': 'user', 'content': 'user'}
    for key in ('thinking', 'reasoning_effort', 'output_config', 'service_tier', 'reasoning_split'):
        assert key not in payload


def test_explicit_environment_model_is_preserved(tmp_path, monkeypatch):
    court = load_module('dashboard/court_discuss.py', monkeypatch)
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('OPENCLAW_LLM_API_KEY', 'offline-placeholder')
    monkeypatch.setenv('OPENCLAW_LLM_BASE_URL', 'https://api.minimax.io/v1')
    monkeypatch.setenv('OPENCLAW_LLM_MODEL', 'MiniMax-M2.7')
    assert court._get_llm_config()['model'] == 'MiniMax-M2.7'
