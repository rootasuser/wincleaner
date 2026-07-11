"""
Empty Recycle Bin module for WinCleaner.
Author: Windel Navales
"""

import ctypes
import tkinter as tk
from tkinter import messagebox


def empty_recycle_bin(parent: tk.Misc | None = None) -> bool:
    """
    Empty the Windows Recycle Bin.

    Args:
        parent: Optional parent tkinter widget.

    Returns:
        True if the recycle bin was emptied successfully, otherwise False.
    """

    # SHERB_NOCONFIRMATION = 0x00000001
    # SHERB_NOPROGRESSUI   = 0x00000002
    # SHERB_NOSOUND        = 0x00000004
    flags = 0x00000001 | 0x00000002 | 0x00000004

    try:
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)

        if result == 0:
            title = "Recycle Bin Emptied"
            message = "Recycle Bin has been emptied successfully."

            if parent is not None:
                messagebox.showinfo(title, message, parent=parent)
            else:
                messagebox.showinfo(title, message)

            return True

        # ── Handle known error codes ──────────────────────────────────────────
        error_map = {
            -2147418113: (
                "Unable to empty the Recycle Bin.",
                "Another program is currently using files in the Recycle Bin.\n\n"
                "Try closing open applications (especially File Explorer) "
                "and try again."
            ),
        }

        title = "Error"
        if result in error_map:
            short_msg, detail_msg = error_map[result]
            message = f"{short_msg}\n\n{detail_msg}"
        else:
            message = f"Unable to empty the Recycle Bin.\n\nError code: {result}"

        if parent is not None:
            messagebox.showerror(title, message, parent=parent)
        else:
            messagebox.showerror(title, message)

        return False

    except AttributeError:
        title = "Error"
        message = "This function is only available on Windows."

        if parent is not None:
            messagebox.showerror(title, message, parent=parent)
        else:
            messagebox.showerror(title, message)

        return False

    except Exception as e:
        title = "Error"
        message = f"An unexpected error occurred:\n\n{e}"

        if parent is not None:
            messagebox.showerror(title, message, parent=parent)
        else:
            messagebox.showerror(title, message)

        return False