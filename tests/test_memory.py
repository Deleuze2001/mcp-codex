from __future__ import annotations

import pytest

from mcp_codex.services import memory


def test_write_read_and_search_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_CODEX_MEMORY_ROOT", str(tmp_path))

    write_result = memory.write_memory("standards/python.md", "# Python\n\nUse pytest.")
    assert write_result["ok"] is True

    read_result = memory.read_memory("standards/python.md")
    assert read_result["ok"] is True
    assert "Use pytest" in read_result["content"]

    search_result = memory.search_memory("pytest")
    assert search_result["matches"][0]["path"] == "standards/python.md"


def test_memory_rejects_path_escape(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_CODEX_MEMORY_ROOT", str(tmp_path))

    with pytest.raises(ValueError, match="escapes"):
        memory.write_memory("../outside.md", "nope")


def test_create_adr_lists_decisions(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_CODEX_MEMORY_ROOT", str(tmp_path))

    result = memory.create_adr(
        title="Use Markdown Memory",
        context="We need durable project notes.",
        decision="Store memory as markdown.",
        consequences="Easy review, no database.",
    )

    assert result["ok"] is True
    decisions = memory.list_decisions()["decisions"]
    assert len(decisions) == 1
    assert decisions[0].endswith("use-markdown-memory.md")

