"""Logging."""
import logging

from rich.logging import RichHandler


def configure() -> None:
    """Configure logging for console output."""
    logging.basicConfig(
        level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
    )
