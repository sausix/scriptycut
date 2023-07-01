# -*- coding: utf-8 -*-

"""
Still on testing.
Pipes are easy and great on Linux to chain ffmpeg streams.
Windows is very restricted and ffmpeg doc is not helping a lot.
Streams via pipes should be preferred instead of writing files to disk first.
It's easier to run multiple ffmpeg processes instead of one with endless processing commands.
"""

# https://stackoverflow.com/questions/48542644/python-and-windows-named-pipes

import os
import subprocess


class Pipe:
    def __init__(self):
        self.read_fd, self.write_fd = os.pipe()

    def get_fds(self):
        return self.read_fd, self.write_fd

    def write(self, data: bytes):
        os.write(self.write_fd, data)

    def read(self, size=0):
        os.read(self.read_fd, size)

    def close_read(self):
        os.close(self.read_fd)
        self.read_fd = None

    def close_write(self):
        os.close(self.write_fd)
        self.write_fd = None

    def __del__(self):
        if self.read_fd:
            self.close_read()

        if self.write_fd:
            os.close(self.write_fd)

    def __repr__(self):
        return f"<{self.__class__.__name__} read={self.read_fd} write={self.write_fd}>"


# Testvideo
# ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 testsrc.mpg

# Linux:
# mkfifo -m 0666 /tmp/my_pipe
# os.mkfifo("/tmp/my_pipe", 0o666)

# Send:
# ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 -f webm pipe:1 > /tmp/my_pipe



# Linux send via stdout, connected to a pipe
# r, w = os.pipe()
p = Pipe()
r, w = p.get_fds()
cmd_send = ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", "testsrc=duration=10:size=1280x720:rate=30", "-f", "webm", "pipe:1"]


# stream = f"/proc/{os.getpid()}/fd/{r}"
stream = "pipe:0"

print(f"ffplay -autoexit -i {stream} -f webm")
cmd_receive = ["ffplay", "-v", "error", "-autoexit", "-i", stream, "-f", "webm"]
# cmd_receive = ["ffplay", "-autoexit", "-i", "/home/as/Downloads/175844.mp4"]

print("Start sending process")
send_proc = subprocess.Popen(cmd_send, bufsize=0, stdout=w, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

print("Starting player")
rec_process = subprocess.Popen(cmd_receive, bufsize=0, stdin=r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

send_proc.wait()
print("Close write")
p.close_write()

rec_process.wait()
print("Close read")
p.close_read()


del p
