import tkinter as tk
import os
from tkinter import filedialog, messagebox, ttk

from mbm_lite import app_state
from mbm_lite.models import make_job
from mbm_lite.state import salva_stato
from mbm_lite.logger import log
from mbm_lite.gui.theme import get_icon_path
from mbm_lite.gui.job_rows import refresh_job_rows
from mbm_lite.scheduler import start_job_scheduler, restart_job_scheduler


def validate_job_paths(source, dest):
    """
    Validates source and destination folders.
    """
    source_abs = os.path.abspath(source)
    dest_abs = os.path.abspath(dest)

    if not os.path.isdir(source_abs):
        messagebox.showerror(
            "Invalid source",
            "The selected source folder does not exist.",
        )
        return None

    if source_abs == dest_abs:
        messagebox.showerror(
            "Invalid folders",
            "Source and destination folders cannot be the same.",
        )
        return None

    try:
        if os.path.commonpath([source_abs, dest_abs]) == source_abs:
            messagebox.showerror(
                "Invalid destination",
                "Destination folder cannot be inside the source folder.",
            )
            return None
    except ValueError:
        pass

    try:
        os.makedirs(dest_abs, exist_ok=True)
    except Exception as e:
        messagebox.showerror(
            "Invalid destination",
            f"Destination folder cannot be created:\n\n{e}",
        )
        return None

    return source_abs, dest_abs


