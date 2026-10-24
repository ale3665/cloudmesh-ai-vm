import click


@click.group()
def ip_group():
    """Manage VM floating IPs."""


cmd = ip_group
