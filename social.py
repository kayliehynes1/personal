# Changed search by username instead of user ID, added pending requests section with Accept buttons, friends list and feed refresh on every screen raise
# and activity feed uses correct field names (activity_type, activity_data, timestamp)

import tkinter as tk
from tkinter import messagebox
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_TITLE, FONT_SMALL, FONT_BODY, FONT_HEADER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class SocialScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)

        tk.Label(self, text="SOCIAL", font=FONT_TITLE,
                 bg=t["bg"], fg=t["accent"]).pack(pady=(30, 20))

        content = tk.Frame(self, bg=t["bg"])
        content.pack(fill="both", expand=True, padx=40, pady=10)

        self._build_friends(content)
        self._build_feed(content)

    def _build_friends(self, parent: tk.Frame) -> None:
        t = self.theme
        left = tk.Frame(parent, bg=t["bg_secondary"], padx=20, pady=20)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left, text="FRIENDS", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["accent"]).pack(anchor="w", pady=(0, 6))

        # Friends list container — cleared and reloaded on each raise
        self._friends_list = tk.Frame(left, bg=t["bg_secondary"])
        self._friends_list.pack(anchor="w", fill="x")

        # CHANGED: pending requests section with Accept buttons
        tk.Label(left, text="PENDING REQUESTS", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w", pady=(16, 4))
        self._pending_list = tk.Frame(left, bg=t["bg_secondary"])
        self._pending_list.pack(anchor="w", fill="x")

        # CHANGED: entry now accepts username not ID
        tk.Label(left, text="ADD FRIEND BY USERNAME", font=FONT_SMALL,
                 bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w", pady=(16, 4))
        self._friend_entry = RetroEntry(left, self.app, width=20)
        self._friend_entry.pack(anchor="w")
        RetroButton(left, self.app, "SEND REQUEST",
                    command=self._send_request).pack(anchor="w", pady=8)

    def _build_feed(self, parent: tk.Frame) -> None:
        t = self.theme
        right = tk.Frame(parent, bg=t["bg_secondary"], padx=20, pady=20)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="ACTIVITY FEED", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["accent"]).pack(anchor="w", pady=(0, 12))

        self._feed_frame = tk.Frame(right, bg=t["bg_secondary"])
        self._feed_frame.pack(anchor="w", fill="x")

    # CHANGED: reload data every time the screen is shown
    def tkraise(self, *args) -> None:
        super().tkraise(*args)
        self._load_friends()
        self._load_pending()
        self._load_feed()

    def _load_friends(self) -> None:
        for w in self._friends_list.winfo_children():
            w.destroy()
        t = self.theme
        result = self.app.server.get_friends(self.app.user_id)
        friends = result.get("friends", [])
        if not friends:
            tk.Label(self._friends_list, text="No friends yet.", font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
        for friend in friends:
            tk.Label(self._friends_list, text=f"• {friend['username']}", font=FONT_BODY,
                     bg=t["bg_secondary"], fg=t["text"]).pack(anchor="w", pady=2)

    def _load_pending(self) -> None:
        for w in self._pending_list.winfo_children():
            w.destroy()
        t = self.theme
        result = self.app.server.get_pending_requests(self.app.user_id)
        requests = result.get("requests", [])
        if not requests:
            tk.Label(self._pending_list, text="No pending requests.", font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
            return
        for req in requests:
            row = tk.Frame(self._pending_list, bg=t["bg_secondary"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=req["username"], font=FONT_BODY,
                     bg=t["bg_secondary"], fg=t["text"]).pack(side="left")
            # CHANGED: Accept button calls accept_friend with the requester's ID
            RetroButton(row, self.app, "ACCEPT",
                        command=lambda fid=req["id"]: self._accept_request(fid)).pack(side="right")

    def _load_feed(self) -> None:
        for w in self._feed_frame.winfo_children():
            w.destroy()
        t = self.theme
        result = self.app.server.get_activity_feed(self.app.user_id)
        feed = result.get("feed", [])
        if not feed:
            tk.Label(self._feed_frame, text="No activity yet.", font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(anchor="w")
            return
        for item in feed:
            # CHANGED: uses correct field names returned by database
            username  = item.get("username", "?")
            activity  = item.get("activity_type", "")
            data      = item.get("activity_data", "")
            timestamp = item.get("timestamp", "")[:16]
            text = f"{username} — {activity} {data}  {timestamp}"
            tk.Label(self._feed_frame, text=text, font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text"],
                     wraplength=260, justify="left").pack(anchor="w", pady=3)

    def _send_request(self) -> None:
        username = self._friend_entry.get().strip()
        if not username:
            return
        # CHANGED: look up user ID from username first
        lookup = self.app.server.find_user(username)
        if lookup.get("status") != "ok":
            messagebox.showerror("Not found", f"No user named '{username}'.")
            return
        friend_id = lookup["user"]["id"]
        result = self.app.server.add_friend(friend_id)
        if result["status"] == "ok":
            messagebox.showinfo("Sent!", f"Friend request sent to {username}.")
            self._friend_entry.delete(0, tk.END)
            self._load_pending()
        else:
            messagebox.showerror("Error", result.get("message", "Could not send request."))

    def _accept_request(self, friend_id: int) -> None:
        # CHANGED: new method to accept incoming friend requests
        result = self.app.server.accept_friend(friend_id)
        if result["status"] == "ok":
            messagebox.showinfo("Accepted!", "Friend request accepted.")
            self._load_friends()
            self._load_pending()
        else:
            messagebox.showerror("Error", result.get("message", "Could not accept request."))
