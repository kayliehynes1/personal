# screens/register.py -add registration screen

import tkinter as tk
from tkinter import messagebox
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_TITLE, FONT_SMALL
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class RegisterScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        tk.Label(self, text="REGISTER", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(60, 40))

        form = tk.Frame(self, bg=t["bg_secondary"], padx=40, pady=40)
        form.pack()

        tk.Label(form, text="USERNAME", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._username = RetroEntry(form, self.app, width=28)
        self._username.pack(pady=(4, 16))

        tk.Label(form, text="PASSWORD", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._password = RetroEntry(form, self.app, width=28, show="*")
        self._password.pack(pady=(4, 16))

        tk.Label(form, text="CONFIRM PASSWORD", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        self._confirm = RetroEntry(form, self.app, width=28, show="*")
        self._confirm.pack(pady=(4, 24))

        RetroButton(form, self.app, "CREATE ACCOUNT",
                    command=self._register).pack(fill="x")

        tk.Label(self, text="← Back to login", font=FONT_SMALL,
                 bg=t["bg"], fg=t["accent"], cursor="hand2").pack(pady=16)
        self.winfo_children()[-1].bind(
            "<Button-1>", lambda e: self.app.show_frame("LoginScreen"))

    def _register(self) -> None:
        username = self._username.get().strip()
        password = self._password.get().strip()
        confirm  = self._confirm.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing fields", "Please fill in all fields.")
            return
        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords do not match.")
            return
        result = self.app.server.register(username, password)
        if result["status"] == "ok":
            messagebox.showinfo("Success", "Account created. Please log in.")
            self.app.show_frame("LoginScreen")
        else:
            messagebox.showerror("Error", result.get("message", "Unknown error"))