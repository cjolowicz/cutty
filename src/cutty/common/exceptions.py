"""Exceptions."""


class CuttyException(Exception):
    """Base class for cutty exceptions."""


class ConfigurationDoesNotExist(CuttyException):
    """The configuration file does not exist."""


class InvalidConfiguration(CuttyException):
    """The configuration file is not valid."""
