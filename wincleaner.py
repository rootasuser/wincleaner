"""
WinCleaner — Windows System Cleaner
Author: Windel Navales
Modern blue Tkinter interface.
"""

import os
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox

from ui_components import (
    ACCENT, ACCENT_H, GREEN, GREEN_H, RED, RED_H, ORANGE, ORANGE_H,
    TEXT_LIGHT, TEXT_MUTED, make_button,
)
from recycle_bin import empty_recycle_bin
from temp_cleaner import clear_temp
from recent_cleaner import clear_recent
from duplicate_finder import open_duplicate_finder
from thumbnail_cache_cleaner import clear_thumbnail_cache
from updater import check_for_updates


APP_VERSION = "1.4.0"
WEBSITE_URL = "https://wincleaner-web.vercel.app/"

# Resolve resources for both normal Python execution and PyInstaller.
def resource_path(filename):
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, filename)


ICO_PATH = resource_path("wincleaner.ico")

# Colors
BLUE = "#003DE3"
BLUE_DARK = "#002A9E"
BLUE_DEEP = "#001B66"
PANEL = "#062B91"
PANEL_HOVER = "#0A369F"
PANEL_BORDER = "#1B55D8"
WHITE = "#FFFFFF"
MUTED = "#D6E4FF"
CYAN = "#28C7FF"
GREEN_ACCENT = "#00D6A0"
PURPLE = "#8157FF"
ORANGE_ACCENT = "#FF922E"
RED_ACCENT = "#FF3658"


# Main window
root = tk.Tk()
root.title(f"WinCleaner v{APP_VERSION}")
root.configure(bg=BLUE)
root.resizable(False, False)

# Set the window icon. PyInstaller's --icon option sets the executable icon.
if os.path.isfile(ICO_PATH):
    try:
        root.iconbitmap(default=ICO_PATH)
    except (tk.TclError, OSError) as error:
        print(f"Could not load WinCleaner icon: {error}")


# Outer window frame
shell = tk.Frame(
    root,
    bg=BLUE_DEEP,
    highlightbackground="#2671FF",
    highlightthickness=1,
)
shell.pack(fill="both", expand=True, padx=10, pady=10)


