"""Filesystem abstraction.

Usage:

>>> from cutty.filesystems.adapters.dict import DictFilesystem
>>> from cutty.filesystems.domain.path import Path
>>> filesystem = DictFilesystem({"README": "hello"})
>>> path = Path(filesystem=filesystem)
>>> assert path.is_dir()
>>> assert (path / "README").read_text() == "hello"
"""
