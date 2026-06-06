from __future__ import annotations

import json

from mcp_codex.services import docs


def test_list_doc_sources_uses_config(tmp_path, monkeypatch):
    config = tmp_path / "sources.json"
    config.write_text(
        json.dumps(
            [
                {
                    "name": "example",
                    "label": "Example",
                    "base_url": "https://example.com/docs/",
                    "search_url": "https://example.com/search?q={query}",
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CODEX_DOC_SOURCES", str(config))

    result = docs.list_doc_sources()

    assert result["sources"][0]["name"] == "example"


def test_text_extractor_collects_headings_and_text():
    parser = docs.TextExtractor()
    parser.feed(
        """
        <html><body>
          <h1>Title</h1>
          <script>secret()</script>
          <p>First paragraph.</p>
        </body></html>
        """
    )

    assert parser.headings == ["Title"]
    assert "First paragraph." in parser.text()
    assert "secret" not in parser.text()


def test_search_docs_uses_sitemap(tmp_path, monkeypatch):
    config = tmp_path / "sources.json"
    config.write_text(
        json.dumps(
            [
                {
                    "name": "example",
                    "label": "Example",
                    "base_url": "https://example.com/docs/",
                    "sitemap_url": "https://example.com/sitemap.xml",
                    "search_url": "https://example.com/search?q={query}",
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CODEX_DOC_SOURCES", str(config))
    monkeypatch.setattr(
        docs,
        "_fetch",
        lambda _: """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/how-to/use-lifespan/</loc></url>
        </urlset>
        """,
    )

    result = docs.search_docs("lifespan", source_name="example")

    assert result["results"][0]["url"] == "https://example.com/docs/how-to/use-lifespan/"
