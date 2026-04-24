# client.py - app controller and entry point

import tkinter as tk
from typing import Optional
 
from theme import THEMES
from server_client import ServerClient
from screens.base import BaseScreen
from screens.login import LoginScreen
from screens.register import RegisterScreen
from screens.lobby import LobbyScreen
from screens.puzzle import PuzzleScreen
from screens.add_puzzle import AddPuzzleScreen
from screens.stats import StatsScreen
from screens.leaderboard import LeaderboardScreen
from screens.social import SocialScreen
 
 
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sudoku Platform")
        self.resizable(False, False)
        self.geometry("600x650")
 
        # Session state
        self.user_id:           Optional[int] = None
        self.username:          Optional[str] = None
        self.current_puzzle_id: Optional[int] = None
 
        # Theme
        self._theme_name: str = "dark"
 
        # Server
        self.server = ServerClient()
 
        # Container
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
 
        # Register all screens
        self.frames: dict[str, BaseScreen] = {}
        self._add_screen("LoginScreen",       LoginScreen(container, self))
        self._add_screen("RegisterScreen",    RegisterScreen(container, self))
        self._add_screen("LobbyScreen",       LobbyScreen(container, self))
        self._add_screen("PuzzleScreen",      PuzzleScreen(container, self))
        self._add_screen("AddPuzzleScreen",   AddPuzzleScreen(container, self))
        self._add_screen("StatsScreen",       StatsScreen(container, self))
        self._add_screen("LeaderboardScreen", LeaderboardScreen(container, self))
        self._add_screen("SocialScreen",      SocialScreen(container, self))
 
        self.show_frame("LoginScreen")
 
    def _add_screen(self, name: str, screen: BaseScreen) -> None:
        self.frames[name] = screen
        screen.grid(row=0, column=0, sticky="nsew")
 
    @property
    def theme(self) -> dict:
        return THEMES[self._theme_name]
 
    def toggle_theme(self) -> None:
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        t = self.theme
        self.config(bg=t["bg"])
        for frame in self.frames.values():
            frame.apply_theme()
        # Update all RetroButtons across all screens
        self._update_buttons(self, t)
 
    def _update_buttons(self, widget: tk.Widget, t: dict) -> None:
        """Walk widget tree and restyle all RetroButtons and accent labels."""
        from screens.base import RetroButton
        if isinstance(widget, RetroButton):
            widget.apply_theme(t)
        for child in widget.winfo_children():
            self._update_buttons(child, t)
 
    def show_frame(self, name: str) -> None:
        self.frames[name].tkraise()
 
    def set_user(self, user_id: int, username: str) -> None:
        self.user_id  = user_id
        self.username = username
 
 
if __name__ == "__main__":
    App().mainloop()