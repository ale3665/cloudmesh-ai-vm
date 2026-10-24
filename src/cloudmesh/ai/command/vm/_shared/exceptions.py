import functools

import click
from rich.console import Console

console = Console()


class VMCommandError(Exception):
    """Base exception for VM command errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def handle_errors(f):
    """Decorator to catch VMCommandError and print it cleanly."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (VMCommandError, SystemExit) as e:
            if isinstance(e, VMCommandError):
                console.print(f"[bold red]Error:[/bold red] {e.message}")
                raise click.Abort()
            raise e
        except Exception as e:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e!s}")
            raise click.Abort()

    return wrapper
