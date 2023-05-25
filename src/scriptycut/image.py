# -*- coding: utf-8 -*-

from collections.abc import Iterable
from pathlib import Path
from hashlib import sha256
from typing import Set
from functools import cached_property

from numpy import ndarray
import imageio.v3 as iio

from scriptycut.common import Pathlike
from scriptycut.clip import Clip
from scriptycut.cache import ClipCachePref
from scriptycut.clipflags import ClipFlags


class Image:
    def __init__(self, data: ndarray, pixel_format):
        self.__data = data
        self.__shape = data.shape
        self.__format = pixel_format or {}

        # Hash the raw data to ensure immutability
        self._hash = "sha256=" + sha256(data.data).digest().hex()  # Hash the data

    def export_to_file(self, file: Pathlike):
        with iio.imopen(file, "w") as file:
            file.write(self.__data)

    @property
    def data(self) -> ndarray:
        return self.__data

    @property
    def data_shape(self) -> tuple:
        return self.__shape

    @property
    def format(self):
        return self.__format

    @property
    def size(self) -> tuple:
        return self.__format.get("shape", (0, 0))

    @property
    def mode(self) -> str:
        return self.__format.get("mode", "")

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self._hash}>"


class ImageFromFile(Image):
    def __init__(self, imagefile: Pathlike):
        self.__sourcefile = Path(imagefile)

        with iio.imopen(self.__sourcefile, "r") as file:
            # print(file, dir(file))
            imagedata = file.read()
            Image.__init__(self, imagedata, file.metadata())

    @property
    def sourcefile(self) -> Path:
        return self.__sourcefile

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.__sourcefile}>"


class ImageClip(Clip):
    """
    A single Image displayed for a time span
    """
    def __init__(self, image: Image, duration: float, cachepref=ClipCachePref.NEVER):
        self._image = image
        self._duration = duration
        Clip.__init__(self, cachepref)

    @property
    def image(self) -> Image:
        return self._image

    @property
    def flags(self) -> Set[ClipFlags]:
        return {ClipFlags.HasVideo}

    @cached_property
    def duration(self) -> float:
        return self._duration

    def _repr_data(self) -> str:
        return f"{self._duration}s:{self._image!r}"


class ImageSequenceClip(Clip):
    """
    Clip containing multiple Images, all being displayed by a constant framecount
    ffmpeg -f image2 -i img%d.jpg /tmp/a.mpg
    cat *.jpg | ffmpeg -f image2pipe -c:v mjpeg -i - output.mpg
    """

    def __init__(self, images: Iterable[Image], duration_each: float, cachepref=ClipCachePref.NEVER):
        self._images = tuple(images)
        self._duration_each = duration_each
        Clip.__init__(self, cachepref)

    @property
    def flags(self) -> Set[ClipFlags]:
        return {ClipFlags.HasVideo}

    def _repr_data(self) -> str:
        return f"{self._duration_each}s@{self._images!r}"

    @cached_property
    def duration(self) -> float:
        return self._duration_each * len(self._images)
