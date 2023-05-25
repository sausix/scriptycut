# -*- coding: utf-8 -*-

import shutil
from typing import Set
from pathlib import Path
from hashlib import sha256
from enum import Enum, auto

from scriptycut.common import Pathlike



class ClipCachePref(Enum):
    CLASS_DEFAULT = auto()
    NEVER = auto()
    ALWAYS = auto()
    DEPENDS_ASK_INSTANCE = auto()


class Cache:
    """
    Cache for Clip data on disk. May be temporary or persistent.
    For a single project or common cache for multiple video projects.
    """
    def __init__(self, cache_root_path: Pathlike = "cache", discard_missing=True):
        """
        :param cache_root_path: Folder on file system. May consume a lot of space.
        :param discard_missing: Automatically removes old cache entries from disk which have not
                                been accessed. Do not use on multi project cache.
        """
        self._root_path = Path(cache_root_path).absolute()
        self._root_path.mkdir(0o750, parents=True, exist_ok=True)
        self._discard_missing = discard_missing
        self._touched_caches: Set[Path] = set()

    def get_item_folder(self, classname: str, item_repr_id: str) -> Path:
        """
        Creates or retrieves a cache folder based a classname and a unique id.
        Classname and the id are being hashed.

        :param classname: Should be the classname of a Clip subclass
        :param item_repr_id: Should be the repr_id of a Clip instance base on the Clip config.
        :return: Path object ready to write or read files from.
        :rtype:
        """
        hash_base_bytes = f"{classname}_{item_repr_id}".encode()  # Hash including classname
        folder_name = f"{classname}_{sha256(hash_base_bytes).digest().hex()}"

        item_folder = self._root_path / folder_name
        if not item_folder.exists():
            # Create cache subdirectory
            item_folder.mkdir(0o750)
            info = item_folder / "repr_id.txt"
            info.write_text(item_repr_id)

        self.touch_cache(item_folder)
        return item_folder

    # def root_path(self) -> Path:
    #     return self._root_path
    #
    def touch_cache(self, item_folder: Pathlike):
        """
        Mark a folder as in use to prevent deletion by discard_missing of Cache
        :param item_folder: Path to "touch"
        """
        if not isinstance(item_folder, Path):
            item_folder = Path(item_folder)
        self._touched_caches.add(item_folder)

    def discard_missing(self):
        # Cleanup cache folder
        all_items = set(self._root_path.iterdir())
        missing = all_items - self._touched_caches

        if not missing:
            return

        print("Removing orphaned items from cache:")
        for p in missing:
            print(p)
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)

    def __del__(self):
        if self._discard_missing:
            try:
                self.discard_missing()
            except Exception as e:
                error(e)
