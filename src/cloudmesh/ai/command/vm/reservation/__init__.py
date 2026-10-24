import click

from .duration import duration


@click.group()
def reservation():
    """Manage VM reservations (leases) on the cloud provider."""


reservation.add_command(duration)

cmd = reservation
