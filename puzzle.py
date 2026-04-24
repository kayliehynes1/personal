"""screens/puzzle.py — Puzzle screen, SudokuGrid widget and Timer."""

import tkinter as tk
from tkinter import messagebox
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_BODY, FONT_SMALL, FONT_HEADER, FONT_CELL
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


# ---------------------------------------------------------------------------
# TIMER
# ---------------------------------------------------------------------------

class Timer:
    """Tracks elapsed solve time, displayed on the puzzle screen."""

    def __init__(self, label: tk.Label, app: "App") -> None:
        self._label   = label
        self._app     = app
        self._seconds = 0
        self._running = False
        self._job     = None

    def start(self) -> None:
        self._running = True
        self._tick()

    def stop(self) -> int:
        """Stop and return elapsed seconds."""
        self._running = False
        if self._job:
            self._app.after_cancel(self._job)
        return self._seconds

    def reset(self) -> None:
        self.stop()
        self._seconds = 0
        self._update_label()

    def _tick(self) -> None:
        if self._running:
            self._seconds += 1
            self._update_label()
            self._job = self._app.after(1000, self._tick)

    def _update_label(self) -> None:
        m, s = divmod(self._seconds, 60)
        self._label.config(text=f"{m:02d}:{s:02d}")


# ---------------------------------------------------------------------------
# SUDOKU GRID WIDGET
# ---------------------------------------------------------------------------

class SudokuGrid(tk.Frame):
    """Interactive 9x9 grid with cell locking, error highlights and hints.

    Visual structure:
    - Thin lines (1px) between cells within the same 3x3 box
    - Thick lines (4px) between 3x3 boxes and around the outer border
    """

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        t = app.theme
        # Outer frame uses accent colour as the thick border colour
        super().__init__(parent, bg=t["accent"], padx=4, pady=4)
        self._app    = app
        self._cells: dict[tuple[int, int], tk.Entry] = {}
        self._locked: set[tuple[int, int]] = set()
        self._cell_frames: list = []
        self._build_grid()

    def _build_grid(self) -> None:
        t = self._app.theme
        # Use a single canvas-like approach:
        # Outer frame bg = accent (thick border colour)
        # Each box is separated by 4px gaps (accent colour shows through)
        # Within each box, cells separated by 1px gaps (text_dim shows through)

        self._box_frames: list[tk.Frame] = []

        for br in range(3):
            for bc in range(3):
                # Equal padx/pady on ALL boxes so every thick border is identical
                box_outer = tk.Frame(self, bg=t["accent"],
                                     padx=1, pady=1)
                box_outer.grid(row=br, column=bc, padx=3, pady=3)
                # Inner container — text_dim bleeds through as thin lines
                box_inner = tk.Frame(box_outer, bg=t["text_dim"])
                box_inner.pack()
                self._box_frames.append(box_outer)

                for cr in range(3):
                    for cc in range(3):
                        row = br * 3 + cr
                        col = bc * 3 + cc
                        cell_frame = tk.Frame(box_inner, bg=t["text_dim"],
                                              padx=(0 if cc == 0 else 1),
                                              pady=(0 if cr == 0 else 1))
                        cell_frame.grid(row=cr, column=cc)
                        vcmd = (self.register(self._validate_cell), "%P")
                        cell = tk.Entry(
                            cell_frame, width=2, font=FONT_CELL,
                            justify="center",
                            bg=t["entry_bg"], fg=t["cell_user"],
                            insertbackground=t["text"],
                            relief="flat", bd=0,
                            validate="key", validatecommand=vcmd,
                        )
                        cell.pack()
                        self._cells[(row, col)] = cell
                        self._cell_frames.append((cell_frame, cell))

    def _validate_cell(self, value: str) -> bool:
        return value == "" or (value.isdigit() and len(value) == 1 and value != "0")

    def load_puzzle(self, initial_grid: list[list[int]]) -> None:
        """Populate grid and lock pre-filled clue cells."""
        self.clear()
        t = self._app.theme
        for row in range(9):
            for col in range(9):
                val = initial_grid[row][col]
                if val != 0:
                    cell = self._cells[(row, col)]
                    cell.insert(0, str(val))
                    cell.config(state="disabled",
                                disabledforeground=t["cell_fixed"],
                                disabledbackground=t["entry_bg"])
                    self._locked.add((row, col))

    def get_current_grid(self) -> list[list[int]]:
        grid = []
        for row in range(9):
            grid.append([
                int(self._cells[(row, col)].get() or 0)
                for col in range(9)
            ])
        return grid

    def highlight_error(self, row: int, col: int) -> None:
        self._cells[(row, col)].config(fg=self._app.theme["cell_error"])

    def highlight_hint(self, row: int, col: int, value: int) -> None:
        cell = self._cells[(row, col)]
        cell.config(state="normal")
        cell.delete(0, tk.END)
        cell.insert(0, str(value))
        cell.config(fg=self._app.theme["cell_hint"])

    def clear(self) -> None:
        self._locked.clear()
        t = self._app.theme
        for cell in self._cells.values():
            cell.config(state="normal", fg=t["cell_user"], bg=t["entry_bg"])
            cell.delete(0, tk.END)

    def apply_theme(self) -> None:
        """Re-apply all colours when theme toggles."""
        t = self._app.theme
        # Outer grid frame — thick border colour
        self.config(bg=t["accent"])
        # Box outer frames — thick border colour
        for bf in self._box_frames:
            bf.config(bg=t["accent"])
        # Cell frames — thin line colour
        for frame, cell in self._cell_frames:
            frame.config(bg=t["text_dim"])
        # Cells themselves
        for (row, col), cell in self._cells.items():
            if (row, col) in self._locked:
                cell.config(disabledforeground=t["cell_fixed"],
                            disabledbackground=t["entry_bg"])
            else:
                cell.config(bg=t["entry_bg"], fg=t["cell_user"],
                            insertbackground=t["text"])


