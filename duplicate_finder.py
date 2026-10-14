"""
Duplicate File Finder window for WinCleaner.
Author: Windel Navales

Blue theme that matches the main WinCleaner window.
Self-contained: it does not depend on ui_components.
"""

import os
import hashlib
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from collections import defaultdict
from typing import Optional


# ── Colors (same palette as the main window) ──────────────────────────────────
BLUE = "#003DE3"
BLUE_DEEP = "#001B66"
PANEL = "#062B91"
PANEL_BORDER = "#1B55D8"
FOOTER_BG = "#00154F"
LINE = "#2A69F0"
WHITE = "#FFFFFF"
MUTED = "#D6E4FF"
SKY = "#9BCBFF"
CYAN = "#28C7FF"
CYAN_H = "#12B0E8"
GREEN = "#00D6A0"
PURPLE = "#8157FF"
PURPLE_H = "#6A43E0"
ORANGE = "#FF922E"
RED = "#FF3658"
RED_H = "#D91F43"
DISABLED_BG = "#4A6FD6"

PLACEHOLDER = "Search files by name..."

# extension -> badge color
BADGE_COLORS = {
    **{e: GREEN for e in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")},
    **{e: PURPLE for e in (".mp4", ".avi", ".mkv", ".mov", ".wmv")},
    **{e: ORANGE for e in (".mp3", ".wav", ".flac", ".aac", ".m4a")},
    **{e: CYAN for e in (".pdf", ".doc", ".docx", ".xls", ".xlsx",
                         ".ppt", ".pptx", ".txt")},
    **{e: RED for e in (".zip", ".rar", ".7z", ".iso")},
}
DEFAULT_BADGE = "#5B7FD6"


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_size(size: float) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def get_file_hash(filepath: str, block_size: int = 65536) -> Optional[str]:
    """Return MD5 hash of a file, or None on error."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            buf = f.read(block_size)
            while buf:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None


def find_duplicates(folders: list, on_progress=None) -> dict:
    """
    Scan one or more folders recursively.

    Returns:
        { md5_hash: [filepath, filepath, ...] }
    Only groups with 2+ files are included.
    """
    hash_map = defaultdict(list)
    scanned = 0
    for folder in folders:
        for dirpath, _, filenames in os.walk(folder):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                if os.path.isfile(fpath):
                    h = get_file_hash(fpath)
                    if h:
                        hash_map[h].append(fpath)
                    scanned += 1
                    if on_progress:
                        on_progress(scanned, fpath)
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


def make_button(parent, text, bg, hover, command, side="left", padx=0):
    """Flat button with hover and a proper disabled look."""
    btn = tk.Button(
        parent, text=text, command=command,
        font=("Segoe UI", 9, "bold"),
        bg=bg, fg=WHITE,
        activebackground=hover, activeforeground=WHITE,
        disabledforeground="#C9D8FF",
        relief="flat", bd=0, cursor="hand2",
        padx=18, pady=9, highlightthickness=0,
    )
    btn.base_bg = bg
    btn.hover_bg = hover
    btn.bind("<Enter>", lambda e: btn.config(bg=btn.hover_bg)
             if str(btn["state"]) == "normal" else None)
    btn.bind("<Leave>", lambda e: btn.config(bg=btn.base_bg)
             if str(btn["state"]) == "normal" else None)
    btn.pack(side=side, padx=padx)
    return btn


def set_enabled(btn, enabled: bool):
    if enabled:
        btn.config(state="normal", bg=btn.base_bg, cursor="hand2")
    else:
        btn.config(state="disabled", bg=DISABLED_BG, cursor="arrow")


def section_heading(parent, text, pady=(16, 8)):
    row = tk.Frame(parent, bg=BLUE)
    row.pack(fill="x", pady=pady)
    tk.Label(row, text=text, font=("Segoe UI", 9, "bold"),
             bg=BLUE, fg=WHITE).pack(side="left")
    tk.Frame(row, bg=LINE, height=1).pack(
        side="left", fill="x", expand=True, padx=(12, 0), pady=6)
    return row


# ── Window ────────────────────────────────────────────────────────────────────

def open_duplicate_finder(root_window: tk.Tk) -> None:
    """Create and open the Duplicate File Finder toplevel window."""
    win = tk.Toplevel(root_window)
    win.title("Duplicate File Finder")
    win.configure(bg=BLUE)
    win.minsize(780, 580)

    # Size and center over the main window
    width = 920
    height = min(740, win.winfo_screenheight() - 80)
    x = root_window.winfo_rootx() + (root_window.winfo_width() - width) // 2
    y = root_window.winfo_rooty() + (root_window.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    try:
        if root_window.iconbitmap():
            win.iconbitmap(root_window.iconbitmap())
    except Exception:
        pass

    # ── State ────────────────────────────────────────────────────────────────
    folders = []              # folders to scan
    duplicates = {}           # hash -> [paths]   (full scan result)
    filtered_duplicates = {}  # hash -> [paths]   (after search filter)
    check_vars = {}           # path -> BooleanVar
    size_map = {}             # path -> bytes
    scanning = [False]
    scanned_once = [False]
    alive = [True]

    def on_destroy(event):
        if event.widget is win:
            alive[0] = False

    win.bind("<Destroy>", on_destroy)

    def ui(callback):
        """Run callback on the Tk thread (safe if the window was closed)."""
        if not alive[0]:
            return
        try:
            win.after(0, callback)
        except (tk.TclError, RuntimeError):
            pass

    # ── Header ───────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg=BLUE_DEEP)
    hdr.pack(fill="x")
    hdr_inner = tk.Frame(hdr, bg=BLUE_DEEP)
    hdr_inner.pack(fill="x", padx=22, pady=16)

    icon_box = tk.Frame(hdr_inner, bg=ORANGE, width=52, height=52)
    icon_box.pack(side="left", padx=(0, 14))
    icon_box.pack_propagate(False)
    tk.Label(icon_box, text="⌕", font=("Segoe UI Symbol", 22, "bold"),
             bg=ORANGE, fg=WHITE).place(relx=0.5, rely=0.5, anchor="center")

    hdr_text = tk.Frame(hdr_inner, bg=BLUE_DEEP)
    hdr_text.pack(side="left")
    tk.Label(hdr_text, text="Duplicate File Finder",
             font=("Segoe UI", 17, "bold"), bg=BLUE_DEEP, fg=WHITE).pack(anchor="w")
    tk.Label(hdr_text, text="Detect and remove identical files across folders",
             font=("Segoe UI", 9), bg=BLUE_DEEP, fg=SKY).pack(anchor="w", pady=(3, 0))

    tk.Frame(win, bg="#2671FF", height=1).pack(fill="x")

    # ── Bottom action bar (packed first so it never gets clipped) ───────────
    action_bar = tk.Frame(win, bg=FOOTER_BG)
    action_bar.pack(side="bottom", fill="x")
    bar_inner = tk.Frame(action_bar, bg=FOOTER_BG)
    bar_inner.pack(fill="x", padx=22, pady=12)

    selection_var = tk.StringVar(value="No files selected")

    # ── Selection helpers ────────────────────────────────────────────────────
    def update_selection(*_):
        chosen = [p for p, v in check_vars.items() if v.get()]
        if not chosen:
            selection_var.set("No files selected")
            return
        total = sum(size_map.get(p, 0) for p in chosen)
        selection_var.set(
            f"{len(chosen)} file(s) selected  •  {format_size(total)} will be freed"
        )

    def select_all_duplicates_only():
        """
        Check every file EXCEPT the first one in each visible group
        (keeps one copy). Toggles: if all are already checked, uncheck them.
        """
        targets = []
        for paths in filtered_duplicates.values():
            visible = [p for p in paths if p in check_vars]
            targets.extend(visible[1:])

        if not targets:
            return

        all_selected = all(check_vars[p].get() for p in targets)
        for p in targets:
            check_vars[p].set(not all_selected)

    def delete_selected():
        if scanning[0]:
            return

        to_delete = [p for p, v in check_vars.items() if v.get()]
        if not to_delete:
            messagebox.showwarning("Nothing Selected",
                                   "Please check at least one file to delete.",
                                   parent=win)
            return

        # Safety net: warn if every copy of any file would be removed.
        chosen = set(to_delete)
        wiped = sum(1 for paths in duplicates.values()
                    if all(p in chosen for p in paths))
        if wiped:
            if not messagebox.askyesno(
                "Every Copy Selected",
                f"You selected ALL copies of {wiped} file group(s).\n"
                "Nothing would be kept for them.\n\n"
                "Do you still want to continue?",
                parent=win, icon="warning", default="no",
            ):
                return

        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete {len(to_delete)} file(s)?\n\n"
            "This cannot be undone.",
            parent=win, icon="warning", default="no",
        ):
            return

        deleted = skipped = 0
        for path in to_delete:
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                skipped += 1

        messagebox.showinfo(
            "Deletion Complete",
            f"Done.\n\n  ✔  Deleted : {deleted}\n  –   Skipped : {skipped}",
            parent=win,
        )
        do_scan()

    select_btn = make_button(bar_inner, "Select All Duplicates",
                             PURPLE, PURPLE_H, select_all_duplicates_only)
    tk.Label(bar_inner, textvariable=selection_var, font=("Segoe UI", 9),
             bg=FOOTER_BG, fg=MUTED).pack(side="left", padx=(14, 0))
    delete_btn = make_button(bar_inner, "Delete Selected",
                             RED, RED_H, delete_selected, side="right")

    # ── Body ─────────────────────────────────────────────────────────────────
    body = tk.Frame(win, bg=BLUE)
    body.pack(fill="both", expand=True, padx=22)

    # Folders
    section_heading(body, "FOLDERS TO SCAN", pady=(16, 8))

    folder_card = tk.Frame(body, bg=PANEL,
                           highlightbackground=PANEL_BORDER, highlightthickness=1)
    folder_card.pack(fill="x")

    folder_list_frame = tk.Frame(folder_card, bg=PANEL)
    folder_list_frame.pack(fill="x", padx=14, pady=(10, 4))

    def remove_folder(index):
        if scanning[0]:
            return
        folders.pop(index)
        refresh_folder_list()

    def refresh_folder_list():
        for widget in folder_list_frame.winfo_children():
            widget.destroy()

        if not folders:
            tk.Label(folder_list_frame, text="No folders added yet.",
                     font=("Segoe UI", 9, "italic"), bg=PANEL, fg=SKY,
                     anchor="w").pack(fill="x", pady=4)
            return

        for i, folder_path in enumerate(folders):
            row = tk.Frame(folder_list_frame, bg=PANEL)
            row.pack(fill="x", pady=3)

            tk.Label(row, text="▤", font=("Segoe UI Symbol", 11),
                     bg=PANEL, fg=CYAN).pack(side="left")
            tk.Label(row, text=folder_path, font=("Segoe UI", 9),
                     bg=PANEL, fg=WHITE, anchor="w", justify="left",
                     wraplength=700).pack(side="left", fill="x",
                                          expand=True, padx=(8, 0))
            rm = tk.Label(row, text="✕", font=("Segoe UI", 10, "bold"),
                          bg=PANEL, fg=RED, cursor="hand2")
            rm.pack(side="right", padx=4)
            rm.bind("<Button-1>", lambda e, idx=i: remove_folder(idx))

    def add_folder():
        path = filedialog.askdirectory(title="Select Folder to Scan", parent=win)
        if not path:
            return
        path = os.path.normpath(path)
        if path in folders:
            messagebox.showwarning("Already Added",
                                   "That folder is already in the list.",
                                   parent=win)
            return
        folders.append(path)
        refresh_folder_list()

    btn_row = tk.Frame(folder_card, bg=PANEL)
    btn_row.pack(fill="x", padx=14, pady=(2, 12))
    add_btn = make_button(btn_row, "+  Add Folder", CYAN, CYAN_H, add_folder)

    refresh_folder_list()

    # Scan row
    scan_row = tk.Frame(body, bg=BLUE)
    scan_row.pack(fill="x", pady=(12, 0))

    progress_var = tk.StringVar(value="")
    tk.Label(scan_row, textvariable=progress_var, font=("Segoe UI", 9),
             bg=BLUE, fg=MUTED, anchor="w").pack(side="left", fill="x", expand=True)

    def set_scanning(state):
        scanning[0] = state
        set_enabled(scan_btn, not state)
        set_enabled(add_btn, not state)
        set_enabled(delete_btn, not state)
        scan_btn.config(text="Scanning…" if state else "Scan for Duplicates")

    def do_scan():
        if scanning[0]:
            return
        if not folders:
            messagebox.showwarning("No Folders",
                                   "Please add at least one folder to scan.",
                                   parent=win)
            return

        set_scanning(True)
        progress_var.set("Scanning…  0 files scanned")
        last_update = [0.0]

        def on_progress(scanned, current_file):
            now = time.monotonic()
            if now - last_update[0] < 0.1:
                return
            last_update[0] = now
            short = os.path.basename(current_file)
            ui(lambda: progress_var.set(
                f"Scanning…  {scanned} files scanned  —  {short}"))

        def run():
            result = find_duplicates(list(folders), on_progress=on_progress)
            ui(lambda: finish(result))

        def finish(result):
            nonlocal duplicates
            duplicates = result
            scanned_once[0] = True
            set_scanning(False)

            if not duplicates:
                progress_var.set("✔  No duplicates found.")
            else:
                total_files = sum(len(v) for v in duplicates.values())
                reclaim = 0
                for paths in duplicates.values():
                    try:
                        reclaim += os.path.getsize(paths[0]) * (len(paths) - 1)
                    except OSError:
                        pass
                progress_var.set(
                    f"✔  {len(duplicates)} group(s)  •  {total_files} files  •  "
                    f"{format_size(reclaim)} can be freed"
                )
            apply_filter()

        threading.Thread(target=run, daemon=True).start()

    scan_btn = make_button(scan_row, "Scan for Duplicates",
                           ORANGE, "#E67E1A", do_scan, side="right")

    # Search bar
    search_wrap = tk.Frame(body, bg=BLUE_DEEP,
                           highlightbackground=PANEL_BORDER, highlightthickness=1)
    search_wrap.pack(fill="x", pady=(12, 0))
    tk.Label(search_wrap, text="⌕", font=("Segoe UI Symbol", 13),
             bg=BLUE_DEEP, fg=SKY).pack(side="left", padx=(10, 4))

    search_var = tk.StringVar(value="")
    search_entry = tk.Entry(
        search_wrap, textvariable=search_var, font=("Segoe UI", 10),
        bg=BLUE_DEEP, fg=WHITE, relief="flat", bd=0,
        insertbackground=WHITE, highlightthickness=0,
    )
    search_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))

    def on_search_focus_in(_e):
        search_wrap.config(highlightbackground=CYAN)
        if search_entry.get() == PLACEHOLDER:
            search_entry.delete(0, tk.END)
            search_entry.config(fg=WHITE)

    def on_search_focus_out(_e):
        search_wrap.config(highlightbackground=PANEL_BORDER)
        if not search_entry.get():
            search_entry.insert(0, PLACEHOLDER)
            search_entry.config(fg=SKY)

    # Results
    section_heading(body, "DUPLICATE GROUPS", pady=(16, 8))

    outer_res = tk.Frame(body, bg=BLUE)
    outer_res.pack(fill="both", expand=True, pady=(0, 12))

    canvas = tk.Canvas(outer_res, bg=BLUE, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer_res, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    results_frame = tk.Frame(canvas, bg=BLUE)
    canvas_window = canvas.create_window((0, 0), window=results_frame, anchor="nw")

    results_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfig(canvas_window, width=e.width))

    def on_mousewheel(event):
        """Scroll only when the pointer is over the results area."""
        widget = win.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget is canvas:
                canvas.yview_scroll(int(-event.delta / 120), "units")
                return
            widget = widget.master

    # Bound to this window only, so it disappears when the window closes.
    win.bind("<MouseWheel>", on_mousewheel)

    def make_toggle(group_vars, group_var):
        def toggle():
            state = group_var.get()
            for v in group_vars:
                v.set(state)
        return toggle

    def populate_results():
        for widget in results_frame.winfo_children():
            widget.destroy()
        check_vars.clear()
        size_map.clear()

        if not filtered_duplicates:
            if not scanned_once[0]:
                message = "Add folders, then press “Scan for Duplicates”."
            elif not duplicates:
                message = "No duplicates found."
            else:
                message = "No files match your search."
            tk.Label(results_frame, text=message,
                     font=("Segoe UI", 10, "italic"), bg=BLUE, fg=MUTED,
                     anchor="w").pack(fill="x", pady=12)
            update_selection()
            return

        for group_idx, paths in enumerate(filtered_duplicates.values()):
            try:
                fsize = os.path.getsize(paths[0])
            except OSError:
                fsize = 0

            card = tk.Frame(results_frame, bg=PANEL,
                            highlightbackground=PANEL_BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(0, 10))

            head = tk.Frame(card, bg=BLUE_DEEP)
            head.pack(fill="x")
            tk.Frame(head, bg=ORANGE, width=5).pack(side="left", fill="y")
            tk.Label(
                head,
                text=(f"Group {group_idx + 1}   •   {len(paths)} identical files"
                      f"   •   {format_size(fsize)} each"),
                font=("Segoe UI", 9, "bold"), bg=BLUE_DEEP, fg=WHITE,
            ).pack(side="left", padx=12, pady=9)

            group_var = tk.BooleanVar(value=False)
            group_vars = []
            toggle_chk = tk.Checkbutton(
                head, variable=group_var, text="Select all",
                font=("Segoe UI", 8), bg=BLUE_DEEP, fg=MUTED,
                activebackground=BLUE_DEEP, activeforeground=WHITE,
                selectcolor=WHITE, cursor="hand2", bd=0, highlightthickness=0,
            )
            toggle_chk.pack(side="right", padx=12)

            for path in paths:
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill="x", padx=10, pady=4)

                var = tk.BooleanVar(value=False)
                var.trace_add("write", update_selection)
                check_vars[path] = var
                group_vars.append(var)
                try:
                    size_map[path] = os.path.getsize(path)
                except OSError:
                    size_map[path] = 0

                tk.Checkbutton(
                    row, variable=var, bg=PANEL, activebackground=PANEL,
                    selectcolor=WHITE, cursor="hand2", bd=0, highlightthickness=0,
                ).pack(side="left")

                ext = os.path.splitext(path)[1].lower()
                badge = (ext[1:5].upper() or "FILE")
                tk.Label(row, text=badge, font=("Segoe UI", 7, "bold"),
                         bg=BADGE_COLORS.get(ext, DEFAULT_BADGE), fg=WHITE,
                         width=5, pady=3).pack(side="left", padx=(0, 10))

                info = tk.Frame(row, bg=PANEL)
                info.pack(side="left", fill="x", expand=True)
                tk.Label(info, text=os.path.basename(path),
                         font=("Segoe UI", 9, "bold"), bg=PANEL, fg=WHITE,
                         anchor="w").pack(fill="x")
                tk.Label(info, text=path, font=("Segoe UI", 8), bg=PANEL,
                         fg=SKY, anchor="w", justify="left",
                         wraplength=620).pack(fill="x")

            toggle_chk.config(command=make_toggle(group_vars, group_var))

        update_selection()

    # Search filter logic
    def apply_filter(*_):
        nonlocal filtered_duplicates
        term = search_var.get().strip().lower()
        if not term or term == PLACEHOLDER.lower():
            filtered_duplicates = dict(duplicates)
        else:
            filtered_duplicates = {}
            for h, paths in duplicates.items():
                matched = [p for p in paths
                           if term in os.path.basename(p).lower()]
                if len(matched) > 1:
                    filtered_duplicates[h] = matched
        populate_results()

    search_entry.insert(0, PLACEHOLDER)
    search_entry.config(fg=SKY)
    search_entry.bind("<FocusIn>", on_search_focus_in)
    search_entry.bind("<FocusOut>", on_search_focus_out)
    search_var.trace_add("write", apply_filter)

    # Initial empty state
    populate_results()