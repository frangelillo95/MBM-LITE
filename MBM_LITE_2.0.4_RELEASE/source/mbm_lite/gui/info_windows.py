import tkinter as tk
from tkinter import ttk

from mbm_lite.metadata import APP_DISPLAY_NAME, APP_VERSION
from mbm_lite.gui.theme import FONT_NORMAL, FONT_SECTION, get_icon_path


def show_help_window(parent):
    """
    Opens the Help window with basic usage instructions.
    """
    window = tk.Toplevel(parent)
    icon_path = get_icon_path()
    try:
        window.iconbitmap(icon_path)
    except Exception:
        pass
    window.title("Help")
    window.geometry("620x520")
    window.transient(parent)

    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Help",
        font=FONT_SECTION,
    ).pack(anchor="w", pady=(0, 10))

    help_text = tk.Text(
        frame,
        wrap="word",
        height=22,
        font=FONT_NORMAL,
    )
    help_text.pack(fill="both", expand=True)

    content = """MBM-Lite Help

MBM-Lite is a lightweight backup manager designed to create and manage incremental backup jobs.

Basic usage:

1. Add a backup job
   Click "Add Job" and select:
   - Source folder
   - Destination folder
   - Schedule interval

2. Start a job manually
   Click "Start" on a job card to run the backup immediately.

3. Pause or resume a job
   Click "Pause" to temporarily disable automatic backups.
   Click "Resume" to enable them again.

4. Edit a job
   Click "Edit" to change source, destination, or schedule interval.

5. Remove a job
   Click "Remove" to delete the job from the current configuration.

6. Logs
   MBM-Lite creates a general log and job-specific logs inside the logs folder.

Important notes:
- Incremental backups copy new or updated files.
- Existing destination files are not deleted automatically.
- Keep destination folders accessible while backup jobs are running.
- Very short schedule intervals should only be used for testing.
"""

    help_text.insert("1.0", content)
    help_text.configure(state="disabled")


def show_credits_window(parent):
    """
    Opens the Credits window.
    """
    window = tk.Toplevel(parent)
    icon_path = get_icon_path()
    try:
        window.iconbitmap(icon_path)
    except Exception:
        pass
    window.title("Credits")
    window.geometry("460x320")
    window.transient(parent)

    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Credits",
        font=FONT_SECTION,
    ).pack(anchor="w", pady=(0, 12))

    credits = (
        f"{APP_DISPLAY_NAME}\n"
        f"Version: {APP_VERSION}\n\n"
        "Created by: Francesco Angelillo\n"
        "Latest Update: 2026-05-06 17:28\n"
        "Company: Aalea S.r.l.\n\n"
        "Purpose:\n"
        "Lightweight incremental backup management tool."
    )

    ttk.Label(
        frame,
        text=credits,
        font=FONT_NORMAL,
        justify="left",
    ).pack(anchor="w")