# ---------------------------------------------------------------------------
# SCREEN: PUZZLE
# ---------------------------------------------------------------------------

class PuzzleScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._puzzle_id: Optional[int] = None
        self._build()

    def _build(self) -> None:
        t = self.theme

        # Top bar
        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=self._back).pack(side="left", padx=12)
        self._title_lbl = tk.Label(bar, text="", font=FONT_HEADER,
                                   bg=t["bg_secondary"], fg=t["accent"])
        self._title_lbl.pack(side="left", padx=12)
        tk.Button(bar, text="⬛/⬜", font=FONT_SMALL, relief="flat",
                  bg=t["bg_secondary"], fg=t["text_dim"],
                  command=self.app.toggle_theme, cursor="hand2").pack(side="right", padx=12)

        # Timer
        self._timer_lbl = tk.Label(self, text="00:00", font=FONT_HEADER,
                                   bg=t["bg"], fg=t["accent2"])
        self._timer_lbl.pack(pady=(6, 2))
        self._timer = Timer(self._timer_lbl, self.app)

        # Grid
        self._grid = SudokuGrid(self, self.app)
        self._grid.pack(pady=6)

        # Action buttons
        btn_row = tk.Frame(self, bg=t["bg"])
        btn_row.pack(pady=6)
        RetroButton(btn_row, self.app, "HINT",     command=self._hint).pack(side="left", padx=6)
        RetroButton(btn_row, self.app, "VALIDATE", command=self._validate).pack(side="left", padx=6)
        RetroButton(btn_row, self.app, "SUBMIT",   command=self._submit).pack(side="left", padx=6)

        # Comments
        tk.Label(self, text="COMMENTS", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(pady=(8, 2))
        self._comment_entry = RetroEntry(self, self.app, width=32)
        self._comment_entry.pack()
        RetroButton(self, self.app, "POST",
                    command=self._post_comment).pack(pady=4)
        # Fixed-height scrollable comments area — prevents window growing
        comments_container = tk.Frame(self, bg=t["bg"], height=100)
        comments_container.pack(fill="x", padx=40, pady=(0, 8))
        comments_container.pack_propagate(False)

        canvas = tk.Canvas(comments_container, bg=t["bg"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(comments_container, orient="vertical",
                                 command=canvas.yview)
        self._comments_frame = tk.Frame(canvas, bg=t["bg"])
        self._comments_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._comments_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

    def apply_theme(self) -> None:
        """Propagate theme change to screen and grid."""
        from screens.base import apply_theme_to_widget
        t = self.theme
        # Full recursive walk for all non-grid widgets
        apply_theme_to_widget(self, t)
        # Grid needs its own apply since it manages colours internally
        self._grid.apply_theme()
        # Timer label needs accent2 specifically — override after walk
        self._timer_lbl.config(bg=t["bg"], fg=t["accent2"])

    def load_puzzle(self, puzzle_id: int) -> None:
        result = self.app.server.get_puzzle(puzzle_id)
        if result["status"] != "ok":
            messagebox.showerror("Error", "Could not load puzzle.")
            return
        puzzle = result["puzzle"]
        self._puzzle_id = puzzle_id
        self._title_lbl.config(text=f"Puzzle #{puzzle_id}")
        # Handle both plain digit string and comma-separated formats
        raw = puzzle["initial_grid"].strip()
        flat = [int(x) for x in (raw.split(",") if "," in raw else list(raw))]
        grid = [flat[i*9:(i+1)*9] for i in range(9)]
        self._grid.load_puzzle(grid)
        self._timer.reset()
        self._timer.start()
        self._load_comments()

    def _back(self) -> None:
        self._timer.stop()
        self.app.show_frame("LobbyScreen")

    def _hint(self) -> None:
        if not self._puzzle_id:
            return
        flat = ",".join(str(c) for row in self._grid.get_current_grid() for c in row)
        result = self.app.server.get_hint(self._puzzle_id, flat)
        if result["status"] == "ok":
            self._grid.highlight_hint(result["row"], result["col"], result["value"])
        else:
            messagebox.showinfo("Hint", "No hint available.")

    def _validate(self) -> None:
        if not self._puzzle_id:
            return
        flat = ",".join(str(c) for row in self._grid.get_current_grid() for c in row)
        result = self.app.server.validate_grid(self._puzzle_id, flat)
        if result.get("valid"):
            messagebox.showinfo("Validate", "Looking good so far!")
        else:
            messagebox.showwarning("Validate", "There are some errors.")

    def _submit(self) -> None:
        if not self._puzzle_id:
            return
        elapsed = self._timer.stop()
        flat    = ",".join(str(c) for row in self._grid.get_current_grid() for c in row)
        result  = self.app.server.submit_solve(self._puzzle_id, elapsed, flat)
        if result["status"] == "ok":
            m, s = divmod(elapsed, 60)
            messagebox.showinfo("Solved!", f"Puzzle complete!  Time: {m:02d}:{s:02d}")
            self.app.show_frame("LobbyScreen")
        else:
            messagebox.showerror("Error", result.get("message", "Submission failed."))

    def _load_comments(self) -> None:
        for w in self._comments_frame.winfo_children():
            w.destroy()
        result = self.app.server.get_comments(self._puzzle_id)
        if result["status"] != "ok":
            return
        t = self.theme
        for c in result["comments"]:
            text = c.get("comment_text") or c.get("text", "")
            tk.Label(self._comments_frame,
                     text=f"[{c['username']}]  {text}",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text"],
                     anchor="w").pack(fill="x", pady=2)

    def _post_comment(self) -> None:
        text = self._comment_entry.get().strip()
        if not text or not self._puzzle_id:
            return
        self.app.server.add_comment(self._puzzle_id, text)
        self._comment_entry.delete(0, tk.END)
        self._load_comments()