from __future__ import annotations

import base64
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


WORKFLOW_PREFIX = ".github/workflows/"
WORKFLOW_SUFFIXES = (".yml", ".yaml")


def _gh(args: list[str], timeout_seconds: int = 60, stdin: str | None = None) -> dict[str, Any]:
    _ensure_gh()
    result = run_command(["gh", *args], timeout_seconds=timeout_seconds, stdin=stdin)
    if not result.ok:
        raise GitHubError(result.stderr or result.stdout or "gh command failed")
    if result.stdout.strip().startswith(("{", "[")):
        return json.loads(result.stdout)
    return {"output": result.stdout}


def _api(path: str, timeout_seconds: int = 60, stdin: str | None = None) -> dict[str, Any]:
    args = ["api"]
    if stdin is not None:
        args.extend(["-X", "PUT", "--input", "-"])
    args.append(path)
    return _gh(args, timeout_seconds=timeout_seconds, stdin=stdin)


def _encoded_repo_path(repo: str, path: str, ref: str | None = None) -> str:
    encoded_path = quote(path.strip("/"))
    query = urlencode({"ref": ref}) if ref else ""
    suffix = f"?{query}" if query else ""
    return f"/repos/{repo}/contents/{encoded_path}{suffix}"


def _validate_workflow_path(path: str) -> str:
    normalized = path.strip("/")
    if not normalized.startswith(WORKFLOW_PREFIX) or not normalized.endswith(WORKFLOW_SUFFIXES):
        raise GitHubError("Workflow edits are restricted to .github/workflows/*.yml or *.yaml files.")
    if ".." in normalized.split("/"):
        raise GitHubError("Workflow path cannot contain '..' segments.")
    return normalized


def get_repo(repo: str) -> dict[str, Any]:
    data = _gh(
        [
            "repo",
            "view",
            repo,
            "--json",
            (
                "nameWithOwner,description,visibility,isPrivate,url,defaultBranchRef,"
                "primaryLanguage,repositoryTopics,licenseInfo,pushedAt,updatedAt"
            ),
        ]
    )
    return {"repository": data}


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
    api_path = _encoded_repo_path(repo, path, ref)
    data = _gh(["api", "-H", "Accept: application/vnd.github.raw", api_path])
    return {"repo": repo, "path": path, "ref": ref, "content": data.get("output", "")}


def list_branches(repo: str, limit: int = 100) -> dict[str, Any]:
    data = _api(f"/repos/{repo}/branches?per_page={limit}")
    return {"branches": data}


def get_branch(repo: str, branch: str) -> dict[str, Any]:
    data = _api(f"/repos/{repo}/branches/{quote(branch, safe='')}")
    return {"branch": data}


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


def get_pr(repo: str, number: int) -> dict[str, Any]:
    data = _gh(
        [
            "pr",
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            (
                "number,title,body,state,author,url,headRefName,baseRefName,isDraft,"
                "mergeable,reviewDecision,commits,files,comments,reviews,statusCheckRollup"
            ),
        ]
    )
    return {"pull_request": data}


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


def list_workflows(repo: str) -> dict[str, Any]:
    data = _api(f"/repos/{repo}/actions/workflows")
    return {"workflows": data.get("workflows", data)}


def get_workflow(repo: str, workflow_id_or_file: str) -> dict[str, Any]:
    encoded = quote(workflow_id_or_file, safe="")
    data = _api(f"/repos/{repo}/actions/workflows/{encoded}")
    return {"workflow": data}


