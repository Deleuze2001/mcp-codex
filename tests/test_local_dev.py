from __future__ import annotations

import json
import sys

from mcp_codex.services import local_dev


def test_run_command_allowlist_rejects_unknown_command(tmp_path, monkeypatch):
    config = tmp_path / "allowlist.json"
    config.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("MCP_CODEX_LOCAL_DEV_CONFIG", str(config))

    result = local_dev.run_command_allowlist("missing")

    assert result["ok"] is False
    assert "available_commands" in result


def test_run_command_allowlist_executes_without_shell(tmp_path, monkeypatch):
    marker = tmp_path / "marker.txt"
    config = tmp_path / "allowlist.json"
    config.write_text(
        json.dumps(
            {
                "mark": {
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ok')",
                    ],
                    "description": "Create a marker file.",
                    "timeout_seconds": 10,
                    "allow_extra_args": True,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CODEX_LOCAL_DEV_CONFIG", str(config))

    result = local_dev.run_command_allowlist("mark", [str(marker)])

    assert result["ok"] is True
    assert marker.read_text(encoding="utf-8") == "ok"


def test_extra_args_require_allowlist_permission(tmp_path, monkeypatch):
    config = tmp_path / "allowlist.json"
    config.write_text(
        json.dumps(
            {
                "no_args": {
                    "command": [sys.executable, "--version"],
                    "description": "No extra args.",
                    "allow_extra_args": False,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CODEX_LOCAL_DEV_CONFIG", str(config))

    result = local_dev.run_command_allowlist("no_args", ["unexpected"])

    assert result["ok"] is False
    assert "does not allow extra arguments" in result["error"]

