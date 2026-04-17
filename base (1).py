# base.py - BaseScreen parent class and shared widgets

import tkinter as tk
from theme import FONT_BODY, FONT_BTN
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class BaseScreen(tk.Frame):
    """Parent class for all screens, provides theme shortcut and app reference"""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        self.app = app
        super().__init__(parent, bg=app.theme["bg"])

    def apply_theme(self) -> None:
        """Called when theme toggled by user"""
        self.config(bg=self.app.theme["bg"])


class RetroButton(tk.Button):
    """Themed button used across all screens"""

    def __init__(self, parent: tk.Widget, app: "App", text: str, **kwargs) -> None:
        t = app.theme
        super().__init__(
            parent, text=text, font=FONT_BTN,
            bg=t["btn_bg"], fg=t["btn_fg"],
            activebackground=t["accent2"],
            relief="flat", padx=14, pady=6,
            cursor="hand2", **kwargs,
        )


class RetroEntry(tk.Entry):
    """Themed entry field used across all screens"""

    def __init__(self, parent: tk.Widget, app: "App", **kwargs) -> None:
        t = app.theme
        super().__init__(
            parent, font=FONT_BODY,
            bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"],
            relief="flat", bd=4, **kwargs,
        )


class PlaceholderScreen(BaseScreen):
    """Temporary screen for ones that are not built yet"""

    def __init__(self, parent: tk.Widget, app: "App", name: str) -> None:
        super().__init__(parent, app)
        t = self.app.theme
        tk.Label(self, text=f"{name}\n(coming soon)",
                 font=FONT_BODY, bg=t["bg"], fg=t["text_dim"]).pack(expand=True)
        RetroButton(self, app, "← BACK",
                    command=lambda: app.show_frame("LobbyScreen")).pack(pady=20)
