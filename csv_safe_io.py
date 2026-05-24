"""
csv_safe_io.py
--------------
Crash-safe CSV writing for the weighbridge application.

Solves two problems:

1. Read-only protection -- after every write the data file is left with the
   Windows read-only attribute set, so opening it in Excel/Notepad opens it
   read-only. The app clears the attribute only for the instant it writes.

2. Power-loss corruption -- writes never truncate the live file in place.
   New content is written to a temporary file, flushed all the way to disk
   with os.fsync(), then swapped in with os.replace(), which is atomic on
   both Windows and Linux. A power cut can never leave the live file empty
   or half-written.

Drop this file next to data_management.py and import from it.
"""

import csv
import os
import stat

__all__ = [
    "atomic_write_csv",
    "append_csv_row",
    "set_readonly",
    "clear_readonly",
    "csv_is_valid",
    "cleanup_stale_temp_files",
]

TEMP_SUFFIX = ".tmp"


def clear_readonly(path):
    """Remove the read-only attribute so the file can be written."""
    if os.path.exists(path):
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            pass


def set_readonly(path):
    """Set the read-only attribute. Excel/Notepad will then open it read-only."""
    if os.path.exists(path):
        try:
            os.chmod(path, stat.S_IREAD)
        except OSError:
            pass


def _fsync_dir(folder):
    """Best-effort: make a rename durable on POSIX. Harmless no-op on Windows."""
    try:
        fd = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, AttributeError):
        pass


def atomic_write_csv(path, header, rows, make_readonly=True):
    """
    Write `header` + `rows` to `path` atomically and crash-safely.

    Steps: write to <path>.tmp -> flush + fsync to physical disk ->
    os.replace() over the real file (atomic) -> restore read-only attribute.

    If anything fails before the swap, the original file is left untouched
    and the partial temp file is removed.

    `header` may be None to write rows only. `rows` is an iterable of lists.
    """
    abspath = os.path.abspath(path)
    folder = os.path.dirname(abspath)
    os.makedirs(folder, exist_ok=True)
    tmp_path = abspath + TEMP_SUFFIX

    # The destination may be read-only from a previous run; os.replace would
    # otherwise fail with access-denied on Windows.
    clear_readonly(abspath)

    try:
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header is not None:
                writer.writerow(header)
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())          # force bytes onto the physical disk

        os.replace(tmp_path, abspath)     # atomic swap -- never half-replaced
        _fsync_dir(folder)                # make the swap itself durable
    except Exception:
        # Failed before the swap completed: remove the partial temp file.
        # The real file was never touched and is still valid.
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise
    finally:
        if make_readonly:
            set_readonly(abspath)


def append_csv_row(path, row, header=None, make_readonly=True):
    """
    Append a single row to `path` durably (flushed to disk), keeping the
    file read-only afterwards. If the file is missing or empty and `header`
    is given, the header is written first so a wiped file is rebuilt cleanly.
    """
    abspath = os.path.abspath(path)
    os.makedirs(os.path.dirname(abspath), exist_ok=True)

    clear_readonly(abspath)
    try:
        need_header = header is not None and (
            not os.path.exists(abspath) or os.path.getsize(abspath) == 0
        )
        with open(abspath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if need_header:
                writer.writerow(header)
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())
    finally:
        if make_readonly:
            set_readonly(abspath)


def csv_is_valid(path, expected_header=None):
    """
    Return True if `path` exists, is non-empty, parses as CSV, and (optionally)
    starts with `expected_header`. Useful for detecting a corrupted file on
    startup.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return False
            if expected_header is not None and header != list(expected_header):
                return False
            for _ in reader:          # consume the rest to surface parse errors
                pass
        return True
    except (csv.Error, UnicodeDecodeError, OSError):
        return False


def cleanup_stale_temp_files(folder):
    """
    Delete leftover *.csv.tmp files under `folder` (recursively). These are
    interrupted atomic writes from a previous crash and are safe to remove.
    Returns the list of removed paths. Call once at application startup.
    """
    removed = []
    if not folder or not os.path.isdir(folder):
        return removed
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.endswith(".csv" + TEMP_SUFFIX):
                p = os.path.join(root, name)
                try:
                    os.remove(p)
                    removed.append(p)
                except OSError:
                    pass
    return removed