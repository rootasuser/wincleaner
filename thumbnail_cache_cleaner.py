"""
Thumbnail Cache Cleaner
Author: Windel Navales

Clears the Windows thumbnail cache (thumbcache_*.db) stored in:
    %%LocalAppData%%\\Microsoft\\Windows\\Explorer

Also removes legacy Thumbs.db files scattered across user folders.
"""

import os
import glob
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk


# ── Thumbnail cache paths ──────────────────────────────────────────────────────

def _get_thumbnail_cache_dir() -> str:
    """Return the path to the central thumbnail cache directory."""
    return os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Microsoft",
        "Windows",
        "Explorer"
    )


THUMB_CACHE_DIR = _get_thumbnail_cache_dir()


# ── Core deletion logic ────────────────────────────────────────────────────────

def _delete_files(file_patterns: list[str]) -> tuple[int, list[str]]:
    """
    Delete files matching wildcard patterns under THUMB_CACHE_DIR.

    Returns (count_deleted, list_of_errors).
    """
    deleted = 0
    errors: list[str] = []

    for pattern in file_patterns:
        full_pattern = os.path.join(THUMB_CACHE_DIR, pattern)
        for path in glob.glob(full_pattern):
            try:
                os.remove(path)
                deleted += 1
            except PermissionError:
                errors.append(f"Permission denied: {path}")
            except OSError as e:
                errors.append(f"{e}: {path}")

    return deleted, errors


def clear_thumbnail_cache(parent: tk.Tk | tk.Toplevel | None = None) -> None:
    """
    Main entry point — called from WinCleaner.

    Deletes all thumbcache_*.db and iconcache_*.db files in the central
    thumbnail cache directory, then restarts Explorer so the shell picks up
    the change and begins rebuilding thumbnails fresh.
    """
    # ── Resolve parent ────────────────────────────────────────────────────
    if parent is None:
        # If we're truly running standalone, create a hidden root
        _root = tk.Tk()
        _root.withdraw()
        effective_parent: tk.Tk | tk.Toplevel = _root
    else:
        effective_parent = parent

    # ── Confirm ────────────────────────────────────────────────────────────
    if not messagebox.askyesno(
        "Clear Thumbnail Cache",
        "This will delete all cached thumbnails and icon cache files.\n\n"
        "Thumbnails will be rebuilt automatically as you browse folders.\n"
        "Continue?",
        parent=effective_parent,
    ):
        if parent is None:
            effective_parent.destroy()
        return

    # ── Build progress window ──────────────────────────────────────────────
    win = tk.Toplevel(effective_parent)
    win.title("Clearing Thumbnail Cache...")
    win.geometry("380x160")
    win.resizable(False, False)
    win.configure(bg="#F0F2F5")
    win.transient(effective_parent)
    win.grab_set()

    # Centre on parent
    win.update_idletasks()
    pw = effective_parent.winfo_width()
    ph = effective_parent.winfo_height()
    px = effective_parent.winfo_x()
    py = effective_parent.winfo_y()
    wx = win.winfo_width()
    wy = win.winfo_height()
    win.geometry(f"+{px + (pw - wx) // 2}+{py + (ph - wy) // 2}")

    lbl = tk.Label(
        win,
        text="Deleting thumbnail cache files...",
        font=("Segoe UI", 10),
        bg="#F0F2F5",
        fg="#1C1E21",
    )
    lbl.pack(pady=(24, 6))

    progress = ttk.Progressbar(win, mode="indeterminate", length=280)
    progress.pack(pady=6)
    progress.start(10)

    info_var = tk.StringVar(value="Scanning...")
    info = tk.Label(win, textvariable=info_var, font=("Segoe UI", 8),
                    bg="#F0F2F5", fg="#65676B")
    info.pack()

    # ── Shared state ──────────────────────────────────────────────────────
    work_done = False
    errors: list[str] = []

    # ── Finish helper ─────────────────────────────────────────────────────
    def _finish(count: int, error_msg: str | None) -> None:
        nonlocal work_done
        work_done = True
        progress.stop()
        win.grab_release()
        win.destroy()

        if error_msg and count == 0:
            messagebox.showwarning(
                "Thumbnail Cache",
                f"Nothing was cleaned.\n\n{error_msg}",
                parent=effective_parent,
            )
            if parent is None:
                effective_parent.destroy()
            return

        summary = (
            f"Deleted {count} cache file{'s' if count != 1 else ''}.\n"
            "Thumbnails will rebuild automatically as you browse folders."
        )
        if errors:
            summary += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                summary += f"\n... and {len(errors) - 5} more."

        messagebox.showinfo("Thumbnail Cache Cleared", summary, parent=effective_parent)

        if parent is None:
            effective_parent.destroy()

    # ── Work ──────────────────────────────────────────────────────────────
    def _do_work() -> None:
        nonlocal errors
        try:
            info_var.set("Checking thumbnail cache directory...")

            if not os.path.isdir(THUMB_CACHE_DIR):
                _finish(0, "Thumbnail cache directory not found.\nNothing to clean.")
                return

            # Patterns to delete
            patterns = [
                "thumbcache_*.db",
                "thumbcache_*.dbx",
                "iconcache_*.db",
            ]

            # ── 1. Kill Explorer so DB files aren't locked ────────────
            info_var.set("Stopping Explorer to unlock cache files...")
            win.update_idletasks()

            startupinfo = None
            creation_flags = 0
            if hasattr(subprocess, "STARTUPINFO"):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                capture_output=True,
                startupinfo=startupinfo,
                creationflags=creation_flags,
            )

            # ── 2. Delete the files ───────────────────────────────────
            info_var.set("Deleting cache database files...")
            win.update_idletasks()
            deleted, errs = _delete_files(patterns)
            errors.extend(errs)

            # ── 3. Also nuke Thumbs.db in user profile folders ───────
            info_var.set("Searching for legacy Thumbs.db files...")
            win.update_idletasks()
            try:
                user_dir = os.environ.get("USERPROFILE", "")
                if user_dir:
                    thumbs_found = 0
                    for root_dir, _dirs, files in os.walk(user_dir):
                        for f in files:
                            if f.lower() == "thumbs.db":
                                path = os.path.join(root_dir, f)
                                try:
                                    os.remove(path)
                                    deleted += 1
                                    thumbs_found += 1
                                except (PermissionError, OSError) as e:
                                    errors.append(f"{e}: {path}")
                                if thumbs_found >= 200:
                                    break
                        if thumbs_found >= 200:
                            break
            except Exception as e:
                errors.append(f"Thumbs.db walk error: {e}")

            # ── 4. Restart Explorer ───────────────────────────────────
            info_var.set("Restarting Explorer...")
            win.update_idletasks()
            subprocess.Popen(
                ["explorer.exe"],
                startupinfo=startupinfo,
                creationflags=creation_flags,
            )

            _finish(deleted, None)

        except Exception as e:
            _finish(0, str(e))

    # ── Poll UI while work runs ──────────────────────────────────────────
    def _poll() -> None:
        if work_done:
            return
        win.update_idletasks()
        win.after(80, _poll)

    # ── Kick off worker after a short delay so UI renders ─────────────
    win.after(200, _do_work)
    _poll()


# ── Standalone entry point (for testing) ───────────────────────────────────────

if __name__ == "__main__":
    clear_thumbnail_cache()