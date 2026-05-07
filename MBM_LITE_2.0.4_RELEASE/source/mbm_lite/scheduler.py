import threading
import time

from . import app_state, backup
from .logger import log


_scheduler_stop_events = {}
_scheduler_threads = {}
_scheduler_lock = threading.Lock()


def _get_interval_seconds(job):
    if "timer_hours" in job:
        try:
            return max(0, float(job.get("timer_hours", 0)) * 3600)
        except (TypeError, ValueError):
            return 0

    schedule = job.get("schedule", {})
    return (
        schedule.get("days", 0) * 86400
        + schedule.get("hours", 0) * 3600
        + schedule.get("minutes", 0) * 60
    )


def _format_interval(interval_s):
    try:
        total_minutes = int(round(float(interval_s) / 60))
    except (TypeError, ValueError):
        total_minutes = 0

    if total_minutes <= 0:
        return "0 minutes"

    days = total_minutes // 1440
    remaining_minutes = total_minutes % 1440
    hours = remaining_minutes // 60
    minutes = remaining_minutes % 60

    parts = []
    if days:
        parts.append(f"{days} day" if days == 1 else f"{days} days")
    if hours:
        parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")
    if minutes:
        parts.append(f"{minutes} minute" if minutes == 1 else f"{minutes} minutes")

    return " ".join(parts)

def job_scheduler_loop(job):
    """
    Scheduler loop for a single backup job.
    """
    key = (job["source"], job["dest"])
    stop_event = _scheduler_stop_events.get(key)
    interval_s = _get_interval_seconds(job)
    if stop_event is None or interval_s <= 0:
        return

    try:
        while not stop_event.is_set():
            waited = 0
            while waited < interval_s and not stop_event.is_set():
                sleep_for = min(1, interval_s - waited)
                time.sleep(sleep_for)
                waited += sleep_for
            if stop_event.is_set():
                break

            if job.get("paused", False):
                log(f"[Scheduler] Job paused, skip: {job['source']}")
                continue
            if key in app_state.jobs_in_esecuzione:
                log(f"[Scheduler] Job already running, wait for next interval: {job['source']}")
                continue

            backup_thread = threading.Thread(
                target=backup.esegui_backup_incrementale,
                args=(job,),
                daemon=True,
            )
            backup_thread.start()
            backup_thread.join()
    finally:
        if _scheduler_threads.get(key) is threading.current_thread():
            _scheduler_threads.pop(key, None)
            _scheduler_stop_events.pop(key, None)


def start_job_scheduler(job=None):
    """
    Starts scheduler threads for all jobs, or for a single job when provided.
    """
    if job is None:
        for scheduled_job in app_state.backup_jobs:
            start_job_scheduler(scheduled_job)
        return

    key = (job["source"], job["dest"])
    interval_s = _get_interval_seconds(job)
    if interval_s <= 0:
        return

    with _scheduler_lock:
        current_thread = _scheduler_threads.get(key)
        if current_thread and current_thread.is_alive():
            return

        stop_event = threading.Event()
        _scheduler_stop_events[key] = stop_event

        scheduler_thread = threading.Thread(
            target=job_scheduler_loop,
            args=(job,),
            daemon=True,
        )

        _scheduler_threads[key] = scheduler_thread
        scheduler_thread.start()

    log(f"[*] Scheduler started for {job['source']}: every {_format_interval(interval_s)}")


def stop_job_scheduler(job=None):
    """
    Stops scheduler threads for all jobs, or for a single job when provided.
    """
    if job is None:
        for scheduled_job in app_state.backup_jobs:
            stop_job_scheduler(scheduled_job)
        return

    key = (job["source"], job["dest"])
    with _scheduler_lock:
        stop_event = _scheduler_stop_events.get(key)
        if stop_event:
            stop_event.set()


def restart_job_scheduler(old_job, new_job):
    old_key = (old_job.get("source", ""), old_job.get("dest", ""))
    new_key = (new_job.get("source", ""), new_job.get("dest", ""))

    # STOP vecchio scheduler
    with _scheduler_lock:
        old_stop_event = _scheduler_stop_events.get(old_key)
        old_thread = _scheduler_threads.get(old_key)
        if old_stop_event:
            old_stop_event.set()

    # Aspetta che muoia davvero
    if old_thread and old_thread.is_alive():
        old_thread.join(timeout=1.5)

    with _scheduler_lock:
        if _scheduler_threads.get(old_key) is old_thread:
            _scheduler_threads.pop(old_key, None)
            _scheduler_stop_events.pop(old_key, None)

    # Avvia nuovo scheduler
    interval_s = _get_interval_seconds(new_job)
    if interval_s <= 0:
        return

    with _scheduler_lock:
        current_thread = _scheduler_threads.get(new_key)
        if current_thread and current_thread.is_alive():
            return

        stop_event = threading.Event()
        _scheduler_stop_events[new_key] = stop_event

        scheduler_thread = threading.Thread(
            target=job_scheduler_loop,
            args=(new_job,),
            daemon=True,
        )

        _scheduler_threads[new_key] = scheduler_thread
        scheduler_thread.start()

    log(
        f"[*] Scheduler restarted for {new_job.get('source', '')}: "
        f"every {_format_interval(interval_s)}"
    )
