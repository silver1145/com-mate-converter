import multiprocessing
import sys
import time
from io import BytesIO
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from queue import Queue
from threading import Thread
from types import FrameType
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

import py7zr
from loguru import logger

from com_mate_converter import CMC_Config


class BackupThread(Thread):
    backup_queue: Queue
    back_files: Dict[Path, py7zr.SevenZipFile]
    _stopped_flag: bool = False
    _killed_flag: bool = False

    def __init__(self, back_paths: Dict[Path, Path]) -> None:
        super().__init__()
        self.backup_queue = Queue()
        self.back_files = {}
        for k, v in back_paths.items():
            if v.exists():
                self.back_files[k] = py7zr.SevenZipFile(v, "a")
                self.back_files[k]
            else:
                self.back_files[k] = py7zr.SevenZipFile(v, "w")

    def start(self) -> None:
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self) -> None:
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    @logger.catch
    def run(self) -> None:
        try:
            _final_empty = False
            while not self._stopped_flag or not _final_empty:
                while not self.backup_queue.empty():
                    t: Tuple[Path, Path, bytes] = self.backup_queue.get_nowait()
                    if len(t) == 3:
                        work_path, file_path, data = t
                        if work_path in self.back_files:
                            self.back_files[work_path].writef(
                                BytesIO(data), str(file_path.relative_to(work_path.parent))
                            )
                time.sleep(0.1)
                if self._stopped_flag and self.backup_queue.empty():
                    _final_empty = True
        finally:
            self.finish_backup()

    @logger.catch
    def add_backup(self, work_path: Path, file_path: Path, data: bytes) -> None:
        self.backup_queue.put_nowait((work_path, file_path, data))

    def finish_backup(self) -> None:
        for f in self.back_files.values():
            f.close()
        self.back_files.clear()

    def stop(self) -> None:
        self._stopped_flag = True

    def is_stopped(self) -> bool:
        return self._stopped_flag

    def globaltrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if self._killed_flag:
            if event == "line":
                raise SystemExit()
        return self.localtrace

    def kill(self) -> None:
        self._killed_flag = True


class WorkThread(Thread):
    finish_callback: Optional[Callable[[], None]]
    _stopped_flag: bool = False
    _killed_flag: bool = False

    def __init__(
        self,
        target: Optional[Callable[..., object]] = ...,
        args: Iterable[Any] = ...,
        kwargs: Optional[Mapping[str, Any]] = None,
        finish_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(target=target, args=args, kwargs=kwargs)
        self.finish_callback = finish_callback

    def start(self) -> None:
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self) -> None:
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def run(self) -> None:
        try:
            if self._target:  # type: ignore
                self._target(*self._args, **self._kwargs, check_stop=self.is_stopped)  # type: ignore
                if not self._stopped_flag:
                    if self.finish_callback is not None:
                        self.finish_callback()
                    self._stopped_flag = True
        finally:
            del self._target, self._args, self._kwargs  # type: ignore

    def stop(self) -> None:
        self._stopped_flag = True

    def is_stopped(self) -> bool:
        return self._stopped_flag

    def globaltrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if self._killed_flag:
            if event == "line":
                raise SystemExit()
        return self.localtrace

    def kill(self) -> None:
        self._killed_flag = True


class WorkPoolThread(Thread):
    finish_callback: Optional[Callable[[], None]]
    _stopped_flag: bool = False
    _killed_flag: bool = False

    def __init__(
        self,
        target: Optional[Callable[..., object]] = ...,
        args: List[Any] = ...,
        finish_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(target=target)
        self._args = args
        self.pool = ThreadPool(max(int(multiprocessing.cpu_count() * CMC_Config.config.cpu_percent), 1))
        self.finish_callback = finish_callback

    def _target_warpper(self, *args) -> Any:
        if self._stopped_flag:
            return None
        return self._target(*args)  # type: ignore

    def _target_run_in_pool(self) -> List:
        results = self.pool.map(self._target_warpper, self._args)
        self.pool.close()
        self.pool.join()
        return results

    def start(self) -> None:
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self) -> None:
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def run(self) -> None:
        try:
            if self._target:  # type: ignore
                self._target_run_in_pool()
                if not self._stopped_flag:
                    if self.finish_callback is not None:
                        self.finish_callback()
                    self._stopped_flag = True
        finally:
            del self._target, self._args  # type: ignore

    def stop(self) -> None:
        self._stopped_flag = True

    def is_stopped(self) -> bool:
        return self._stopped_flag

    def globaltrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if self._killed_flag:
            if event == "line":
                raise SystemExit()
        return self.localtrace

    def kill(self) -> None:
        self._killed_flag = True
