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


APP_VERSION = "1.5.0"
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


# Footer (packed first so it always spans the full window width)
footer = tk.Frame(shell, bg="#00154F")
footer.pack(side="bottom", fill="x")


# Main layout
sidebar = tk.Frame(shell, bg=BLUE_DEEP, width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

main = tk.Frame(shell, bg=BLUE)
main.pack(side="left", fill="both", expand=True)

# Views live inside this container; only one is visible at a time.
content = tk.Frame(main, bg=BLUE)
content.pack(fill="both", expand=True)

home_view = tk.Frame(content, bg=BLUE)
about_view = tk.Frame(content, bg=BLUE)

views = {"home": home_view, "about": about_view}
nav_items = {}


# Sidebar brand
brand = tk.Frame(sidebar, bg=BLUE_DEEP)
brand.pack(fill="x", padx=20, pady=(24, 26))

tk.Label(
    brand,
    text="WinCleaner",
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


# View switching
def set_active(key):
    for name, (item, text) in nav_items.items():
        active = name == key
        bg = "#0755D9" if active else BLUE_DEEP
        fg = WHITE if active else MUTED
        item.config(bg=bg)
        text.config(
            bg=bg,
            fg=fg,
            font=("Segoe UI", 10, "bold" if active else "normal"),
        )


def show_view(name):
    for view in views.values():
        view.pack_forget()
    views[name].pack(fill="both", expand=True)
    set_active(name)


# Sidebar navigation
def nav_item(label, icon, command=None, key=None):
    item = tk.Frame(sidebar, bg=BLUE_DEEP, cursor="hand2")
    item.pack(fill="x", padx=10, pady=4)

    text = tk.Label(
        item,
        text=f"  {icon}    {label}",
        anchor="w",
        font=("Segoe UI", 10),
        bg=BLUE_DEEP,
        fg=MUTED,
        padx=8,
        pady=12,
        cursor="hand2",
    )
    text.pack(fill="x")

    if key:
        nav_items[key] = (item, text)

    if command:
        item.bind("<Button-1>", lambda _event: command())
        text.bind("<Button-1>", lambda _event: command())

    return item


nav_item("Home", "⌂", command=lambda: show_view("home"), key="home")

nav_item(
    "Settings",
    "⚙",
    command=lambda: messagebox.showinfo(
        "Settings",
        "Settings will be available in a future version.",
        parent=root,
    ),
)

nav_item("About", "ⓘ", command=lambda: show_view("about"), key="about")

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


# =====================================================================
# HOME VIEW
# =====================================================================

# Main header
header = tk.Frame(home_view, bg=BLUE)
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
section = tk.Frame(home_view, bg=BLUE)
section.pack(fill="x", padx=28, pady=(0, 12))

tk.Label(
    section,
    text="CLEANUP ACTIONS",
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

cards = tk.Frame(home_view, bg=BLUE)
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
badges = tk.Frame(home_view, bg=BLUE)
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


# =====================================================================
# ABOUT VIEW (shown in the right-side panel)
# =====================================================================

about_header = tk.Frame(about_view, bg=BLUE)
about_header.pack(fill="x", padx=26, pady=(24, 14))

about_header_text = tk.Frame(about_header, bg=BLUE)
about_header_text.pack(side="left", fill="x", expand=True)

tk.Label(
    about_header_text,
    text="About WinCleaner",
    font=("Segoe UI", 23, "bold"),
    bg=BLUE,
    fg=WHITE,
).pack(anchor="w")

tk.Label(
    about_header_text,
    text="Windows System Cleaner",
    font=("Segoe UI", 10),
    bg=BLUE,
    fg=MUTED,
).pack(anchor="w", pady=(5, 0))

about_info_box = tk.Frame(
    about_header,
    bg=BLUE_DEEP,
    highlightbackground=PANEL_BORDER,
    highlightthickness=1,
)
about_info_box.pack(side="right", padx=(14, 0), ipadx=14, ipady=10)

tk.Label(
    about_info_box,
    text=f"Version  {APP_VERSION}",
    font=("Segoe UI", 10, "bold"),
    bg=BLUE_DEEP,
    fg=WHITE,
).pack(anchor="w", padx=2)

tk.Label(
    about_info_box,
    text="Developer: Windel Navales",
    font=("Segoe UI", 8),
    bg=BLUE_DEEP,
    fg="#9BCBFF",
).pack(anchor="w", padx=2, pady=(4, 0))

about_cards = tk.Frame(about_view, bg=BLUE)
about_cards.pack(fill="both", expand=True, padx=26)

ABOUT_WRAP = 610


def about_card(title, color, body):
    card = tk.Frame(
        about_cards,
        bg=PANEL,
        highlightbackground=color,
        highlightthickness=1,
    )
    card.pack(fill="x", pady=5)

    tk.Frame(card, bg=color, width=5).pack(side="left", fill="y")

    inner = tk.Frame(card, bg=PANEL)
    inner.pack(side="left", fill="both", expand=True, padx=14, pady=10)

    tk.Label(
        inner,
        text=title,
        font=("Segoe UI", 10, "bold"),
        bg=PANEL,
        fg=color,
    ).pack(anchor="w")

    tk.Label(
        inner,
        text=body,
        font=("Segoe UI", 9),
        bg=PANEL,
        fg=WHITE,
        justify="left",
        wraplength=ABOUT_WRAP,
    ).pack(anchor="w", pady=(5, 0))


about_card(
    "ABOUT THIS APPLICATION",
    CYAN,
    "WinCleaner is a utility designed to help users maintain and "
    "organize their Windows computers. It focuses on Windows cleaning, "
    "so you no longer have to deal with the hassle of typing CMD "
    "commands or hunting down the specific folder paths to clean. "
    "Everything is just a click away.",
)

about_card(
    "WHY WINCLEANER?",
    GREEN_ACCENT,
    "•  No command prompt needed — skip memorizing and typing cleanup "
    "commands.\n"
    "•  No digging for paths — it already knows where temp files, "
    "recent items, thumbnail caches and the Recycle Bin live.\n"
    "•  One simple interface for every common cleanup task.",
)

about_card(
    "SAFETY & SECURITY",
    PURPLE,
    "•  Designed for legitimate system maintenance.\n"
    "•  Does not intentionally exploit system vulnerabilities.\n"
    "•  Does not install malware or spyware.\n"
    "•  Does not perform unauthorized access or attacks.\n"
    "•  Cleanup actions target only the specific files and locations "
    "described by each feature.",
)

about_card(
    "IMPORTANT",
    ORANGE_ACCENT,
    "Some cleanup actions permanently delete files. Review each "
    "action carefully before proceeding.",
)

about_footer = tk.Frame(about_view, bg=BLUE)
about_footer.pack(fill="x", padx=26, pady=(8, 12))

tk.Button(
    about_footer,
    text="◎  Visit Website",
    command=lambda: webbrowser.open(WEBSITE_URL),
    font=("Segoe UI", 9, "bold"),
    bg=CYAN,
    fg=WHITE,
    activebackground=CYAN,
    activeforeground=WHITE,
    relief="flat",
    bd=0,
    cursor="hand2",
    padx=18,
    pady=8,
).pack(side="left")

tk.Button(
    about_footer,
    text="←  Back to Home",
    command=lambda: show_view("home"),
    font=("Segoe UI", 9, "bold"),
    bg=BLUE_DEEP,
    fg=WHITE,
    activebackground=BLUE_DEEP,
    activeforeground=WHITE,
    relief="flat",
    bd=0,
    cursor="hand2",
    padx=18,
    pady=8,
).pack(side="left", padx=(8, 0))


# Footer contents
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


# Start on the Home view. Build the About view once so the window is
# sized to fit the taller of the two.
show_view("about")
root.update_idletasks()
about_req_h = root.winfo_reqheight()
show_view("home")
root.update_idletasks()


# Size and center the window
width = max(root.winfo_reqwidth(), 1000)
height = max(root.winfo_reqheight(), about_req_h, 700)

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

x = max(0, (screen_w - width) // 2)
y = max(0, (screen_h - height) // 2)

root.geometry(f"{width}x{height}+{x}+{y}")
root.minsize(width, height)


# Check for updates after the interface appears.
root.after(1000, lambda: check_for_updates(root, APP_VERSION))


if __name__ == "__main__":
    root.mainloop()