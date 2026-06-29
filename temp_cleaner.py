"""
Clear Temporary Files module for WinCleaner.
Author: Windel Navales
"""

import os
import shutil
import tempfile
import tkinter as tk
from tkinter import messagebox


def clear_folder(folder: str) -> tuple[int, int]:
    """
    Delete all files and subdirectories inside the specified folder.

    Returns:
        (deleted_count, skipped_count)
    """
    deleted = 0
    skipped = 0

    if not os.path.isdir(folder):
        return deleted, skipped

    for item in os.listdir(folder):
        path = os.path.join(folder, item)

        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

            deleted += 1

        except Exception:
            skipped += 1

    return deleted, skipped


def clear_temp(parent: tk.Misc | None = None) -> None:
    """Delete everything inside the system TEMP directory."""

    deleted, skipped = clear_folder(tempfile.gettempdir())

    title = "Temp Files Cleaned"
    message = (
        "Temporary files cleaned.\n\n"
        f"✔ Deleted : {deleted}\n"
        f"– Skipped : {skipped}"
    )

    if parent is not None:
        messagebox.showinfo(title, message, parent=parent)
    else:
        messagebox.showinfo(title, message)