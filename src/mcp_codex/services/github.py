from __future__ import annotations

import json
import shutil
from typing import Any
from urllib.parse import quote, urlencode

from mcp_codex.runtime import run_command


class GitHubError(RuntimeError):
    pass


def _ensure_gh() -> None:
    if not shutil.which("gh"):
        raise GitHubError("GitHub CLI `gh` is not installed or not on PATH.")


def _gh(args: list[str], timeout_seconds: int = 60) -> dict[str, Any]:
    _ensure_gh()
    result = run_command(["gh", *args], timeout_seconds=timeout_seconds)
    if not result.ok:
        raise GitHubError(result.stderr or result.stdout or "gh command failed")
    if result.stdout.strip().startswith(("{", "[")):
        return json.loads(result.stdout)
    return {"output": result.stdout}


def list_repos(owner: str | None = None, limit: int = 50) -> dict[str, Any]:
    args = ["repo", "list"]
    if owner:
        args.append(owner)
    args.extend(
        [
            "--limit",
            str(limit),
            "--json",
            "nameWithOwner,description,visibility,isPrivate,url,updatedAt",
        ]
    )
    return {"repositories": _gh(args)}


def read_file(repo: str, path: str, ref: str = "HEAD") -> dict[str, Any]:
    encoded_path = quote(path.strip("/"))
    query = urlencode({"ref": ref})
    api_path = f"/repos/{repo}/contents/{encoded_path}?{query}"
    data = _gh(["api", "-H", "Accept: application/vnd.github.raw", api_path])
    return {"repo": repo, "path": path, "ref": ref, "content": data.get("output", "")}


def search_code(query: str, repo: str | None = None, limit: int = 30) -> dict[str, Any]:
    args = ["search", "code", query, "--limit", str(limit), "--json", "path,repository,url"]
    if repo:
        args.extend(["--repo", repo])
    return {"results": _gh(args)}


def list_prs(repo: str, state: str = "open", limit: int = 30) -> dict[str, Any]:
    return {
        "pull_requests": _gh(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                state,
                "--limit",
                str(limit),
                "--json",
                "number,title,state,author,url,headRefName,baseRefName,isDraft,updatedAt",
            ]
        )
    }


def create_pr(
    repo: str,
    title: str,
    body: str,
    base: str,
    head: str,
    draft: bool = False,
) -> dict[str, Any]:
    args = [
        "pr",
        "create",
        "--repo",
        repo,
        "--title",
        title,
        "--body",
        body,
        "--base",
        base,
        "--head",
        head,
    ]
    if draft:
        args.append("--draft")
    return _gh(args)


def list_issues(repo: str, state: str = "open", limit: int = 30) -> dict[str, Any]:
    return {
        "issues": _gh(
            [
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                state,
                "--limit",
                str(limit),
                "--json",
                "number,title,state,author,url,labels,updatedAt",
            ]
        )
    }


def create_issue(repo: str, title: str, body: str = "") -> dict[str, Any]:
    return _gh(["issue", "create", "--repo", repo, "--title", title, "--body", body])


def get_workflow_runs(repo: str, limit: int = 20) -> dict[str, Any]:
    return {
        "workflow_runs": _gh(
            [
                "run",
                "list",
                "--repo",
                repo,
                "--limit",
                str(limit),
                "--json",
                "databaseId,name,status,conclusion,event,headBranch,createdAt,updatedAt,url",
            ]
        )
    }


def get_workflow_logs(repo: str, run_id: str) -> dict[str, Any]:
    data = _gh(["run", "view", run_id, "--repo", repo, "--log"], timeout_seconds=120)
    return {"repo": repo, "run_id": run_id, "logs": data.get("output", "")}


def get_deployments(repo: str, limit: int = 20) -> dict[str, Any]:
    data = _gh(["api", f"/repos/{repo}/deployments?per_page={limit}"])
    return {"deployments": data}

