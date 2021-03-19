"""Filesystem abstraction.

Usage:

>>> from cutty.filesystem.dict import DictFilesystem
>>> from cutty.filesystem.path import Path
>>> filesystem = DictFilesystem({})
>>> path = Path(filesystem=filesystem)
>>> assert path.exists()
>>> assert not (path / "README").exists()
"""
