"""Time utilities."""
import datetime


def asdatetime(timestamp: int, *, offset: int) -> datetime.datetime:
    """Build a `datetime` instance from a POSIX timestamp."""
    return datetime.datetime.fromtimestamp(
        timestamp,
        tz=datetime.timezone(offset=datetime.timedelta(minutes=offset)),
    )
