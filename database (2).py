# database.py — SQLite backend for the Sudoku platform
# Teammate responsibility: Database layer
#
# The server imports this as:
#     from database import SudokuDB
#     db = SudokuDB()
#
# Every method on SudokuDB matches a db.* call in the server exactly:
#
#   db.register_user(username, password)            → bool
#   db.login_user(username, password)               → int | None   (user_id)
#   db.get_all_puzzles()                            → list[dict]
#   db.get_puzzle(puzzle_id)                        → dict | None
#   db.add_puzzle(initial_grid, solution_grid,
#                 difficulty, user_id)              → int | None   (puzzle_id)
#   db.record_solve(user_id, puzzle_id, time_taken) → None
#   db.get_user_stats(user_id)                      → dict
#   db.get_puzzle_stats(puzzle_id)                  → dict
#   db.get_leaderboard(limit)                       → list[dict]
#   db.add_comment(user_id, puzzle_id, comment_text)→ bool
#   db.get_comments(puzzle_id)                      → list[dict]
#   db.set_rating(user_id, puzzle_id, rating)       → bool
#   db.get_rating(user_id, puzzle_id)               → int | None
#   db.add_friend_request(user_id, friend_id)       → tuple[bool, str]
#   db.accept_friend_request(user_id, friend_id)    → bool
#   db.get_friends(user_id)                         → list[dict]
#   db.get_pending_requests(user_id)                → list[dict]
#   db.get_activity_feed(user_id, limit)            → list[dict]

import hashlib
import sqlite3
from typing import Optional

DB_PATH = "sudoku.db"


