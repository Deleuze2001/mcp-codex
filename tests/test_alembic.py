from __future__ import annotations

import stat

from mcp_codex.services import alembic


def _fake_alembic_project(tmp_path):
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    executable = bin_dir / "alembic"
    executable.write_text("#!/usr/bin/env sh\necho \"$@\"\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    (tmp_path / "alembic.ini").write_text("[alembic]\nscript_location = migrations\n", encoding="utf-8")
    (tmp_path / "migrations" / "versions").mkdir(parents=True)
    return tmp_path


def test_check_env_finds_project_alembic(tmp_path):
    workspace = _fake_alembic_project(tmp_path)

    result = alembic.check_env(workspace_root=str(workspace))

    assert result["config_exists"] is True
    assert result["alembic_command"] == [str(workspace / ".venv" / "bin" / "alembic")]
    assert result["versions_dirs"] == ["migrations/versions"]


def test_current_runs_alembic_with_config(tmp_path):
    workspace = _fake_alembic_project(tmp_path)

    result = alembic.current(workspace_root=str(workspace))

    assert result["ok"] is True
    assert "-c alembic.ini current --verbose" in result["stdout"]


def test_upgrade_defaults_to_sql_preview(tmp_path):
    workspace = _fake_alembic_project(tmp_path)

    result = alembic.upgrade(workspace_root=str(workspace))

    assert result["ok"] is True
    assert "upgrade head --sql" in result["stdout"]


def test_database_write_requires_double_opt_in(tmp_path):
    workspace = _fake_alembic_project(tmp_path)

    result = alembic.upgrade(workspace_root=str(workspace), sql=False, allow_database_write=True)

    assert result["ok"] is False
    assert "Refusing to modify the database" in result["error"]


def test_database_write_runs_with_env_and_argument(tmp_path, monkeypatch):
    workspace = _fake_alembic_project(tmp_path)
    monkeypatch.setenv("MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE", "1")

    result = alembic.upgrade(workspace_root=str(workspace), sql=False, allow_database_write=True)

    assert result["ok"] is True
    assert "upgrade head" in result["stdout"]
    assert "--sql" not in result["stdout"]


def test_project_root_can_come_from_environment(tmp_path, monkeypatch):
    workspace = _fake_alembic_project(tmp_path)
    monkeypatch.setenv("MCP_CODEX_WORKSPACE_ROOT", str(workspace))

    result = alembic.heads()

    assert result["ok"] is True
    assert "heads --verbose" in result["stdout"]
