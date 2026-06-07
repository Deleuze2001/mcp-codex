from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from mcp_codex.runtime import project_root, run_command


class AlembicError(RuntimeError):
    pass


def _workspace(workspace_root: str | None = None) -> Path:
    return Path(workspace_root).expanduser().resolve() if workspace_root else project_root()


def _alembic_command(workspace: Path) -> list[str]:
    candidates = [
        workspace / ".venv" / "bin" / "alembic",
        workspace / "venv" / "bin" / "alembic",
    ]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return [str(candidate)]

    path_command = shutil.which("alembic")
    if path_command:
        return [path_command]

    python_candidates = [
        workspace / ".venv" / "bin" / "python",
        workspace / "venv" / "bin" / "python",
    ]
    for candidate in python_candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return [str(candidate), "-m", "alembic"]

    raise AlembicError(
        "Could not find Alembic. Expected a project virtualenv with `alembic`, "
        "or an `alembic` command on PATH."
    )


def _config_args(config_file: str) -> list[str]:
    return ["-c", config_file] if config_file else []


def _x_args(x_args: list[str] | None = None) -> list[str]:
    args: list[str] = []
    for value in x_args or []:
        args.extend(["-x", value])
    return args


def _run_alembic(
    args: list[str],
    *,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    workspace = _workspace(workspace_root)
    command = [
        *_alembic_command(workspace),
        *_config_args(config_file),
        *_x_args(x_args),
        *args,
    ]
    result = run_command(command, cwd=workspace, timeout_seconds=timeout_seconds)
    return result.to_dict()


def _database_write_allowed(allow_database_write: bool) -> bool:
    return allow_database_write and os.environ.get("MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE") == "1"


def _versions_dirs(workspace: Path) -> list[str]:
    candidates = [
        workspace / "alembic" / "versions",
        workspace / "migrations" / "versions",
    ]
    found = [path for path in candidates if path.is_dir()]
    if not found:
        found = [path for path in workspace.glob("*/versions") if path.is_dir()]
    return sorted(str(path.relative_to(workspace)) for path in found)


def check_env(workspace_root: str | None = None, config_file: str = "alembic.ini") -> dict[str, Any]:
    workspace = _workspace(workspace_root)
    config_path = workspace / config_file
    try:
        command = _alembic_command(workspace)
        command_error = ""
    except AlembicError as exc:
        command = []
        command_error = str(exc)

    return {
        "workspace_root": str(workspace),
        "config_file": str(config_path),
        "config_exists": config_path.exists(),
        "versions_dirs": _versions_dirs(workspace),
        "alembic_command": command,
        "alembic_command_error": command_error,
        "database_write_env_enabled": os.environ.get("MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE") == "1",
    }


def current(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    return _run_alembic(["current", "--verbose"], workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def heads(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    return _run_alembic(["heads", "--verbose"], workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def history(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    return _run_alembic(["history", "--verbose"], workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def show_revision(
    revision: str,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    return _run_alembic(["show", revision], workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def check_pending(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    return _run_alembic(["check"], workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def create_revision(
    message: str,
    autogenerate: bool = False,
    head: str | None = None,
    branch_label: str | None = None,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    args = ["revision", "-m", message]
    if autogenerate:
        args.append("--autogenerate")
    if head:
        args.extend(["--head", head])
    if branch_label:
        args.extend(["--branch-label", branch_label])
    return _run_alembic(args, workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def upgrade(
    target: str = "head",
    sql: bool = True,
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    if not sql and not _database_write_allowed(allow_database_write):
        return {
            "ok": False,
            "error": (
                "Refusing to modify the database. Use sql=True for preview, or set "
                "MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE=1 and pass allow_database_write=True."
            ),
        }
    args = ["upgrade", target]
    if sql:
        args.append("--sql")
    return _run_alembic(args, workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def downgrade(
    target: str = "-1",
    sql: bool = True,
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    if not sql and not _database_write_allowed(allow_database_write):
        return {
            "ok": False,
            "error": (
                "Refusing to modify the database. Use sql=True for preview, or set "
                "MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE=1 and pass allow_database_write=True."
            ),
        }
    args = ["downgrade", target]
    if sql:
        args.append("--sql")
    return _run_alembic(args, workspace_root=workspace_root, config_file=config_file, x_args=x_args)


def stamp(
    target: str = "head",
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict[str, Any]:
    if not _database_write_allowed(allow_database_write):
        return {
            "ok": False,
            "error": (
                "Refusing to stamp the database. Set MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE=1 "
                "and pass allow_database_write=True."
            ),
        }
    return _run_alembic(["stamp", target], workspace_root=workspace_root, config_file=config_file, x_args=x_args)
