"""Abbreviations."""
from typing import Mapping

from . import exceptions


class Abbreviations:
    """Abbreviations for template locations."""

    def __init__(self) -> None:
        """Initialize."""
        self.abbreviations = {
            "gh": "https://github.com/{}.git",
            "gl": "https://gitlab.com/{}.git",
            "bb": "https://bitbucket.org/{}",
        }

    def update(self, abbreviations: Mapping[str, str]) -> None:
        """Update the registered abbreviations."""
        self.abbreviations.update(abbreviations)

    def expand(self, template: str) -> str:
        """Expand abbreviations in a template location."""
        if template in self.abbreviations:
            return self.abbreviations[template]

        prefix, _, rest = template.partition(":")
        abbreviation = self.abbreviations.get(prefix)
        if abbreviation is not None:
            with exceptions.InvalidAbbreviation(prefix, template, abbreviation):
                return abbreviation.format(rest)

        return template