# Main layout
sidebar = tk.Frame(shell, bg=BLUE_DEEP, width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

main = tk.Frame(shell, bg=BLUE)
main.pack(side="left", fill="both", expand=True)


# Sidebar brand
brand = tk.Frame(sidebar, bg=BLUE_DEEP)
brand.pack(fill="x", padx=20, pady=(24, 26))

tk.Label(
    brand,
    text="✦  WinCleaner",
    font=("Segoe UI", 19, "bold"),
    bg=BLUE_DEEP,
    fg=WHITE,
).pack(anchor="w")

tk.Label(
    brand,
    text="CLEAN  •  OPTIMIZE  •  KEEP IT FAST",
    font=("Segoe UI", 7, "bold"),
    bg=BLUE_DEEP,
    fg="#9BCBFF",
).pack(anchor="w", pady=(7, 0))


# Sidebar navigation
def nav_item(label, icon, command=None, active=False):
    bg = "#0755D9" if active else BLUE_DEEP
    fg = WHITE if active else MUTED

    item = tk.Frame(sidebar, bg=bg, cursor="hand2")
    item.pack(fill="x", padx=10, pady=4)

    text = tk.Label(
        item,
        text=f"  {icon}    {label}",
        anchor="w",
        font=("Segoe UI", 10, "bold" if active else "normal"),
        bg=bg,
        fg=fg,
        padx=8,
        pady=12,
        cursor="hand2",
    )
    text.pack(fill="x")

    if command:
        item.bind("<Button-1>", lambda _event: command())
        text.bind("<Button-1>", lambda _event: command())

    return item


nav_item("Home", "⌂", active=True)

nav_item(
    "Settings",
    "⚙",
    command=lambda: messagebox.showinfo(
        "Settings",
        "Settings will be available in a future version.",
        parent=root,
    ),
)

nav_item(
    "About",
    "ⓘ",
    command=lambda: messagebox.showinfo(
        "About WinCleaner",
        f"Windows System Cleaner\n"
        f"Version: {APP_VERSION}\n"
        "Developer: Windel Navales",
        parent=root,
    ),
)

nav_item(
    "Website",
    "◎",
    command=lambda: webbrowser.open(WEBSITE_URL),
)

spacer = tk.Frame(sidebar, bg=BLUE_DEEP)
spacer.pack(fill="both", expand=True)

tk.Label(
    sidebar,
    text="▰  Windows",
    font=("Segoe UI", 13, "bold"),
    bg=BLUE_DEEP,
    fg="#35A8FF",
).pack(anchor="w", padx=22, pady=(0, 4))

tk.Label(
    sidebar,
    text="A Cleaner PC\nA Faster You",
    font=("Segoe UI", 10),
    bg=BLUE_DEEP,
    fg="#9BCBFF",
    justify="left",
).pack(anchor="w", padx=22, pady=(0, 22))


# Main header
header = tk.Frame(main, bg=BLUE)
header.pack(fill="x", padx=26, pady=(24, 18))

header_text = tk.Frame(header, bg=BLUE)
header_text.pack(side="left", fill="x", expand=True)

tk.Label(
    header_text,
    text="Welcome to WinCleaner",
    font=("Segoe UI", 23, "bold"),
    bg=BLUE,
    fg=WHITE,
).pack(anchor="w")

tk.Label(
    header_text,
    text="Keep your Windows system clean, organized and running at its best.",
    font=("Segoe UI", 10),
    bg=BLUE,
    fg=MUTED,
).pack(anchor="w", pady=(5, 0))

version_box = tk.Frame(
    header,
    bg=BLUE_DEEP,
    highlightbackground=PANEL_BORDER,
    highlightthickness=1,
)
version_box.pack(side="right", padx=(14, 0), ipadx=14, ipady=10)

tk.Label(
    version_box,
    text=f"Version  {APP_VERSION}",
    font=("Segoe UI", 10, "bold"),
    bg=BLUE_DEEP,
    fg=WHITE,
).pack(anchor="w", padx=2)

tk.Label(
    version_box,
    text="●  Update check enabled",
    font=("Segoe UI", 8),
    bg=BLUE_DEEP,
    fg=GREEN_ACCENT,
).pack(anchor="w", padx=2, pady=(4, 0))


# Cleanup section heading
section = tk.Frame(main, bg=BLUE)
section.pack(fill="x", padx=28, pady=(0, 12))

tk.Label(
    section,
    text="✦   CLEANUP ACTIONS",
    font=("Segoe UI", 10, "bold"),
    bg=BLUE,
    fg=WHITE,
).pack(side="left")

tk.Frame(
    section,
    bg="#2A69F0",
    height=1,
).pack(side="left", fill="x", expand=True, padx=(14, 0), pady=7)


# Cleanup actions
actions = [
    (
        "▤",
        "Clear Temporary Files",
        "Removes junk from %TEMP%",
        CYAN,
        lambda: clear_temp(parent=root),
    ),
    (
        "▣",
        "Clear Recent Items",
        "Cleans Recent files list",
        GREEN_ACCENT,
        lambda: clear_recent(parent=root),
    ),
    (
        "♻",
        "Empty Recycle Bin",
        "Permanently deletes recycled files",
        RED_ACCENT,
        lambda: empty_recycle_bin(parent=root),
    ),
    (
        "▧",
        "Clear Thumbnail Cache",
        "Removes cached thumbnails to free up space",
        PURPLE,
        lambda: clear_thumbnail_cache(parent=root),
    ),
    (
        "⌕",
        "Find Duplicate Files",
        "Detect and remove identical files in any folder",
        ORANGE_ACCENT,
        lambda: open_duplicate_finder(root),
    ),
]

cards = tk.Frame(main, bg=BLUE)
cards.pack(fill="both", expand=True, padx=26)

for symbol, title, subtitle, color, action in actions:
    card = tk.Frame(
        cards,
        bg=PANEL,
        highlightbackground=color,
        highlightthickness=1,
    )
    card.pack(fill="x", pady=5)

    icon_box = tk.Frame(card, bg=color, width=58, height=58)
    icon_box.pack(side="left", padx=(14, 14), pady=10)
    icon_box.pack_propagate(False)

    tk.Label(
        icon_box,
        text=symbol,
        font=("Segoe UI Symbol", 24, "bold"),
        bg=color,
        fg=WHITE,
    ).place(relx=0.5, rely=0.5, anchor="center")

    description = tk.Frame(card, bg=PANEL)
    description.pack(side="left", fill="both", expand=True, pady=10)

    tk.Label(
        description,
        text=title,
        font=("Segoe UI", 12, "bold"),
        bg=PANEL,
        fg=WHITE,
    ).pack(anchor="w")

    tk.Label(
        description,
        text=subtitle,
        font=("Segoe UI", 9),
        bg=PANEL,
        fg=MUTED,
    ).pack(anchor="w", pady=(4, 0))

    button = tk.Button(
        card,
        text="Start   →",
        command=action,
        font=("Segoe UI", 9, "bold"),
        bg=color,
        fg=WHITE,
        activebackground=color,
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=18,
        pady=9,
        highlightthickness=0,
    )
    button.pack(side="right", padx=14, pady=14)

    button.bind(
        "<Enter>",
        lambda _event, b=button: b.config(relief="raised"),
    )
    button.bind(
        "<Leave>",
        lambda _event, b=button: b.config(relief="flat"),
    )


# Status badges
badges = tk.Frame(main, bg=BLUE)
badges.pack(fill="x", padx=26, pady=(10, 12))

for icon, label, color in [
    ("◆", "Safe — no system files touched", CYAN),
    ("ϟ", "Instant cleanup, no reboot needed", PURPLE),
]:
    badge = tk.Frame(
        badges,
        bg=BLUE_DEEP,
        highlightbackground=color,
        highlightthickness=1,
    )
    badge.pack(side="left", padx=(0, 8))

    tk.Label(
        badge,
        text=f"{icon}  {label}",
        font=("Segoe UI", 8, "bold"),
        bg=BLUE_DEEP,
        fg=WHITE,
        padx=10,
        pady=7,
    ).pack()


# Footer
footer = tk.Frame(shell, bg="#00154F")
footer.pack(side="bottom", fill="x")

tk.Label(
    footer,
    text=f"Windows System Cleaner   •   v{APP_VERSION}",
    font=("Segoe UI", 8),
    bg="#00154F",
    fg=WHITE,
).pack(side="left", padx=(18, 12), pady=12)

tk.Label(
    footer,
    text="│   Developer: Windel Navales",
    font=("Segoe UI", 8),
    bg="#00154F",
    fg="#9BCBFF",
).pack(side="left", padx=(0, 12), pady=12)

website = tk.Label(
    footer,
    text="◎  wincleaner-web.vercel.app",
    font=("Segoe UI", 8, "bold"),
    bg="#00154F",
    fg=CYAN,
    cursor="hand2",
)
website.pack(side="left", padx=4, pady=12)
website.bind(
    "<Button-1>",
    lambda _event: webbrowser.open(WEBSITE_URL),
)

close_button = tk.Button(
    footer,
    text="✕  Close",
    command=root.destroy,
    font=("Segoe UI", 9, "bold"),
    bg=RED_ACCENT,
    fg=WHITE,
    activebackground="#D91F43",
    activeforeground=WHITE,
    relief="flat",
    bd=0,
    cursor="hand2",
    padx=18,
    pady=7,
)
close_button.pack(side="right", padx=14, pady=7)


# Size and center the window
root.update_idletasks()

width = max(root.winfo_reqwidth(), 1000)
height = max(root.winfo_reqheight(), 700)

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

x = max(0, (screen_w - width) // 2)
y = max(0, (screen_h - height) // 2)

root.geometry(f"{width}x{height}+{x}+{y}")
root.minsize(1000, 700)


# Check for updates after the interface appears.
root.after(1000, lambda: check_for_updates(root))


if __name__ == "__main__":
    root.mainloop()
