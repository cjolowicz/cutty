"""Filesystem abstraction.

Usage:

>>> from cutty.filesystems.adapters.dict import DictFilesystem
>>> from cutty.filesystems.domain.path import Path
>>> filesystem = DictFilesystem({})
>>> path = Path(filesystem=filesystem)
>>> assert path.exists()
>>> assert not (path / "README").exists()
"""
