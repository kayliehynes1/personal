# App controller and entry point

import tkinter as tk
from typing import Optional

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sudoku")
        self.resizable(False, False)

        # Session state
        self.user_id:           Optional[int] = None
        self.username:          Optional[str] = None
        self.current_puzzle_id: Optional[int] = None

        # Theme
        self._theme_name: str = "test"

        # Server
        self.server = ServerClient()

        # Container
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Register all screens (at least all the ones in schema)
        self.frames: dict[str, BaseScreen] = {}
        self._add_screen("LoginScreen",       LoginScreen(container, self))
        self._add_screen("RegisterScreen",    RegisterScreen(container, self))
        self._add_screen("LobbyScreen",       LobbyScreen(container, self))
        self._add_screen("PuzzleScreen",      PlaceholderScreen(container, self, "PUZZLE"))
        self._add_screen("AddPuzzleScreen",   PlaceholderScreen(container, self, "ADD PUZZLE"))
        self._add_screen("StatsScreen",       PlaceholderScreen(container, self, "STATS"))
        self._add_screen("LeaderboardScreen", PlaceholderScreen(container, self, "LEADERBOARD"))
        self._add_screen("SocialScreen",      PlaceholderScreen(container, self, "SOCIAL"))

        self.show_frame("LoginScreen")

    def _add_screen(self, name: str, screen: BaseScreen) -> None:
        self.frames[name] = screen
        screen.grid(row=0, column=0, sticky="nsew")

    @property
    def theme(self) -> dict:
        return THEMES[self._theme_name]

    def toggle_theme(self) -> None:
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        for frame in self.frames.values():
            frame.apply_theme()

    def show_frame(self, name: str) -> None:
        self.frames[name].tkraise()

    def set_user(self, user_id: int, username: str) -> None:
        self.user_id  = user_id
        self.username = username


if __name__ == "__main__":
    App().mainloop()