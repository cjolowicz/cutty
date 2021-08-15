"""Repository provider for a local directory."""
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.repositories.domain.mounters import unversioned_mounter
from cutty.repositories.domain.providers import localprovider2


diskprovider = localprovider2(
    match=lambda path: path.is_dir(),
    mount=unversioned_mounter(DiskFilesystem),
)
