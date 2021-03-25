"""Command-line interface."""
import click

import cutty.application.cookiecutter.main


@click.command()
@click.argument("url")
@click.option(
    "--interactive / --no-interactive",
    default=True,
    show_default=True,
    help="Prompt for template variables.",
)
@click.version_option()
def main(url: str, interactive: bool) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(url, interactive=interactive)


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
