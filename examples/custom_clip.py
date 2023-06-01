# -*- coding: utf-8 -*-

"""
How to write a custom Clip subclass with step by step explanations.
"""

# This example module uses (the optional) typing and annotations features of Python as YOU also
# should do because:
#
# - Define what data types your functions expect and return.
# - See type mismatches and design flaws earlier.
# - Help the IDE that it helps you and others back.
# - Reduces lookups into the documentation for choosing proper data types or understand arguments.
# - Helps to create the documentation.

# TODO: Usable example?

from typing import Set
from collections.abc import Generator
from functools import cached_property

from scriptycut.clip import Clip
from scriptycut.cache import ClipCachePref
from scriptycut.clipflags import ClipFlags


class MyCustomClip(Clip):
    def __init__(self, other_clip: Clip, my_options, cachepref=ClipCachePref.DEPENDS_ASK_INSTANCE):
        """
        Each Clip subclass provides individual creation or
        transforming video clips or single media streams.

        Every Clip (and subclass) instance is immutable!
        So you can only pass options once and only by your init call.
        Remember: Clip config is written in stone! Always.
        """

        # Collect and save the clip config.
        # Use single underscores to keep these attributes private.
        # Remember? Immutable clips.
        # Of course Python has no real private attributes.
        # DON'T change options of a clip later like "clip._x = 123".
        # It will probably break the clip or the result because of cache mismatches.
        # Your Python IDE or linter should help you and throw a warning.
        self._other_clip = other_clip
        self._my_options = my_options


        # cachepref is optional as input argument.
        # Expose it if the user should choose the cache preference for each instance individually.
        # The upper Clip class magic handles the cachepref. Just pass a preference what suits
        # best for your class (or let the user choose).
        Clip.__init__(self, cachepref)

        # After Clip.__init__() you can access the cache folder and:
        # - Do some further checks
        # - Save some meta or log into it
        # - Everything except heavy operations like encoding.
        print(self.cachedir)

    @property
    def flags(self) -> Set[ClipFlags]:
        # Flags describe some states or contain information about the clip instance.
        # They should be immutable also.
        # You can parse the options or read media files to decide for corresponding flags.
        # If this operation is heavy, you should already choose a cached_property decorator instead.
        #
        # Return a set out of scriptycut.clipflags.ClipFlags enum members.
        return {ClipFlags.HasVideo, ClipFlags.HasAudio}

    @property
    def my_options(self):
        # Remember? Changing the clip config is not allowed.
        # But we are no monsters and allow reading them through properties.
        return self._my_options

    @cached_property
    def duration(self) -> float:
        # Imagine this attribute can be heavy in calculation. Maybe because of reading large files.
        # @cached_property is the way to go.
        return 42.

    # We are not a sequence and represent a range in the master clip.
    def iter_sequenced_clips(self) -> Generator[Clip, None, None]:
        yield self

    def iter_all_clips(self) -> Generator[Clip, None, None]:
        yield from self._other_clip.iter_all_clips()  # Yield _other_clip's subclips and itself
        yield self  # At last yield this instance.

    def _repr_data(self) -> str:
        # Required function to generate the unique id for the instance.
        # It's called as last part in __repr__():
        #  f"<{self.__class__.__name__}{self.av_info_str}:{self._repr_data()}>"
        # Returm a simple human readable string.
        return f"{self._other_clip}:{self._my_options}"
