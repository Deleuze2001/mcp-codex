from __future__ import annotations

import pytest

from mcp_codex.services import github


def test_missing_gh_returns_clear_error(monkeypatch):
    monkeypatch.setattr(github.shutil, "which", lambda _: None)

    with pytest.raises(github.GitHubError, match="gh"):
        github.list_repos()


def test_workflow_path_validation_restricts_to_github_actions():
    assert github._validate_workflow_path(".github/workflows/ci.yml") == ".github/workflows/ci.yml"

    with pytest.raises(github.GitHubError, match="restricted"):
        github._validate_workflow_path("README.md")

    with pytest.raises(github.GitHubError, match="restricted"):
        github._validate_workflow_path(".github/workflows/ci.txt")


def test_draft_commit_message_includes_context_and_verification():
    result = github.draft_commit_message(
        summary="add GitHub Actions helpers",
        scope="github",
        details=["list workflows", "update workflow files safely"],
        tests=["python -m pytest"],
    )

    assert result["subject"] == "github: add GitHub Actions helpers"
    assert "Changes:" in result["message"]
    assert "- list workflows" in result["message"]
    assert "Verification:" in result["message"]


def test_draft_pr_description_has_review_sections():
    result = github.draft_pr_description(
        title="Build out GitHub MCP support",
        summary=["Adds workflow inspection tools"],
        tests=["16 passed"],
        risks=["Requires gh authentication"],
    )

    assert result["title"] == "Build out GitHub MCP support"
    assert "## Summary" in result["body"]
    assert "- Adds workflow inspection tools" in result["body"]
    assert "## Verification" in result["body"]
    assert "## Risks" in result["body"]


def test_update_workflow_file_requires_nonempty_message(monkeypatch):
    with pytest.raises(github.GitHubError, match="commit message"):
        github.update_workflow_file(
            repo="owner/repo",
            workflow_path=".github/workflows/ci.yml",
            content="name: CI\n",
            message=" ",
            branch="feature",
        )


def test_update_workflow_file_detects_sha_conflict(monkeypatch):
    monkeypatch.setattr(github, "_api", lambda *_, **__: {"sha": "actual"})

    with pytest.raises(github.GitHubError, match="SHA"):
        github.update_workflow_file(
            repo="owner/repo",
            workflow_path=".github/workflows/ci.yml",
            content="name: CI\n",
            message="ci: update workflow",
            branch="feature",
            expected_sha="expected",
        )


def test_update_workflow_file_sends_base64_payload(monkeypatch):
    calls = []

    def fake_api(path, timeout_seconds=60, stdin=None):
        calls.append({"path": path, "timeout_seconds": timeout_seconds, "stdin": stdin})
        if stdin is None:
            return {"sha": "abc123"}
        return {"commit": {"sha": "def456"}, "content": {"path": ".github/workflows/ci.yml"}}

    monkeypatch.setattr(github, "_api", fake_api)

    result = github.update_workflow_file(
        repo="owner/repo",
        workflow_path=".github/workflows/ci.yml",
        content="name: CI\n",
        message="ci: update workflow",
        branch="feature",
    )

    assert result["commit"]["sha"] == "def456"
    assert calls[1]["stdin"] is not None
    assert '"branch": "feature"' in calls[1]["stdin"]
    assert '"sha": "abc123"' in calls[1]["stdin"]


def test_update_workflow_file_create_only_swallows_missing_file(monkeypatch):
    calls = []

    def fake_api(path, timeout_seconds=60, stdin=None):
        calls.append({"path": path, "stdin": stdin})
        if stdin is None:
            raise github.GitHubError("HTTP 404: Not Found")
        return {"commit": {"sha": "created"}, "content": {"path": ".github/workflows/new.yml"}}

    monkeypatch.setattr(github, "_api", fake_api)

    result = github.update_workflow_file(
        repo="owner/repo",
        workflow_path=".github/workflows/new.yml",
        content="name: New\n",
        message="ci: add workflow",
        branch="feature",
        create=True,
    )

    assert result["commit"]["sha"] == "created"
    assert len(calls) == 2


def test_update_workflow_file_create_reraises_non_404(monkeypatch):
    monkeypatch.setattr(
        github,
        "_api",
        lambda *_, **__: (_ for _ in ()).throw(github.GitHubError("HTTP 401: Unauthorized")),
    )

    with pytest.raises(github.GitHubError, match="401"):
        github.update_workflow_file(
            repo="owner/repo",
            workflow_path=".github/workflows/new.yml",
            content="name: New\n",
            message="ci: add workflow",
            branch="feature",
            create=True,
        )