def list_workflow_runs(
    repo: str,
    workflow_id_or_file: str | None = None,
    branch: str | None = None,
    event: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    query = {"per_page": str(limit)}
    if branch:
        query["branch"] = branch
    if event:
        query["event"] = event
    if status:
        query["status"] = status
    encoded_query = urlencode(query)
    if workflow_id_or_file:
        workflow = quote(workflow_id_or_file, safe="")
        path = f"/repos/{repo}/actions/workflows/{workflow}/runs?{encoded_query}"
    else:
        path = f"/repos/{repo}/actions/runs?{encoded_query}"
    data = _api(path)
    return {"workflow_runs": data.get("workflow_runs", data)}


def get_workflow_logs(repo: str, run_id: str) -> dict[str, Any]:
    data = _gh(["run", "view", run_id, "--repo", repo, "--log"], timeout_seconds=120)
    return {"repo": repo, "run_id": run_id, "logs": data.get("output", "")}


def get_workflow_run(repo: str, run_id: str) -> dict[str, Any]:
    data = _gh(
        [
            "run",
            "view",
            run_id,
            "--repo",
            repo,
            "--json",
            (
                "databaseId,name,status,conclusion,event,headBranch,headSha,createdAt,"
                "updatedAt,url,jobs,workflowName,displayTitle"
            ),
        ]
    )
    return {"workflow_run": data}


def read_workflow_file(repo: str, workflow_path: str, ref: str = "HEAD") -> dict[str, Any]:
    path = _validate_workflow_path(workflow_path)
    return read_file(repo, path, ref=ref)


def update_workflow_file(
    repo: str,
    workflow_path: str,
    content: str,
    message: str,
    branch: str,
    expected_sha: str | None = None,
    create: bool = False,
) -> dict[str, Any]:
    path = _validate_workflow_path(workflow_path)
    if not message.strip():
        raise GitHubError("A non-empty commit message is required for workflow edits.")
    if not branch.strip():
        raise GitHubError("A target branch is required for workflow edits.")

    metadata: dict[str, Any] | None = None
    try:
        metadata = _api(_encoded_repo_path(repo, path, branch))
    except GitHubError as exc:
        if not create or "404" not in str(exc):
            raise

    sha = expected_sha or (metadata or {}).get("sha")
    if metadata and expected_sha and metadata.get("sha") != expected_sha:
        raise GitHubError("Workflow file SHA does not match expected_sha; refetch before editing.")

    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    data = _api(_encoded_repo_path(repo, path), stdin=json.dumps(payload), timeout_seconds=120)
    return {"commit": data.get("commit"), "content": data.get("content"), "path": path, "branch": branch}


def draft_commit_message(
    summary: str,
    details: list[str] | None = None,
    tests: list[str] | None = None,
    scope: str | None = None,
    breaking_change: str | None = None,
) -> dict[str, Any]:
    subject_prefix = f"{scope.strip()}: " if scope else ""
    subject = f"{subject_prefix}{summary.strip()}"
    body_parts = []
    if details:
        body_parts.append("Changes:\n" + "\n".join(f"- {item}" for item in details if item.strip()))
    if tests:
        body_parts.append("Verification:\n" + "\n".join(f"- {item}" for item in tests if item.strip()))
    if breaking_change:
        body_parts.append(f"BREAKING CHANGE: {breaking_change.strip()}")
    message = subject if not body_parts else subject + "\n\n" + "\n\n".join(body_parts)
    return {"subject": subject, "body": "\n\n".join(body_parts), "message": message}


def draft_pr_description(
    title: str,
    summary: list[str],
    tests: list[str] | None = None,
    screenshots: list[str] | None = None,
    risks: list[str] | None = None,
    follow_ups: list[str] | None = None,
) -> dict[str, Any]:
    sections = ["## Summary", *[f"- {item}" for item in summary if item.strip()]]
    if tests:
        sections.extend(["", "## Verification", *[f"- {item}" for item in tests if item.strip()]])
    if screenshots:
        sections.extend(["", "## Screenshots", *[f"- {item}" for item in screenshots if item.strip()]])
    if risks:
        sections.extend(["", "## Risks", *[f"- {item}" for item in risks if item.strip()]])
    if follow_ups:
        sections.extend(["", "## Follow-ups", *[f"- {item}" for item in follow_ups if item.strip()]])
    body = "\n".join(sections).strip() + "\n"
    return {"title": title.strip(), "body": body}


def get_deployments(repo: str, limit: int = 20) -> dict[str, Any]:
    data = _gh(["api", f"/repos/{repo}/deployments?per_page={limit}"])
    return {"deployments": data}
