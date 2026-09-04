from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sidecar.main import run  # noqa: E402
from sidecar.service import DEFAULT_SETTINGS, SidecarService  # noqa: E402


class SidecarProtocolTests(unittest.TestCase):
    def test_health_response_reports_stdio_transport(self) -> None:
        stdin = StringIO('{"requestId":"health-1","command":"health"}\n')
        stdout = StringIO()

        self.assertEqual(run(stdin, stdout), 0)

        message = json.loads(stdout.getvalue())
        self.assertEqual(message["type"], "response")
        self.assertEqual(message["request_id"], "health-1")
        self.assertTrue(message["payload"]["ok"])
        self.assertEqual(message["payload"]["transport"], "stdio-jsonl")

    def test_task_submit_emits_task_and_status_events(self) -> None:
        stdin = StringIO(
            '{"requestId":"task-1","command":"task.submit","payload":{"title":"实现一期"}}\n'
            '{"requestId":"status-1","command":"status"}\n'
        )
        stdout = StringIO()

        run(stdin, stdout)

        messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(messages[0]["payload"]["task"]["title"], "实现一期")
        self.assertEqual(messages[1]["payload"]["name"], "task.created")
        self.assertEqual(messages[-1]["payload"]["taskCount"], 1)

    def test_task_submit_snapshots_execution_preferences_and_queue_event(self) -> None:
        service = SidecarService()

        messages = service.handle(
            {
                "requestId": "task-config-1",
                "command": "task.submit",
                "payload": {
                    "title": "检查配置快照",
                    "description": "验证执行中心上下文",
                    "agent": "general",
                    "thinking": "deep",
                    "network": "off",
                    "skills": ["code-review"],
                    "mcp": False,
                },
            }
        )

        task = messages[0]["payload"]["task"]
        self.assertEqual(task["description"], "验证执行中心上下文")
        self.assertEqual(task["agent"], "general")
        self.assertEqual(task["thinking"], "deep")
        self.assertEqual(task["network"], "off")
        self.assertEqual(task["skills"], ["code-review"])
        self.assertFalse(task["mcp"])
        self.assertEqual(task["phase"], "queued")
        self.assertEqual(task["progress"], 0)
        self.assertEqual(messages[2]["payload"]["name"], "execution.queued")
        self.assertEqual(messages[2]["payload"]["taskId"], task["id"])

    def test_invalid_json_is_reported_without_crash(self) -> None:
        stdin = StringIO("not-json\n")
        stdout = StringIO()

        run(stdin, stdout)

        message = json.loads(stdout.getvalue())
        self.assertEqual(message["type"], "error")
        self.assertEqual(message["payload"]["code"], "invalid_json")

    def test_settings_get_returns_first_run_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as config_dir:
            service = SidecarService(config_dir)

            messages = service.handle({"requestId": "settings-1", "command": "settings.get"})

            self.assertEqual(messages[0]["type"], "response")
            self.assertEqual(messages[0]["payload"]["settings"], DEFAULT_SETTINGS)
            self.assertIsNone(messages[0]["payload"]["updatedAt"])

    def test_settings_update_deep_merges_and_emits_event(self) -> None:
        with tempfile.TemporaryDirectory() as config_dir:
            service = SidecarService(config_dir)

            messages = service.handle(
                {
                    "requestId": "settings-2",
                    "command": "settings.update",
                    "payload": {
                        "settings": {
                            "agent": {"model": "gpt-5"},
                            "network": {"policy": "off"},
                        }
                    },
                }
            )

            self.assertEqual(messages[0]["type"], "response")
            payload = messages[0]["payload"]
            self.assertEqual(payload["settings"]["agent"]["model"], "gpt-5")
            self.assertEqual(payload["settings"]["agent"]["defaultAgent"], "general")
            self.assertEqual(payload["settings"]["network"]["policy"], "off")
            self.assertIsInstance(payload["updatedAt"], str)
            self.assertEqual(messages[1]["type"], "event")
            self.assertEqual(messages[1]["payload"]["name"], "settings.updated")
            self.assertEqual(messages[1]["payload"]["settings"], payload["settings"])

            persisted = json.loads((Path(config_dir) / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["version"], 1)
            self.assertEqual(persisted["settings"], payload["settings"])

    def test_settings_persist_across_sidecar_instances(self) -> None:
        with tempfile.TemporaryDirectory() as config_dir:
            first = StringIO(
                '{"requestId":"settings-3","command":"settings.update",'
                '"payload":{"settings":{"thinking":{"mode":"deep"}}}}\n'
            )
            run(first, StringIO(), config_dir=config_dir)

            second_stdout = StringIO()
            run(
                StringIO('{"requestId":"settings-4","command":"settings.get"}\n'),
                second_stdout,
                config_dir=config_dir,
            )
            message = json.loads(second_stdout.getvalue())
            self.assertEqual(message["payload"]["settings"]["thinking"]["mode"], "deep")

    def test_settings_update_rejects_invalid_values_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as config_dir:
            service = SidecarService(config_dir)
            with self.assertRaises(ValueError):
                service.handle(
                    {
                        "requestId": "settings-5",
                        "command": "settings.update",
                        "payload": {"settings": {"network": {"policy": "sometimes"}}},
                    }
                )

            self.assertFalse((Path(config_dir) / "settings.json").exists())
            self.assertEqual(service._settings.payload()["settings"], DEFAULT_SETTINGS)

    def test_run_uses_edict_config_dir_environment_variable(self) -> None:
        with tempfile.TemporaryDirectory() as config_dir:
            request = StringIO(
                '{"requestId":"settings-6","command":"settings.update",'
                '"payload":{"settings":{"mcp":{"enabled":true}}}}\n'
            )
            with mock.patch.dict(os.environ, {"EDICT_CONFIG_DIR": config_dir}):
                run(request, StringIO())

            self.assertTrue((Path(config_dir) / "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
