"""Determine the author and committer information for a Git commit."""
from __future__ import annotations

import contextlib
import datetime
import email.utils
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitSignature:
    """Author or committer information."""

    name: Optional[str]
    email: Optional[str]
    date: Optional[datetime.datetime]

    @staticmethod
    def readenv(env: Mapping[str, str], role: str, item: str) -> Optional[str]:
        """Read an environment variable."""
        variable = "_".join(["git", role, item]).upper()
        name = env.get(variable)
        if name is not None:
            name = name.strip()
            if item == "email":
                name = name.strip("<>").strip()
            if name:
                return name
        return None

    @staticmethod
    def parsedate(text: str) -> Optional[datetime.datetime]:
        """Parse date format like git-commit(1)."""
        with contextlib.suppress(ValueError):
            return datetime.datetime.fromisoformat(text)

        with contextlib.suppress(ValueError, TypeError):
            return email.utils.parsedate_to_datetime(text)

        with contextlib.suppress(ValueError, OverflowError, OSError):
            time, offset = text.split()
            timestamp = int(time)
            timezone = datetime.datetime.strptime(offset, "%z").tzinfo
            return datetime.datetime.fromtimestamp(timestamp, tz=timezone)

        return None

    @classmethod
    def fromenv(cls, env: Mapping[str, str], role: str) -> GitSignature:
        """Read the signature from the environment."""
        name = cls.readenv(env, role, "name")
        email = cls.readenv(env, role, "email", strip="<>")
        daterep = cls.readenv(env, role, "date")
        date = cls.parsedate(daterep) if daterep is not None else None
        return cls(name, email, date)
