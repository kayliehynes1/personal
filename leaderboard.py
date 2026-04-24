#leaderboard now reloads every time the screen is raised

import tkinter as tk
from screens.base import BaseScreen, RetroButton
from theme import FONT_TITLE, FONT_SMALL, FONT_BODY
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class LeaderboardScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)

        tk.Label(self, text="LEADERBOARD", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(40, 30))

        # CHANGED: panel stored so _load_board can repopulate it
        self._panel = tk.Frame(self, bg=t["bg_secondary"], padx=50, pady=30)
        self._panel.pack()

        # Header row — static, only built once
        header = tk.Frame(self._panel, bg=t["bg_secondary"])
        header.pack(fill="x", pady=(0, 8))
        for txt, w in [("RANK", 6), ("USERNAME", 18), ("SOLVED", 10), ("AVG TIME", 12)]:
            tk.Label(header, text=txt, font=FONT_SMALL, width=w,
                     bg=t["bg_secondary"], fg=t["text_dim"],
                     anchor="w").pack(side="left")

        # CHANGED: rows container separate so it can be cleared on refresh
        self._rows_frame = tk.Frame(self._panel, bg=t["bg_secondary"])
        self._rows_frame.pack(fill="x")

        self._load_board()

    def _load_board(self) -> None:
        """Fetch latest leaderboard data and redraw rows."""
        for w in self._rows_frame.winfo_children():
            w.destroy()
        t = self.theme
        result = self.app.server.get_leaderboard()
        board  = result.get("leaderboard", [])
        for i, entry in enumerate(board, start=1):
            row = tk.Frame(self._rows_frame, bg=t["bg_secondary"])
            row.pack(fill="x", pady=3)
            colour   = t["accent"] if entry.get("username") == self.app.username else t["text"]
            solved   = entry.get("puzzles_solved") or entry.get("solved", 0)
            avg_time = entry.get("avg_time")
            avg_str  = f"{round(avg_time)}s" if avg_time else "-"
            for val, w in [
                (f"#{i}",                    6),
                (entry.get("username", "?"), 18),
                (str(solved),               10),
                (avg_str,                   12),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, width=w,
                         bg=t["bg_secondary"], fg=colour,
                         anchor="w").pack(side="left")

    # CHANGED: added tkraise so leaderboard refreshes every time screen is shown
    def tkraise(self, *args) -> None:
        super().tkraise(*args)
        self._load_board()
