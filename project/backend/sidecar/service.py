"""Edict desktop task service and its local settings store.

The service intentionally owns no socket or web server. The Electron main process
starts it as a child process and communicates through stdin/stdout only.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .protocol import PROTOCOL_VERSION, event, now_iso, response


SETTINGS_VERSION = 1

# Keep the first-run configuration useful without implying that any remote
# provider, agent runtime, skill registry, or MCP server is already connected.
DEFAULT_SETTINGS: dict[str, Any] = {
    "backend": {
        "provider": "local",
        "baseUrl": "http://127.0.0.1:7891",
    },
    "agent": {
        "defaultAgent": "general",
        "allowedAgents": ["general"],
        "model": "auto",
    },
    "thinking": {"mode": "balanced"},
    "network": {"policy": "ask"},
    "skills": {"enabledSkillIds": []},
    "mcp": {"enabled": False, "servers": []},
}

_SETTINGS_SHAPE: dict[str, set[str]] = {
    "backend": {"provider", "baseUrl"},
    "agent": {"defaultAgent", "allowedAgents", "model"},
    "thinking": {"mode"},
    "network": {"policy"},
    "skills": {"enabledSkillIds"},
    "mcp": {"enabled", "servers"},
}


def _copy_default_settings() -> dict[str, Any]:
    """Return a fresh settings tree so callers cannot mutate the defaults."""
    return copy.deepcopy(DEFAULT_SETTINGS)


def _merge_settings(target: dict[str, Any], patch: dict[str, Any]) -> None:
    """Deep-merge a validated-shaped patch into a settings tree."""
    for key, value in patch.items():
        if key not in _SETTINGS_SHAPE:
            raise ValueError(f"unsupported settings section: {key!r}")
        if not isinstance(value, dict):
            raise ValueError(f"settings.{key} must be an object")
        unknown = set(value) - _SETTINGS_SHAPE[key]
        if unknown:
            names = ", ".join(sorted(str(item) for item in unknown))
            raise ValueError(f"unsupported settings.{key} field(s): {names}")
        target_section = target[key]
        target_section.update(copy.deepcopy(value))


def _validate_settings(settings: dict[str, Any]) -> None:
    """Validate the stable Phase 1 settings contract in place."""
    if set(settings) != set(_SETTINGS_SHAPE):
        missing = set(_SETTINGS_SHAPE) - set(settings)
        unknown = set(settings) - set(_SETTINGS_SHAPE)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unsupported " + ", ".join(sorted(unknown)))
        raise ValueError("invalid settings sections: " + "; ".join(details))

    backend = settings["backend"]
    if not isinstance(backend, dict):
        raise ValueError("settings.backend must be an object")
    if backend.get("provider") not in {"local", "legacy", "fastapi"}:
        raise ValueError("settings.backend.provider must be local, legacy, or fastapi")
    if not isinstance(backend.get("baseUrl"), str) or not backend["baseUrl"].strip():
        raise ValueError("settings.backend.baseUrl must be a non-empty string")

    agent = settings["agent"]
    if not isinstance(agent, dict):
        raise ValueError("settings.agent must be an object")
    allowed_agents = agent.get("allowedAgents")
    if (
        not isinstance(allowed_agents, list)
        or not allowed_agents
        or any(not isinstance(item, str) or not item.strip() for item in allowed_agents)
    ):
        raise ValueError("settings.agent.allowedAgents must be a non-empty string list")
    if len(set(allowed_agents)) != len(allowed_agents):
        raise ValueError("settings.agent.allowedAgents must not contain duplicates")
    if not isinstance(agent.get("defaultAgent"), str) or not agent["defaultAgent"].strip():
        raise ValueError("settings.agent.defaultAgent must be a non-empty string")
    if agent["defaultAgent"] not in allowed_agents:
        raise ValueError("settings.agent.defaultAgent must be included in allowedAgents")
    if not isinstance(agent.get("model"), str) or not agent["model"].strip():
        raise ValueError("settings.agent.model must be a non-empty string")

    thinking = settings["thinking"]
    if not isinstance(thinking, dict) or thinking.get("mode") not in {"fast", "balanced", "deep"}:
        raise ValueError("settings.thinking.mode must be fast, balanced, or deep")

    network = settings["network"]
    if not isinstance(network, dict) or network.get("policy") not in {"off", "ask", "on"}:
        raise ValueError("settings.network.policy must be off, ask, or on")

    skills = settings["skills"]
    enabled_skills = skills.get("enabledSkillIds") if isinstance(skills, dict) else None
    if (
        not isinstance(enabled_skills, list)
        or any(not isinstance(item, str) or not item.strip() for item in enabled_skills)
        or len(set(enabled_skills)) != len(enabled_skills)
    ):
        raise ValueError("settings.skills.enabledSkillIds must be a unique string list")

    mcp = settings["mcp"]
    if not isinstance(mcp, dict) or not isinstance(mcp.get("enabled"), bool):
        raise ValueError("settings.mcp.enabled must be a boolean")
    servers = mcp.get("servers")
    if not isinstance(servers, list) or any(not isinstance(server, dict) for server in servers):
        raise ValueError("settings.mcp.servers must be an object list")


class SettingsPersistenceError(OSError):
    """Raised when a settings update cannot be written to disk."""


class SettingsStore:
    """Small JSON-backed settings store owned by the Python sidecar."""

    def __init__(self, config_dir: str | Path | None = None) -> None:
        raw_config_dir = config_dir
        if raw_config_dir is None:
            raw_config_dir = os.environ.get("EDICT_CONFIG_DIR")
        self.config_dir = Path(raw_config_dir).expanduser() if raw_config_dir else None
        self.path = self.config_dir / "settings.json" if self.config_dir else None
        self.settings, self.updated_at = self._load()

    def _load(self) -> tuple[dict[str, Any], str | None]:
        if self.path is None or not self.path.is_file():
            return _copy_default_settings(), None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("settings"), dict):
                persisted = raw["settings"]
                updated_at = raw.get("updatedAt")
            else:
                # Accept a plain settings object from early development builds.
                persisted = raw
                updated_at = None
            if not isinstance(persisted, dict):
                raise ValueError("settings file must contain an object")
            settings = _copy_default_settings()
            _merge_settings(settings, persisted)
            _validate_settings(settings)
            return settings, updated_at if isinstance(updated_at, str) else None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # A damaged local file must not prevent the desktop shell from
            # starting; the next successful update will replace it atomically.
            return _copy_default_settings(), None

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        next_settings = copy.deepcopy(self.settings)
        _merge_settings(next_settings, patch)
        _validate_settings(next_settings)
        next_updated_at = now_iso()
        self._persist(next_settings, next_updated_at)
        self.settings = next_settings
        self.updated_at = next_updated_at
        return self.payload()

    def payload(self) -> dict[str, Any]:
        return {
            "settings": copy.deepcopy(self.settings),
            "updatedAt": self.updated_at,
        }

    def _persist(self, settings: dict[str, Any], updated_at: str) -> None:
        if self.path is None:
            return
        temporary_path: Path | None = None
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd, temporary_name = tempfile.mkstemp(
                prefix=".settings.", suffix=".tmp", dir=self.config_dir
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "version": SETTINGS_VERSION,
                        "settings": settings,
                        "updatedAt": updated_at,
                    },
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                # Permissions are best-effort on filesystems that do not expose
                # POSIX modes; the atomic replacement remains guaranteed.
                pass
        except OSError as exc:
            raise SettingsPersistenceError(f"unable to persist settings: {exc}") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass


@dataclass
class Task:
    id: str
    title: str
    status: str
    created_at: str
    description: str = ""
    agent: str = "general"
    thinking: str = "balanced"
    network: str = "ask"
    skills: list[str] | None = None
    mcp: bool = False
    phase: str = "queued"
    progress: int = 0
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["skills"] = list(self.skills or [])
        payload["updated_at"] = self.updated_at or self.created_at
        return payload


class SidecarService:
    """Handles JSONL commands and produces response/event message pairs."""

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self._tasks: list[Task] = []
        self._settings = SettingsStore(config_dir)

    def handle(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        request_id = request.get("requestId")
        command = request.get("command")

        if command == "health":
            return [
                response(
                    request_id,
                    {
                        "ok": True,
                        "service": "edict-sidecar",
                        "protocolVersion": PROTOCOL_VERSION,
                        "transport": "stdio-jsonl",
                    },
                ).to_dict()
            ]

        if command == "status":
            return [
                response(request_id, self._status_payload()).to_dict(),
                event("status", self._status_payload()).to_dict(),
            ]

        if command == "settings.get":
            return [response(request_id, self._settings.payload()).to_dict()]

        if command == "settings.update":
            payload = request.get("payload")
            if not isinstance(payload, dict):
                raise ValueError("settings.update requires an object payload")
            # The documented form wraps the patch in `settings`; accepting a
            # direct patch keeps early renderer builds compatible as well.
            patch = payload.get("settings", payload)
            if not isinstance(patch, dict):
                raise ValueError("settings.update payload.settings must be an object")
            result = self._settings.update(patch)
            return [
                response(request_id, result).to_dict(),
                event("settings.updated", result).to_dict(),
            ]

        if command == "task.submit":
            payload = request.get("payload")
            title = payload.get("title") if isinstance(payload, dict) else None
            if not isinstance(title, str) or not title.strip():
                raise ValueError("task.submit requires a non-empty payload.title")

            task_settings = self._task_settings(payload)
            created_at = now_iso()

            task = Task(
                id=str(uuid4()),
                title=title.strip(),
                status="queued",
                created_at=created_at,
                description=task_settings["description"],
                agent=task_settings["agent"],
                thinking=task_settings["thinking"],
                network=task_settings["network"],
                skills=task_settings["skills"],
                mcp=task_settings["mcp"],
                updated_at=created_at,
            )
            self._tasks.append(task)
            return [
                response(request_id, {"task": task.to_dict()}).to_dict(),
                event("task.created", {"task": task.to_dict()}).to_dict(),
                event(
                    "execution.queued",
                    {
                        "taskId": task.id,
                        "phase": task.phase,
                        "progress": task.progress,
                        "detail": "任务已进入队列，等待执行器接管",
                    },
                ).to_dict(),
                event("status", self._status_payload()).to_dict(),
            ]

        raise LookupError(f"unsupported command: {command!r}")

    def _status_payload(self) -> dict[str, Any]:
        return {
            "state": "ready",
            "taskCount": len(self._tasks),
            "tasks": [task.to_dict() for task in self._tasks],
            "transport": "stdio-jsonl",
        }

    def _task_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate and snapshot per-task execution preferences."""
        defaults = self._settings.settings
        description = payload.get("description", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise ValueError("task.submit payload.description must be a string")

        agent = payload.get("agent", defaults["agent"]["defaultAgent"])
        allowed_agents = defaults["agent"]["allowedAgents"]
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("task.submit payload.agent must be a non-empty string")
        if agent not in allowed_agents:
            raise ValueError(f"task.submit payload.agent is not allowed: {agent!r}")

        thinking = payload.get("thinking", defaults["thinking"]["mode"])
        if thinking not in {"fast", "balanced", "deep"}:
            raise ValueError("task.submit payload.thinking must be fast, balanced, or deep")

        network = payload.get("network", defaults["network"]["policy"])
        if network not in {"off", "ask", "on"}:
            raise ValueError("task.submit payload.network must be off, ask, or on")

        skills = payload.get("skills", defaults["skills"]["enabledSkillIds"])
        if (
            not isinstance(skills, list)
            or any(not isinstance(item, str) or not item.strip() for item in skills)
            or len(set(skills)) != len(skills)
        ):
            raise ValueError("task.submit payload.skills must be a unique string list")

        mcp = payload.get("mcp", defaults["mcp"]["enabled"])
        if not isinstance(mcp, bool):
            raise ValueError("task.submit payload.mcp must be a boolean")

        return {
            "description": description.strip(),
            "agent": agent.strip(),
            "thinking": thinking,
            "network": network,
            "skills": list(skills),
            "mcp": mcp,
        }
