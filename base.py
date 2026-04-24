"""screens/base.py — BaseScreen parent class and shared widgets."""

import tkinter as tk
from theme import FONT_BODY, FONT_BTN
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


# All known bg values across both themes — used to remap on toggle
_ALL_BG = {
    "#1a1a2e", "#16213e",   # dark bg, bg_secondary
    "#fdf6e3", "#eee8d5",   # light bg, bg_secondary
}
_ALL_SECONDARY = {"#16213e", "#eee8d5"}


def apply_theme_to_widget(widget: tk.Widget, t: dict) -> None:
    """Recursively update bg/fg on all widgets in a hierarchy."""
    from screens.base import RetroButton
    wtype = widget.winfo_class()
    try:
        if wtype == "Frame":
            current_bg = widget.cget("bg")
            # Preserve secondary panels vs main background
            if current_bg in _ALL_SECONDARY:
                widget.config(bg=t["bg_secondary"])
            else:
                widget.config(bg=t["bg"])
        elif wtype == "Label":
            current_bg = widget.cget("bg")
            new_bg = t["bg_secondary"] if current_bg in _ALL_SECONDARY else t["bg"]
            current_fg = widget.cget("fg")
            # Preserve accent-coloured labels (titles, links)
            if current_fg in (t.get("accent",""), "#e94560", "#cb4b16"):
                new_fg = t["accent"]
            elif current_fg in ("#8888aa", "#888888", t.get("text_dim","")):
                new_fg = t["text_dim"]
            else:
                new_fg = t["text"]
            widget.config(bg=new_bg, fg=new_fg)
        elif wtype == "Button":
            # Plain tk.Button (theme toggle button) — not RetroButton
            if not isinstance(widget, RetroButton):
                current_bg = widget.cget("bg")
                new_bg = t["bg_secondary"] if current_bg in _ALL_SECONDARY else t["bg"]
                widget.config(bg=new_bg, fg=t["text_dim"])
        elif wtype in ("Entry", "Text"):
            widget.config(bg=t["entry_bg"], fg=t["entry_fg"],
                          insertbackground=t["text"])
        elif wtype == "Canvas":
            current_bg = widget.cget("bg")
            new_bg = t["bg_secondary"] if current_bg in _ALL_SECONDARY else t["bg"]
            widget.config(bg=new_bg)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        apply_theme_to_widget(child, t)


class BaseScreen(tk.Frame):
    """Parent class for all screens. Provides theme shortcut and app reference."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        self.app = app
        super().__init__(parent, bg=app.theme["bg"])

    @property
    def theme(self) -> dict:
        return self.app.theme

    def apply_theme(self) -> None:
        """Recursively restyle all child widgets on theme toggle."""
        apply_theme_to_widget(self, self.theme)


class RetroButton(tk.Button):
    """Themed button used across all screens."""

    def __init__(self, parent: tk.Widget, app: "App", text: str, **kwargs) -> None:
        self._app = app
        t = app.theme
        super().__init__(
            parent, text=text, font=FONT_BTN,
            bg=t["btn_bg"], fg=t["btn_fg"],
            activebackground=t["accent2"],
            relief="flat", padx=14, pady=6,
            cursor="hand2", **kwargs,
        )

    def apply_theme(self, t: dict) -> None:
        self.config(bg=t["btn_bg"], fg=t["btn_fg"],
                    activebackground=t["accent2"])


class RetroEntry(tk.Entry):
    """Themed entry field used across all screens."""

    def __init__(self, parent: tk.Widget, app: "App", **kwargs) -> None:
        t = app.theme
        super().__init__(
            parent, font=FONT_BODY,
            bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"],
            relief="flat", bd=4, **kwargs,
        )