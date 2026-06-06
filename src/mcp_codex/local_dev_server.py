from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import local_dev


mcp = FastMCP("Codex Local Dev")


@mcp.tool()
def run_tests(extra_args: list[str] | None = None) -> dict:
    """Run the allowlisted test command."""
    return local_dev.run_tests(extra_args=extra_args)


@mcp.tool()
def run_linter() -> dict:
    """Run the allowlisted linter command."""
    return local_dev.run_linter()


@mcp.tool()
def run_typecheck() -> dict:
    """Run the allowlisted typecheck command."""
    return local_dev.run_typecheck()


@mcp.tool()
def start_app(extra_args: list[str] | None = None) -> dict:
    """Start the allowlisted local app command."""
    return local_dev.start_app(extra_args=extra_args)


@mcp.tool()
def read_local_logs(path: str = ".mcp-codex/logs/tools.jsonl", lines: int = 100) -> dict:
    """Read local development or MCP tool logs."""
    return local_dev.read_local_logs(path=path, lines=lines)


@mcp.tool()
def check_env() -> dict:
    """Check local command availability and active configuration paths."""
    return local_dev.check_env()


@mcp.tool()
def run_command_allowlist(command_name: str, extra_args: list[str] | None = None) -> dict:
    """Run an explicitly allowlisted local development command."""
    return local_dev.run_command_allowlist(command_name=command_name, extra_args=extra_args)


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()

