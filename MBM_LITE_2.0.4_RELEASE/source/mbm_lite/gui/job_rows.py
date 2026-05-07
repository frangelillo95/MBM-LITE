import threading
from tkinter import ttk, messagebox

from mbm_lite import app_state
from mbm_lite.backup import esegui_backup_incrementale
from mbm_lite.state import salva_stato
from mbm_lite.logger import log
from mbm_lite.scheduler import stop_job_scheduler
from mbm_lite.gui.theme import (
    COLOR_ACCENT,
    COLOR_CARD,
    COLOR_ERROR,
    COLOR_MUTED,
    COLOR_TEXT,
    COLOR_WARNING,
    FONT_NORMAL,
    FONT_SECTION,
    FONT_SMALL,
)


def refresh_job_rows():
    """
    Rebuilds the job list in the GUI.
    """
    if app_state.jobs_frame is None:
        return

    expanded_jobs = getattr(refresh_job_rows, "_expanded_jobs", None)
    if expanded_jobs is None:
        expanded_jobs = set()
        refresh_job_rows._expanded_jobs = expanded_jobs

    known_jobs = getattr(refresh_job_rows, "_known_jobs", None)
    if known_jobs is None:
        known_jobs = set()
        refresh_job_rows._known_jobs = known_jobs

    current_keys = {
        (job.get("source", ""), job.get("dest", ""))
        for job in app_state.backup_jobs
    }
    expanded_jobs.intersection_update(current_keys)
    known_jobs.intersection_update(current_keys)

    for widget in app_state.jobs_frame.winfo_children():
        widget.destroy()

    app_state.job_widgets.clear()

    def short_path(value):
        text = str(value or "")
        trimmed = text.rstrip("\\/")
        parts = trimmed.replace("\\", "/").split("/")
        return parts[-1] if parts and parts[-1] else trimmed or "Not set"

    def toggle_job_expanded(row_key):
        if row_key in expanded_jobs:
            expanded_jobs.remove(row_key)
        else:
            expanded_jobs.add(row_key)
        refresh_job_rows()

    def render_job_card(job):
        source = job.get("source", "")
        dest = job.get("dest", "")
        timer_hours = job.get("timer_hours", 24)
        paused = job.get("paused", False)
        last_backup = job.get("last_backup") or "Never"

        key = (source, dest)
        if key not in known_jobs:
            expanded_jobs.add(key)
            known_jobs.add(key)

        is_expanded = key in expanded_jobs
        has_error = key in app_state.job_errors
        error_text = app_state.job_errors.get(key, "")

        if paused:
            status = "PAUSED"
            status_color = COLOR_WARNING
        elif key in app_state.jobs_in_esecuzione:
            status = "RUNNING"
            status_color = COLOR_ACCENT
        elif has_error:
            status = "ERROR"
            status_color = COLOR_ERROR
        else:
            status = "READY"
            status_color = COLOR_MUTED

        card = ttk.Frame(
            app_state.jobs_frame,
            style="Card.TFrame",
            padding=12,
        )
        card.pack(fill="x", padx=8, pady=7)

        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x")

        ttk.Button(
            header,
            text=" - " if is_expanded else " + ",
            width=3,
            command=lambda row_key=key: toggle_job_expanded(row_key),
        ).pack(side="left", padx=(0, 8))

        title = ttk.Label(
            header,
            text=f"Backup Job: {short_path(source)}",
            font=FONT_SECTION,
            foreground=COLOR_TEXT,
            background=COLOR_CARD,
        )
        title.pack(side="left", anchor="w")

        status_label = ttk.Label(
            header,
            text=status,
            font=FONT_SMALL,
            foreground=status_color,
            background=COLOR_CARD,
        )
        status_label.pack(side="right", anchor="e")

        summary = ttk.Label(
            card,
            text=(
                f"{short_path(source)} -> {short_path(dest)} | "
                f"Schedule: every {format_schedule_interval(timer_hours)}"
            ),
            font=FONT_SMALL,
            foreground=COLOR_MUTED,
            background=COLOR_CARD,
        )
        summary.pack(anchor="w", pady=(8, 0))

        if not is_expanded:
            app_state.progress_bars.pop(key, None)
            app_state.job_widgets[key] = card
            return

        details_frame = ttk.Frame(card, style="Card.TFrame")
        details_frame.pack(fill="x")

        ttk.Label(
            details_frame,
            text="Source folder",
            font=FONT_SMALL,
            foreground=COLOR_MUTED,
            background=COLOR_CARD,
        ).pack(anchor="w", pady=(10, 0))

        ttk.Label(
            details_frame,
            text=source,
            font=FONT_NORMAL,
            foreground=COLOR_TEXT,
            background=COLOR_CARD,
            wraplength=780,
        ).pack(anchor="w")

        ttk.Label(
            details_frame,
            text="Destination folder",
            font=FONT_SMALL,
            foreground=COLOR_MUTED,
            background=COLOR_CARD,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Label(
            details_frame,
            text=dest,
            font=FONT_NORMAL,
            foreground=COLOR_TEXT,
            background=COLOR_CARD,
            wraplength=780,
        ).pack(anchor="w")

        meta = ttk.Frame(details_frame, style="Card.TFrame")
        meta.pack(fill="x", pady=(8, 0))

        ttk.Label(
            meta,
            text=f"Schedule: every {format_schedule_interval(timer_hours)}",
            font=FONT_SMALL,
            foreground=COLOR_MUTED,
            background=COLOR_CARD,
        ).pack(side="left")

        ttk.Label(
            meta,
            text=f"Last backup: {last_backup}",
            font=FONT_SMALL,
            foreground=COLOR_MUTED,
            background=COLOR_CARD,
        ).pack(side="right")

        if has_error:
            ttk.Label(
                details_frame,
                text=f"Last error: {error_text}",
                font=FONT_SMALL,
                foreground=COLOR_ERROR,
                background=COLOR_CARD,
                wraplength=780,
            ).pack(anchor="w", pady=(8, 0))

        current_value = 0
        existing_progress = app_state.progress_bars.get(key)

        if existing_progress is not None:
            try:
                current_value = existing_progress["value"]
            except Exception:
                current_value = 0

        progress = ttk.Progressbar(
            details_frame,
            mode="determinate",
            maximum=100,
            value=current_value,
            style="green.Horizontal.TProgressbar",
        )
        progress.pack(fill="x", pady=(12, 8))

        app_state.progress_bars[key] = progress

        buttons_frame = ttk.Frame(details_frame, style="Card.TFrame")
        buttons_frame.pack(anchor="w")

        ttk.Button(
            buttons_frame,
            text="Start",
            state="disabled" if status == "RUNNING" else "normal",
            command=lambda: start_job(job),
        ).pack(side="left", padx=(0, 6))

        pause_text = "Resume" if paused else "Pause"

        ttk.Button(
            buttons_frame,
            text=pause_text,
            command=lambda: toggle_pause_job(job),
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            buttons_frame,
            text="Edit",
            command=lambda: open_edit_job_dialog(job),
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            buttons_frame,
            text="Remove",
            state="disabled" if status == "RUNNING" else "normal",
            command=lambda: remove_job(job),
        ).pack(side="left")

        app_state.job_widgets[key] = card

    for job in app_state.backup_jobs:
        render_job_card(job)

def format_schedule_interval(timer_hours):
    """
    Formats timer_hours as HH:MM.
    """
    try:
        total_minutes = int(round(float(timer_hours) * 60))
    except (TypeError, ValueError):
        total_minutes = 0

    hours = total_minutes // 60
    minutes = total_minutes % 60

    return f"{hours:02d}:{minutes:02d}"

# candidate for cleanup in 2.0.5
def create_job_row(job):
    """
    Creates a modern visual card for one backup job.
    """
    source = job.get("source", "")
    dest = job.get("dest", "")
    timer_hours = job.get("timer_hours", 24)
    paused = job.get("paused", False)
    last_backup = job.get("last_backup") or "Never"

    key = (source, dest)

    if key in app_state.jobs_in_esecuzione:
        status = "RUNNING"
        status_color = COLOR_ACCENT
    elif paused:
        status = "PAUSED"
        status_color = COLOR_WARNING
    else:
        status = "READY"
        status_color = COLOR_MUTED

    card = ttk.Frame(
        app_state.jobs_frame,
        style="Card.TFrame",
        padding=12,
    )
    card.pack(fill="x", padx=8, pady=7)

    header = ttk.Frame(card, style="Card.TFrame")
    header.pack(fill="x")

    title = ttk.Label(
        header,
        text="Backup Job",
        font=FONT_SECTION,
        foreground=COLOR_TEXT,
        background=COLOR_CARD,
    )
    title.pack(side="left", anchor="w")

    status_label = ttk.Label(
        header,
        text=status,
        font=FONT_SMALL,
        foreground=status_color,
        background=COLOR_CARD,
    )
    status_label.pack(side="right", anchor="e")

    ttk.Label(
        card,
        text="Source folder",
        font=FONT_SMALL,
        foreground=COLOR_MUTED,
        background=COLOR_CARD,
    ).pack(anchor="w", pady=(10, 0))

    ttk.Label(
        card,
        text=source,
        font=FONT_NORMAL,
        foreground=COLOR_TEXT,
        background=COLOR_CARD,
        wraplength=780,
    ).pack(anchor="w")

    ttk.Label(
        card,
        text="Destination folder",
        font=FONT_SMALL,
        foreground=COLOR_MUTED,
        background=COLOR_CARD,
    ).pack(anchor="w", pady=(8, 0))

    ttk.Label(
        card,
        text=dest,
        font=FONT_NORMAL,
        foreground=COLOR_TEXT,
        background=COLOR_CARD,
        wraplength=780,
    ).pack(anchor="w")

    meta = ttk.Frame(card, style="Card.TFrame")
    meta.pack(fill="x", pady=(8, 0))

    ttk.Label(
        meta,
        text=f"Schedule: every {format_schedule_interval(timer_hours)}",
        font=FONT_SMALL,
        foreground=COLOR_MUTED,
        background=COLOR_CARD,
    ).pack(side="left")

    ttk.Label(
        meta,
        text=f"Last backup: {last_backup}",
        font=FONT_SMALL,
        foreground=COLOR_MUTED,
        background=COLOR_CARD,
    ).pack(side="right")

    current_value = 0
    existing_progress = app_state.progress_bars.get(key)

    if existing_progress is not None:
        try:
            current_value = existing_progress["value"]
        except Exception:
            current_value = 0

    progress = ttk.Progressbar(
        card,
        mode="determinate",
        maximum=100,
        value=current_value,
        style="green.Horizontal.TProgressbar",
    )
    progress.pack(fill="x", pady=(12, 8))

    app_state.progress_bars[key] = progress

    buttons_frame = ttk.Frame(card, style="Card.TFrame")
    buttons_frame.pack(anchor="w")

    ttk.Button(
        buttons_frame,
        text="Start",
        command=lambda: start_job(job),
    ).pack(side="left", padx=(0, 6))

    pause_text = "Resume" if paused else "Pause"

    ttk.Button(
        buttons_frame,
        text=pause_text,
        command=lambda: toggle_pause_job(job),
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        buttons_frame,
        text="Edit",
        command=lambda: open_edit_job_dialog(job),
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        buttons_frame,
        text="Remove",
        command=lambda: remove_job(job),
    ).pack(side="left")

    app_state.job_widgets[key] = card

def open_edit_job_dialog(job):
    """
    Opens the edit dialog for a job.
    Import is local to avoid circular imports.
    """
    from mbm_lite.gui.dialogs import edit_job_dialog

    edit_job_dialog(app_state.root, job)

def start_job(job):
    """
    Starts a backup job in a background thread if it is not already running.
    """
    source = job.get("source", "")
    dest = job.get("dest", "")
    key = (source, dest)

    if key in app_state.jobs_in_esecuzione:
        log(f"Job already running: {source} -> {dest}")
        return

    thread = threading.Thread(
        target=esegui_backup_incrementale,
        args=(job,),
        daemon=True,
    )
    thread.start()

    log(f"Job started manually: {source} -> {dest}")


def toggle_pause_job(job):
    """
    Toggles pause state for a job.
    """
    job["paused"] = not job.get("paused", False)
    salva_stato()

    if job["paused"]:
        log(f"Job paused: {job.get('source', '')}")
    else:
        log(f"Job resumed: {job.get('source', '')}")

    refresh_job_rows()


def remove_job(job):
    """
    Removes a job from the current job list and stops scheduler.
    """
    from mbm_lite.scheduler import stop_job_scheduler

    source = job.get("source", "")
    dest = job.get("dest", "")
    key = (source, dest)

    #Stop scheduler del job
    stop_job_scheduler(job)

    #Rimuovi da jobs in esecuzione (sicurezza)
    app_state.jobs_in_esecuzione.discard(key)

    #Rimuovi job dalla lista
    if job in app_state.backup_jobs:
        app_state.backup_jobs.remove(job)

    salva_stato()
    log(f"Job removed: {source} -> {dest}")

    refresh_job_rows()


def start_all_jobs():
    """
    Starts all non-paused jobs.
    """
    for job in app_state.backup_jobs:
        if not job.get("paused", False):
            start_job(job)

    log("All active jobs started.")


def pause_all_jobs():
    """
    Pauses all jobs.
    """
    for job in app_state.backup_jobs:
        job["paused"] = True

    salva_stato()
    refresh_job_rows()
    log("All jobs paused.")


def resume_all_jobs():
    """
    Resumes all jobs.
    """
    for job in app_state.backup_jobs:
        job["paused"] = False

    salva_stato()
    refresh_job_rows()
    log("All jobs resumed.")
