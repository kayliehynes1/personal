# screens/social.py - social screen: friends, activity feed, comments

import tkinter as tk
from screens.base import BaseScreen, RetroButton, RetroEntry
from theme import FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_HEADER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import App


class SocialScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        t = self.app.theme

        bar = tk.Frame(self, bg=t["bg_secondary"], pady=10)
        bar.pack(fill="x")
        RetroButton(bar, self.app, "← BACK",
                    command=lambda: self.app.show_frame("LobbyScreen")).pack(side="left", padx=12)
        tk.Label(bar, text="SOCIAL", font=FONT_HEADER,
                 bg=t["bg_secondary"], fg=t["accent"]).pack(side="left", padx=12)
        RetroButton(bar, self.app, "↺ REFRESH",
                    command=self._load_all).pack(side="right", padx=12)

        cols = tk.Frame(self, bg=t["bg"])
        cols.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Friends ───────────────────────────────────────────────────────────
        fc = tk.Frame(cols, bg=t["bg"], width=220)
        fc.pack(side="left", fill="y", padx=(0, 10))
        fc.pack_propagate(False)

        tk.Label(fc, text="Friends", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))

        add_row = tk.Frame(fc, bg=t["bg"])
        add_row.pack(fill="x", pady=(0, 8))
        self._friend_entry = RetroEntry(add_row, self.app, width=12)
        self._friend_entry.pack(side="left", padx=(0, 4))
        RetroButton(add_row, self.app, "+ ADD",
                    command=self._send_request).pack(side="left")

        self._friends_frame = tk.Frame(fc, bg=t["bg"])
        self._friends_frame.pack(fill="both", expand=True)

        # ── Activity Feed ─────────────────────────────────────────────────────
        feed_col = tk.Frame(cols, bg=t["bg"])
        feed_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(feed_col, text="Activity Feed", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))
        feed_sf = tk.Frame(feed_col, bg=t["bg"])
        feed_sf.pack(fill="both", expand=True)
        feed_canvas = tk.Canvas(feed_sf, bg=t["bg"], highlightthickness=0)
        feed_sb     = tk.Scrollbar(feed_sf, orient="vertical", command=feed_canvas.yview)
        self._feed_inner = tk.Frame(feed_canvas, bg=t["bg"])
        self._feed_inner.bind("<Configure>",
                              lambda e: feed_canvas.configure(
                                  scrollregion=feed_canvas.bbox("all")))
        feed_canvas.create_window((0, 0), window=self._feed_inner, anchor="nw")
        feed_canvas.configure(yscrollcommand=feed_sb.set)
        feed_sb.pack(side="right", fill="y")
        feed_canvas.pack(side="left", fill="both", expand=True)

        # ── Comments ──────────────────────────────────────────────────────────
        cc = tk.Frame(cols, bg=t["bg"], width=260)
        cc.pack(side="left", fill="y")
        cc.pack_propagate(False)
        tk.Label(cc, text="Comments", font=FONT_HEADER,
                 bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=(0, 6))
        pid_row = tk.Frame(cc, bg=t["bg"])
        pid_row.pack(fill="x", pady=(0, 6))
        tk.Label(pid_row, text="Puzzle #", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(side="left")
        self._pid_entry = RetroEntry(pid_row, self.app, width=5)
        self._pid_entry.pack(side="left", padx=4)
        RetroButton(pid_row, self.app, "LOAD",
                    command=self._load_comments).pack(side="left")
        self._comments_frame = tk.Frame(cc, bg=t["bg"])
        self._comments_frame.pack(fill="both", expand=True)
        tk.Label(cc, text="Add comment:", font=FONT_SMALL,
                 bg=t["bg"], fg=t["text_dim"]).pack(anchor="w", pady=(8, 0))
        self._comment_box = tk.Text(cc, font=FONT_SMALL, width=30, height=3,
                                    bg=t["entry_bg"], fg=t["entry_fg"],
                                    insertbackground=t["text"], relief="flat", bd=4)
        self._comment_box.pack(fill="x", pady=4)
        RetroButton(cc, self.app, "POST",
                    command=self._post_comment).pack(anchor="e")

        self._msg = tk.Label(self, text="", font=FONT_SMALL,
                             bg=t["bg"], fg=t["accent"])
        self._msg.pack(pady=4)

    def tkraise(self, *args) -> None:  # type: ignore[override]
        super().tkraise(*args)
        self._load_all()

    def _load_all(self) -> None:
        self._load_friends()
        self._load_feed()

    def _load_friends(self) -> None:
        for w in self._friends_frame.winfo_children():
            w.destroy()
        t       = self.app.theme
        result  = self.app.server.get_friends()
        friends = result.get("friends", []) if isinstance(result, dict) else []
        if not friends:
            tk.Label(self._friends_frame, text="No friends yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
            return
        for f in friends:
            tk.Label(self._friends_frame, text=f"• {f['username']}",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text"]).pack(anchor="w", pady=1)

    def _send_request(self) -> None:
        fid_str = self._friend_entry.get().strip()
        if not fid_str.isdigit():
            self._msg.config(text="Enter the numeric user ID to add.")
            return
        result = self.app.server.add_friend(int(fid_str))
        if result.get("status") == "ok":
            self._friend_entry.delete(0, "end")
            self._msg.config(text="Friend request sent!", fg=self.app.theme["accent2"])
            self._load_friends()
        else:
            self._msg.config(text=result.get("message", "Could not send request."),
                             fg=self.app.theme["accent"])

    def _load_feed(self) -> None:
        for w in self._feed_inner.winfo_children():
            w.destroy()
        t      = self.app.theme
        result = self.app.server.get_activity_feed()
        feed   = result.get("feed", []) if isinstance(result, dict) else []
        if not feed:
            tk.Label(self._feed_inner, text="Nothing in your feed yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w", pady=8)
            return
        for item in feed:
            row = tk.Frame(self._feed_inner, bg=t["bg_secondary"], pady=4, padx=8)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=item.get("username", "?"), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["accent2"]).pack(side="left")
            tk.Label(row, text="  " + item.get("message", ""), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text"]).pack(side="left")
            tk.Label(row, text=str(item.get("created_at", ""))[:16], font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["text_dim"]).pack(side="right")

    def _load_comments(self) -> None:
        for w in self._comments_frame.winfo_children():
            w.destroy()
        t = self.app.theme
        try:
            puzzle_id = int(self._pid_entry.get().strip())
        except ValueError:
            self._msg.config(text="Enter a valid puzzle ID.")
            return
        result   = self.app.server.get_comments(puzzle_id)
        comments = result.get("comments", []) if isinstance(result, dict) else []
        if not comments:
            tk.Label(self._comments_frame, text="No comments yet.",
                     font=FONT_SMALL, bg=t["bg"], fg=t["text_dim"]).pack(anchor="w")
            return
        for c in comments:
            row = tk.Frame(self._comments_frame, bg=t["bg_secondary"], pady=3, padx=6)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=c.get("username", "?"), font=FONT_SMALL,
                     bg=t["bg_secondary"], fg=t["accent2"]).pack(anchor="w")
            tk.Label(row, text=c.get("comment_text", ""), font=FONT_SMALL,
                     wraplength=200, justify="left",
                     bg=t["bg_secondary"], fg=t["text"]).pack(anchor="w")

    def _post_comment(self) -> None:
        body = self._comment_box.get("1.0", "end").strip()
        if not body:
            return
        try:
            puzzle_id = int(self._pid_entry.get().strip())
        except ValueError:
            self._msg.config(text="Enter a valid puzzle ID.")
            return
        result = self.app.server.add_comment(puzzle_id, body)
        if result.get("status") == "ok":
            self._comment_box.delete("1.0", "end")
            self._msg.config(text="Comment posted! ✓", fg=self.app.theme["accent2"])
            self._load_comments()
        else:
            self._msg.config(text=result.get("message", "Failed to post."),
                             fg=self.app.theme["accent"])