class SudokuDB:
    """Encapsulates all database access for the Sudoku platform."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    # ── connection ────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ── schema & seed ─────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create tables on first run and seed one sample puzzle."""
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT    UNIQUE NOT NULL,
                    password TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS puzzles (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    initial_grid TEXT    NOT NULL,
                    solution_grid TEXT   NOT NULL,
                    difficulty   TEXT    NOT NULL DEFAULT 'medium',
                    user_id      INTEGER REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS solves (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL REFERENCES users(id),
                    puzzle_id  INTEGER NOT NULL REFERENCES puzzles(id),
                    time_taken REAL    NOT NULL,
                    solved_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS comments (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      INTEGER NOT NULL REFERENCES users(id),
                    puzzle_id    INTEGER NOT NULL REFERENCES puzzles(id),
                    comment_text TEXT    NOT NULL,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ratings (
                    user_id   INTEGER NOT NULL REFERENCES users(id),
                    puzzle_id INTEGER NOT NULL REFERENCES puzzles(id),
                    rating    INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    PRIMARY KEY (user_id, puzzle_id)
                );

                CREATE TABLE IF NOT EXISTS friend_requests (
                    from_user INTEGER NOT NULL REFERENCES users(id),
                    to_user   INTEGER NOT NULL REFERENCES users(id),
                    status    TEXT    NOT NULL DEFAULT 'pending',
                    PRIMARY KEY (from_user, to_user)
                );

                CREATE TABLE IF NOT EXISTS activity_feed (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL REFERENCES users(id),
                    message    TEXT    NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Seed one classic 9×9 puzzle on first run
            count = con.execute("SELECT COUNT(*) FROM puzzles").fetchone()[0]
            if count == 0:
                initial = (
                    "530070000"
                    "600195000"
                    "098000060"
                    "800060003"
                    "400803001"
                    "700020006"
                    "060000280"
                    "000419005"
                    "000080079"
                )
                solution = (
                    "534678912"
                    "672195348"
                    "198342567"
                    "859761423"
                    "426853791"
                    "713924856"
                    "961537284"
                    "287419635"
                    "345286179"
                )
                con.execute(
                    "INSERT INTO puzzles (initial_grid, solution_grid, difficulty, user_id) "
                    "VALUES (?, ?, 'easy', NULL)",
                    (initial, solution),
                )

    # ── users ──────────────────────────────────────────────────────────────────

    def register_user(self, username: str, password: str) -> bool:
        """Register a new user.  Returns True on success, False if username taken."""
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, self._hash(password)),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate a user.  Returns user_id on success, None on failure."""
        with self._connect() as con:
            row = con.execute(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, self._hash(password)),
            ).fetchone()
        return row["id"] if row else None

    # ── puzzles ────────────────────────────────────────────────────────────────

    def get_all_puzzles(self) -> list[dict]:
        """Return a summary list of all puzzles (no solution exposed)."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT p.id, p.difficulty, u.username AS author "
                "FROM puzzles p LEFT JOIN users u ON p.user_id = u.id "
                "ORDER BY p.id"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_puzzle(self, puzzle_id: int) -> Optional[dict]:
        """Return a full puzzle row including solution_grid, or None."""
        with self._connect() as con:
            row = con.execute(
                "SELECT p.*, u.username AS author "
                "FROM puzzles p LEFT JOIN users u ON p.user_id = u.id "
                "WHERE p.id = ?",
                (puzzle_id,),
            ).fetchone()
        return dict(row) if row else None

    def add_puzzle(
        self,
        initial_grid: str,
        solution_grid: str,
        difficulty: str,
        user_id: int,
    ) -> Optional[int]:
        """Insert a new puzzle.  Returns puzzle_id on success, None on failure."""
        try:
            with self._connect() as con:
                cur = con.execute(
                    "INSERT INTO puzzles (initial_grid, solution_grid, difficulty, user_id) "
                    "VALUES (?, ?, ?, ?)",
                    (initial_grid, solution_grid, difficulty, user_id),
                )
                puzzle_id = cur.lastrowid
                self._log_activity(
                    con, user_id, f"posted a new puzzle (id {puzzle_id})"
                )
            return puzzle_id
        except sqlite3.Error:
            return None

    # ── solving ────────────────────────────────────────────────────────────────

    def record_solve(self, user_id: int, puzzle_id: int, time_taken: float) -> None:
        """Persist a completed solve and write an activity entry."""
        with self._connect() as con:
            con.execute(
                "INSERT INTO solves (user_id, puzzle_id, time_taken) VALUES (?, ?, ?)",
                (user_id, puzzle_id, time_taken),
            )
            self._log_activity(
                con, user_id, f"solved puzzle #{puzzle_id} in {time_taken:.1f}s"
            )

    # ── statistics ─────────────────────────────────────────────────────────────

    def get_user_stats(self, user_id: int) -> dict:
        """Return solve statistics for one user."""
        with self._connect() as con:
            user = con.execute(
                "SELECT username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            solves = con.execute(
                "SELECT COUNT(*) AS total, "
                "       MIN(time_taken) AS best, "
                "       AVG(time_taken) AS avg "
                "FROM solves WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            posted = con.execute(
                "SELECT COUNT(*) AS total FROM puzzles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return {
            "user_id":        user_id,
            "username":       user["username"] if user else None,
            "puzzles_solved": solves["total"],
            "best_time":      solves["best"],
            "avg_time":       solves["avg"],
            "puzzles_posted": posted["total"],
        }

    def get_puzzle_stats(self, puzzle_id: int) -> dict:
        """Return solve statistics for one puzzle."""
        with self._connect() as con:
            solves = con.execute(
                "SELECT COUNT(*) AS total, "
                "       MIN(time_taken) AS best, "
                "       AVG(time_taken) AS avg "
                "FROM solves WHERE puzzle_id = ?",
                (puzzle_id,),
            ).fetchone()
            avg_rating = con.execute(
                "SELECT AVG(rating) AS avg FROM ratings WHERE puzzle_id = ?",
                (puzzle_id,),
            ).fetchone()
        return {
            "puzzle_id":   puzzle_id,
            "times_solved": solves["total"],
            "best_time":   solves["best"],
            "avg_time":    solves["avg"],
            "avg_rating":  avg_rating["avg"],
        }

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """Return top users ranked by puzzles solved then average time."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT u.id, u.username, "
                "       COUNT(s.id)       AS puzzles_solved, "
                "       MIN(s.time_taken) AS best_time, "
                "       AVG(s.time_taken) AS avg_time "
                "FROM users u LEFT JOIN solves s ON u.id = s.user_id "
                "GROUP BY u.id "
                "ORDER BY puzzles_solved DESC, avg_time ASC "
                "LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── comments ───────────────────────────────────────────────────────────────

    def add_comment(self, user_id: int, puzzle_id: int, comment_text: str) -> bool:
        """Insert a comment.  Returns True on success."""
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO comments (user_id, puzzle_id, comment_text) "
                    "VALUES (?, ?, ?)",
                    (user_id, puzzle_id, comment_text),
                )
            return True
        except sqlite3.Error:
            return False

    def get_comments(self, puzzle_id: int) -> list[dict]:
        """Return all comments for a puzzle, oldest first."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT c.id, u.username, c.comment_text, c.created_at "
                "FROM comments c JOIN users u ON c.user_id = u.id "
                "WHERE c.puzzle_id = ? ORDER BY c.created_at",
                (puzzle_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── ratings ────────────────────────────────────────────────────────────────

    def set_rating(self, user_id: int, puzzle_id: int, rating: int) -> bool:
        """Upsert a 1–5 star rating.  Returns True on success."""
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO ratings (user_id, puzzle_id, rating) VALUES (?, ?, ?) "
                    "ON CONFLICT(user_id, puzzle_id) DO UPDATE SET rating = excluded.rating",
                    (user_id, puzzle_id, rating),
                )
            return True
        except sqlite3.Error:
            return False

    def get_rating(self, user_id: int, puzzle_id: int) -> Optional[int]:
        """Return a user's rating for a puzzle, or None if not yet rated."""
        with self._connect() as con:
            row = con.execute(
                "SELECT rating FROM ratings WHERE user_id = ? AND puzzle_id = ?",
                (user_id, puzzle_id),
            ).fetchone()
        return row["rating"] if row else None

    # ── friends ────────────────────────────────────────────────────────────────

    def add_friend_request(self, user_id: int, friend_id: int) -> tuple[bool, str]:
        """Send a friend request.  Returns (success, message)."""
        if user_id == friend_id:
            return False, "Cannot add yourself as a friend"
        with self._connect() as con:
            # Check the target user exists
            target = con.execute(
                "SELECT id FROM users WHERE id = ?", (friend_id,)
            ).fetchone()
            if not target:
                return False, "User not found"
            # Check for existing request or friendship
            existing = con.execute(
                "SELECT status FROM friend_requests "
                "WHERE (from_user = ? AND to_user = ?) "
                "   OR (from_user = ? AND to_user = ?)",
                (user_id, friend_id, friend_id, user_id),
            ).fetchone()
            if existing:
                if existing["status"] == "accepted":
                    return False, "Already friends"
                return False, "Friend request already sent"
            try:
                con.execute(
                    "INSERT INTO friend_requests (from_user, to_user) VALUES (?, ?)",
                    (user_id, friend_id),
                )
            except sqlite3.Error as e:
                return False, str(e)
        return True, "Friend request sent"

    def accept_friend_request(self, user_id: int, friend_id: int) -> bool:
        """Accept a pending friend request from friend_id to user_id.  Returns True on success."""
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM friend_requests "
                "WHERE from_user = ? AND to_user = ? AND status = 'pending'",
                (friend_id, user_id),
            ).fetchone()
            if not row:
                return False
            con.execute(
                "UPDATE friend_requests SET status = 'accepted' "
                "WHERE from_user = ? AND to_user = ?",
                (friend_id, user_id),
            )
        return True

    def get_friends(self, user_id: int) -> list[dict]:
        """Return list of accepted friends for a user."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT u.id, u.username "
                "FROM friend_requests fr "
                "JOIN users u ON ("
                "    CASE WHEN fr.from_user = ? THEN fr.to_user ELSE fr.from_user END = u.id"
                ") "
                "WHERE (fr.from_user = ? OR fr.to_user = ?) "
                "  AND fr.status = 'accepted'",
                (user_id, user_id, user_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_pending_requests(self, user_id: int) -> list[dict]:
        """Return pending friend requests sent TO user_id."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT u.id, u.username "
                "FROM friend_requests fr "
                "JOIN users u ON fr.from_user = u.id "
                "WHERE fr.to_user = ? AND fr.status = 'pending'",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── activity feed ──────────────────────────────────────────────────────────

    def _log_activity(self, con: sqlite3.Connection, user_id: int, message: str) -> None:
        """Internal helper — write an activity entry inside an open transaction."""
        con.execute(
            "INSERT INTO activity_feed (user_id, message) VALUES (?, ?)",
            (user_id, message),
        )

    def get_activity_feed(self, user_id: int, limit: int = 20) -> list[dict]:
        """Return recent activity for a user and their accepted friends."""
        with self._connect() as con:
            rows = con.execute(
                "SELECT u.username, a.message, a.created_at "
                "FROM activity_feed a JOIN users u ON a.user_id = u.id "
                "WHERE a.user_id = ? "
                "   OR a.user_id IN ( "
                "       SELECT CASE WHEN from_user = ? THEN to_user ELSE from_user END "
                "       FROM friend_requests "
                "       WHERE (from_user = ? OR to_user = ?) AND status = 'accepted'"
                "   ) "
                "ORDER BY a.created_at DESC LIMIT ?",
                (user_id, user_id, user_id, user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
