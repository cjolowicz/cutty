"""Filesystem abstraction.

Usage:

>>> from cutty.filesystem.adapters.dict import DictFilesystem
>>> from cutty.filesystem.domain.path import Path
>>> filesystem = DictFilesystem({})
>>> path = Path(filesystem=filesystem)
>>> assert path.exists()
>>> assert not (path / "README").exists()
"""
