from __future__ import annotations

import sys

from mcp_codex.runtime import run_command


def test_run_command_supports_stdin(tmp_path):
    result = run_command(
        [sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
        cwd=tmp_path,
        stdin="hello",
    )

    assert result.ok is True
    assert result.stdout.strip() == "HELLO"
