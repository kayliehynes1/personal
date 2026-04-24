# removed solution grid input; the server now auto-solves the puzzle

import tkinter as tk
from tkinter import messagebox, ttk
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_TITLE, FONT_SMALL, FONT_BODY
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class AddPuzzleScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)

        tk.Label(self, text="ADD PUZZLE", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(30, 20))

        form = tk.Frame(self, bg=t["bg_secondary"], padx=40, pady=30)
        form.pack()

        # CHANGED: removed title field — database has no title column
        tk.Label(form, text="DIFFICULTY", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._difficulty = ttk.Combobox(
            form, values=["easy", "medium", "hard"],
            font=FONT_BODY, state="readonly", width=10)
        self._difficulty.set("medium")
        self._difficulty.pack(pady=(4, 16), anchor="w")

        # CHANGED: label updated — accepts plain string or comma-separated, digits 0-9 only
        tk.Label(form, text="INITIAL GRID  (81 digits 0–9, 0 = empty. Plain string or comma-separated)",
                 font=FONT_SMALL, bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._initial = tk.Text(form, font=FONT_SMALL, width=52, height=3,
                                bg=t["entry_bg"], fg=t["entry_fg"], relief="flat")
        self._initial.pack(pady=(4, 16))

        # CHANGED: removed solution grid — server solves it automatically
        tk.Label(form, text="The solution will be calculated automatically.",
                 font=FONT_SMALL, bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w", pady=(0, 16))

        RetroButton(form, self.app, "SUBMIT PUZZLE",
                    command=self._submit).pack(fill="x")

    def _submit(self) -> None:
        initial = self._initial.get("1.0", tk.END).strip()
        diff    = self._difficulty.get()

        if not initial:
            messagebox.showwarning("Missing fields", "Please enter the initial grid.")
            return

        # CHANGED: normalise input — strip spaces/newlines, accept plain or comma-separated
        initial = "".join(initial.split())            # remove all whitespace
        if "," in initial:
            parts = [x.strip() for x in initial.split(",")]
            initial = "".join(parts)

        # Validate: must be exactly 81 digits 0-9
        if len(initial) != 81:
            messagebox.showerror("Invalid grid", f"Grid must have 81 digits, got {len(initial)}.")
            return
        if not initial.isdigit():
            messagebox.showerror("Invalid grid", "Grid must contain digits 0–9 only.")
            return

        # CHANGED: only passes initial_grid — no solution_grid
        result = self.app.server.add_puzzle(initial, diff)
        if result["status"] == "ok":
            messagebox.showinfo("Success", "Puzzle submitted! Solution calculated automatically.")
            self._initial.delete("1.0", tk.END)
            self.app.show_frame("LobbyScreen")
        else:
            messagebox.showerror("Error", result.get("message", "Submission failed."))
