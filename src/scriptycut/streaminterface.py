# -*- coding: utf-8 -*-

class StreamInterface:
    pass


class Raw(StreamInterface):
    pass


class FileReEncode(StreamInterface):
    pass


class UnixPipe(StreamInterface):
    pass


class FromFile(StreamInterface):
    pass
