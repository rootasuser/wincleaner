"""
Clear Recent Items module for WinCleaner.
Author: Windel Navales
"""

import os
import shutil
import tkinter as tk
from tkinter import messagebox


def clear_recent(parent: tk.Misc | None = None) -> None:
    """Delete everything inside the Windows Recent Items folder."""

    folder = os.path.join(
        os.environ["APPDATA"],
        "Microsoft",
        "Windows",
        "Recent",
    )

    deleted = 0
    skipped = 0

    if os.path.isdir(folder):
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

    title = "Recent Items Cleared"
    message = (
        "Recent items cleared.\n\n"
        f"✔ Deleted : {deleted}\n"
        f"– Skipped : {skipped}"
    )

    if parent is not None:
        messagebox.showinfo(title, message, parent=parent)
    else:
        messagebox.showinfo(title, message)