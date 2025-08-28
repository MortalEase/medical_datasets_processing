import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO


class _Tee:
    """将标准输出/错误复制写入日志文件与控制台.

    此类作为 file-like 包装器, 同时把写入内容写到原始流与日志文件中.
    """

    def __init__(self, original: TextIO, file: TextIO):
        self._orig = original
        self._file = file

    def write(self, data: str):
        try:
            self._orig.write(data)
        except Exception:
            pass
        try:
            self._file.write(data)
        except Exception:
            pass

    def flush(self):
        try:
            self._orig.flush()
        except Exception:
            pass
        try:
            self._file.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self._orig.isatty()
        except Exception:
            return False


def tee_stdout_stderr(log_dir: str | Path = 'logs', script_basename: Optional[str] = None) -> str:
    """把标准输出与标准错误复制到日志文件并保留原有控制台输出.

    会在 log_dir 下创建按时间戳命名的日志文件, 返回该日志文件的绝对路径.
    """
    base = Path(log_dir)
    base.mkdir(parents=True, exist_ok=True)
    if script_basename is None:
        # Try to detect the caller script name; fallback to 'script'
        script_basename = Path(sys.argv[0]).stem or 'script'
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    # 调整命名：时间戳在前，便于按名称排序: YYYYMMDD_HHMMSS_scriptname.log
    log_path = base / f"{ts}_{script_basename}.log"

    # Open in text mode with utf-8 to support CN output
    f = open(log_path, 'w', encoding='utf-8', buffering=1)

    header = f"===== {script_basename} start {datetime.now().isoformat(timespec='seconds')} =====\n"
    cmdline = ' '.join(sys.argv)
    try:
        f.write(header)
        f.write(f"cmd: {cmdline}\n")
        f.flush()
    except Exception:
        pass

    sys.stdout = _Tee(sys.stdout, f)  # type: ignore
    sys.stderr = _Tee(sys.stderr, f)  # type: ignore

    return str(log_path)


def log_info(message: str) -> None:
    """输出信息级别日志到控制台与日志文件, 统一前缀为 '[INFO] '."""
    if message is None or str(message).strip() == "":
        print("")
        return
    print(f"[INFO] {message}")


def log_warn(message: str) -> None:
    """输出警告级别日志到控制台与日志文件, 统一前缀为 '[WARN] '."""
    if message is None or str(message).strip() == "":
        print("")
        return
    print(f"[WARN] {message}")


def log_error(message: str) -> None:
    """输出错误级别日志到控制台与日志文件, 统一前缀为 '[ERROR] '."""
    if message is None or str(message).strip() == "":
        print("")
        return
    print(f"[ERROR] {message}")
