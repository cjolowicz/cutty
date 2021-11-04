"""Package providers for ZIP archives."""
from pathlib import Path

from cutty.filesystems.adapters.zip import ZipFilesystem
from cutty.packages.adapters.fetchers.file import filefetcher
from cutty.packages.adapters.fetchers.ftp import ftpfetcher
from cutty.packages.adapters.fetchers.http import httpfetcher
from cutty.packages.domain.loader import MountedPackageRepositoryLoader
from cutty.packages.domain.mounters import unversioned_mounter
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory


def match(path: Path) -> bool:
    """Return True if the path is a ZIP archive."""
    return path.suffix.lower() == ".zip" and path.is_file()


mount = unversioned_mounter(ZipFilesystem)
localzipprovider = LocalProvider(
    "localzip", match=match, loader=MountedPackageRepositoryLoader(mount)
)
zipproviderfactory = RemoteProviderFactory(
    "zip",
    match=lambda url: url.path.lower().endswith(".zip"),
    fetch=[httpfetcher, ftpfetcher, filefetcher],
    loader=MountedPackageRepositoryLoader(mount),
)
