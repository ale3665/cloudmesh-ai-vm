import click


@click.group()
def provider_group():
    """Manage VM cloud provider."""


cmd = provider_group
