from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_codex.runtime import parse_transport
from mcp_codex.services import alembic


mcp = FastMCP("Codex Alembic")


@mcp.tool()
def check_env(workspace_root: str | None = None, config_file: str = "alembic.ini") -> dict:
    """Inspect Alembic configuration and command availability."""
    return alembic.check_env(workspace_root=workspace_root, config_file=config_file)


@mcp.tool()
def current(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Show the current database revision."""
    return alembic.current(workspace_root=workspace_root, config_file=config_file, x_args=x_args)


@mcp.tool()
def heads(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Show current migration heads."""
    return alembic.heads(workspace_root=workspace_root, config_file=config_file, x_args=x_args)


@mcp.tool()
def history(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Show migration history."""
    return alembic.history(workspace_root=workspace_root, config_file=config_file, x_args=x_args)


@mcp.tool()
def show_revision(
    revision: str,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Show details for one migration revision."""
    return alembic.show_revision(
        revision=revision,
        workspace_root=workspace_root,
        config_file=config_file,
        x_args=x_args,
    )


@mcp.tool()
def check_pending(
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Run Alembic's pending migration check."""
    return alembic.check_pending(workspace_root=workspace_root, config_file=config_file, x_args=x_args)


@mcp.tool()
def create_revision(
    message: str,
    autogenerate: bool = False,
    head: str | None = None,
    branch_label: str | None = None,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Create a new Alembic migration revision."""
    return alembic.create_revision(
        message=message,
        autogenerate=autogenerate,
        head=head,
        branch_label=branch_label,
        workspace_root=workspace_root,
        config_file=config_file,
        x_args=x_args,
    )


@mcp.tool()
def upgrade(
    target: str = "head",
    sql: bool = True,
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Preview or run an Alembic upgrade. Defaults to SQL preview."""
    return alembic.upgrade(
        target=target,
        sql=sql,
        allow_database_write=allow_database_write,
        workspace_root=workspace_root,
        config_file=config_file,
        x_args=x_args,
    )


@mcp.tool()
def downgrade(
    target: str = "-1",
    sql: bool = True,
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Preview or run an Alembic downgrade. Defaults to SQL preview."""
    return alembic.downgrade(
        target=target,
        sql=sql,
        allow_database_write=allow_database_write,
        workspace_root=workspace_root,
        config_file=config_file,
        x_args=x_args,
    )


@mcp.tool()
def stamp(
    target: str = "head",
    allow_database_write: bool = False,
    workspace_root: str | None = None,
    config_file: str = "alembic.ini",
    x_args: list[str] | None = None,
) -> dict:
    """Stamp the database revision. Requires explicit database-write opt-in."""
    return alembic.stamp(
        target=target,
        allow_database_write=allow_database_write,
        workspace_root=workspace_root,
        config_file=config_file,
        x_args=x_args,
    )


def main() -> None:
    mcp.run(transport=parse_transport())


if __name__ == "__main__":
    main()

