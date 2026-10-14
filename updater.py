
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


# --------------------------------------------------
# APPLICATION VERSION
# --------------------------------------------------

CURRENT_VERSION = "1.3.0"

# CHANGE THIS to your actual GitHub repository.
GITHUB_USERNAME = "rootasuser"
GITHUB_REPOSITORY = "wincleaner"

VERSION_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/main/version.json"
)

REQUEST_TIMEOUT = 8


# --------------------------------------------------
# VERSION COMPARISON
# --------------------------------------------------

def parse_version(version):
    """
    Converts versions such as 1.3.0 or 1.4.0 to tuples.
    Supports numeric versions with optional v prefix.
    """

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
    latest = parse_version(latest_version)
    current = parse_version(current_version)

    if latest is None or current is None:
        return False

    # Normalize different version lengths:
    # 1.4 is equivalent to 1.4.0.
    length = max(len(latest), len(current))

    latest += (0,) * (length - len(latest))
    current += (0,) * (length - len(current))

    return latest > current


# --------------------------------------------------
# DOWNLOAD VERSION INFORMATION
# --------------------------------------------------

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
        if response.status != 200:
            raise URLError("Could not retrieve update information.")

        raw_data = response.read(100_000)

    data = json.loads(raw_data.decode("utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Invalid update information.")

    latest_version = data.get("version")
    download_url = data.get("download_url")
    release_notes = data.get(
        "release_notes",
        "Bug fixes and improvements.",
    )

    if not isinstance(latest_version, str):
        raise ValueError("Missing version number.")

    if not is_newer_version(latest_version, CURRENT_VERSION):
        return None

    if not isinstance(download_url, str):
        raise ValueError("Missing download URL.")

    parsed_url = urlparse(download_url)

    # Only allow HTTPS links to GitHub.
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in {
            "github.com",
            "objects.githubusercontent.com",
        }
    ):
        raise ValueError("Untrusted download URL.")

    if not isinstance(release_notes, str):
        release_notes = "Bug fixes and improvements."

    return {
        "version": latest_version,
        "download_url": download_url,
        "release_notes": release_notes[:2000],
    }


# --------------------------------------------------
# DISPLAY UPDATE NOTIFICATION
# --------------------------------------------------

def show_update_notification(parent, update_info):
    if not parent.winfo_exists():
        return

    latest = update_info["version"]
    download_url = update_info["download_url"]
    notes = update_info["release_notes"]

    answer = messagebox.askyesno(
        "WinCleaner Update Available",
        (
            f"A new version of WinCleaner is available!\n\n"
            f"Current version: {CURRENT_VERSION}\n"
            f"Latest version: {latest}\n\n"
            f"What's new:\n{notes}\n\n"
            "Would you like to open the download page?"
        ),
        parent=parent,
    )

    if answer:
        webbrowser.open(download_url)


# --------------------------------------------------
# CHECK IN BACKGROUND
# --------------------------------------------------

def check_for_updates(parent):
    """
    Checks for updates without freezing the Tkinter UI.
    If offline or the server is unavailable, the app
    continues normally.
    """

    def worker():
        try:
            update_info = fetch_update_info()

            if update_info is not None:
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
            # Do not prevent users from using WinCleaner
            # when GitHub is unavailable.
            pass

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()
