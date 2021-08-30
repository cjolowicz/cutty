"""Repository providers for ZIP archives."""
from pathlib import Path

from cutty.filesystems.adapters.zip import ZipFilesystem
from cutty.repositories.adapters.fetchers.file import filefetcher
from cutty.repositories.adapters.fetchers.ftp import ftpfetcher
from cutty.repositories.adapters.fetchers.http import httpfetcher
from cutty.repositories.domain.mounters import unversioned_mounter
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import RemoteProviderFactory


def match(path: Path) -> bool:
    """Return True if the path is a ZIP archive."""
    return path.suffix.lower() == ".zip" and path.is_file()


mount = unversioned_mounter(ZipFilesystem)
localzipprovider = LocalProvider("localzip", match=match, mount=mount)
zipproviderfactory = RemoteProviderFactory(
    "zip",
    match=lambda url: url.path.lower().endswith(".zip"),
    fetch=[httpfetcher, ftpfetcher, filefetcher],
    mount=mount,
)
