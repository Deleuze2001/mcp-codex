from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import docs


mcp = FastMCP("Codex Docs")


@mcp.tool()
def search_docs(query: str, source_name: str | None = None, limit: int = 10) -> dict:
    """Search configured authoritative documentation sources."""
    return docs.search_docs(query=query, source_name=source_name, limit=limit)


@mcp.tool()
def fetch_doc_page(source_name: str, path_or_url: str, max_chars: int = 12000) -> dict:
    """Fetch and extract readable text from a documentation page."""
    return docs.fetch_doc_page(source_name=source_name, path_or_url=path_or_url, max_chars=max_chars)


@mcp.tool()
def summarise_doc(source_name: str, path_or_url: str, max_chars: int = 4000) -> dict:
    """Return headings and leading paragraphs from a documentation page."""
    return docs.summarise_doc(source_name=source_name, path_or_url=path_or_url, max_chars=max_chars)


@mcp.tool()
def list_doc_sources() -> dict:
    """List configured documentation sources."""
    return docs.list_doc_sources()


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()

