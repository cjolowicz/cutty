"""Command-line interface."""
import click

import cutty.application.cookiecutter.main


@click.command()
@click.argument("url")
@click.version_option()
def main(url: str) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(url)


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
