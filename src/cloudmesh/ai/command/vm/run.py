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
@click.argument("command", required=False)
@vm_options
@handle_errors
def run(
    ctx: click.Context,
    name: str | None = None,
    command: str | None = None,
    **kwargs,
) -> None:
    """
    Executes a command on a VM.

    Example:
        cmx vm run my-vm "ls -la /home"
        cmx vm run "ls -la /home"
    """
    if command is None:
        actual_command = name
        vm_name = resolve_vm_name(ctx, None)
    else:
        actual_command = command
        vm_name = resolve_vm_name(ctx, name)

    if not actual_command:
        raise VMCommandError("No command provided to run.")

    provider = get_active_provider(ctx)
    result = provider.run_command(vm_name, actual_command)
    if result:
        state.set_last_vm(provider.cloud_name, vm_name)
        console.print(result)
    else:
        raise VMCommandError(f"Failed to execute command on VM {vm_name}.")


cmd = run
