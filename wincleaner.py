import os
import shutil
import tempfile
import ctypes
import tkinter as tk
from tkinter import messagebox


# ==============================
# Windows System Cleaner
# Developer: Windel Navales
# ==============================


ICO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wincleaner.ico")

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = "#F0F4F8"          # cool light-grey canvas
CARD        = "#FFFFFF"          # white card
BORDER      = "#DDE3EC"          # subtle card border
HEADER_BG   = "#0A2350"          # deep navy header
ACCENT      = "#1A73E8"          # primary blue
ACCENT_H    = "#1558B0"          # hover blue
GREEN       = "#1E8A4C"
GREEN_H     = "#166B3C"
RED         = "#C0392B"
RED_H       = "#962D22"
TEXT_LIGHT  = "#FFFFFF"
TEXT_DARK   = "#1A1F36"
TEXT_MUTED  = "#6B7280"
FOOTER_BG   = "#E8EDF4"


# ── Helpers ────────────────────────────────────────────────────────────────────

def clear_folder(folder):
    deleted = skipped = 0
    if not os.path.exists(folder):
        return deleted, skipped
    for item in os.listdir(folder):
        path = os.path.join(folder, item)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)
            deleted += 1
        except Exception:
            skipped += 1
    return deleted, skipped


def clear_temp():
    deleted, skipped = clear_folder(tempfile.gettempdir())
    messagebox.showinfo(
        "Temp Files Cleaned",
        f"Temporary files cleaned.\n\n"
        f"  ✔  Deleted : {deleted}\n"
        f"  –   Skipped : {skipped}"
    )

def clear_recent():
    folder = os.path.join(
        os.environ["APPDATA"], "Microsoft", "Windows", "Recent"
    )
    deleted, skipped = clear_folder(folder)
    messagebox.showinfo(
        "Recent Items Cleared",
        f"Recent items cleared.\n\n"
        f"  ✔  Deleted : {deleted}\n"
        f"  –   Skipped : {skipped}"
    )

def empty_recycle_bin():
    flags = 0x00000001 | 0x00000002 | 0x00000004
    result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
    if result == 0:
        messagebox.showinfo("Recycle Bin Emptied", "Recycle Bin has been emptied successfully.")
    else:
        messagebox.showerror("Error", "Unable to empty the Recycle Bin.")


# ── Button factory ─────────────────────────────────────────────────────────────

def make_button(parent, icon, label, sublabel, color, hover_color, command):
    frame = tk.Frame(parent, bg=CARD, cursor="hand2")

    # Left colour strip
    strip = tk.Frame(frame, bg=color, width=5)
    strip.pack(side="left", fill="y")

    # Icon badge
    badge = tk.Frame(frame, bg=color, width=54, height=54)
    badge.pack(side="left", padx=(14, 10), pady=12)
    badge.pack_propagate(False)
    icon_lbl = tk.Label(badge, text=icon, font=("Segoe UI Emoji", 20),
                        bg=color, fg=TEXT_LIGHT)
    icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Text block
    text_frame = tk.Frame(frame, bg=CARD)
    text_frame.pack(side="left", fill="both", expand=True, pady=12)
    tk.Label(text_frame, text=label, font=("Segoe UI", 11, "bold"),
             bg=CARD, fg=TEXT_DARK, anchor="w").pack(fill="x")
    tk.Label(text_frame, text=sublabel, font=("Segoe UI", 8),
             bg=CARD, fg=TEXT_MUTED, anchor="w").pack(fill="x")

    # Arrow indicator
    arrow = tk.Label(frame, text="›", font=("Segoe UI", 18),
                     bg=CARD, fg=TEXT_MUTED)
    arrow.pack(side="right", padx=14)

    # Hover behaviour
    def on_enter(e):
        for w in (frame, text_frame, arrow):
            w.config(bg="#F5F9FF")
        badge.config(bg=hover_color)
        icon_lbl.config(bg=hover_color)
        strip.config(bg=hover_color)

    def on_leave(e):
        for w in (frame, text_frame, arrow):
            w.config(bg=CARD)
        badge.config(bg=color)
        icon_lbl.config(bg=color)
        strip.config(bg=color)

    def on_click(e):
        command()

    for w in (frame, strip, badge, icon_lbl, text_frame, arrow):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)

    return frame


# ── Root window ────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("WinCleaner")
root.geometry("480x490")
root.resizable(False, False)
root.configure(bg=BG)

# Window icon
if os.path.exists(ICO_PATH):
    try:
        root.iconbitmap(ICO_PATH)
    except Exception:
        pass


# ── Header ─────────────────────────────────────────────────────────────────────

header = tk.Frame(root, bg=HEADER_BG, height=100)
header.pack(fill="x")
header.pack_propagate(False)

title_frame = tk.Frame(header, bg=HEADER_BG)
title_frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(
    title_frame,
    text="⚙  WinCleaner",
    font=("Segoe UI", 20, "bold"),
    bg=HEADER_BG,
    fg=TEXT_LIGHT
).pack()

tk.Label(
    title_frame,
    text="Windows System Cleanup Utility",
    font=("Segoe UI", 9),
    bg=HEADER_BG,
    fg="#7BAAF7"
).pack()


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
             ACCENT,  ACCENT_H,  clear_temp),
    ("📄",  "Clear Recent Items",
             "Cleans Recent files list",
             GREEN,   GREEN_H,   clear_recent),
    ("♻",  "Empty Recycle Bin",
             "Permanently deletes recycled files",
             RED,     RED_H,     empty_recycle_bin),
]

for i, (icon, label, sub, col, hov, cmd) in enumerate(buttons_data):
    btn = make_button(card, icon, label, sub, col, hov, cmd)
    btn.pack(fill="x")
    if i < len(buttons_data) - 1:
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=12)


# ── Status strip ───────────────────────────────────────────────────────────────

status = tk.Frame(root, bg=BG)
status.pack(fill="x", padx=20, pady=(14, 0))

info_items = [
    ("🔒", "Safe — no system files touched"),
    ("⚡", "Instant cleanup, no reboot needed"),
]
for icon, text in info_items:
    pill = tk.Frame(status, bg="#E1ECFF", padx=10, pady=4)
    pill.pack(side="left", padx=(0, 8))
    tk.Label(pill, text=f"{icon}  {text}", font=("Segoe UI", 8),
             bg="#E1ECFF", fg="#1A4FA0").pack()


# ── Footer ─────────────────────────────────────────────────────────────────────

footer = tk.Frame(root, bg=FOOTER_BG)
footer.pack(side="bottom", fill="x")

tk.Frame(footer, bg=BORDER, height=1).pack(fill="x")

footer_inner = tk.Frame(footer, bg=FOOTER_BG)
footer_inner.pack(fill="x", padx=20, pady=10)

tk.Label(
    footer_inner,
    text="Windows System Cleaner  •  v1.0",
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
).pack(side="right")


root.mainloop()