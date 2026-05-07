import mbm_lite.gui.theme
from tkinter import ttk

from mbm_lite.gui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_SOFT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_WARNING,
    FONT_NORMAL,
    COLOR_CARD,
    COLOR_TEXT,
)
from mbm_lite.gui.theme import FONT_NORMAL, FONT_SMALL

def get_font_family(root):
    fonts = root.tk.call("font", "families")
    return mbm_lite.gui.theme.FONT_FAMILY


def configure_styles(root):
    """
    Configures Tkinter/ttk styles used by the application.
    """
    root.configure(bg=COLOR_BG)

    style = ttk.Style(root)

    font_family = get_font_family(root)

    FONT_NORMAL_LOCAL = (font_family, 10)
    FONT_SMALL_LOCAL = (font_family, 9)
    FONT_SECTION_LOCAL = (font_family, 13, "bold")
    
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        ".",
        font=FONT_NORMAL,
        background=COLOR_BG,
        foreground="#1F2D2D",
    )

    style.configure(
        "TFrame",
        background=COLOR_BG,
    )

    style.configure(
        "Card.TFrame",
        background=COLOR_CARD,
        relief="flat",
        borderwidth=0,
    )

    style.configure(
        "TLabel",
        background=COLOR_BG,
        foreground="#1F2D2D",
    )

    style.configure(
        "Muted.TLabel",
        background=COLOR_BG,
        foreground="#6B7C7C",
    )

    style.configure(
        "TButton",
        padding=8,
        background=COLOR_ACCENT_SOFT,
        foreground=COLOR_TEXT,
        borderwidth=0,
    )

    style.map(
        "TButton",
        background=[
            ("active", COLOR_ACCENT),
            ("pressed", COLOR_BORDER),
        ],
    )

    style.configure(
        "green.Horizontal.TProgressbar",
        troughcolor="#EAF7F6",
        background=COLOR_ACCENT,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_ACCENT,
        darkcolor=COLOR_ACCENT,
    )

    style.configure(
        "yellow.Horizontal.TProgressbar",
        troughcolor="#FFF8E1",
        background=COLOR_WARNING,
    )

    style.configure(
        "red.Horizontal.TProgressbar",
        troughcolor="#FFEBEE",
        background=COLOR_ERROR,
    )

    style.configure(
        "Pause.TButton",
        padding=6,
    )

    style.configure(
        "Resume.TButton",
        padding=6,
    )
