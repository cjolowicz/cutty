"""Decorator to disable runtime type-checking for a function."""
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    F = TypeVar("F")

    def typeguard_ignore(f: F) -> F:
        """This decorator is a noop during static type-checking."""
        return f


else:
    from typing import no_type_check as typeguard_ignore


__all__ = ["typeguard_ignore"]
