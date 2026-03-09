"""
文件锁工具：防止多个进程并发读写 JSON 文件导致数据丢失。

跨平台说明：
- POSIX（Linux/macOS）使用 fcntl.flock
- Windows 使用 msvcrt.locking
- 若锁实现异常，仍保留原子写（tmp file + replace）能力
"""
import json
import os
import pathlib
import tempfile
from contextlib import contextmanager
from typing import Any, Callable

try:
    import fcntl  # type: ignore
except ImportError:
    fcntl = None

try:
    import msvcrt  # type: ignore
except ImportError:
    msvcrt = None


LOCK_EX = 1
LOCK_SH = 2
LOCK_UN = 8


def _lock_path(path: pathlib.Path) -> pathlib.Path:
    return path.parent / (path.name + '.lock')


@contextmanager
def _locked_fd(lock_file: pathlib.Path, mode: int):
    """Open a lock file and hold a best-effort cross-platform lock."""
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX if mode == LOCK_EX else fcntl.LOCK_SH)
        elif msvcrt is not None:
            # Lock the first byte; ensure file has at least one byte.
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                os.write(fd, b'0')
            except OSError:
                pass
            os.lseek(fd, 0, os.SEEK_SET)
            lock_mode = msvcrt.LK_LOCK if mode == LOCK_EX else msvcrt.LK_RLCK
            msvcrt.locking(fd, lock_mode, 1)
        yield fd
    finally:
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
            elif msvcrt is not None:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)


def atomic_json_read(path: pathlib.Path, default: Any = None) -> Any:
    """原子读取 JSON 文件。"""
    lock_file = _lock_path(path)
    with _locked_fd(lock_file, LOCK_SH):
        try:
            return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
        except Exception:
            return default


def atomic_json_update(
    path: pathlib.Path,
    modifier: Callable[[Any], Any],
    default: Any = None,
) -> Any:
    """原子读-改-写 JSON 文件。"""
    lock_file = _lock_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _locked_fd(lock_file, LOCK_EX):
        try:
            data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
        except Exception:
            data = default
        result = modifier(data)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix='.tmp', prefix=path.stem + '_')
        try:
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        return result


def atomic_json_write(path: pathlib.Path, data: Any) -> None:
    """原子写入 JSON 文件。"""
    lock_file = _lock_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _locked_fd(lock_file, LOCK_EX):
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix='.tmp', prefix=path.stem + '_')
        try:
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
