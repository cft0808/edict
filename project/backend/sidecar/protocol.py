"""JSONL protocol primitives shared by the sidecar runtime and tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

PROTOCOL_VERSION = "1.0"


def now_iso() -> str:
    """Return an RFC 3339 compatible UTC timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Message:
    """A single JSONL message emitted by the sidecar."""

    type: str
    request_id: str | None
    payload: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def response(request_id: str | None, payload: dict[str, Any]) -> Message:
    return Message("response", request_id, payload, now_iso())


def event(name: str, payload: dict[str, Any]) -> Message:
    return Message("event", None, {"name": name, **payload}, now_iso())


def error(request_id: str | None, code: str, message: str) -> Message:
    return Message(
        "error",
        request_id,
        {"code": code, "message": message},
        now_iso(),
    )
