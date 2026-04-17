# screens.py — all screens for the Sudoku client
# Client teammate responsibility
#
# Contains:
#   LoginScreen, RegisterScreen, LobbyScreen, PuzzleScreen,
#   AddPuzzleScreen, StatsScreen, LeaderboardScreen, SocialScreen

import time
import tkinter as tk
from typing import Optional, TYPE_CHECKING

from base import BaseScreen, RetroButton, RetroEntry
from theme import (FONT_TITLE, FONT_HEADER, FONT_BODY,
                   FONT_CELL, FONT_SMALL, FONT_BTN)

if TYPE_CHECKING:
    from client import App


# ── LoginScreen ───────────────────────────────────────────────────────────────

class LoginScreen(BaseScreen):
    """Login screen — username + password, leads to LobbyScreen on success."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        wrapper = tk.Frame(self, bg=t["bg"])
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrapper, text="SUDOKU", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(0, 30))

        tk.Label(wrapper, text="Username", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
        self._username = RetroEntry(wrapper, self.app, width=28)
        self._username.pack(pady=(0, 12))

        tk.Label(wrapper, text="Password", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
        self._password = RetroEntry(wrapper, self.app, width=28, show="•")
        self._password.pack(pady=(0, 20))

        self._msg = tk.Label(wrapper, text="", font=FONT_SMALL,
                             bg=t["bg"], fg=t["accent"])
        self._msg.pack(pady=(0, 8))

        RetroButton(wrapper, self.app, "LOG IN",
                    command=self._on_login).pack(fill="x", pady=(0, 8))
        RetroButton(wrapper, self.app, "REGISTER",
                    command=lambda: self.app.show_frame("RegisterScreen")).pack(fill="x")

        tk.Button(self, text="☀ / ☾", font=FONT_SMALL, relief="flat",
                  bg=t["bg"], fg=t["text_dim"], cursor="hand2",
                  command=self.app.toggle_theme).place(relx=1.0, rely=0.0,
                                                       anchor="ne", x=-10, y=10)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _on_login(self) -> None:
        username = self._username.get().strip()
        password = self._password.get()
        if not username or not password:
            self._msg.config(text="Please enter username and password.")
            return
        result = self.app.server.login(username, password)
        if result.get("status") == "ok":
            self.app.set_user(result["user_id"], result["username"])
            self._msg.config(text="")
            self._password.delete(0, "end")
            self.app.show_frame("LobbyScreen")
        else:
            self._msg.config(text=result.get("message", "Login failed."))


# ── RegisterScreen ────────────────────────────────────────────────────────────

class RegisterScreen(BaseScreen):
    """New account screen."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        wrapper = tk.Frame(self, bg=t["bg"])
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrapper, text="REGISTER", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(0, 30))

        tk.Label(wrapper, text="Username", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
        self._username = RetroEntry(wrapper, self.app, width=28)
        self._username.pack(pady=(0, 12))

        tk.Label(wrapper, text="Password", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
        self._password = RetroEntry(wrapper, self.app, width=28, show="•")
        self._password.pack(pady=(0, 12))

        tk.Label(wrapper, text="Confirm Password", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
        self._confirm = RetroEntry(wrapper, self.app, width=28, show="•")
        self._confirm.pack(pady=(0, 20))

        self._msg = tk.Label(wrapper, text="", font=FONT_SMALL,
                             bg=t["bg"], fg=t["accent"])
        self._msg.pack(pady=(0, 8))

        RetroButton(wrapper, self.app, "CREATE ACCOUNT",
                    command=self._on_register).pack(fill="x", pady=(0, 8))
        RetroButton(wrapper, self.app, "← BACK TO LOGIN",
                    command=lambda: self.app.show_frame("LoginScreen")).pack(fill="x")

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _on_register(self) -> None:
        username = self._username.get().strip()
        password = self._password.get()
        confirm  = self._confirm.get()
        if not username or not password:
            self._msg.config(text="All fields are required.")
            return
        if password != confirm:
            self._msg.config(text="Passwords do not match.")
            return
        if len(password) < 4:
            self._msg.config(text="Password must be at least 4 characters.")
            return
        result = self.app.server.register(username, password)
        if result.get("status") == "ok":
            self._msg.config(text="Account created! Please log in.",
                             fg=self.app.theme["accent2"])
            self._username.delete(0, "end")
            self._password.delete(0, "end")
            self._confirm.delete(0, "end")
            self.after(1200, lambda: self.app.show_frame("LoginScreen"))
        else:
            self._msg.config(text=result.get("message", "Registration failed."),
                             fg=self.app.theme["accent"])


# ── LobbyScreen ───────────────────────────────────────────────────────────────

_DIFFICULTY_COLOURS = {"easy": "#4caf50", "medium": "#ff9800", "hard": "#f44336"}


class LobbyScreen(BaseScreen):
    """Main lobby — puzzle list and navigation to all other screens."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        tk.Label(bar, text="SUDOKU", font=FONT_TITLE,
                 bg=t["bg_secondary"], fg=t["accent"]).pack(side="left", padx=16)
        self._user_label = tk.Label(bar, text="", font=FONT_SMALL,
                                    bg=t["bg_secondary"], fg=t["text_dim"])
        self._user_label.pack(side="right", padx=16)
        tk.Button(bar, text="☀ / ☾", font=FONT_SMALL, relief="flat",
                  bg=t["bg_secondary"], fg=t["text_dim"], cursor="hand2",
                  command=self.app.toggle_theme).pack(side="right", padx=4)

        nav = tk.Frame(self, bg=t["bg"], pady=6)
        nav.pack(fill="x", padx=16)
        for label, screen in [("+ ADD PUZZLE", "AddPuzzleScreen"),
                               ("MY STATS",     "StatsScreen"),
                               ("LEADERBOARD",  "LeaderboardScreen"),
                               ("SOCIAL",       "SocialScreen")]:
            RetroButton(nav, self.app, label,
                        command=lambda s=screen: self.app.show_frame(s)).pack(
                side="left", padx=6, pady=6)
        RetroButton(nav, self.app, "LOG OUT",
                    command=self._logout).pack(side="right", padx=6, pady=6)

        hdr = tk.Frame(self, bg=t["bg_secondary"])
        hdr.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(hdr, text="Puzzles", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left", padx=10, pady=6)
        RetroButton(hdr, self.app, "↺ REFRESH",
                    command=self._load_puzzles).pack(side="right", padx=8, pady=4)

        lf = tk.Frame(self, bg=t["bg"])
        lf.pack(fill="both", expand=True, padx=16, pady=8)
        self._canvas = tk.Canvas(lf, bg=t["bg"], highlightthickness=0)
        sb = tk.Scrollbar(lf, orient="vertical", command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg=t["bg"])
        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(
                             scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._status = tk.Label(self, text="", font=FONT_SMALL,
                                bg=t["bg"], fg=t["text_dim"])
        self._status.pack(pady=4)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self._load_puzzles()

    def tkraise(self, *args) -> None:  # type: ignore[override]
        super().tkraise(*args)
        if self.app.username:
            self._user_label.config(text=f"👤 {self.app.username}")
        self._load_puzzles()

    def _load_puzzles(self) -> None:
        for w in self._inner.winfo_children():
            w.destroy()
        self._status.config(text="Loading…")
        result  = self.app.server.get_puzzles()
        puzzles = result.get("puzzles", []) if isinstance(result, dict) else []
        if not puzzles:
            self._status.config(text="No puzzles found — add one!")
            return
        self._status.config(text="")
        t = self.app.theme
        for p in puzzles:
            row = tk.Frame(self._inner, bg=t["bg_secondary"], pady=6, padx=10)
            row.pack(fill="x", pady=3)
            diff   = (p.get("difficulty") or "medium").lower()
            colour = _DIFFICULTY_COLOURS.get(diff, t["text_dim"])
            tk.Label(row, text=f"Puzzle #{p['id']}", font=FONT_BODY,
                     bg=t["bg_secondary"], fg=t["text"]).pack(side="left")
            tk.Label(row, text=f"  {diff}", font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=colour).pack(side="left")
            tk.Label(row, text=f"  by {p.get('author') or 'unknown'}",
                     font=FONT_SMALL, bg=t["bg_secondary"],
                     fg=t["text_dim"]).pack(side="left")
            RetroButton(row, self.app, "PLAY",
                        command=lambda pid=p["id"]: self._open(pid)).pack(
                side="right", padx=4)

    def _open(self, puzzle_id: int) -> None:
        self.app.current_puzzle_id = puzzle_id
        self.app.frames["PuzzleScreen"].load_puzzle(puzzle_id)
        self.app.show_frame("PuzzleScreen")

    def _logout(self) -> None:
        self.app.user_id         = None
        self.app.username        = None
        self.app.server.user_id  = None
        self.app.server.username = None
        self.app.show_frame("LoginScreen")


# ── PuzzleScreen ──────────────────────────────────────────────────────────────

_GIVEN_FG = "#aaaacc"
_USER_FG  = "#eaeaea"
_ERROR_BG = "#6b0f1a"
_HINT_FG  = "#f5a623"


class PuzzleScreen(BaseScreen):
    """Interactive Sudoku grid with timer, hints, validation and submission."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._puzzle:      Optional[dict] = None
        self._cells:       list[tk.Label] = []
        self._given:       list[bool]     = []
        self._user_values: list[int]      = []
        self._selected:    Optional[int]  = None
        self._start_time:  float          = 0.0
        self._timer_id:    Optional[str]  = None
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← LOBBY",
                    command=self._back).pack(side="left", padx=10)
        self._title_label = tk.Label(bar, text="", font=FONT_HEADER,
                                     bg=t["bg_secondary"], fg=t["text"])
        self._title_label.pack(side="left", padx=16)
        self._timer_label = tk.Label(bar, text="00:00", font=FONT_HEADER,
                                     bg=t["bg_secondary"], fg=t["accent2"])
        self._timer_label.pack(side="right", padx=16)

        self._grid_frame = tk.Frame(self, bg=t["bg"])
        self._grid_frame.pack(expand=True)

        btn_row = tk.Frame(self, bg=t["bg"])
        btn_row.pack(pady=10)
        for label, cmd in [("HINT",     self._hint),
                            ("VALIDATE", self._validate),
                            ("SUBMIT",   self._submit),
                            ("CLEAR",    self._clear)]:
            RetroButton(btn_row, self.app, label, command=cmd).pack(side="left", padx=6)

        self._msg = tk.Label(self, text="", font=FONT_SMALL,
                             bg=t["bg"], fg=t["accent"])
        self._msg.pack(pady=4)

        pad = tk.Frame(self, bg=t["bg"])
        pad.pack(pady=(0, 12))
        for n in range(1, 10):
            tk.Button(pad, text=str(n), font=FONT_BTN, width=3,
                      bg=t["entry_bg"], fg=t["text"],
                      activebackground=t["accent2"], relief="flat", cursor="hand2",
                      command=lambda v=n: self._enter(v)).pack(side="left", padx=2)
        tk.Button(pad, text="⌫", font=FONT_BTN, width=3,
                  bg=t["entry_bg"], fg=t["accent"],
                  activebackground=t["accent2"], relief="flat", cursor="hand2",
                  command=lambda: self._enter(0)).pack(side="left", padx=2)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._cells = []
        self._build()
        if self._puzzle:
            self.load_puzzle(self._puzzle["id"])

    def load_puzzle(self, puzzle_id: int) -> None:
        result = self.app.server.get_puzzle(puzzle_id)
        if result.get("status") != "ok":
            self._msg.config(text="Could not load puzzle.")
            return
        self._puzzle      = result["puzzle"]
        self._selected    = None
        initial: str      = self._puzzle["initial_grid"]
        self._given       = [ch != "0" for ch in initial]
        self._user_values = [int(ch) for ch in initial]
        self._title_label.config(text=f"Puzzle #{puzzle_id}")
        self._msg.config(text="")
        self._draw_grid()
        self._refresh_cells()
        self._start_timer()

    def _draw_grid(self) -> None:
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._cells = []
        t, size, box = self.app.theme, 9, 3
        for idx in range(81):
            r, c = divmod(idx, size)
            cell = tk.Label(self._grid_frame, text="", font=FONT_CELL,
                            width=2, height=1, bg=t["entry_bg"], fg=t["text"],
                            relief="flat", bd=0)
            cell.grid(row=r, column=c,
                      padx=(3 if c % box == 0 else 1, 3 if c == size - 1 else 0),
                      pady=(3 if r % box == 0 else 1, 3 if r == size - 1 else 0),
                      ipadx=4, ipady=4)
            cell.bind("<Button-1>", lambda e, i=idx: self._select(i))
            self._cells.append(cell)
        self.bind_all("<Key>", self._on_key)

    def _refresh_cells(self) -> None:
        t = self.app.theme
        for idx, cell in enumerate(self._cells):
            val = self._user_values[idx]
            bg  = t["bg_secondary"] if idx == self._selected else t["entry_bg"]
            cell.config(text=str(val) if val != 0 else "",
                        bg=bg,
                        fg=_GIVEN_FG if self._given[idx] else _USER_FG)

    def _select(self, idx: int) -> None:
        self._selected = idx if not self._given[idx] else None
        self._refresh_cells()

    def _enter(self, value: int) -> None:
        if self._selected is None:
            return
        self._user_values[self._selected] = value
        self._refresh_cells()

    def _on_key(self, event: tk.Event) -> None:
        if event.char.isdigit():
            self._enter(int(event.char))
        elif event.keysym == "BackSpace":
            self._enter(0)

    def _start_timer(self) -> None:
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self._start_time = time.monotonic()
        self._tick()

    def _tick(self) -> None:
        m, s = divmod(int(time.monotonic() - self._start_time), 60)
        self._timer_label.config(text=f"{m:02d}:{s:02d}")
        self._timer_id = self.after(1000, self._tick)

    def _stop_timer(self) -> int:
        elapsed = int(time.monotonic() - self._start_time)
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        return elapsed

    def _hint(self) -> None:
        if not self._puzzle or self._selected is None:
            self._msg.config(text="Select an empty cell first.")
            return
        grid_str = "".join(str(v) for v in self._user_values)
        result   = self.app.server.get_hint(self._puzzle["id"], grid_str)
        if result.get("status") == "ok":
            r, c, v = result["row"], result["col"], result["value"]
            idx = r * 9 + c
            self._user_values[idx] = v
            self._refresh_cells()
            self._cells[idx].config(fg=_HINT_FG)
            self._msg.config(text=f"Hint: row {r}, col {c} = {v}",
                             fg=self.app.theme["accent2"])
        else:
            self._msg.config(text=result.get("message", "No hint available."))

    def _validate(self) -> None:
        if not self._puzzle:
            return
        solution = self._puzzle["solution_grid"]
        grid_str = "".join(str(v) for v in self._user_values)
        t        = self.app.theme
        for idx, cell in enumerate(self._cells):
            cell.config(bg=t["bg_secondary"] if idx == self._selected else t["entry_bg"])
        errors = [i for i, (u, s) in enumerate(zip(grid_str, solution))
                  if u != "0" and u != s]
        for i in errors:
            self._cells[i].config(bg=_ERROR_BG)
        if errors:
            self._msg.config(text=f"{len(errors)} incorrect cell(s) highlighted.",
                             fg=t["accent"])
        else:
            self._msg.config(text="All filled cells are correct! ✓", fg=t["accent2"])

    def _submit(self) -> None:
        if not self._puzzle:
            return
        if 0 in self._user_values:
            self._msg.config(text="Fill all cells before submitting.")
            return
        grid_str = "".join(str(v) for v in self._user_values)
        elapsed  = self._stop_timer()
        result   = self.app.server.submit_solve(self._puzzle["id"], grid_str, elapsed)
        if result.get("status") == "ok":
            m, s = divmod(elapsed, 60)
            self._msg.config(text=f"Solved in {m:02d}:{s:02d}! 🎉",
                             fg=self.app.theme["accent2"])
        else:
            self._msg.config(text=result.get("message", "Incorrect solution."))
            self._start_timer()

    def _clear(self) -> None:
        self._refresh_cells()
        self._msg.config(text="")

    def _back(self) -> None:
        self._stop_timer()
        self.app.show_frame("LobbyScreen")


# ── AddPuzzleScreen ───────────────────────────────────────────────────────────

class AddPuzzleScreen(BaseScreen):
    """Form for submitting a new puzzle."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← LOBBY",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=10)
        tk.Label(bar, text="ADD PUZZLE", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left", padx=16)

        w = tk.Frame(self, bg=t["bg"])
        w.pack(expand=True, fill="both", padx=40, pady=20)

        tk.Label(w, text="Difficulty", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).grid(row=0, column=0, sticky="w", pady=6)
        self._diff_var = tk.StringVar(value="medium")
        df = tk.Frame(w, bg=t["bg"])
        df.grid(row=0, column=1, sticky="w", padx=8)
        for d in ("easy", "medium", "hard"):
            tk.Radiobutton(df, text=d.capitalize(), variable=self._diff_var, value=d,
                           font=FONT_SMALL, bg=t["bg"], fg=t["text"],
                           selectcolor=t["bg_secondary"],
                           activebackground=t["bg"]).pack(side="left", padx=6)

        tk.Label(w, text="Initial grid\n(0 = empty)", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).grid(row=1, column=0, sticky="nw", pady=6)
        self._initial = tk.Text(w, font=FONT_SMALL, width=42, height=4,
                                bg=t["entry_bg"], fg=t["entry_fg"],
                                insertbackground=t["text"], relief="flat", bd=4)
        self._initial.grid(row=1, column=1, sticky="w", pady=6, padx=8)

        tk.Label(w, text="Solution grid", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).grid(row=2, column=0, sticky="nw", pady=6)
        self._solution = tk.Text(w, font=FONT_SMALL, width=42, height=4,
                                 bg=t["entry_bg"], fg=t["entry_fg"],
                                 insertbackground=t["text"], relief="flat", bd=4)
        self._solution.grid(row=2, column=1, sticky="w", pady=6, padx=8)

        self._msg = tk.Label(w, text="", font=FONT_SMALL, bg=t["bg"],
                             fg=t["accent"], wraplength=480, justify="left")
        self._msg.grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

        RetroButton(w, self.app, "SUBMIT PUZZLE",
                    command=self._submit).grid(row=4, column=1, sticky="w", padx=8)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _submit(self) -> None:
        initial  = "".join(self._initial.get("1.0", "end").split())
        solution = "".join(self._solution.get("1.0", "end").split())
        if len(initial) != 81 or not initial.isdigit():
            self._msg.config(text=f"Initial grid must be 81 digits (got {len(initial)}).")
            return
        if len(solution) != 81 or not solution.isdigit():
            self._msg.config(text=f"Solution grid must be 81 digits (got {len(solution)}).")
            return
        result = self.app.server.add_puzzle(initial, solution, self._diff_var.get())
        if result.get("status") == "ok":
            self._msg.config(text="Puzzle added! ✓", fg=self.app.theme["accent2"])
            self._initial.delete("1.0", "end")
            self._solution.delete("1.0", "end")
        else:
            self._msg.config(text=result.get("message", "Failed to add puzzle."),
                             fg=self.app.theme["accent"])


# ── StatsScreen ───────────────────────────────────────────────────────────────

def _fmt(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class StatsScreen(BaseScreen):
    """Personal statistics for the logged-in user."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])
        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← LOBBY",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=10)
        tk.Label(bar, text="MY STATS", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left", padx=16)
        RetroButton(bar, self.app, "↺ REFRESH",
                    command=self._load).pack(side="right", padx=10)
        self._content = tk.Frame(self, bg=t["bg"])
        self._content.pack(expand=True)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self._load()

    def tkraise(self, *args) -> None:  # type: ignore[override]
        super().tkraise(*args)
        self._load()

    def _load(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()
        t      = self.app.theme
        result = self.app.server.get_user_stats()
        if result.get("status") != "ok":
            tk.Label(self._content, text="Could not load stats.",
                     font=FONT_BODY, bg=t["bg"], fg=t["accent"]).pack(pady=40)
            return
        stats = result["stats"]
        for label, value in [
            ("Player",          stats.get("username", "—")),
            ("Puzzles solved",  str(stats.get("puzzles_solved", 0))),
            ("Puzzles posted",  str(stats.get("puzzles_posted", 0))),
            ("Best solve time", _fmt(stats.get("best_time"))),
            ("Avg solve time",  _fmt(stats.get("avg_time"))),
        ]:
            row = tk.Frame(self._content, bg=t["bg_secondary"], pady=6, padx=20)
            row.pack(fill="x", pady=3, padx=60)
            tk.Label(row, text=label, font=FONT_BODY, width=20, anchor="w",
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="left")
            tk.Label(row, text=value, font=FONT_BODY, anchor="w",
                     bg=t["bg_secondary"], fg=t["text"]).pack(side="left")


# ── LeaderboardScreen ─────────────────────────────────────────────────────────

_MEDALS = {0: "🥇", 1: "🥈", 2: "🥉"}


class LeaderboardScreen(BaseScreen):
    """Global leaderboard ranked by puzzles solved then average time."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])
        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← LOBBY",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=10)
        tk.Label(bar, text="LEADERBOARD", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left", padx=16)
        RetroButton(bar, self.app, "↺ REFRESH",
                    command=self._load).pack(side="right", padx=10)

        hdr = tk.Frame(self, bg=t["bg_secondary"])
        hdr.pack(fill="x", padx=16, pady=(8, 0))
        for col, width in [("#", 4), ("Player", 20), ("Solved", 8),
                           ("Best", 8), ("Average", 8)]:
            tk.Label(hdr, text=col, font=FONT_SMALL, width=width, anchor="w",
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="left", padx=4, pady=4)

        lf = tk.Frame(self, bg=t["bg"])
        lf.pack(fill="both", expand=True, padx=16, pady=4)
        canvas = tk.Canvas(lf, bg=t["bg"], highlightthickness=0)
        sb     = tk.Scrollbar(lf, orient="vertical", command=canvas.yview)
        self._inner = tk.Frame(canvas, bg=t["bg"])
        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._load()

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def tkraise(self, *args) -> None:  # type: ignore[override]
        super().tkraise(*args)
        self._load()

    def _load(self) -> None:
        for w in self._inner.winfo_children():
            w.destroy()
        t      = self.app.theme
        result = self.app.server.get_leaderboard()
        board  = result.get("leaderboard", []) if isinstance(result, dict) else []
        if not board:
            tk.Label(self._inner, text="No data yet.", font=FONT_BODY,
                     bg=t["bg"], fg=t["text_dim"]).pack(pady=30)
            return
        for rank, entry in enumerate(board):
            is_me = entry.get("username") == self.app.username
            bg    = t["entry_bg"] if is_me else (t["bg_secondary"] if rank % 2 == 0 else t["bg"])
            row   = tk.Frame(self._inner, bg=bg)
            row.pack(fill="x", pady=1)
            fg = t["accent2"] if rank < 3 else t["text"]
            for val, width in [(_MEDALS.get(rank, str(rank + 1)), 4),
                                (entry.get("username", "—"),       20),
                                (str(entry.get("puzzles_solved", 0)), 8),
                                (_fmt(entry.get("best_time")),      8),
                                (_fmt(entry.get("avg_time")),       8)]:
                tk.Label(row, text=val, font=FONT_SMALL, width=width, anchor="w",
                         bg=bg, fg=fg).pack(side="left", padx=4, pady=4)


# ── SocialScreen ──────────────────────────────────────────────────────────────

class SocialScreen(BaseScreen):
    """Social hub: friends, activity feed and puzzle comments."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme
        self.config(bg=t["bg"])

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=8)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← LOBBY",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=10)
        tk.Label(bar, text="SOCIAL", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left", padx=16)
        RetroButton(bar, self.app, "↺ REFRESH",
                    command=self._load_all).pack(side="right", padx=10)

        cols = tk.Frame(self, bg=t["bg"])
        cols.pack(fill="both", expand=True, padx=12, pady=10)

        # Friends
        fc = tk.Frame(cols, bg=t["bg"], width=220)
        fc.pack(side="left", fill="y", padx=(0, 10))
        fc.pack_propagate(False)
        tk.Label(fc, text="Friends", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))
        add_row = tk.Frame(fc, bg=t["bg"])
        add_row.pack(fill="x", pady=(0, 8))
        self._friend_entry = RetroEntry(add_row, self.app, width=12)
        self._friend_entry.pack(side="left", padx=(0, 4))
        RetroButton(add_row, self.app, "+ ADD",
                    command=self._send_request).pack(side="left")
        self._friends_frame = tk.Frame(fc, bg=t["bg"])
        self._friends_frame.pack(fill="both", expand=True)

        # Feed
        feed_col = tk.Frame(cols, bg=t["bg"])
        feed_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(feed_col, text="Activity Feed", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))
        feed_sf = tk.Frame(feed_col, bg=t["bg"])
        feed_sf.pack(fill="both", expand=True)
        feed_canvas = tk.Canvas(feed_sf, bg=t["bg"], highlightthickness=0)
        feed_sb     = tk.Scrollbar(feed_sf, orient="vertical", command=feed_canvas.yview)
        self._feed_inner = tk.Frame(feed_canvas, bg=t["bg"])
        self._feed_inner.bind("<Configure>",
                              lambda e: feed_canvas.configure(
                                  scrollregion=feed_canvas.bbox("all")))
        feed_canvas.create_window((0, 0), window=self._feed_inner, anchor="nw")
        feed_canvas.configure(yscrollcommand=feed_sb.set)
        feed_sb.pack(side="right", fill="y")
        feed_canvas.pack(side="left", fill="both", expand=True)

        # Comments
        cc = tk.Frame(cols, bg=t["bg"], width=260)
        cc.pack(side="left", fill="y")
        cc.pack_propagate(False)
        tk.Label(cc, text="Comments", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))
        pid_row = tk.Frame(cc, bg=t["bg"])
        pid_row.pack(fill="x", pady=(0, 6))
        tk.Label(pid_row, text="Puzzle #", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(side="left")
        self._pid_entry = RetroEntry(pid_row, self.app, width=5)
        self._pid_entry.pack(side="left", padx=4)
        RetroButton(pid_row, self.app, "LOAD",
                    command=self._load_comments).pack(side="left")
        self._comments_frame = tk.Frame(cc, bg=t["bg"])
        self._comments_frame.pack(fill="both", expand=True)
        tk.Label(cc, text="Add comment:", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w", pady=(8, 0))
        self._comment_box = tk.Text(cc, font=FONT_SMALL, width=30, height=3,
                                    bg=t["entry_bg"], fg=t["entry_fg"],
                                    insertbackground=t["text"], relief="flat", bd=4)
        self._comment_box.pack(fill="x", pady=4)
        RetroButton(cc, self.app, "POST",
                    command=self._post_comment).pack(anchor="e")

        self._msg = tk.Label(self, text="", font=FONT_SMALL,
                             bg=t["bg"], fg=t["accent"])
        self._msg.pack(pady=4)

    def apply_theme(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self._load_all()

    def tkraise(self, *args) -> None:  # type: ignore[override]
        super().tkraise(*args)
        self._load_all()

    def _load_all(self) -> None:
        self._load_friends()
        self._load_feed()

    def _load_friends(self) -> None:
        for w in self._friends_frame.winfo_children():
            w.destroy()
        t       = self.app.theme
        result  = self.app.server.get_friends()
        friends = result.get("friends", []) if isinstance(result, dict) else []
        if not friends:
            tk.Label(self._friends_frame, text="No friends yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
            return
        for f in friends:
            tk.Label(self._friends_frame, text=f"• {f['username']}",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=1)

    def _send_request(self) -> None:
        fid_str = self._friend_entry.get().strip()
        if not fid_str.isdigit():
            self._msg.config(text="Enter the numeric user ID to add.")
            return
        result = self.app.server.add_friend(int(fid_str))
        if result.get("status") == "ok":
            self._friend_entry.delete(0, "end")
            self._msg.config(text="Friend request sent!", fg=self.app.theme["accent2"])
            self._load_friends()
        else:
            self._msg.config(text=result.get("message", "Could not send request."),
                             fg=self.app.theme["accent"])

    def _load_feed(self) -> None:
        for w in self._feed_inner.winfo_children():
            w.destroy()
        t      = self.app.theme
        result = self.app.server.get_activity_feed()
        feed   = result.get("feed", []) if isinstance(result, dict) else []
        if not feed:
            tk.Label(self._feed_inner, text="Nothing in your feed yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w", pady=8)
            return
        for item in feed:
            row = tk.Frame(self._feed_inner, bg=t["bg_secondary"], pady=4, padx=8)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=item.get("username", "?"), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["accent2"]).pack(side="left")
            tk.Label(row, text="  " + item.get("message", ""), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text"]).pack(side="left")
            tk.Label(row, text=str(item.get("created_at", ""))[:16], font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="right")

    def _load_comments(self) -> None:
        for w in self._comments_frame.winfo_children():
            w.destroy()
        t = self.app.theme
        try:
            puzzle_id = int(self._pid_entry.get().strip())
        except ValueError:
            self._msg.config(text="Enter a valid puzzle ID.")
            return
        result   = self.app.server.get_comments(puzzle_id)
        comments = result.get("comments", []) if isinstance(result, dict) else []
        if not comments:
            tk.Label(self._comments_frame, text="No comments yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
            return
        for c in comments:
            row = tk.Frame(self._comments_frame, bg=t["bg_secondary"], pady=3, padx=6)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=c.get("username", "?"), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["accent2"]).pack(anchor="w")
            tk.Label(row, text=c.get("comment_text", ""), font=FONT_SMALL,
                     wraplength=200, justify="left",
                     bg=t["bg_secondary"], fg=t["text"]).pack(anchor="w")

    def _post_comment(self) -> None:
        body = self._comment_box.get("1.0", "end").strip()
        if not body:
            return
        try:
            puzzle_id = int(self._pid_entry.get().strip())
        except ValueError:
            self._msg.config(text="Enter a valid puzzle ID.")
            return
        result = self.app.server.add_comment(puzzle_id, body)
        if result.get("status") == "ok":
            self._comment_box.delete("1.0", "end")
            self._msg.config(text="Comment posted! ✓", fg=self.app.theme["accent2"])
            self._load_comments()
        else:
            self._msg.config(text=result.get("message", "Failed to post."),
                             fg=self.app.theme["accent"])
