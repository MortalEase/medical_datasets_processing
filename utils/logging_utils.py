import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO


class _Tee:
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
    """
    Duplicate stdout/stderr to a timestamped log file under `log_dir`.
    Returns the absolute path to the log file.
    """
    base = Path(log_dir)
    base.mkdir(parents=True, exist_ok=True)
    if script_basename is None:
        # Try to detect the caller script name; fallback to 'script'
        script_basename = Path(sys.argv[0]).stem or 'script'
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = base / f"{script_basename}_{ts}.log"

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
