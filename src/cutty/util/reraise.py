"""Utility for handling an exception by raising another one."""
from typing import NoReturn
from typing import Union

from cutty.util.exceptionhandlers import ExceptionHandler
from cutty.util.exceptionhandlers import exceptionhandler


def reraise(
    exception: BaseException,
    *,
    when: Union[type[BaseException], tuple[type[BaseException], ...]] = ()
) -> ExceptionHandler:
    """Raise the given exception when any of the specified exceptions is caught."""
    if not isinstance(when, tuple):
        when = (when,)
    elif not when:
        when = (Exception,)

    @exceptionhandler(*when)
    def _(other: BaseException) -> NoReturn:
        raise exception

    return _
