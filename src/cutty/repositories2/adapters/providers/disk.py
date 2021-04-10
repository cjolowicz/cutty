"""Repository provider for a local directory."""
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.repositories2.domain.mounters import unversioned_mounter
from cutty.repositories2.domain.providers import localprovider


diskprovider = localprovider(
    match=lambda path: path.is_dir(),
    mount=unversioned_mounter(DiskFilesystem),
)
