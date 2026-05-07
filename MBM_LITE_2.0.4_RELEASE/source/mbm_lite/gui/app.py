import os
import sys
import ctypes
import tkinter as tk
from tkinter import ttk

from mbm_lite.metadata import APP_DISPLAY_NAME
from mbm_lite import app_state
from mbm_lite.logger import log
from mbm_lite.state import carica_stato, salva_stato
from mbm_lite.scheduler import start_job_scheduler, stop_job_scheduler
from mbm_lite.gui.styles import configure_styles
from mbm_lite.gui.job_rows import (
    refresh_job_rows,
    start_all_jobs,
    pause_all_jobs,
    resume_all_jobs,
)
from mbm_lite.gui.dialogs import add_job_dialog
from mbm_lite.gui.theme import FONT_TITLE, FONT_SECTION, get_icon_path
from mbm_lite.gui.info_windows import show_help_window, show_credits_window


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def on_close():
    """
    Handles application shutdown.
    """
    stop_job_scheduler()
    salva_stato()

    if app_state.root is not None:
        app_state.root.destroy()


def start_gui():
    """
    Starts the main GUI application.
    """
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "mbm.lite.2.0.4"
    )

    root = tk.Tk()

    icon_path = get_icon_path()
    try:
        root.iconbitmap(icon_path)
    except Exception:
        pass

    app_state.root = root

    root.title(APP_DISPLAY_NAME)
    root.geometry("900x650")

    menu_bar = tk.Menu(root)

    info_menu = tk.Menu(menu_bar, tearoff=0)
    info_menu.add_command(
        label="Help",
        command=lambda: show_help_window(root),
    )
    info_menu.add_command(
        label="Credits",
        command=lambda: show_credits_window(root),
    )

    menu_bar.add_cascade(label="Info", menu=info_menu)
    root.config(menu=menu_bar)

    configure_styles(root)

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    title_label = ttk.Label(
        main_frame,
        text=APP_DISPLAY_NAME,
        font=FONT_TITLE,
    )
    title_label.pack(anchor="w")

    status_label = ttk.Label(
        main_frame,
        text="Multi Backup Manager, Made by Francesco Angelillo, 2026.",
    )
    status_label.pack(anchor="w", pady=(8, 10))

    toolbar = ttk.Frame(main_frame)
    toolbar.pack(fill="x", pady=(0, 12))

    ttk.Button(
        toolbar,
        text="Add Job",
        command=lambda: add_job_dialog(root),
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        toolbar,
        text="Start All",
        command=start_all_jobs,
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        toolbar,
        text="Pause All",
        command=pause_all_jobs,
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        toolbar,
        text="Resume All",
        command=resume_all_jobs,
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        toolbar,
        text="Save State",
        command=salva_stato,
    ).pack(side="left")

    ttk.Label(
        main_frame,
        text="Jobs",
        font=FONT_SECTION,
    ).pack(anchor="w")

    jobs_container = ttk.Frame(main_frame)
    jobs_container.pack(fill="x", pady=(5, 15))

    jobs_canvas = tk.Canvas(jobs_container, height=220, highlightthickness=0)
    jobs_scrollbar = ttk.Scrollbar(
        jobs_container,
        orient="vertical",
        command=jobs_canvas.yview,
    )
    app_state.jobs_frame = ttk.Frame(jobs_canvas)

    jobs_canvas.configure(yscrollcommand=jobs_scrollbar.set)
    jobs_window = jobs_canvas.create_window(
        (0, 0),
        window=app_state.jobs_frame,
        anchor="nw",
    )

    def update_jobs_scrollregion(event=None):
        jobs_canvas.configure(scrollregion=jobs_canvas.bbox("all"))

    def update_jobs_frame_width(event):
        jobs_canvas.itemconfigure(jobs_window, width=event.width)

    app_state.jobs_frame.bind("<Configure>", update_jobs_scrollregion)
    jobs_canvas.bind("<Configure>", update_jobs_frame_width)

    jobs_mousewheel_active = {"enabled": False}

    def pointer_is_over_jobs():
        pointer_x, pointer_y = root.winfo_pointerxy()
        widget = root.winfo_containing(pointer_x, pointer_y)
        while widget is not None:
            if widget in (jobs_container, jobs_canvas, app_state.jobs_frame):
                return True
            widget = getattr(widget, "master", None)
        return False

    def scroll_jobs(event):
        if not pointer_is_over_jobs():
            return None
        jobs_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def enable_jobs_mousewheel(event=None):
        if not jobs_mousewheel_active["enabled"]:
            jobs_canvas.bind_all("<MouseWheel>", scroll_jobs)
            jobs_mousewheel_active["enabled"] = True

    def disable_jobs_mousewheel(event=None):
        if pointer_is_over_jobs():
            return
        if jobs_mousewheel_active["enabled"]:
            jobs_canvas.unbind_all("<MouseWheel>")
            jobs_mousewheel_active["enabled"] = False

    for jobs_widget in (jobs_container, jobs_canvas, app_state.jobs_frame):
        jobs_widget.bind("<Enter>", enable_jobs_mousewheel)
        jobs_widget.bind("<Leave>", disable_jobs_mousewheel)

    jobs_canvas.pack(side="left", fill="both", expand=True)
    jobs_scrollbar.pack(side="right", fill="y")

    ttk.Label(
        main_frame,
        text="Logs",
        font=FONT_SECTION,
    ).pack(anchor="w")

    app_state.log_box = tk.Text(main_frame, height=14)
    app_state.log_box.pack(fill="both", expand=True, pady=(5, 0))

    carica_stato()
    refresh_job_rows()
    start_job_scheduler()

    log(f"{APP_DISPLAY_NAME} started.")


    def invoke_focused_button(event):
        focused_widget = root.focus_get()
        if isinstance(focused_widget, (tk.Button, ttk.Button)):
            try:
                focused_widget.invoke()
                return "break"
            except Exception:
                pass
        return None

    root.bind("<Return>", invoke_focused_button)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
