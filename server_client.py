# server_client.py - server integration with groupmate's server code

from typing import Optional
import requests


class ServerClient:
    BASE_URL = "http://localhost:5000"

    def __init__(self) -> None:
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None

    # Auth

    def login(self, username: str, password: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/login",
                json={"username": username, "password": password}
            )
            data = res.json()

            if data["status"] == "ok":
                self.user_id = data["user_id"]
                self.username = data["username"]

            return data

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def register(self, username: str, password: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/register",
                json={"username": username, "password": password}
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Puzzles

    def get_puzzles(self) -> dict:
        try:
            res = requests.get(f"{self.BASE_URL}/puzzles")
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_puzzle(self, puzzle_id: int) -> dict:
        try:
            res = requests.get(f"{self.BASE_URL}/puzzle/{puzzle_id}")
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_puzzle(self, initial_grid: str, solution_grid: str,
                   difficulty: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/puzzle",
                json={
                    "user_id": self.user_id,
                    "initial_grid": initial_grid,
                    "solution_grid": solution_grid,
                    "difficulty": difficulty
                }
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Solving

    def submit_solve(self, puzzle_id: int, current_grid: str,
                     time_taken: int) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/solve",
                json={
                    "user_id": self.user_id,
                    "puzzle_id": puzzle_id,
                    "current_grid": current_grid,
                    "time_taken": time_taken
                }
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_hint(self, puzzle_id: int, current_grid: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/hint",
                json={
                    "puzzle_id": puzzle_id,
                    "current_grid": current_grid
                }
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_grid(self, puzzle_id: int, current_grid: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/puzzles/{puzzle_id}/validate",
                json={"current_grid": current_grid}
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Stats

    def get_user_stats(self) -> dict:
        try:
            res = requests.get(
                f"{self.BASE_URL}/user_stats/{self.user_id}"
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_leaderboard(self) -> dict:
        try:
            res = requests.get(f"{self.BASE_URL}/leaderboard")
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Social
    
    def get_comments(self, puzzle_id: int) -> dict:
        try:
            res = requests.get(
                f"{self.BASE_URL}/comments/{puzzle_id}"
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_comment(self, puzzle_id: int, text: str) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/comment",
                json={
                    "user_id": self.user_id,
                    "puzzle_id": puzzle_id,
                    "comment_text": text
                }
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_friends(self) -> dict:
        try:
            res = requests.get(
                f"{self.BASE_URL}/friends/{self.user_id}"
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_friend(self, friend_id: int) -> dict:
        try:
            res = requests.post(
                f"{self.BASE_URL}/friend_request",
                json={
                    "user_id": self.user_id,
                    "friend_id": friend_id
                }
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_activity_feed(self) -> dict:
        try:
            res = requests.get(
                f"{self.BASE_URL}/activity/{self.user_id}"
            )
            return res.json()

        except Exception as e:
            return {"status": "error", "message": str(e)}