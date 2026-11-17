"""Nonblocking thread/process locks released by the OS on process termination."""
from contextlib import contextmanager
from pathlib import Path
import os
import threading


class RuntimeLockBusy(RuntimeError):
    pass


_LOCKS: dict[str, threading.Lock] = {}
_GUARD = threading.Lock()


@contextmanager
def file_lock(path: Path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _GUARD:
        lock = _LOCKS.setdefault(str(path), threading.Lock())
    if not lock.acquire(blocking=False):
        raise RuntimeLockBusy("runtime transaction is already active")
    handle = None
    held = False
    try:
        handle = path.open("a+b")
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeLockBusy("runtime transaction is already active") from error
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise RuntimeLockBusy("runtime transaction is already active") from error
        held = True
        yield
    finally:
        if handle is not None:
            if held:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
        lock.release()
