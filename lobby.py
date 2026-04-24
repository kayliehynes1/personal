# screens/lobby.py - lobby allows puzzle selection

import tkinter as tk
from screens.base import BaseScreen, RetroButton
from theme import FONT_BODY, FONT_SMALL
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class LobbyScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        tk.Label(bar, text="SUDOKU", font=("Courier", 14, "bold"),
                 bg=t["bg_secondary"], fg=t["accent"]).pack(side="left", padx=16)
        for label, screen in [("SOCIAL", "SocialScreen"),
                               ("LEADERBOARD", "LeaderboardScreen"),
                               ("STATS", "StatsScreen")]:
            RetroButton(bar, self.app, label,
                        command=lambda s=screen: self.app.show_frame(s)).pack(side="right", padx=6)
        tk.Button(bar, text="⬛/⬜", font=FONT_SMALL, relief="flat",
                  bg=t["bg_secondary"], fg=t["text_dim"],
                  command=self.app.toggle_theme, cursor="hand2").pack(side="right", padx=6)

        tk.Label(self, text="SELECT A PUZZLE", font=FONT_BODY,
                 bg=t["bg"], fg=t["text_dim"]).pack(pady=(20, 10))

        # Fixed-height scrollable puzzle list — prevents window growing
        scroll_container = tk.Frame(self, bg=t["bg"], height=300)
        scroll_container.pack(fill="x", padx=40, pady=(0, 4))
        scroll_container.pack_propagate(False)

        canvas = tk.Canvas(scroll_container, bg=t["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        self._list_frame = tk.Frame(canvas, bg=t["bg"])
        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._load_puzzles()

        RetroButton(self, self.app, "+ ADD PUZZLE",
                    command=lambda: self.app.show_frame("AddPuzzleScreen")).pack(pady=16)

    def _load_puzzles(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        result = self.app.server.get_puzzles()
        if result["status"] != "ok":
            tk.Label(self._list_frame, text="Failed to load puzzles.",
                     font=FONT_BODY, bg=self.theme["bg"],
                     fg=self.theme["accent"]).pack()
            return
        for puzzle in result["puzzles"]:
            self._puzzle_row(puzzle)

    def _puzzle_row(self, puzzle: dict) -> None:
        t = self.theme
        row = tk.Frame(self._list_frame, bg=t["bg_secondary"],
                       pady=10, padx=16, cursor="hand2")
        row.pack(fill="x", pady=4)

        title      = f"Puzzle #{puzzle.get('id', '?')}"
        difficulty = puzzle.get("difficulty", "medium")
        author     = puzzle.get("author") or "unknown"

        diff_colour = {"easy": "#00d4aa", "medium": t["accent2"],
                       "hard": t["accent"]}.get(difficulty, t["text"])
        tk.Label(row, text=title, font=FONT_BODY,
                 bg=t["bg_secondary"], fg=t["text"]).pack(side="left")
        tk.Label(row, text=f"[{difficulty.upper()}]", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=diff_colour).pack(side="left", padx=12)
        tk.Label(row, text=f"by {author}", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="left")
        for widget in [row] + list(row.winfo_children()):
            widget.bind("<Button-1>",
                        lambda e, pid=puzzle["id"]: self._open_puzzle(pid))

    def _open_puzzle(self, puzzle_id: int) -> None:
        self.app.current_puzzle_id = puzzle_id
        self.app.show_frame("PuzzleScreen")
        self.app.frames["PuzzleScreen"].load_puzzle(puzzle_id)

    def tkraise(self, *args) -> None:
        """Refresh puzzle list every time lobby is shown."""
        super().tkraise(*args)
        self._load_puzzles()