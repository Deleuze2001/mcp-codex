from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

from mcp_codex.runtime import env_path


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_hidden = False
        self.parts: list[str] = []
        self.headings: list[str] = []
        self._current_heading: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_hidden = True
        if tag in {"h1", "h2", "h3"}:
            self._current_heading = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_hidden = False
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")
        if tag in {"h1", "h2", "h3"} and self._current_heading is not None:
            heading = " ".join("".join(self._current_heading).split())
            if heading:
                self.headings.append(heading)
            self._current_heading = None

    def handle_data(self, data: str) -> None:
        if self.in_hidden:
            return
        text = html.unescape(data)
        if self._current_heading is not None:
            self._current_heading.append(text)
        self.parts.append(text)

    def text(self) -> str:
        collapsed = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.parts))
        return re.sub(r"\n{3,}", "\n\n", collapsed).strip()


def docs_sources_path() -> Path:
    return env_path("MCP_CODEX_DOC_SOURCES", "config/docs_sources.json")


def load_sources() -> list[dict[str, Any]]:
    with docs_sources_path().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_by_name(source_name: str) -> dict[str, Any]:
    for source in load_sources():
        if source["name"] == source_name:
            return source
    raise ValueError(f"Unknown docs source: {source_name}")


def _fetch(url: str, timeout_seconds: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "mcp-codex-docs/0.1"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def _within_source(url: str, base_url: str) -> bool:
    parsed = urlparse(url)
    base = urlparse(base_url)
    return parsed.scheme in {"http", "https"} and parsed.netloc == base.netloc


def _sitemap_urls(sitemap_url: str, base_url: str, limit: int = 5000) -> list[str]:
    raw = _fetch(sitemap_url)
    root = ET.fromstring(raw)
    urls: list[str] = []

    for loc in root.findall(".//{*}url/{*}loc"):
        if loc.text and _within_source(loc.text, base_url):
            urls.append(loc.text)
            if len(urls) >= limit:
                return urls

    for loc in root.findall(".//{*}sitemap/{*}loc")[:10]:
        if not loc.text or not _within_source(loc.text, base_url):
            continue
        try:
            urls.extend(_sitemap_urls(loc.text, base_url, limit=limit - len(urls)))
        except Exception:
            continue
        if len(urls) >= limit:
            return urls[:limit]

    return urls


def list_doc_sources() -> dict[str, Any]:
    return {"sources": load_sources()}


def fetch_doc_page(source_name: str, path_or_url: str, max_chars: int = 12000) -> dict[str, Any]:
    source = _source_by_name(source_name)
    url = path_or_url if path_or_url.startswith("http") else urljoin(source["base_url"], path_or_url)
    if not _within_source(url, source["base_url"]):
        return {"ok": False, "error": "URL is outside the configured documentation source."}
    raw = _fetch(url)
    parser = TextExtractor()
    parser.feed(raw)
    text = parser.text()
    return {
        "ok": True,
        "source": source_name,
        "url": url,
        "headings": parser.headings[:30],
        "text": text[:max_chars],
        "truncated": len(text) > max_chars,
    }


def summarise_doc(source_name: str, path_or_url: str, max_chars: int = 4000) -> dict[str, Any]:
    page = fetch_doc_page(source_name, path_or_url, max_chars=20000)
    if not page.get("ok"):
        return page
    text = page["text"]
    paragraphs = [part.strip() for part in text.split("\n") if len(part.strip()) > 40]
    return {
        "ok": True,
        "source": source_name,
        "url": page["url"],
        "headings": page["headings"][:12],
        "summary_text": "\n\n".join(paragraphs[:8])[:max_chars],
    }


def search_docs(query: str, source_name: str | None = None, limit: int = 10) -> dict[str, Any]:
    sources = [_source_by_name(source_name)] if source_name else load_sources()
    results: list[dict[str, str]] = []
    query_terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9_/-]+", query)]

    for source in sources:
        source_result_count = len(results)
        if source.get("search_index_url"):
            try:
                index = json.loads(_fetch(source["search_index_url"]))
                docs = index.get("docs", [])
                for doc in docs:
                    haystack = " ".join(
                        str(doc.get(key, "")) for key in ("title", "text", "location")
                    ).lower()
                    if all(term in haystack for term in query_terms):
                        results.append(
                            {
                                "source": source["name"],
                                "title": str(doc.get("title", "")),
                                "url": urljoin(source["base_url"], str(doc.get("location", ""))),
                            }
                        )
                        if len(results) >= limit:
                            return {"results": results}
            except Exception as exc:  # noqa: BLE001 - return useful tool output instead of crashing.
                results.append(
                    {
                        "source": source["name"],
                        "title": f"Search index unavailable: {exc}",
                        "url": source["search_url"].format(query=quote_plus(query)),
                    }
                )
        if source.get("sitemap_url"):
            try:
                for url in _sitemap_urls(source["sitemap_url"], source["base_url"]):
                    normalized = url.lower().replace("-", " ").replace("_", " ").replace("/", " ")
                    if all(term.replace("-", " ") in normalized for term in query_terms):
                        results.append(
                            {
                                "source": source["name"],
                                "title": url.rstrip("/").split("/")[-1].replace("-", " ").title(),
                                "url": url,
                            }
                        )
                        if len(results) >= limit:
                            return {"results": results}
            except Exception as exc:  # noqa: BLE001 - return useful tool output instead of crashing.
                results.append(
                    {
                        "source": source["name"],
                        "title": f"Sitemap unavailable: {exc}",
                        "url": source["search_url"].format(query=quote_plus(query)),
                    }
                )
        if source.get("search_url") and len(results) == source_result_count:
            results.append(
                {
                    "source": source["name"],
                    "title": f"Search {source['label']} for `{query}`",
                    "url": source["search_url"].format(query=quote_plus(query)),
                }
            )

    return {"results": results[:limit]}
