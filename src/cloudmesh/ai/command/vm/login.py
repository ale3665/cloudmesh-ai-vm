import click

from cloudmesh.ai.command._shared.context import (
    get_active_provider,
    resolve_vm_name,
    vm_options,
)
from cloudmesh.ai.command._shared.exceptions import VMCommandError, handle_errors


@click.command()
@click.argument("name", required=False)
@vm_options
@handle_errors
@click.pass_context
def login(ctx: click.Context, name: str | None = None, **kwargs) -> None:
    """
    Log into a VM or get connection details.
    If name is omitted, the last started VM is used.
    """
    provider = get_active_provider(ctx)
    vm_name = resolve_vm_name(ctx, name)

    if not vm_name:
        raise VMCommandError("No VM specified and no last-used VM found in context.")

    if not provider.login(vm_name):
        raise VMCommandError(f"Failed to login to VM {vm_name}.")


cmd = login
