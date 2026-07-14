import importlib.util
import json
import urllib.request
from pathlib import Path

import pytest


def _load_court_discuss():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "dashboard" / "court_discuss.py"
    spec = importlib.util.spec_from_file_location("court_discuss", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload


@pytest.mark.parametrize(
    ("base_url", "api_type", "expected_url"),
    [
        (
            "https://api.minimax.io/v1",
            "openai-completions",
            "https://api.minimax.io/v1/chat/completions",
        ),
        (
            "https://api.minimax.io/anthropic",
            "anthropic-messages",
            "https://api.minimax.io/anthropic/v1/messages",
        ),
        (
            "https://api.minimaxi.com/v1",
            "openai-completions",
            "https://api.minimaxi.com/v1/chat/completions",
        ),
        (
            "https://api.minimaxi.com/anthropic",
            "anthropic-messages",
            "https://api.minimaxi.com/anthropic/v1/messages",
        ),
    ],
)
def test_minimax_request_paths(base_url, api_type, expected_url, monkeypatch):
    court_discuss = _load_court_discuss()
    captured = {}

    monkeypatch.setattr(
        court_discuss,
        "_get_llm_config",
        lambda: {
            "api_key": "test-key",
            "base_url": base_url,
            "model": "MiniMax-M3",
            "api_type": api_type,
        },
    )

    def capture_request(request, timeout):
        captured["url"] = request.full_url
        if api_type == "anthropic-messages":
            return _Response({"content": [{"text": "ok"}]})
        return _Response({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(urllib.request, "urlopen", capture_request)

    assert court_discuss._llm_complete("system", "user") == "ok"
    assert captured["url"] == expected_url
