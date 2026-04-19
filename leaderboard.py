# screens/leaderboard.py - global leaderboard screen

import tkinter as tk
from screens.base import BaseScreen, RetroButton
from theme import FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_HEADER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App

_MEDALS = {0: "🥇", 1: "🥈", 2: "🥉"}


def _fmt(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class LeaderboardScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)
        RetroButton(bar, self.app, "↺ REFRESH",
                    command=self._load).pack(side="right", padx=12)

        tk.Label(self, text="LEADERBOARD", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(30, 10))

        # Column headers
        hdr = tk.Frame(self, bg=t["bg_secondary"])
        hdr.pack(fill="x", padx=40, pady=(0, 4))
        for col, width in [("#", 4), ("Player", 20), ("Solved", 8),
                           ("Best", 8), ("Average", 8)]:
            tk.Label(hdr, text=col, font=FONT_SMALL, width=width, anchor="w",
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="left", padx=4, pady=4)

        # Scrollable list
        lf = tk.Frame(self, bg=t["bg"])
        lf.pack(fill="both", expand=True, padx=40, pady=4)
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
            for val, width in [
                (_MEDALS.get(rank, str(rank + 1)),        4),
                (entry.get("username", "—"),             20),
                (str(entry.get("puzzles_solved", 0)),     8),
                (_fmt(entry.get("best_time")),             8),
                (_fmt(entry.get("avg_time")),              8),
            ]:
                tk.Label(row, text=val, font=FONT_SMALL, width=width, anchor="w",
                         bg=bg, fg=fg).pack(side="left", padx=4, pady=6)
