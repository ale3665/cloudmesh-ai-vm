import click


@click.group()
def config_group():
    """Manage VM CLI configuration."""


cmd = config_group
