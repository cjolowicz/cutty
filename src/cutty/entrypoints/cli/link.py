"""Command-line interface for linking projects to a Cookiecutter template."""
import click


@click.argument("template")
def link(template: str) -> None:
    """Link project to a Cookiecutter template."""
