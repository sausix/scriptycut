# -*- coding: utf-8 -*-

import shutil
from typing import Set, Union
from pathlib import Path
from hashlib import sha256
from logging import getLogger
from datetime import datetime
from json import dumps

from scriptycut.common import Pathlike

logger = getLogger(__name__)
_CLASS_DEFAULT = object()


class Cache:
    """
    Cache for Clip data on disk. May be temporary or persistent.
    For a single project or common cache for multiple video projects.
    """

    CACHE_ROOT_PATH = Path("cache")
    AUTO_DISCARD_ORPHANS = True

    def __init__(self, cache_root_path: Pathlike = CACHE_ROOT_PATH, auto_discard_orphans=_CLASS_DEFAULT):
        """
        :param cache_root_path: Folder on file system. May consume a lot of space.
        :param auto_discard_orphans: Automatically removes old cache entries from disk which have not
                                     been accessed. Do not use on multi project cache.
        """
        logger.info(f"Creating cache instance for: {cache_root_path}")
        self._root_path = Path(cache_root_path).absolute()
        self._root_path.mkdir(0o750, parents=True, exist_ok=True)

        self._auto_discard_orphans = self.AUTO_DISCARD_ORPHANS if auto_discard_orphans is _CLASS_DEFAULT else auto_discard_orphans
        self._touched_caches: Set[Path] = set()  # Remember items here
        logger.info(f"Created cache instance in: {self._root_path}")

    def get_item_folder(self, classname: str, version: Union[int, str, None], item_repr_id: str) -> Path:
        """
        Creates or retrieves a cache folder based a classname, version and the unique instance definition.
        Classname, version and the id are being hashed.

        :param classname: Should be the classname of a Clip subclass
        :param version: Cache could be depending on specific class versions
        :param item_repr_id: Should be the repr_id of a Clip instance base on the Clip config.
        :return: Path object ready to write or read files from.
        """
        hash_base_bytes = f"{classname}_{version}_{item_repr_id}".encode()  # Hash including classname
        item_folder = self._root_path / f"{classname}_{sha256(hash_base_bytes).digest().hex()}"

        # Basic info files in cache
        last_access_file = item_folder / "_cache_last_access.txt"

        if not item_folder.exists():
            # Create cache subdirectory
            item_folder.mkdir(0o750)

            info_file = item_folder / "_cache_info.json"
            info = {
                "class": classname,
                "version": version,
                "repr_id": item_repr_id,
                "created_iso": datetime.now().isoformat(),
                "created_ts": datetime.now().timestamp()
            }
            info_file.write_text(dumps(info))

        last_access_file.write_text(datetime.now().isoformat())

        self.touch_item_cache(item_folder)
        return item_folder

    @property
    def root_path(self) -> Path:
        return self._root_path

    def touch_item_cache(self, item_folder: Pathlike):
        """
        Mark a folder as in use to prevent deletion by discard_missing of Cache
        :param item_folder: Path to "touch"
        """
        self._touched_caches.add(Path(item_folder))

    def discard_orphans(self):
        """
        Remove all cached files which have not been touched in this instance.
        """

        all_items = set(self._root_path.iterdir())
        missing = all_items - self._touched_caches

        if not missing:
            return

        logger.info("Discarding orphaned items from cache")
        for p in missing:
            try:
                if p.is_file():
                    logger.debug(f"Removing file: {p}")
                    p.unlink()
                elif p.is_dir():
                    logger.debug(f"Removing folder: {p}")
                    shutil.rmtree(p)
                else:
                    logger.warning(f"Ignoring. Not a folder, neither a file: {p}")
            except Exception as e:
                logger.error(f"Could not delete element: {p}", exc_info=e)

    def __del__(self):
        if self._auto_discard_orphans:
            try:
                self.discard_orphans()
            except Exception as e:
                logger.exception("Error on discarding missing cache folders.", exc_info=e)
