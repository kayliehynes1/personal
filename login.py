# screens/login.py - login screen

import tkinter as tk
from tkinter import messagebox
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_TITLE, FONT_SMALL
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class LoginScreen(BaseScreen):
    def __init__(self, parent:tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        tk.Label(self, text="SUDOKU", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(60, 4))
        tk.Label(self, text="[ PLATFORM ]", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(pady=(0, 40))
 
        form = tk.Frame(self, bg=t["bg_secondary"], padx=40, pady=40)
        form.pack()
 
        tk.Label(form, text="USERNAME", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._username = RetroEntry(form, self.app, width=28)
        self._username.pack(pady=(4, 16))
 
        tk.Label(form, text="PASSWORD", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._password = RetroEntry(form, self.app, width=28, show="*")
        self._password.pack(pady=(4, 24))
 
        RetroButton(form, self.app, "LOGIN", command=self._login).pack(fill="x")
 
        tk.Label(self, text="No account? REGISTER", font=FONT_SMALL,
                 bg=t["bg"], fg=t["accent"], cursor="hand2").pack(pady=16)
        self.winfo_children()[-1].bind(
            "<Button-1>", lambda e: self.app.show_frame("RegisterScreen"))
 
        tk.Button(self, text="⬛/⬜", font=FONT_SMALL, bg=t["bg"],
                  fg=t["text_dim"], relief="flat",
                  command=self.app.toggle_theme, cursor="hand2").pack()
 
    def _login(self) -> None:
        username = self._username.get().strip()
        password = self._password.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing fields", "Please enter username and password.")
            return
        result = self.app.server.login(username, password)
        if result["status"] == "ok":
            self.app.set_user(result["user_id"], result["username"])
            self.app.show_frame("LobbyScreen")
        else:
            messagebox.showerror("Login failed", result.get("message", "Unknown error"))