from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SECRET_PATTERN = re.compile(
    r"(?i)(aws_access_key_id|aws_secret_access_key|github_token|api_key|token|password|secret)"
)


@dataclass
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        return data


def project_root() -> Path:
    return env_path("MCP_CODEX_WORKSPACE_ROOT", ".").resolve()


def env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


def redact(value: str) -> str:
    lines: list[str] = []
    for line in value.splitlines():
        if SECRET_PATTERN.search(line):
            lines.append("[redacted]")
        else:
            lines.append(line)
    return "\n".join(lines)


def log_tool_execution(tool_name: str, duration_ms: int, success: bool, detail: str = "") -> None:
    log_dir = env_path("MCP_CODEX_LOG_DIR", ".mcp-codex/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool_name,
        "duration_ms": duration_ms,
        "success": success,
        "detail": redact(detail)[:500],
    }
    with (log_dir / "tools.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 60,
) -> CommandResult:
    started = time.monotonic()
    command_cwd = cwd or project_root()
    try:
        completed = subprocess.run(
            command,
            cwd=command_cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        result = CommandResult(
            command=command,
            cwd=str(command_cwd),
            returncode=completed.returncode,
            stdout=redact(completed.stdout),
            stderr=redact(completed.stderr),
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = CommandResult(
            command=command,
            cwd=str(command_cwd),
            returncode=124,
            stdout=redact(exc.stdout or ""),
            stderr=redact(exc.stderr or f"Command timed out after {timeout_seconds}s"),
            duration_ms=duration_ms,
            timed_out=True,
        )
    log_tool_execution("run_command", result.duration_ms, result.ok, " ".join(command))
    return result


def parse_transport(argv: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport to use.",
    )
    args = parser.parse_args(argv)
    return args.transport
