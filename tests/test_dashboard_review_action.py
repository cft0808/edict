"""Regression tests for dashboard review completion gates."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys


DASHBOARD_DIR = pathlib.Path(__file__).resolve().parent.parent / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

_SPEC = importlib.util.spec_from_file_location("dashboard_server", DASHBOARD_DIR / "server.py")
dashboard_server = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(dashboard_server)


def test_review_approve_rejects_incomplete_todos(monkeypatch):
    """Review approve should not close a task when todos are still incomplete."""
    tasks = [{
        "id": "JJC-REVIEW-001",
        "title": "review gate",
        "state": "Review",
        "org": "尚书省",
        "now": "汇总中",
        "flow_log": [],
        "todos": [
            {"id": "1", "title": "已完成", "status": "completed"},
            {"id": "2", "title": "未完成", "status": "in-progress"},
        ],
    }]

    saved = {}

    monkeypatch.setattr(dashboard_server, "load_tasks", lambda: json.loads(json.dumps(tasks, ensure_ascii=False)))
    monkeypatch.setattr(
        dashboard_server,
        "save_tasks",
        lambda payload: saved.setdefault("tasks", json.loads(json.dumps(payload, ensure_ascii=False))),
    )

    result = dashboard_server.handle_review_action("JJC-REVIEW-001", "approve", "试图提前完结")

    assert result["ok"] is False
    assert "2/2" not in result["error"]
    assert "不能直接准奏完结" in result["error"]
    assert "tasks" not in saved


def test_review_approve_allows_complete_todos(monkeypatch):
    """Review approve may finish a task once all todos are completed."""
    tasks = [{
        "id": "JJC-REVIEW-002",
        "title": "review gate ok",
        "state": "Review",
        "org": "尚书省",
        "now": "汇总中",
        "flow_log": [],
        "todos": [
            {"id": "1", "title": "已完成", "status": "completed"},
            {"id": "2", "title": "已完成2", "status": "completed"},
        ],
    }]

    saved = {}

    monkeypatch.setattr(dashboard_server, "load_tasks", lambda: json.loads(json.dumps(tasks, ensure_ascii=False)))
    monkeypatch.setattr(
        dashboard_server,
        "save_tasks",
        lambda payload: saved.setdefault("tasks", json.loads(json.dumps(payload, ensure_ascii=False))),
    )

    result = dashboard_server.handle_review_action("JJC-REVIEW-002", "approve", "全部完成")

    assert result["ok"] is True
    assert saved["tasks"][0]["state"] == "Done"
