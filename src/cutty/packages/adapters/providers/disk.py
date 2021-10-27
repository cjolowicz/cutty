"""Package provider for a local directory."""
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.packages.domain.mounters import unversioned_mounter2
from cutty.packages.domain.providers import LocalProvider


diskprovider = LocalProvider(
    "local",
    match=lambda path: path.is_dir(),
    mount2=unversioned_mounter2(DiskFilesystem),
)
