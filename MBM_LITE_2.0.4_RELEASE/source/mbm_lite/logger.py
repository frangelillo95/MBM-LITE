import os
import hashlib
from datetime import datetime

from . import app_state


_LOG_RUN_TIMESTAMP = datetime.now()
_INVALID_FILENAME_CHARS = '<>:"/\\|?*'
_JOB_LOG_FILES = {}


def get_log_day_dir():
    day_dir = os.path.join(
        os.getcwd(),
        "logs",
        f"log_{_LOG_RUN_TIMESTAMP.strftime('%Y-%m-%d')}",
    )
    try:
        os.makedirs(day_dir, exist_ok=True)
    except Exception:
        pass
    return day_dir


def sanitize_filename_part(value):
    text = str(value) if value is not None else "unknown"
    sanitized = "".join(
        "_" if char in _INVALID_FILENAME_CHARS or ord(char) < 32 else char
        for char in text
    ).strip(" .")
    return sanitized[:80] or "unknown"


def get_general_log_file():
    filename = f"MBM_log_general_{_LOG_RUN_TIMESTAMP.strftime('%Y%m%d_%H%M%S')}.txt"
    return os.path.join(get_log_day_dir(), filename)


def get_job_log_file(source, dest):
    key = (str(source), str(dest))
    if key not in _JOB_LOG_FILES:
        source_part = sanitize_filename_part(get_last_part(source))
        dest_part = sanitize_filename_part(get_last_part(dest))
        hash_part = short_hash(source, dest)
        filename = (
            f"MBM_log_{source_part}_TO_{dest_part}_{hash_part}_"
            f"{_LOG_RUN_TIMESTAMP.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        _JOB_LOG_FILES[key] = os.path.join(get_log_day_dir(), filename)
    return _JOB_LOG_FILES[key]


def _write_line(file_path, line):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except Exception:
        pass


def _write_visible(line):
    print(line)

    if app_state.log_box is not None:
        try:
            app_state.log_box.insert("end", line + "\n")
            app_state.log_box.see("end")
        except Exception:
            pass


def _format_line(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"


def log(message):
    """
    Central logger.
    Messages may be displayed in the GUI, so they must be in English.
    """
    line = _format_line(message)
    _write_visible(line)
    _write_line(get_general_log_file(), line)


def log_job(message, source, dest):
    """
    Writes a job-related message to the general log and to the job log.
    Messages may be displayed in the GUI, so they must be in English.
    """
    line = _format_line(message)
    _write_visible(line)
    _write_line(get_general_log_file(), line)
    _write_line(get_job_log_file(source, dest), line)


def short_hash(source, dest):
    raw = f"{source}|{dest}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:6]


def get_last_part(path):
    return os.path.basename(os.path.normpath(path)) or "root"