def add_job_dialog(parent):
    """
    Opens a dialog to create a new backup job.
    """
    dialog = tk.Toplevel(parent)
    icon_path = get_icon_path()
    try:
        dialog.iconbitmap(icon_path)
    except Exception:
        pass
    dialog.title("Add Backup Job")
    dialog.geometry("600x260")
    dialog.transient(parent)
    dialog.grab_set()

    source_var = tk.StringVar()
    dest_var = tk.StringVar()
    hours_var = tk.StringVar(value="24")
    minutes_var = tk.StringVar(value="0")

    frame = ttk.Frame(dialog, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Source folder").pack(anchor="w")
    source_row = ttk.Frame(frame)
    source_row.pack(fill="x", pady=(0, 8))

    source_entry = ttk.Entry(source_row, textvariable=source_var)
    source_entry.pack(side="left", fill="x", expand=True)

    ttk.Button(
        source_row,
        text="Browse",
        command=lambda: source_var.set(
            filedialog.askdirectory(title="Select source folder")
        ),
    ).pack(side="left", padx=(6, 0))

    ttk.Label(frame, text="Destination folder").pack(anchor="w")
    dest_row = ttk.Frame(frame)
    dest_row.pack(fill="x", pady=(0, 8))

    dest_entry = ttk.Entry(dest_row, textvariable=dest_var)
    dest_entry.pack(side="left", fill="x", expand=True)

    ttk.Button(
        dest_row,
        text="Browse",
        command=lambda: dest_var.set(
            filedialog.askdirectory(title="Select destination folder")
        ),
    ).pack(side="left", padx=(6, 0))

    ttk.Label(frame, text="Schedule interval").pack(anchor="w")

    schedule_row = ttk.Frame(frame)
    schedule_row.pack(fill="x", pady=(0, 12))

    hours_spin = ttk.Spinbox(
        schedule_row,
        from_=0,
        to=999,
        textvariable=hours_var,
        width=6,
    )
    hours_spin.pack(side="left")

    ttk.Label(schedule_row, text="hours").pack(side="left", padx=(6, 12))

    minutes_spin = ttk.Spinbox(
        schedule_row,
        from_=0,
        to=59,
        textvariable=minutes_var,
        width=6,
    )
    minutes_spin.pack(side="left")

    ttk.Label(schedule_row, text="minutes").pack(side="left", padx=(6, 0))

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="e")

    def save_job():
        source = source_var.get().strip()
        dest = dest_var.get().strip()

        try:
            hours = int(hours_var.get().strip())
            minutes = int(minutes_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid value", "Hours and minutes must be numbers.")
            return

        if hours < 0 or minutes < 0 or minutes > 59:
            messagebox.showerror("Invalid value", "Use valid hours and minutes.")
            return

        timer_hours = hours + (minutes / 60)

        if timer_hours <= 0:
            messagebox.showerror("Invalid value", "Schedule interval must be greater than zero.")
            return

        if not source:
            messagebox.showerror("Missing source", "Please select a source folder.")
            return

        if not dest:
            messagebox.showerror("Missing destination", "Please select a destination folder.")
            return
        
        validated_paths = validate_job_paths(source, dest)
        if validated_paths is None:
            return

        source, dest = validated_paths

        if timer_hours <= 0:
            messagebox.showerror("Invalid value", "Schedule interval must be greater than zero.")
            return

        job = make_job(
            source=source,
            dest=dest,
            timer_hours=timer_hours,
        )

        app_state.backup_jobs.append(job)
        salva_stato()
        refresh_job_rows()
        start_job_scheduler(job)

        log(f"Job added: {source} -> {dest}")

        dialog.destroy()

    ttk.Button(
        buttons,
        text="Cancel",
        command=dialog.destroy,
    ).pack(side="right", padx=(6, 0))

    ttk.Button(
        buttons,
        text="Save",
        command=save_job,
    ).pack(side="right")



def edit_job_dialog(parent, job):
    """
    Opens a dialog to edit an existing backup job.
    """
    dialog = tk.Toplevel(parent)
    icon_path = get_icon_path()
    try:
        dialog.iconbitmap(icon_path)
    except Exception:
        pass
    dialog.title("Edit Backup Job")
    dialog.geometry("600x260")
    dialog.transient(parent)
    dialog.grab_set()

    source_var = tk.StringVar(value=job.get("source", ""))
    dest_var = tk.StringVar(value=job.get("dest", ""))
    current_timer = float(job.get("timer_hours", 24))
    current_hours = int(current_timer)
    current_minutes = int(round((current_timer - current_hours) * 60))

    hours_var = tk.StringVar(value=str(current_hours))
    minutes_var = tk.StringVar(value=str(current_minutes))

    frame = ttk.Frame(dialog, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Source folder").pack(anchor="w")
    source_row = ttk.Frame(frame)
    source_row.pack(fill="x", pady=(0, 8))

    ttk.Entry(source_row, textvariable=source_var).pack(side="left", fill="x", expand=True)

    ttk.Button(
        source_row,
        text="Browse",
        command=lambda: source_var.set(
            filedialog.askdirectory(title="Select source folder")
        ),
    ).pack(side="left", padx=(6, 0))

    ttk.Label(frame, text="Destination folder").pack(anchor="w")
    dest_row = ttk.Frame(frame)
    dest_row.pack(fill="x", pady=(0, 8))

    ttk.Entry(dest_row, textvariable=dest_var).pack(side="left", fill="x", expand=True)

    ttk.Button(
        dest_row,
        text="Browse",
        command=lambda: dest_var.set(
            filedialog.askdirectory(title="Select destination folder")
        ),
    ).pack(side="left", padx=(6, 0))

    ttk.Label(frame, text="Schedule interval").pack(anchor="w")

    schedule_row = ttk.Frame(frame)
    schedule_row.pack(fill="x", pady=(0, 12))

    hours_spin = ttk.Spinbox(
        schedule_row,
        from_=0,
        to=999,
        textvariable=hours_var,
        width=6,
    )
    hours_spin.pack(side="left")

    ttk.Label(schedule_row, text="hours").pack(side="left", padx=(6, 12))

    minutes_spin = ttk.Spinbox(
        schedule_row,
        from_=0,
        to=59,
        textvariable=minutes_var,
        width=6,
    )
    minutes_spin.pack(side="left")

    ttk.Label(schedule_row, text="minutes").pack(side="left", padx=(6, 0))

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="e")

    def save_changes():
        source = source_var.get().strip()
        dest = dest_var.get().strip()

        try:
            hours = int(hours_var.get().strip())
            minutes = int(minutes_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid value", "Hours and minutes must be numbers.")
            return

        if hours < 0 or minutes < 0 or minutes > 59:
            messagebox.showerror("Invalid value", "Use valid hours and minutes.")
            return

        timer_hours = hours + (minutes / 60)

        if not source:
            messagebox.showerror("Missing source", "Please select a source folder.")
            return

        if not dest:
            messagebox.showerror("Missing destination", "Please select a destination folder.")
            return
        
        validated_paths = validate_job_paths(source, dest)
        if validated_paths is None:
            return

        source, dest = validated_paths 

        old_job = job.copy()

        job["source"] = source
        job["dest"] = dest
        job["timer_hours"] = timer_hours

        salva_stato()
        refresh_job_rows()
        restart_job_scheduler(old_job, job)

        log(f"Job updated: {source} -> {dest}")
        dialog.destroy()


    ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="right", padx=(6, 0))
    ttk.Button(buttons, text="Save", command=save_changes).pack(side="right")



