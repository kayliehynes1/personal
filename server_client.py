# server_client.py - client integrated to server endpoints

import requests
from typing import Optional


class ServerClient:
    def __init__(self, base_url: str = "http://localhost:5000") -> None:
        self.base_url = base_url
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None

    # Request helper - handles all HTTP requests (adds timeout, error handling, and JSON parsing)

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        try:
            r = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                timeout=5,
                **kwargs
            )
            return r.json()
        except requests.RequestException as e:
            return {"status": "error", "message": str(e)}

    def _require_auth(self) -> bool:
        return self.user_id is not None

    # Auth

    def login(self, username: str, password: str) -> dict:
        data = self._request("POST", "/login",
                             json={"username": username, "password": password})
        if data.get("status") == "ok":
            self.user_id = data["user_id"]
            self.username = data["username"]
        return data

    def register(self, username: str, password: str) -> dict:
        return self._request("POST", "/register",
                             json={"username": username, "password": password})

    # Puzzles

    def get_puzzles(self) -> dict:
        return self._request("GET", "/puzzles")

    def get_puzzle(self, puzzle_id: int) -> dict:
        return self._request("GET", f"/puzzle/{puzzle_id}")

    def add_puzzle(self, initial_grid: str, difficulty: str) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}
        return self._request("POST", "/puzzle", json={
            "user_id": self.user_id,
            "initial_grid": initial_grid,
            "difficulty": difficulty,
        })

    # Solving

    def submit_solve(self, puzzle_id: int,
                     time_taken: int, current_grid: str = "") -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        return self._request("POST", "/solve", json={
            "user_id": self.user_id,
            "puzzle_id": puzzle_id,
            "time_taken": time_taken,
            "current_grid": current_grid,
        })

    def get_hint(self, puzzle_id: int, current_grid: str) -> dict:
        return self._request("POST", "/hint", json={
            "puzzle_id": puzzle_id,
            "current_grid": current_grid,
        })

    def validate_grid(self, puzzle_id: int, current_grid: str) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        data = self._request("POST", "/solve", json={
            "user_id": self.user_id,
            "puzzle_id": puzzle_id,
            "time_taken": 0,
            "current_grid": current_grid,
        })

        return {"status": "ok", "valid": data.get("status") == "ok"}

    # Stats

    def get_user_stats(self, user_id: Optional[int] = None) -> dict:
        user_id = user_id or self.user_id

        if not user_id:
            return {"status": "error", "message": "Not logged in"}

        return self._request("GET", f"/user_stats/{user_id}")

    def get_leaderboard(self) -> dict:
        return self._request("GET", "/leaderboard")

    # Comments & Ratings

    def get_comments(self, puzzle_id: int) -> dict:
        return self._request("GET", f"/comments/{puzzle_id}")

    def add_comment(self, puzzle_id: int, text: str) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        return self._request("POST", "/comment", json={
            "user_id": self.user_id,
            "puzzle_id": puzzle_id,
            "comment_text": text,
        })

    def rate_puzzle(self, puzzle_id: int, rating: int) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        return self._request("POST", "/rating", json={
            "user_id": self.user_id,
            "puzzle_id": puzzle_id,
            "rating": rating,
        })

    # Friends & Feed

    def get_friends(self, user_id: Optional[int] = None) -> dict:
        user_id = user_id or self.user_id

        if not user_id:
            return {"status": "error", "message": "Not logged in"}

        return self._request("GET", f"/friends/{user_id}")

    def find_user(self, username: str) -> dict:
        return self._request("GET", f"/find_user/{username}")

    def add_friend(self, friend_id: int) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        return self._request("POST", "/friend_request", json={
            "user_id": self.user_id,
            "friend_id": friend_id,
        })

    def get_pending_requests(self, user_id: Optional[int] = None) -> dict:
        user_id = user_id or self.user_id

        if not user_id:
            return {"status": "error", "message": "Not logged in"}

        return self._request("GET", f"/pending_requests/{user_id}")

    def accept_friend(self, friend_id: int) -> dict:
        if not self._require_auth():
            return {"status": "error", "message": "Not logged in"}

        return self._request("POST", "/accept_friend", json={
            "user_id": self.user_id,
            "friend_id": friend_id,
        })  

    def get_activity_feed(self, user_id: Optional[int] = None) -> dict:
        user_id = user_id or self.user_id

        if not user_id:
            return {"status": "error", "message": "Not logged in"}

        return self._request("GET", f"/activity/{user_id}")
