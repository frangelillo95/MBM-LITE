import json
import os
import threading

from . import app_state
from . import paths
from .logger import log


_state_lock = threading.Lock()


def salva_stato(verbose=False):
    """
    Saves the current jobs state to JSON.
    """
    with _state_lock:
        tmp_file = paths.STATE_FILE + ".tmp"

        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(app_state.backup_jobs, f, indent=4, ensure_ascii=False)

            os.replace(tmp_file, paths.STATE_FILE)

            if verbose:
                log("State saved successfully.")

        except Exception as e:
            log(f"Error saving state: {e}")


def carica_stato():
    """
    Loads the jobs state from JSON.
    """
    if not os.path.exists(paths.STATE_FILE):
        log("No state file found.")
        return

    try:
        with open(paths.STATE_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        if isinstance(jobs, list):
            app_state.backup_jobs.clear()
            app_state.backup_jobs.extend(jobs)
            log("State loaded successfully.")
        else:
            log("Invalid state file: content is not a list.")

    except Exception as e:
        log(f"Error loading state: {e}")