from __future__ import annotations

import pytest

from mcp_codex.services import github


def test_missing_gh_returns_clear_error(monkeypatch):
    monkeypatch.setattr(github.shutil, "which", lambda _: None)

    with pytest.raises(github.GitHubError, match="gh"):
        github.list_repos()

