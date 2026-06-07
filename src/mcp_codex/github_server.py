from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import github


mcp = FastMCP("Codex GitHub")


@mcp.tool()
def get_repo(repo: str) -> dict:
    """Get repository metadata, including default branch and visibility."""
    return github.get_repo(repo=repo)


@mcp.tool()
def list_repos(owner: str | None = None, limit: int = 50) -> dict:
    """List repositories visible to the authenticated GitHub CLI user."""
    return github.list_repos(owner=owner, limit=limit)


@mcp.tool()
def read_file(repo: str, path: str, ref: str = "HEAD") -> dict:
    """Read a file from a GitHub repository at a branch, tag, or SHA."""
    return github.read_file(repo=repo, path=path, ref=ref)


@mcp.tool()
def list_branches(repo: str, limit: int = 100) -> dict:
    """List repository branches."""
    return github.list_branches(repo=repo, limit=limit)


@mcp.tool()
def get_branch(repo: str, branch: str) -> dict:
    """Get metadata for a repository branch."""
    return github.get_branch(repo=repo, branch=branch)


@mcp.tool()
def search_code(query: str, repo: str | None = None, limit: int = 30) -> dict:
    """Search GitHub code, optionally scoped to a repository."""
    return github.search_code(query=query, repo=repo, limit=limit)


@mcp.tool()
def list_prs(repo: str, state: str = "open", limit: int = 30) -> dict:
    """List pull requests for a repository."""
    return github.list_prs(repo=repo, state=state, limit=limit)


@mcp.tool()
def create_pr(repo: str, title: str, body: str, base: str, head: str, draft: bool = False) -> dict:
    """Create a pull request for an existing branch."""
    return github.create_pr(repo=repo, title=title, body=body, base=base, head=head, draft=draft)


@mcp.tool()
def get_pr(repo: str, number: int) -> dict:
    """Get pull request details, files, commits, reviews, and checks."""
    return github.get_pr(repo=repo, number=number)


@mcp.tool()
def list_issues(repo: str, state: str = "open", limit: int = 30) -> dict:
    """List issues for a repository."""
    return github.list_issues(repo=repo, state=state, limit=limit)


@mcp.tool()
def create_issue(repo: str, title: str, body: str = "") -> dict:
    """Create a GitHub issue."""
    return github.create_issue(repo=repo, title=title, body=body)


@mcp.tool()
def get_workflow_runs(repo: str, limit: int = 20) -> dict:
    """List recent GitHub Actions workflow runs."""
    return github.get_workflow_runs(repo=repo, limit=limit)


@mcp.tool()
def list_workflows(repo: str) -> dict:
    """List GitHub Actions workflows for a repository."""
    return github.list_workflows(repo=repo)


@mcp.tool()
def get_workflow(repo: str, workflow_id_or_file: str) -> dict:
    """Get GitHub Actions workflow metadata by id or file name."""
    return github.get_workflow(repo=repo, workflow_id_or_file=workflow_id_or_file)


@mcp.tool()
def list_workflow_runs(
    repo: str,
    workflow_id_or_file: str | None = None,
    branch: str | None = None,
    event: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict:
    """List GitHub Actions runs, optionally scoped by workflow, branch, event, or status."""
    return github.list_workflow_runs(
        repo=repo,
        workflow_id_or_file=workflow_id_or_file,
        branch=branch,
        event=event,
        status=status,
        limit=limit,
    )


@mcp.tool()
def get_workflow_logs(repo: str, run_id: str) -> dict:
    """Fetch logs for a GitHub Actions workflow run."""
    return github.get_workflow_logs(repo=repo, run_id=run_id)


@mcp.tool()
def get_workflow_run(repo: str, run_id: str) -> dict:
    """Get one GitHub Actions workflow run with jobs and status details."""
    return github.get_workflow_run(repo=repo, run_id=run_id)


@mcp.tool()
def read_workflow_file(repo: str, workflow_path: str, ref: str = "HEAD") -> dict:
    """Read a GitHub Actions workflow file."""
    return github.read_workflow_file(repo=repo, workflow_path=workflow_path, ref=ref)


@mcp.tool()
def update_workflow_file(
    repo: str,
    workflow_path: str,
    content: str,
    message: str,
    branch: str,
    expected_sha: str | None = None,
    create: bool = False,
) -> dict:
    """Create or update a GitHub Actions workflow file on a branch."""
    return github.update_workflow_file(
        repo=repo,
        workflow_path=workflow_path,
        content=content,
        message=message,
        branch=branch,
        expected_sha=expected_sha,
        create=create,
    )


@mcp.tool()
def draft_commit_message(
    summary: str,
    details: list[str] | None = None,
    tests: list[str] | None = None,
    scope: str | None = None,
    breaking_change: str | None = None,
) -> dict:
    """Draft a structured, well-documented commit message."""
    return github.draft_commit_message(
        summary=summary,
        details=details,
        tests=tests,
        scope=scope,
        breaking_change=breaking_change,
    )


@mcp.tool()
def draft_pr_description(
    title: str,
    summary: list[str],
    tests: list[str] | None = None,
    screenshots: list[str] | None = None,
    risks: list[str] | None = None,
    follow_ups: list[str] | None = None,
) -> dict:
    """Draft a structured pull request title and body."""
    return github.draft_pr_description(
        title=title,
        summary=summary,
        tests=tests,
        screenshots=screenshots,
        risks=risks,
        follow_ups=follow_ups,
    )


@mcp.tool()
def get_deployments(repo: str, limit: int = 20) -> dict:
    """List recent GitHub deployments for a repository."""
    return github.get_deployments(repo=repo, limit=limit)


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()
