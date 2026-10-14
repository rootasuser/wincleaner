
"""
WinCleaner Update Checker
Author: Windel Navales

Checks GitHub for a newer WinCleaner release.
Uses Python's standard library only.
"""

import json
import re
import threading
import tkinter as tk
import webbrowser

from tkinter import messagebox
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


# ==================================================
# APPLICATION SETTINGS
# ==================================================

CURRENT_VERSION = "1.3.0"

GITHUB_USERNAME = "rootasuser"
GITHUB_REPOSITORY = "wincleaner"
GITHUB_BRANCH = "main"

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

REQUEST_TIMEOUT = 8


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


# ==================================================
# FETCH ONLINE VERSION INFORMATION
# ==================================================

def fetch_update_info():
    request = Request(
        VERSION_URL,
        headers={
            "User-Agent": "WinCleaner-Update-Checker/1.0",
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

    if not is_newer_version(latest_version, CURRENT_VERSION):
        return None

    if not isinstance(release_notes, str):
        release_notes = "Bug fixes and improvements."

    return {
        "version": latest_version,
        "download_url": RELEASES_URL,
        "release_notes": release_notes[:2000],
    }


# ==================================================
# SHOW UPDATE NOTIFICATION
# ==================================================

def show_update_notification(parent, update_info):
    """Display the update dialog on the Tkinter thread."""

    try:
        if not parent.winfo_exists():
            return
    except tk.TclError:
        return

    latest = update_info["version"]
    notes = update_info["release_notes"]

    answer = messagebox.askyesno(
        "WinCleaner Update Available",
        (
            "A new version of WinCleaner is available!\n\n"
            f"Installed version: {CURRENT_VERSION}\n"
            f"Latest version: {latest}\n\n"
            f"What's new:\n{notes}\n\n"
            "Would you like to open the download page?"
        ),
        parent=parent,
        icon="info",
    )

    if answer:
        try:
            webbrowser.open(RELEASES_URL, new=2)
        except Exception:
            messagebox.showerror(
                "Unable to Open Browser",
                f"Please open this link manually:\n{RELEASES_URL}",
                parent=parent,
            )


# ==================================================
# BACKGROUND UPDATE CHECK
# ==================================================

def check_for_updates(parent):
    """
    Check GitHub without freezing the interface.
    Internet errors do not prevent WinCleaner from opening.
    """

    def worker():
        try:
            update_info = fetch_update_info()

            if update_info is None:
                return

            try:
                parent.after(
                    0,
                    lambda info=update_info:
                        show_update_notification(parent, info),
                )
            except tk.TclError:
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
