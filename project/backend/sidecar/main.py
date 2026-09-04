"""Run the Edict desktop sidecar over stdin/stdout JSONL.

No networking modules are imported or used here by design.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from .protocol import error
from .service import SidecarService


def process_line(service: SidecarService, line: str) -> list[dict[str, Any]]:
    """Parse and process one JSONL request without terminating the process."""
    try:
        request = json.loads(line)
    except json.JSONDecodeError as exc:
        return [error(None, "invalid_json", str(exc)).to_dict()]

    if not isinstance(request, dict):
        return [
            error(None, "invalid_request", "request must be a JSON object").to_dict()
        ]

    request_id = request.get("requestId")
    if request_id is not None and not isinstance(request_id, str):
        return [error(None, "invalid_request", "requestId must be a string").to_dict()]

    try:
        return service.handle(request)
    except ValueError as exc:
        return [error(request_id, "invalid_request", str(exc)).to_dict()]
    except OSError as exc:
        return [error(request_id, "storage_error", str(exc)).to_dict()]
    except LookupError as exc:
        return [error(request_id, "unsupported_command", str(exc)).to_dict()]


def run(
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    config_dir: str | Path | None = None,
) -> int:
    """Serve until EOF, emitting exactly one JSON object per stdout line."""
    service = SidecarService(config_dir)
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        for message in process_line(service, line):
            stdout.write(
                json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
