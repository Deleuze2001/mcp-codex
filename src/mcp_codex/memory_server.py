from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import memory


mcp = FastMCP("Codex Markdown Memory")


@mcp.tool()
def search_memory(query: str) -> dict:
    """Search markdown project memory."""
    return memory.search_memory(query=query)


@mcp.tool()
def read_memory(relative_path: str) -> dict:
    """Read a markdown memory document."""
    return memory.read_memory(relative_path=relative_path)


@mcp.tool()
def write_memory(relative_path: str, content: str, overwrite: bool = False) -> dict:
    """Create a markdown memory document."""
    return memory.write_memory(relative_path=relative_path, content=content, overwrite=overwrite)


@mcp.tool()
def update_memory(relative_path: str, content: str) -> dict:
    """Replace an existing markdown memory document."""
    return memory.update_memory(relative_path=relative_path, content=content)


@mcp.tool()
def list_decisions() -> dict:
    """List architecture decision records and decision notes."""
    return memory.list_decisions()


@mcp.tool()
def create_adr(title: str, context: str, decision: str, consequences: str) -> dict:
    """Create a dated architecture decision record."""
    return memory.create_adr(
        title=title,
        context=context,
        decision=decision,
        consequences=consequences,
    )


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()

