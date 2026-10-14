"""
WinCleaner Update Checker & Auto-Updater
Author: Windel Navales

Checks GitHub for a newer WinCleaner version. If the user agrees, the new
executable is downloaded, verified (SHA-256), installed over the current
one and WinCleaner restarts by itself.

Auto-install only works for a single-file (--onefile) PyInstaller build.
In every other case (running from source, one-folder build, read-only
install folder, missing checksum) the user is offered the download page.

Uses Python's standard library only.

version.json (in the repository root, branch "main"):
{
  "version": "1.5.0",
  "release_notes": "What's new in this version.",
  "sha256": "<SHA-256 of the WinCleaner.exe attached to the release>",
  "download_url": "optional - defaults to the latest release's WinCleaner.exe"
}
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser

from tkinter import messagebox
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


# ==================================================
# APPLICATION SETTINGS
# ==================================================

# Fallback only. main.py passes its own APP_VERSION to check_for_updates().
CURRENT_VERSION = "1.5.0"

GITHUB_USERNAME = "rootasuser"
GITHUB_REPOSITORY = "wincleaner"
GITHUB_BRANCH = "main"

# The asset name attached to every GitHub release.
EXE_NAME = "WinCleaner.exe"

VERSION_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_USERNAME}/"
    f"{GITHUB_REPOSITORY}/"
    f"{GITHUB_BRANCH}/version.json"
)

RELEASES_URL = (
    f"https://github.com/"
    f"{GITHUB_USERNAME}/"
    f"{GITHUB_REPOSITORY}/releases/latest"
)

# Always points at the EXE of the newest release.
DEFAULT_DOWNLOAD_URL = (
    f"https://github.com/"
    f"{GITHUB_USERNAME}/"
    f"{GITHUB_REPOSITORY}/releases/latest/download/{EXE_NAME}"
)

REQUEST_TIMEOUT = 8
DOWNLOAD_TIMEOUT = 30
CHUNK_SIZE = 64 * 1024
MAX_DOWNLOAD_BYTES = 300 * 1024 * 1024

# Downloads are only accepted from GitHub.
ALLOWED_HOST_SUFFIXES = ("github.com", "githubusercontent.com")

# Colors (same palette as the main window)
BLUE_DEEP = "#001B66"
PANEL = "#062B91"
CYAN = "#28C7FF"
WHITE = "#FFFFFF"
MUTED = "#D6E4FF"
RED_ACCENT = "#FF3658"


class DownloadCancelled(Exception):
    """Raised when the user cancels the download."""


# ==================================================
# VERSION UTILITIES
# ==================================================

def parse_version(version):
    """Parse versions such as 1.3.0 or v1.4.0."""

    if not isinstance(version, str):
        return None

    version = version.strip()

    if version.lower().startswith("v"):
        version = version[1:]

    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        return None

    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None


def is_newer_version(latest_version, current_version):
    """Return True if latest_version is newer."""

    latest = parse_version(latest_version)
    current = parse_version(current_version)

    if latest is None or current is None:
        return False

    length = max(len(latest), len(current))

    latest += (0,) * (length - len(latest))
    current += (0,) * (length - len(current))

    return latest > current


def is_allowed_url(url):
    """Only HTTPS links that belong to GitHub are trusted."""

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme != "https" or not parsed.hostname:
        return False

    host = parsed.hostname.lower()

    return any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ALLOWED_HOST_SUFFIXES
    )


# ==================================================
# FETCH ONLINE VERSION INFORMATION
# ==================================================

def fetch_update_info(current_version):
    request = Request(
        VERSION_URL,
        headers={
            "User-Agent": "WinCleaner-Update-Checker/2.0",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw_data = response.read(100_000)

    data = json.loads(raw_data.decode("utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Invalid version information.")

    latest_version = data.get("version")
    release_notes = data.get(
        "release_notes",
        "Bug fixes and improvements.",
    )

    if not isinstance(latest_version, str):
        raise ValueError("Missing version number.")

    if parse_version(latest_version) is None:
        raise ValueError("Invalid version format.")

    if not is_newer_version(latest_version, current_version):
        return None

    if not isinstance(release_notes, str):
        release_notes = "Bug fixes and improvements."

    download_url = data.get("download_url", DEFAULT_DOWNLOAD_URL)
    if not isinstance(download_url, str) or not is_allowed_url(download_url):
        download_url = None

    sha256 = data.get("sha256")
    if isinstance(sha256, str):
        sha256 = sha256.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            sha256 = None
    else:
        sha256 = None

    return {
        "version": latest_version,
        "download_url": download_url,
        "sha256": sha256,
        "release_notes": release_notes[:2000],
    }


# ==================================================
# AUTO-INSTALL SUPPORT CHECK
# ==================================================

def can_auto_install(update_info):
    """True only when the running program can safely replace itself."""

    if os.name != "nt":
        return False

    if not getattr(sys, "frozen", False):
        return False

    if not update_info.get("download_url") or not update_info.get("sha256"):
        return False

    exe_path = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(exe_path)

    # '%' breaks batch-file paths.
    if "%" in exe_path:
        return False

    # One-folder builds keep their files in <exe folder>\_internal and
    # cannot be replaced by a single downloaded EXE.
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        meipass = os.path.abspath(meipass).lower()
        if meipass.startswith(exe_dir.lower() + os.sep):
            return False

    return os.access(exe_dir, os.W_OK)


# ==================================================
# DOWNLOAD + VERIFY
# ==================================================

def download_update(url, expected_sha256, dest_path, on_progress, cancel_event):
    """Download to dest_path and verify size, host, header and checksum."""

    request = Request(
        url,
        headers={"User-Agent": "WinCleaner-Update-Checker/2.0"},
    )

    digest = hashlib.sha256()
    downloaded = 0

    with urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        if not is_allowed_url(response.geturl()):
            raise ValueError("The download was redirected to an untrusted address.")

        total = int(response.headers.get("Content-Length") or 0)

        if total > MAX_DOWNLOAD_BYTES:
            raise ValueError("The update file is unexpectedly large.")

        with open(dest_path, "wb") as output:
            while True:
                if cancel_event.is_set():
                    raise DownloadCancelled()

                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break

                downloaded += len(chunk)
                if downloaded > MAX_DOWNLOAD_BYTES:
                    raise ValueError("The update file is unexpectedly large.")

                output.write(chunk)
                digest.update(chunk)
                on_progress(downloaded, total)

    if total and downloaded != total:
        raise ValueError("The download was incomplete.")

    if digest.hexdigest() != expected_sha256:
        raise ValueError(
            "The downloaded file failed the security check (checksum mismatch)."
        )

    with open(dest_path, "rb") as check:
        if check.read(2) != b"MZ":
            raise ValueError("The downloaded file is not a Windows program.")


def remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


# ==================================================
# INSTALL: swap the EXE after WinCleaner closes, then restart
# ==================================================

def launch_installer_script(new_exe_path):
    """
    A running EXE cannot overwrite itself on Windows, so a tiny batch
    script waits for WinCleaner to close, swaps the file and restarts it.
    """

    target = os.path.abspath(sys.executable)

    script_path = os.path.join(
        tempfile.gettempdir(),
        f"wincleaner_update_{os.getpid()}.bat",
    )

    # ping is used for delays because "timeout" fails without a console.
    script = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'set "TARGET={target}"\r\n'
        f'set "NEWEXE={new_exe_path}"\r\n'
        "set /a TRIES=0\r\n"
        ":retry\r\n"
        "set /a TRIES+=1\r\n"
        'move /y "%NEWEXE%" "%TARGET%" >nul 2>&1\r\n'
        "if not errorlevel 1 goto launch\r\n"
        "if %TRIES% GEQ 60 goto fail\r\n"
        "ping 127.0.0.1 -n 2 >nul\r\n"
        "goto retry\r\n"
        ":launch\r\n"
        "ping 127.0.0.1 -n 3 >nul\r\n"
        'start "" "%TARGET%"\r\n'
        "goto cleanup\r\n"
        ":fail\r\n"
        'del /f /q "%NEWEXE%" >nul 2>&1\r\n'
        ":cleanup\r\n"
        '(goto) 2>nul & del "%~f0"\r\n'
    )

    with open(script_path, "w", encoding="utf-8", newline="") as file:
        file.write(script)

    # Lets the restarted onefile EXE unpack itself instead of reusing the
    # old process's temporary folder.
    env = os.environ.copy()
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

    subprocess.Popen(
        ["cmd.exe", "/c", script_path],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=(
            subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
        ),
    )


# ==================================================
# PROGRESS WINDOW + UPDATE FLOW
# ==================================================

def _post(parent, callback):
    """Run callback on the Tkinter thread."""

    try:
        parent.after(0, callback)
    except (tk.TclError, RuntimeError):
        pass


def open_release_page(parent):
    try:
        webbrowser.open(RELEASES_URL, new=2)
    except Exception:
        messagebox.showerror(
            "Unable to Open Browser",
            f"Please open this link manually:\n{RELEASES_URL}",
            parent=parent,
        )


def start_auto_update(parent, update_info):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    new_exe = os.path.join(exe_dir, "WinCleaner_update.exe")
    cancel_event = threading.Event()

    # ---- progress window ----
    win = tk.Toplevel(parent)
    win.title("Updating WinCleaner")
    win.configure(bg=BLUE_DEEP)
    win.resizable(False, False)
    win.transient(parent)

    tk.Label(
        win,
        text=f"Downloading WinCleaner {update_info['version']}",
        font=("Segoe UI", 12, "bold"),
        bg=BLUE_DEEP,
        fg=WHITE,
    ).pack(anchor="w", padx=24, pady=(22, 4))

    status = tk.Label(
        win,
        text="Starting download...",
        font=("Segoe UI", 9),
        bg=BLUE_DEEP,
        fg=MUTED,
    )
    status.pack(anchor="w", padx=24)

    bar_width = 360
    bar = tk.Canvas(
        win,
        width=bar_width,
        height=14,
        bg=PANEL,
        highlightthickness=0,
    )
    bar.pack(padx=24, pady=(14, 6))
    fill = bar.create_rectangle(0, 0, 0, 14, fill=CYAN, width=0)

    cancel_button = tk.Button(
        win,
        text="Cancel",
        font=("Segoe UI", 9, "bold"),
        bg=RED_ACCENT,
        fg=WHITE,
        activebackground="#D91F43",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=16,
        pady=6,
        command=cancel_event.set,
    )
    cancel_button.pack(anchor="e", padx=24, pady=(10, 20))

    win.protocol("WM_DELETE_WINDOW", cancel_event.set)

    win.update_idletasks()
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
        win.grab_set()
    except tk.TclError:
        pass

    # ---- UI callbacks (Tkinter thread) ----
    def close_window():
        try:
            win.grab_release()
        except tk.TclError:
            pass
        try:
            win.destroy()
        except tk.TclError:
            pass

    def set_progress(done, total):
        try:
            if total:
                fraction = min(done / total, 1.0)
                bar.coords(fill, 0, 0, int(bar_width * fraction), 14)
                status.config(
                    text=f"{done / 1_048_576:.1f} MB of "
                         f"{total / 1_048_576:.1f} MB  "
                         f"({int(fraction * 100)}%)"
                )
            else:
                status.config(text=f"{done / 1_048_576:.1f} MB downloaded")
        except tk.TclError:
            pass

    def on_error(message):
        close_window()
        remove_quietly(new_exe)

        if messagebox.askyesno(
            "Update Failed",
            f"WinCleaner could not install the update:\n\n{message}\n\n"
            "Would you like to open the download page instead?",
            parent=parent,
            icon="warning",
        ):
            open_release_page(parent)

    def finish_install():
        try:
            launch_installer_script(new_exe)
        except OSError as error:
            on_error(str(error))
            return

        close_window()
        parent.destroy()

    def on_ready():
        try:
            cancel_button.config(state="disabled")
            bar.coords(fill, 0, 0, bar_width, 14)
            status.config(text="Download verified. Restarting WinCleaner...")
            win.after(800, finish_install)
        except tk.TclError:
            finish_install()

    # ---- background download ----
    last_update = [0.0]

    def on_progress(done, total):
        now = time.monotonic()
        if now - last_update[0] < 0.1 and (not total or done < total):
            return
        last_update[0] = now
        _post(parent, lambda: set_progress(done, total))

    def worker():
        try:
            download_update(
                update_info["download_url"],
                update_info["sha256"],
                new_exe,
                on_progress,
                cancel_event,
            )
        except DownloadCancelled:
            remove_quietly(new_exe)
            _post(parent, close_window)
            return
        except Exception as error:
            remove_quietly(new_exe)
            message = str(error) or error.__class__.__name__
            _post(parent, lambda m=message: on_error(m))
            return

        _post(parent, on_ready)

    threading.Thread(target=worker, daemon=True).start()


# ==================================================
# SHOW UPDATE NOTIFICATION
# ==================================================

def show_update_notification(parent, update_info, current_version):
    """Display the update dialog on the Tkinter thread."""

    try:
        if not parent.winfo_exists():
            return
    except tk.TclError:
        return

    latest = update_info["version"]
    notes = update_info["release_notes"]
    auto = can_auto_install(update_info)

    if auto:
        question = (
            "Would you like to download and install it now?\n"
            "WinCleaner will restart automatically."
        )
    else:
        question = "Would you like to open the download page?"

    answer = messagebox.askyesno(
        "WinCleaner Update Available",
        (
            "A new version of WinCleaner is available!\n\n"
            f"Installed version: {current_version}\n"
            f"Latest version: {latest}\n\n"
            f"What's new:\n{notes}\n\n"
            f"{question}"
        ),
        parent=parent,
        icon="info",
    )

    if not answer:
        return

    if auto:
        start_auto_update(parent, update_info)
    else:
        open_release_page(parent)


# ==================================================
# BACKGROUND UPDATE CHECK
# ==================================================

def check_for_updates(parent, current_version=CURRENT_VERSION):
    """
    Check GitHub without freezing the interface.
    Internet errors do not prevent WinCleaner from opening.
    """

    def worker():
        try:
            update_info = fetch_update_info(current_version)

            if update_info is None:
                return

            try:
                parent.after(
                    0,
                    lambda info=update_info:
                        show_update_notification(
                            parent, info, current_version
                        ),
                )
            except (tk.TclError, RuntimeError):
                pass

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ):
            # Offline or unavailable GitHub:
            # allow the user to keep using WinCleaner.
            pass

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )
    thread.start()