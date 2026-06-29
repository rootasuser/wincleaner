"""
Shared UI components and styling constants for WinCleaner.
Author: Windel Navales
"""

import tkinter as tk
from typing import Literal, Callable, Optional

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = "#F0F4F8"
CARD        = "#FFFFFF"
BORDER      = "#DDE3EC"
HEADER_BG   = "#0A2350"
ACCENT      = "#1A73E8"
ACCENT_H    = "#1558B0"
GREEN       = "#1E8A4C"
GREEN_H     = "#166B3C"
RED         = "#C0392B"
RED_H       = "#962D22"
ORANGE      = "#D97706"
ORANGE_H    = "#B45309"
PURPLE      = "#6B21A8"
PURPLE_H    = "#581C87"
TEXT_LIGHT  = "#FFFFFF"
TEXT_DARK   = "#1A1F36"
TEXT_MUTED  = "#6B7280"
FOOTER_BG   = "#E8EDF4"


def make_button(parent: tk.Widget,
                icon: str,
                label: str,
                sublabel: str,
                color: str,
                hover_color: str,
                command: Callable) -> tk.Frame:
    """
    Create a consistent card-style button with an icon, label, sublabel,
    colored accent strip, and hover effects.
    """
    frame = tk.Frame(parent, bg=CARD, cursor="hand2")

    strip = tk.Frame(frame, bg=color, width=5)
    strip.pack(side="left", fill="y")

    badge = tk.Frame(frame, bg=color, width=54, height=54)
    badge.pack(side="left", padx=(14, 10), pady=12)
    badge.pack_propagate(False)
    icon_lbl = tk.Label(badge, text=icon, font=("Segoe UI Emoji", 20),
                        bg=color, fg=TEXT_LIGHT)
    icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

    text_frame = tk.Frame(frame, bg=CARD)
    text_frame.pack(side="left", fill="both", expand=True, pady=12)
    tk.Label(text_frame, text=label, font=("Segoe UI", 11, "bold"),
             bg=CARD, fg=TEXT_DARK, anchor="w").pack(fill="x")
    tk.Label(text_frame, text=sublabel, font=("Segoe UI", 8),
             bg=CARD, fg=TEXT_MUTED, anchor="w").pack(fill="x")

    arrow = tk.Label(frame, text="›", font=("Segoe UI", 18),
                     bg=CARD, fg=TEXT_MUTED)
    arrow.pack(side="right", padx=14)

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


def styled_btn(parent: tk.Widget,
               text: str,
               color: str,
               hover: str,
               command: Callable,
               side: Literal["left", "right", "top", "bottom"] = "left") -> tk.Label:
    """
    Create a small rectangular label-as-button with hover color change.
    """
    b = tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                 bg=color, fg=TEXT_LIGHT, padx=12, pady=6, cursor="hand2")
    b.pack(side=side, padx=(0, 8))
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    b.bind("<Button-1>", lambda e: command())
    return b


def format_size(size_bytes: float) -> str:
    """Convert byte count to human-readable string (B, KB, MB, GB, TB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def section_header(parent: tk.Widget, text: str) -> None:
    """Draw a section label with a horizontal line."""
    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="x")
    tk.Label(frame, text=text, font=("Segoe UI", 8, "bold"),
             bg=BG, fg=TEXT_MUTED).pack(side="left")
    tk.Frame(frame, bg=BORDER, height=1).pack(
        side="left", fill="x", expand=True, padx=(10, 0), pady=6)