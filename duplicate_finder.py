"""
Duplicate File Finder window for WinCleaner.
Author: Windel Navales
"""

import os
import hashlib
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from collections import defaultdict
from typing import Optional

from ui_components import (
    BG, CARD, BORDER, HEADER_BG, ACCENT, ACCENT_H,
    RED, RED_H, PURPLE, PURPLE_H,
    TEXT_LIGHT, TEXT_DARK, TEXT_MUTED, FOOTER_BG,
    styled_btn, format_size
)


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


def open_duplicate_finder(root_window: tk.Tk) -> None:
    """
    Create and open the Duplicate File Finder toplevel window.
    """
    win = tk.Toplevel(root_window)
    win.title("Duplicate File Finder")
    win.geometry("780x700")
    win.resizable(True, True)
    win.configure(bg=BG)
    win.minsize(680, 550)

    # Try to load icon from main window
    try:
        if root_window.iconbitmap():
            win.iconbitmap(root_window.iconbitmap())
    except Exception:
        pass

    # ── State ──────────────────────────────────────────────────────────────────
    folders = []             # list of folder paths to scan
    duplicates = {}          # hash → [paths]      (full scan result)
    filtered_duplicates = {} # hash → [paths]      (after search filtering)
    check_vars = {}          # path → BooleanVar

    # ── Header ─────────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg=HEADER_BG, height=72)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    hdr_inner = tk.Frame(hdr, bg=HEADER_BG)
    hdr_inner.place(relx=0.5, rely=0.5, anchor="center")
    tk.Label(hdr_inner, text="🔍  Duplicate File Finder",
             font=("Segoe UI", 16, "bold"), bg=HEADER_BG, fg=TEXT_LIGHT).pack()
    tk.Label(hdr_inner, text="Detect and remove identical files across folders",
             font=("Segoe UI", 8), bg=HEADER_BG, fg="#7BAAF7").pack()

    # ── Folder list panel ──────────────────────────────────────────────────────
    folder_panel = tk.Frame(win, bg=BG)
    folder_panel.pack(fill="x", padx=16, pady=(14, 0))

    sec_row = tk.Frame(folder_panel, bg=BG)
    sec_row.pack(fill="x")
    tk.Label(sec_row, text="FOLDERS TO SCAN", font=("Segoe UI", 8, "bold"),
             bg=BG, fg=TEXT_MUTED).pack(side="left")
    tk.Frame(sec_row, bg=BORDER, height=1).pack(
        side="left", fill="x", expand=True, padx=(10, 0), pady=6)

    folder_card = tk.Frame(folder_panel,
                           bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    folder_card.pack(fill="x", pady=(6, 0))

    folder_list_frame = tk.Frame(folder_card, bg=CARD)
    folder_list_frame.pack(fill="x", padx=10, pady=6)

    def refresh_folder_list():
        for widget in folder_list_frame.winfo_children():
            widget.destroy()

        if not folders:
            tk.Label(folder_list_frame, text="No folders added yet.",
                     font=("Segoe UI", 8, "italic"), bg=CARD, fg=TEXT_MUTED,
                     anchor="w").pack(fill="x", pady=4)
            return

        for i, folder_path in enumerate(folders):
            row = tk.Frame(folder_list_frame, bg=CARD)
            row.pack(fill="x", pady=2)

            tk.Label(row, text="📁", font=("Segoe UI Emoji", 10),
                     bg=CARD, fg=ACCENT).pack(side="left")
            tk.Label(row, text=folder_path, font=("Segoe UI", 9),
                     bg=CARD, fg=TEXT_DARK, anchor="w",
                     wraplength=540, justify="left").pack(side="left", fill="x",
                                                          expand=True, padx=(6, 0))
            rm_btn = tk.Label(row, text="✕", font=("Segoe UI", 9, "bold"),
                              bg=CARD, fg=RED, cursor="hand2")
            rm_btn.pack(side="right", padx=4)
            rm_btn.bind("<Button-1>", lambda e, idx=i: (
                folders.pop(idx), refresh_folder_list()
            ))

    refresh_folder_list()

    btn_row = tk.Frame(folder_card, bg=CARD)
    btn_row.pack(fill="x", padx=10, pady=(0, 10))

    def add_folder():
        path = filedialog.askdirectory(title="Select Folder to Scan", parent=win)
        if path and path not in folders:
            folders.append(path)
            refresh_folder_list()
        elif path in folders:
            messagebox.showwarning("Already Added",
                                   "That folder is already in the list.", parent=win)

    styled_btn(btn_row, "+ Add Folder", ACCENT, ACCENT_H, add_folder)

    # ── Scan & filter controls ─────────────────────────────────────────────────
    ctrl_frame = tk.Frame(win, bg=BG)
    ctrl_frame.pack(fill="x", padx=16, pady=(10, 0))

    progress_var = tk.StringVar(value="")
    progress_lbl = tk.Label(ctrl_frame, textvariable=progress_var,
                            font=("Segoe UI", 8), bg=BG, fg=TEXT_MUTED)
    progress_lbl.pack(side="left")

    # ── Search bar ─────────────────────────────────────────────────────────────
    search_frame = tk.Frame(win, bg=BG)
    search_frame.pack(fill="x", padx=16, pady=(4, 0))

    tk.Label(search_frame, text="🔎", font=("Segoe UI Emoji", 10),
             bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0, 4))

    search_var = tk.StringVar(value="")
    search_entry = tk.Entry(
        search_frame,
        textvariable=search_var,
        font=("Segoe UI", 10),
        bg=CARD, fg=TEXT_DARK,
        relief="flat",
        highlightbackground=BORDER,
        highlightthickness=1,
        insertbackground=TEXT_DARK
    )
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)

    PLACEHOLDER = "Search files by name..."
    def on_search_focus_in(e):
        if search_entry.get() == PLACEHOLDER:
            search_entry.delete(0, tk.END)
            search_entry.config(fg=TEXT_DARK)

    def on_search_focus_out(e):
        if not search_entry.get():
            search_entry.insert(0, PLACEHOLDER)
            search_entry.config(fg=TEXT_MUTED)

    search_entry.insert(0, PLACEHOLDER)
    search_entry.config(fg=TEXT_MUTED)
    search_entry.bind("<FocusIn>", on_search_focus_in)
    search_entry.bind("<FocusOut>", on_search_focus_out)

    scan_btn_ref = []

    def do_scan():
        if not folders:
            messagebox.showwarning("No Folders",
                                   "Please add at least one folder to scan.", parent=win)
            return

        if scan_btn_ref:
            scan_btn_ref[0].config(bg=TEXT_MUTED, cursor="arrow")
            for ev in ("<Enter>", "<Leave>", "<Button-1>"):
                scan_btn_ref[0].unbind(ev)

        progress_var.set("⏳  Scanning…  (0 files scanned)")

        def on_progress(scanned, current_file):
            short = os.path.basename(current_file)
            win.after(0, lambda: progress_var.set(
                f"⏳  Scanning…  {scanned} files scanned  —  {short}"
            ))

        def run():
            result = find_duplicates(folders, on_progress=on_progress)
            win.after(0, lambda: finish(result))

        def finish(result):
            nonlocal duplicates, filtered_duplicates
            duplicates = result
            apply_filter()

            if not duplicates:
                progress_var.set("✔  No duplicates found.")
            else:
                total_files = sum(len(v) for v in duplicates.values())
                progress_var.set(
                    f"✔  Found {len(duplicates)} group(s) — {total_files} files total"
                )

            if scan_btn_ref:
                btn = scan_btn_ref[0]
                btn.config(bg=ACCENT, cursor="hand2")
                btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_H))
                btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))
                btn.bind("<Button-1>", lambda e: do_scan())

        threading.Thread(target=run, daemon=True).start()

    scan_btn = styled_btn(ctrl_frame, "🔍  Scan for Duplicates",
                          ACCENT, ACCENT_H, do_scan, side="right")
    scan_btn_ref.append(scan_btn)

    # ── Filter logic ───────────────────────────────────────────────────────────
    def apply_filter(*args):
        nonlocal filtered_duplicates
        term = search_var.get().strip().lower()
        if not term or term == PLACEHOLDER.lower():
            filtered_duplicates = dict(duplicates)
        else:
            filtered_duplicates = {}
            for h, paths in duplicates.items():
                matched = [p for p in paths if term in os.path.basename(p).lower()]
                if len(matched) > 1:
                    filtered_duplicates[h] = matched
        populate_results()

    search_var.trace_add("write", apply_filter)

    # ── Results panel ──────────────────────────────────────────────────────────
    res_sec = tk.Frame(win, bg=BG)
    res_sec.pack(fill="x", padx=16, pady=(14, 0))
    res_sec_row = tk.Frame(res_sec, bg=BG)
    res_sec_row.pack(fill="x")
    tk.Label(res_sec_row, text="DUPLICATE GROUPS", font=("Segoe UI", 8, "bold"),
             bg=BG, fg=TEXT_MUTED).pack(side="left")
    tk.Frame(res_sec_row, bg=BORDER, height=1).pack(
        side="left", fill="x", expand=True, padx=(10, 0), pady=6)

    # Scrollable results area
    outer_res = tk.Frame(win, bg=BG, padx=16)
    outer_res.pack(fill="both", expand=True, pady=(6, 0))

    canvas = tk.Canvas(outer_res, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer_res, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    results_frame = tk.Frame(canvas, bg=BG)
    canvas_window = canvas.create_window((0, 0), window=results_frame, anchor="nw")

    def on_frame_configure(e):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(e):
        canvas.itemconfig(canvas_window, width=e.width)

    results_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    def _on_mousewheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def select_all_duplicates_only():
        """
        Check all files EXCEPT the first one in each group (keep one copy).
        Acts as a toggle: if everything's already selected, deselect all.
        """
        data = filtered_duplicates if filtered_duplicates else duplicates
        if not data:
            return

        all_selected = True
        for h, paths in data.items():
            visible = [p for p in paths if p in check_vars]
            if len(visible) < 2:
                continue
            for p in visible[1:]:
                if p in check_vars and not check_vars[p].get():
                    all_selected = False
                    break
            if not all_selected:
                break

        for h, paths in data.items():
            visible = [p for p in paths if p in check_vars]
            if len(visible) < 2:
                continue
            for p in visible[1:]:
                if p in check_vars:
                    check_vars[p].set(not all_selected)

    def populate_results():
        for widget in results_frame.winfo_children():
            widget.destroy()
        check_vars.clear()

        data = filtered_duplicates if filtered_duplicates else duplicates

        if not data:
            tk.Label(results_frame,
                     text="No duplicates found. Add folders and scan to begin.",
                     font=("Segoe UI", 9, "italic"), bg=BG, fg=TEXT_MUTED,
                     anchor="w").pack(fill="x", pady=10)
            return

        for group_idx, (file_hash, paths) in enumerate(data.items()):
            group_card = tk.Frame(results_frame, bg=CARD,
                                  highlightbackground=BORDER, highlightthickness=1)
            group_card.pack(fill="x", pady=(0, 8))

            try:
                fsize = os.path.getsize(paths[0])
            except OSError:
                fsize = 0

            gh = tk.Frame(group_card, bg="#EBF3FF")
            gh.pack(fill="x")
            gh_left = tk.Frame(gh, bg="#EBF3FF")
            gh_left.pack(side="left", padx=10, pady=6)
            tk.Label(gh_left,
                     text=f"Group {group_idx + 1}  •  {len(paths)} identical files  •  {format_size(fsize)} each",
                     font=("Segoe UI", 9, "bold"), bg="#EBF3FF", fg=ACCENT).pack(side="left")

            grp_var = tk.BooleanVar(value=False)
            group_vars = []

            def make_toggle(gvars, gvar):
                def toggle():
                    state = gvar.get()
                    for v in gvars:
                        v.set(state)
                return toggle

            toggle_btn_frame = tk.Frame(gh, bg="#EBF3FF")
            toggle_btn_frame.pack(side="right", padx=10)
            toggle_chk = tk.Checkbutton(toggle_btn_frame, variable=grp_var,
                                        bg="#EBF3FF", activebackground="#EBF3FF",
                                        text="Select all", font=("Segoe UI", 8),
                                        fg=TEXT_MUTED, cursor="hand2")
            toggle_chk.pack()

            for path in paths:
                row_frame = tk.Frame(group_card, bg=CARD)
                row_frame.pack(fill="x", padx=8, pady=3)

                var = tk.BooleanVar(value=False)
                check_vars[path] = var
                group_vars.append(var)

                chk = tk.Checkbutton(row_frame, variable=var,
                                     bg=CARD, activebackground=CARD,
                                     cursor="hand2")
                chk.pack(side="left")

                ext = os.path.splitext(path)[1].lower()
                file_icon = {
                    ".jpg": "🖼", ".jpeg": "🖼", ".png": "🖼", ".gif": "🖼", ".bmp": "🖼",
                    ".mp4": "🎬", ".avi": "🎬", ".mkv": "🎬", ".mov": "🎬",
                    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵",
                    ".pdf": "📕", ".doc": "📄", ".docx": "📄",
                    ".zip": "📦", ".rar": "📦", ".7z": "📦",
                }.get(ext, "📄")

                tk.Label(row_frame, text=file_icon, font=("Segoe UI Emoji", 10),
                         bg=CARD).pack(side="left", padx=(0, 4))

                name_frame = tk.Frame(row_frame, bg=CARD)
                name_frame.pack(side="left", fill="x", expand=True)
                tk.Label(name_frame, text=os.path.basename(path),
                         font=("Segoe UI", 9, "bold"), bg=CARD,
                         fg=TEXT_DARK, anchor="w").pack(fill="x")
                tk.Label(name_frame, text=path, font=("Segoe UI", 7),
                         bg=CARD, fg=TEXT_MUTED, anchor="w",
                         wraplength=480, justify="left").pack(fill="x")

            toggle_chk.config(command=make_toggle(group_vars, grp_var))
            if group_idx < len(data) - 1:
                tk.Frame(group_card, bg=BORDER, height=1).pack(fill="x")

    # ── Bottom action bar ──────────────────────────────────────────────────────
    action_bar = tk.Frame(win, bg=FOOTER_BG)
    action_bar.pack(side="bottom", fill="x")
    tk.Frame(action_bar, bg=BORDER, height=1).pack(fill="x")

    bar_inner = tk.Frame(action_bar, bg=FOOTER_BG)
    bar_inner.pack(fill="x", padx=16, pady=10)

    styled_btn(bar_inner, "📋  Select All Duplicates",
               PURPLE, PURPLE_H, select_all_duplicates_only, side="left")

    sel_label = tk.Label(bar_inner, text="Check files above to delete them.",
                         font=("Segoe UI", 8), bg=FOOTER_BG, fg=TEXT_MUTED)
    sel_label.pack(side="left", padx=(10, 0))

    def delete_selected():
        to_delete = [path for path, var in check_vars.items() if var.get()]
        if not to_delete:
            messagebox.showwarning("Nothing Selected",
                                   "Please check at least one file to delete.", parent=win)
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete {len(to_delete)} file(s)?\n\nThis cannot be undone.",
            parent=win
        )
        if not confirm:
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
            parent=win
        )
        do_scan()

    styled_btn(bar_inner, "🗑  Delete Selected", RED, RED_H, delete_selected, side="right")

    # Initial empty state
    populate_results()