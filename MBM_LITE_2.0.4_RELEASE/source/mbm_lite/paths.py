import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SOURCE_DIR, ".."))

STATE_FILE = os.path.join(PROJECT_ROOT, "backup_state.json")

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_FILE = os.path.join(ASSETS_DIR, "MBM.ico")
ICON_48_FILE = os.path.join(ASSETS_DIR, "MBM_48.png")


def resource_path(relative_path):
    """
    Returns correct path both in normal execution and inside PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = SOURCE_DIR

    return os.path.join(base_path, relative_path)