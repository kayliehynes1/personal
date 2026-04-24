# stats now reload every time the screen is raised

import tkinter as tk
from screens.base import BaseScreen, RetroButton
from theme import FONT_TITLE, FONT_SMALL, FONT_BODY, FONT_HEADER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class StatsScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)

        tk.Label(self, text="YOUR STATS", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(40, 30))

        self._panel = tk.Frame(self, bg=t["bg_secondary"], padx=60, pady=40)
        self._panel.pack()
        self._load_stats()

    def _load_stats(self) -> None:
        """Fetch latest stats from server and redraw the panel rows."""
        for w in self._panel.winfo_children():
            w.destroy()
        t = self.theme
        result = self.app.server.get_user_stats()
        stats  = result.get("stats", {})

        # Guard against None values from database when user has no solves yet
        avg_time  = stats.get("avg_time")
        best_time = stats.get("best_time")

        rows = [
            ("Puzzles Solved", stats.get("puzzles_solved", 0)),
            ("Puzzles Posted", stats.get("puzzles_posted", 0)),
            ("Avg Solve Time", f"{round(avg_time)}s" if avg_time else "N/A"),
            ("Best Time",      f"{round(best_time)}s" if best_time else "N/A"),
            ("Global Rank",    f"#{stats.get('rank', '-')}"),
        ]
        for label, value in rows:
            row = tk.Frame(self._panel, bg=t["bg_secondary"])
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, font=FONT_BODY, width=18,
                     bg=t["bg_secondary"], fg=t["text_dim"],
                     anchor="w").pack(side="left")
            tk.Label(row, text=str(value), font=FONT_HEADER,
                     bg=t["bg_secondary"], fg=t["accent2"]).pack(side="left")

    def tkraise(self, *args) -> None:
        super().tkraise(*args)
        self._load_stats()