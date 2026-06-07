# Codex MCP Workspace

Local-first MCP servers for using Codex across a solo developer workflow:

- GitHub repo, PR, issue, workflow, and deployment inspection through the `gh` CLI
- GitHub Actions workflow inspection and guarded workflow file updates
- Current documentation lookup against configured authoritative sources
- Local development commands through an explicit allowlist
- Alembic migration inspection and guarded migration commands
- Markdown project memory stored in this repository
- Browser testing via the official Playwright MCP server

The initial scope intentionally excludes AWS, Terraform, and Ansible mutation tools. Add those once the basic workflow is reliable.

## Servers

Install the package in a virtual environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev,browser]"
```

Run a server over stdio:

```sh
mcp-codex-alembic
mcp-codex-github
mcp-codex-docs
mcp-codex-local-dev
mcp-codex-memory
```

Each command also accepts `--transport streamable-http` for local inspector testing.

## Fedora Silverblue

On Silverblue, keep development dependencies inside a toolbox:

```sh
toolbox create mcp-codex
toolbox enter mcp-codex
cd /var/home/fg/git/mcp-codex
scripts/setup-silverblue-toolbox
scripts/smoke-test
```

If your MCP client runs on the host, use `config/mcp.silverblue.example.json`. It starts each server through:

```sh
/run/host/usr/bin/toolbox run --container mcp-codex /var/home/fg/git/mcp-codex/scripts/mcp-server docs
```

The wrapper script changes into the repository, uses `.venv`, and sets absolute config paths so the servers behave the same whether started from the toolbox shell or the host MCP client.

## Browser MCP

Browser automation is delegated to Playwright's maintained MCP server. See `config/mcp.example.json` for a client configuration entry.

## Configuration

Environment variables:

- `MCP_CODEX_LOG_DIR`: directory for JSONL tool logs, defaults to `.mcp-codex/logs`
- `MCP_CODEX_LOCAL_DEV_CONFIG`: local dev allowlist path, defaults to `config/local_dev.allowlist.json`
- `MCP_CODEX_DOC_SOURCES`: docs source config, defaults to `config/docs_sources.json`
- `MCP_CODEX_MEMORY_ROOT`: markdown memory root, defaults to `memory`
- `MCP_CODEX_WORKSPACE_ROOT`: target project root for local dev and Alembic tools, defaults to the server working directory
- `MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE`: set to `1` to allow Alembic database-changing commands when the tool call also passes `allow_database_write=True`

GitHub tools use your existing `gh` authentication. No GitHub tokens, AWS credentials, SSH keys, or other secrets should be committed.

## GitHub Support

The GitHub MCP server can inspect repositories, branches, pull requests, issues, deployments, Actions workflows, workflow runs, run logs, and workflow files. It also includes helpers for drafting well-structured commit messages and pull request descriptions.

Workflow editing is intentionally scoped. The `update_workflow_file` tool only writes files under `.github/workflows/*.yml` or `.github/workflows/*.yaml`, requires a target branch, and requires a non-empty commit message. Prefer editing a feature branch and opening a PR rather than writing directly to the default branch.

## Tool Safety

Local command execution is allowlisted. Tools never use a shell for command execution, and extra arguments are appended only for allowlist entries that explicitly enable them.

Markdown memory tools are constrained to the configured memory root.

Alembic tools default to read-only inspection or SQL preview. Commands that modify a database require both `MCP_CODEX_ALEMBIC_ALLOW_DB_WRITE=1` and an explicit `allow_database_write=True` tool argument.

## Tests

```sh
python -m pytest
```
