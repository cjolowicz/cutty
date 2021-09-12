"""Command-line interface for linking projects to a Cookiecutter template."""
import click

from cutty.services.link import link as service_link


@click.argument("template")
def link(template: str) -> None:
    """Link project to a Cookiecutter template."""
    service_link(template)
