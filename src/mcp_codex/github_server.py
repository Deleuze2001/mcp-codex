from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import github


mcp = FastMCP("Codex GitHub")


@mcp.tool()
def list_repos(owner: str | None = None, limit: int = 50) -> dict:
    """List repositories visible to the authenticated GitHub CLI user."""
    return github.list_repos(owner=owner, limit=limit)


@mcp.tool()
def read_file(repo: str, path: str, ref: str = "HEAD") -> dict:
    """Read a file from a GitHub repository at a branch, tag, or SHA."""
    return github.read_file(repo=repo, path=path, ref=ref)


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
def get_workflow_logs(repo: str, run_id: str) -> dict:
    """Fetch logs for a GitHub Actions workflow run."""
    return github.get_workflow_logs(repo=repo, run_id=run_id)


@mcp.tool()
def get_deployments(repo: str, limit: int = 20) -> dict:
    """List recent GitHub deployments for a repository."""
    return github.get_deployments(repo=repo, limit=limit)


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()

