from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp_codex.runtime import env_path, log_tool_execution, project_root, run_command


@dataclass
class AllowlistEntry:
    command: list[str]
    description: str = ""
    timeout_seconds: int = 60
    allow_extra_args: bool = False
    long_running: bool = False
    cwd: str | None = None


def allowlist_path() -> Path:
    return env_path("MCP_CODEX_LOCAL_DEV_CONFIG", "config/local_dev.allowlist.json")


def load_allowlist(path: Path | None = None) -> dict[str, AllowlistEntry]:
    config_path = path or allowlist_path()
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {name: AllowlistEntry(**entry) for name, entry in raw.items()}


def check_env() -> dict[str, Any]:
    tools = ["python", "pytest", "ruff", "mypy", "uvicorn", "gh", "npx"]
    from shutil import which

    return {
        "project_root": str(project_root()),
        "allowlist_path": str(allowlist_path()),
        "tools": {tool: which(tool) for tool in tools},
    }


def run_command_allowlist(command_name: str, extra_args: list[str] | None = None) -> dict[str, Any]:
    allowlist = load_allowlist()
    if command_name not in allowlist:
        return {
            "ok": False,
            "error": f"`{command_name}` is not in the local dev allowlist.",
            "available_commands": sorted(allowlist),
        }
    entry = allowlist[command_name]
    args = extra_args or []
    if args and not entry.allow_extra_args:
        return {"ok": False, "error": f"`{command_name}` does not allow extra arguments."}

    command = [*entry.command, *args]
    cwd = project_root() / entry.cwd if entry.cwd else project_root()

    if entry.long_running:
        started = time.monotonic()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        log_tool_execution(command_name, duration_ms, True, " ".join(command))
        return {
            "ok": True,
            "pid": process.pid,
            "command": command,
            "cwd": str(cwd),
            "message": "Started long-running process; stop it manually when finished.",
        }

    result = run_command(command, cwd=cwd, timeout_seconds=entry.timeout_seconds)
    return result.to_dict()


def run_tests(extra_args: list[str] | None = None) -> dict[str, Any]:
    return run_command_allowlist("tests", extra_args)


def run_linter() -> dict[str, Any]:
    return run_command_allowlist("linter")


def run_typecheck() -> dict[str, Any]:
    return run_command_allowlist("typecheck")


def start_app(extra_args: list[str] | None = None) -> dict[str, Any]:
    return run_command_allowlist("start_app", extra_args)


def read_local_logs(path: str = ".mcp-codex/logs/tools.jsonl", lines: int = 100) -> dict[str, Any]:
    log_path = Path(path).expanduser()
    if not log_path.is_absolute():
        log_path = project_root() / log_path
    if not log_path.exists():
        return {"ok": False, "error": f"Log file does not exist: {log_path}"}
    content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"ok": True, "path": str(log_path), "lines": content[-lines:]}

