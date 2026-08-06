import json
import importlib.util
import sys
from pathlib import Path


def _load_sync_agent_config():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "sync_agent_config.py"
    spec = importlib.util.spec_from_file_location("sync_agent_config", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(script_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(script_path.parent))
    return module


def test_sync_agent_config_accepts_allow_agents_key(tmp_path, monkeypatch):
    sync_agent_config = _load_sync_agent_config()

    cfg = {
        "agents": {
            "defaults": {"model": "openai/gpt-4o"},
            "list": [
                {
                    "id": "taizi",
                    "workspace": str(tmp_path / "ws-taizi"),
                    "allowAgents": ["zhongshu"]
                }
            ]
        }
    }

    cfg_path = tmp_path / "openclaw.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False))

    monkeypatch.setattr(sync_agent_config, "OPENCLAW_CFG", cfg_path)
    monkeypatch.setattr(sync_agent_config, "DATA", tmp_path / "data")

    sync_agent_config.main()

    out = json.loads((tmp_path / "data" / "agent_config.json").read_text())
    taizi = next(agent for agent in out["agents"] if agent["id"] == "taizi")
    assert taizi["allowAgents"] == ["zhongshu"]


def test_known_models_include_minimax_text_models():
    sync_agent_config = _load_sync_agent_config()
    models = {model["id"]: model for model in sync_agent_config.KNOWN_MODELS}

    assert models["minimax/MiniMax-M3"] == {
        "id": "minimax/MiniMax-M3",
        "label": "MiniMax M3",
        "provider": "MiniMax",
    }
    assert models["minimax/MiniMax-M2.7"] == {
        "id": "minimax/MiniMax-M2.7",
        "label": "MiniMax M2.7",
        "provider": "MiniMax",
    }
