from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from mcp_codex.runtime import env_path


SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def memory_root() -> Path:
    return env_path("MCP_CODEX_MEMORY_ROOT", "memory").resolve()


def _safe_path(relative_path: str) -> Path:
    root = memory_root()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Path escapes the configured memory root.")
    if path.suffix != ".md":
        raise ValueError("Memory documents must be markdown files.")
    return path


def _slugify(value: str) -> str:
    slug = SLUG_PATTERN.sub("-", value.lower()).strip("-")
    return slug or "untitled"


def search_memory(query: str) -> dict[str, Any]:
    root = memory_root()
    matches = []
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line": line_number,
                        "text": line.strip(),
                    }
                )
    return {"matches": matches}


def read_memory(relative_path: str) -> dict[str, Any]:
    path = _safe_path(relative_path)
    if not path.exists():
        return {"ok": False, "error": f"Memory document does not exist: {relative_path}"}
    return {"ok": True, "path": relative_path, "content": path.read_text(encoding="utf-8")}


def write_memory(relative_path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    path = _safe_path(relative_path)
    if path.exists() and not overwrite:
        return {"ok": False, "error": "Memory document already exists. Use update_memory."}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path.relative_to(memory_root()))}


def update_memory(relative_path: str, content: str) -> dict[str, Any]:
    path = _safe_path(relative_path)
    if not path.exists():
        return {"ok": False, "error": "Memory document does not exist. Use write_memory."}
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path.relative_to(memory_root()))}


def list_decisions() -> dict[str, Any]:
    root = memory_root()
    decisions_dir = root / "decisions"
    decisions = []
    if decisions_dir.exists():
        for path in sorted(decisions_dir.rglob("*.md")):
            decisions.append(str(path.relative_to(root)))
    return {"decisions": decisions}


def create_adr(title: str, context: str, decision: str, consequences: str) -> dict[str, Any]:
    date = time.strftime("%Y-%m-%d", time.localtime())
    slug = _slugify(title)
    relative_path = f"decisions/{date}-{slug}.md"
    content = f"""# {title}

Date: {date}

## Context

{context.strip()}

## Decision

{decision.strip()}

## Consequences

{consequences.strip()}
"""
    return write_memory(relative_path, content, overwrite=False)

