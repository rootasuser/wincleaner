"""
Windows System Cleaner
Author: Windel Navales
"""

import os
import tkinter as tk
import webbrowser

from ui_components import (
    BG, CARD, BORDER, HEADER_BG, FOOTER_BG,
    ACCENT, ACCENT_H, GREEN, GREEN_H, RED, RED_H, ORANGE, ORANGE_H,
    TEXT_LIGHT, TEXT_DARK, TEXT_MUTED,
    make_button
)
from recycle_bin    import empty_recycle_bin
from temp_cleaner   import clear_temp
from recent_cleaner import clear_recent
from duplicate_finder import open_duplicate_finder
from thumbnail_cache_cleaner import clear_thumbnail_cache


# ── Paths ──────────────────────────────────────────────────────────────────────
ICO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wincleaner.ico")


# ── Build window ───────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("WinCleaner")
root.resizable(False, False)
root.configure(bg=BG)

if os.path.exists(ICO_PATH):
    try:
        root.iconbitmap(ICO_PATH)
    except Exception:
        pass


# ── Section label ──────────────────────────────────────────────────────────────
section_frame = tk.Frame(root, bg=BG)
section_frame.pack(fill="x", padx=20, pady=(18, 6))

tk.Label(
    section_frame,
    text="CLEANUP ACTIONS",
    font=("Segoe UI", 8, "bold"),
    bg=BG,
    fg=TEXT_MUTED
).pack(side="left")

tk.Frame(section_frame, bg=BORDER, height=1).pack(
    side="left", fill="x", expand=True, padx=(10, 0), pady=6
)


# ── Card container ─────────────────────────────────────────────────────────────
card_outer = tk.Frame(root, bg=BG, padx=20)
card_outer.pack(fill="x")

card = tk.Frame(card_outer, bg=CARD, relief="flat",
                highlightbackground=BORDER, highlightthickness=1)
card.pack(fill="x")

buttons_data = [
    ("🗑",  "Clear Temporary Files",
             "Removes junk from %TEMP%",
             ACCENT,  ACCENT_H,
             lambda: clear_temp(parent=root)),

    ("📄",  "Clear Recent Items",
             "Cleans Recent files list",
             GREEN,   GREEN_H,
             lambda: clear_recent(parent=root)),

    ("♻",  "Empty Recycle Bin",
             "Permanently deletes recycled files",
             RED,     RED_H,
             lambda: empty_recycle_bin(parent=root)),

    ("🖼",  "Clear Thumbnail Cache",
            "Removes cached thumbnails to free up space",
            "#7B58EE", "#6A5ACD",
            lambda: clear_thumbnail_cache(parent=root)),

    ("🔍",  "Find Duplicate Files",
             "Detect & remove identical files in any folder",
             ORANGE,  ORANGE_H,
             lambda: open_duplicate_finder(root)),
]

for i, (icon, label, sub, col, hov, cmd) in enumerate(buttons_data):
    btn = make_button(card, icon, label, sub, col, hov, cmd)
    btn.pack(fill="x")
    if i < len(buttons_data) - 1:
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=12)


# ── Footer ─────────────────────────────────────────────────────────────────────
footer = tk.Frame(root, bg=FOOTER_BG)
footer.pack(side="bottom", fill="x")

tk.Frame(footer, bg=BORDER, height=1).pack(fill="x")

footer_inner = tk.Frame(footer, bg=FOOTER_BG)
footer_inner.pack(fill="x", padx=16, pady=10)

tk.Label(
    footer_inner,
    text="Windows System Cleaner  •  v1.3",
    font=("Segoe UI", 8, "bold"),
    bg=FOOTER_BG,
    fg=TEXT_DARK
).pack(side="left")

tk.Label(
    footer_inner,
    text="Developer: Windel Navales",
    font=("Segoe UI", 8),
    bg=FOOTER_BG,
    fg=TEXT_MUTED
).pack(side="left", padx=(8, 0))

# ── Website link ──────────────────────────────────────────────────────────────
site_link = tk.Label(
    footer_inner,
    text="🌐  windelnavales.com",
    font=("Segoe UI", 8, "bold"),
    bg=FOOTER_BG,
    fg=ACCENT,
    cursor="hand2"
)
site_link.pack(side="left", padx=(8, 0))
site_link.bind("<Enter>", lambda e: site_link.config(fg=ACCENT_H))
site_link.bind("<Leave>", lambda e: site_link.config(fg=ACCENT))
site_link.bind("<Button-1>", lambda e: webbrowser.open("https://wincleaner-web.vercel.app"))
# ───────────────────────────────────────────────────────────────────────────────

close_btn = tk.Label(
    footer_inner,
    text="✕  Close",
    font=("Segoe UI", 8, "bold"),
    bg=RED, fg=TEXT_LIGHT,
    padx=10, pady=4,
    cursor="hand2"
)
close_btn.pack(side="right")
close_btn.bind("<Enter>", lambda e: close_btn.config(bg=RED_H))
close_btn.bind("<Leave>", lambda e: close_btn.config(bg=RED))
close_btn.bind("<Button-1>", lambda e: root.destroy())


# ── Status strip ───────────────────────────────────────────────────────────────
status = tk.Frame(root, bg=BG)
status.pack(side="bottom", fill="x", padx=16, pady=(0, 10))

info_items = [
    ("🔒", "Safe — no system files touched"),
    ("⚡", "Instant cleanup, no reboot needed"),
]
for icon, text in info_items:
    pill = tk.Frame(status, bg="#E1ECFF", padx=10, pady=4)
    pill.pack(side="left", padx=(0, 8))
    tk.Label(pill, text=f"{icon}  {text}", font=("Segoe UI", 8),
             bg="#E1ECFF", fg="#1A4FA0").pack()


# ── Final auto-sizing & centering ──────────────────────────────────────────────
root.update_idletasks()

MIN_W = 480
MIN_H = 420

w = max(root.winfo_reqwidth(), MIN_W)
h = max(root.winfo_reqheight(), MIN_H)

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x = (sw - w) // 2
y = (sh - h) // 2

root.geometry(f"{w}x{h}+{x}+{y}")
root.minsize(MIN_W, MIN_H)


# ── Launch ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root.mainloop()