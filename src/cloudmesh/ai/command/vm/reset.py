import click

from cloudmesh.ai.command._shared.context import (
    console,
    get_active_provider,
    resolve_vm_name,
    state,
    vm_options,
)
from cloudmesh.ai.command._shared.exceptions import VMCommandError, handle_errors


@click.command()
@click.pass_context
@click.argument("name", required=False)
@vm_options
@handle_errors
def reset(ctx: click.Context, name: str | None = None, **kwargs) -> None:
    """
    Resets a VM or the provider service.

    Example:
        cmx vm reset multipass
    """
    vm_name = resolve_vm_name(ctx, name)
    provider = get_active_provider(ctx)
    if provider.reset(vm_name):
        state.set_last_vm(provider.cloud_name, vm_name)
        console.print(f"Successfully reset [bold green]{vm_name}[/bold green].")
    else:
        raise VMCommandError(f"Failed to reset {vm_name}.")


cmd = reset
