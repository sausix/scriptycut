# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from threading import Thread
from subprocess import run, DEVNULL, CompletedProcess

from scriptycut.common import Pathlike


class JobThread(Thread):
    _RUNNING_JOBS: List["JobThread"] = []

    def __init__(self, cmd: List[str], cwd: Pathlike = None, timeout: int = None,
                 read_fd: int = DEVNULL, write_fd: int = DEVNULL, err_fd: int = DEVNULL, close_std_fds=True,
                 autorun=False):
        self.cmd = cmd
        self.cwd = cwd
        self.timeout = timeout
        self.result: Optional[CompletedProcess] = None

        self._read_fd = read_fd
        self._write_fd = write_fd
        self._err_fd = err_fd
        self.close_std_fds = close_std_fds and (read_fd>=0 or write_fd>=0 or err_fd>=0)

        Thread.__init__(self, target=self._job_wrapper)
        if autorun:
            self.run()

    @staticmethod
    def _try_close_fd(fd) -> bool:
        if not isinstance(fd, int):
            return False

        try:
            os.close(fd)
        except OSError:
            return False

        return True

    def _job_wrapper(self):
        self._RUNNING_JOBS.append(self)
        print(f"JOB {id(self)} START:" , self.cmd)
        self.result = run(self.cmd,
                          stdin=self._read_fd, stdout=self._write_fd, stderr=self._err_fd,
                          cwd=self.cwd, timeout=self.timeout)

        self._RUNNING_JOBS.remove(self)
        print(f"JOB {id(self)} FINISH")

        if self.close_std_fds:
            for fd in self._read_fd, self._write_fd, self._err_fd:
                self._try_close_fd(fd)

    def run(self):
        if self.is_alive():
            raise RuntimeError("Job already running")

        if self in self._RUNNING_JOBS:
            raise RuntimeError("Job already in running pool?")

        Thread.run(self)

    def join_if_alive(self, timeout: float = None):
        """A friendly join which checks if thread is running"""
        if not self.is_alive():
            return
        self.join(timeout)
