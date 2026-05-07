import os
import sys
import ctypes


def resource_path(relative_path):
    """
    Returns the correct path in normal execution and PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    return os.path.join(base_path, relative_path)


def get_icon_path():
    """
    Returns the MBM icon path in normal execution and PyInstaller.
    """
    candidates = [
        resource_path(os.path.join("source", "assets", "MBM.ico")),
        resource_path(os.path.join("..", "assets", "MBM.ico")),
        resource_path(os.path.join("assets", "MBM.ico")),
    ]

    for icon_path in candidates:
        if os.path.exists(icon_path):
            return icon_path

    return candidates[0]


def load_private_font(font_filename):
    """
    Loads a private font on Windows.
    """
    if os.name != "nt":
        return

    font_path = resource_path(os.path.join("assets", "fonts", font_filename))

    if os.path.exists(font_path):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
        except Exception:
            pass


FONT_FAMILY = "Segoe UI"
FONT_FAMILY_BOLD = "Segoe UI Semibold"
FONT_MONO = "Consolas"

FONT_TITLE = (FONT_FAMILY_BOLD, 17)
FONT_SECTION = (FONT_FAMILY_BOLD, 12)
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_LOG = (FONT_MONO, 9)

COLOR_BG = "#F6F8FA"
COLOR_PANEL = "#FFFFFF"
COLOR_CARD = "#FFFFFF"
COLOR_CARD_SOFT = "#F9FAFB"

COLOR_TEXT = "#1F2933"
COLOR_MUTED = "#6B7280"

COLOR_AQUA = "#3BAFA9"
COLOR_AQUA_SOFT = "#D7F0EE"
COLOR_AQUA_LIGHT = "#EEF8F7"

COLOR_BLUE_BORDER = "#D0D7DE"
COLOR_BLUE_SOFT = "#F1F5F9"

COLOR_WARNING = "#D97706"
COLOR_ERROR = "#DC2626"

BUTTON_PADDING = 7
CARD_PADDING = 12

# Compatibility aliases
COLOR_ACCENT = COLOR_AQUA
COLOR_ACCENT_SOFT = COLOR_AQUA_SOFT
COLOR_ACCENT_LIGHT = COLOR_AQUA_LIGHT
COLOR_BORDER = COLOR_BLUE_BORDER
