# database.py — SQLite backend for the Sudoku platform
# Teammate responsibility: Database layer
#
# All functions in this file are called by server2.py via  import database as db
# Required surface:
#   init_db, register_user, login_user, get_user_by_username,
#   get_puzzles, get_puzzle, add_puzzle,
#   record_solve, increment_hints,
#   get_user_stats, get_all_user_stats,
#   get_comments, add_comment,
#   rate_puzzle,
#   get_friends, add_friend,
#   get_feed

import hashlib
import sqlite3
from typing import Optional

DB_PATH = "sudoku.db"


# ── connection helper ─────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── schema & seed ─────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables and seed one sample puzzle so the UI can be tested immediately."""
    with _connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    UNIQUE NOT NULL,
                password TEXT    NOT NULL,
                hints    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS puzzles (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT    NOT NULL,
                author_id    INTEGER REFERENCES users(id),
                initial_grid TEXT    NOT NULL,
                solution     TEXT    NOT NULL,
                difficulty   TEXT    NOT NULL DEFAULT 'medium',
                size         INTEGER NOT NULL DEFAULT 9
            );

            CREATE TABLE IF NOT EXISTS solves (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                puzzle_id  INTEGER NOT NULL REFERENCES puzzles(id),
                time_taken REAL    NOT NULL,
                solved_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS comments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                puzzle_id  INTEGER NOT NULL REFERENCES puzzles(id),
                body       TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ratings (
                user_id   INTEGER NOT NULL REFERENCES users(id),
                puzzle_id INTEGER NOT NULL REFERENCES puzzles(id),
                rating    INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                PRIMARY KEY (user_id, puzzle_id)
            );

            CREATE TABLE IF NOT EXISTS friends (
                user_id   INTEGER NOT NULL REFERENCES users(id),
                friend_id INTEGER NOT NULL REFERENCES users(id),
                PRIMARY KEY (user_id, friend_id)
            );

            CREATE TABLE IF NOT EXISTS feed (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                message    TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Seed one classic 9×9 puzzle so the interface works on first launch
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
                "INSERT INTO puzzles "
                "(title, author_id, initial_grid, solution, difficulty, size) "
                "VALUES (?, NULL, ?, ?, 'easy', 9)",
                ("Classic Starter", initial, solution),
            )


# ── users ─────────────────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> dict:
    """Register a new user.  Returns {"ok": True} or {"ok": False, "error": str}."""
    try:
        with _connect() as con:
            con.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, _hash(password)),
            )
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Username already taken"}


def login_user(username: str, password: str) -> dict:
    """Authenticate a user.  Returns {"ok": True, "user_id": int, "username": str} or error."""
    with _connect() as con:
        row = con.execute(
            "SELECT id, username FROM users "
            "WHERE username = ? AND password = ?",
            (username, _hash(password)),
        ).fetchone()
    if row:
        return {"ok": True, "user_id": row["id"], "username": row["username"]}
    return {"ok": False, "error": "Invalid username or password"}


def get_user_by_username(username: str) -> Optional[dict]:
    """Look up a user by username.  Returns {"id": int, "username": str} or None."""
    with _connect() as con:
        row = con.execute(
            "SELECT id, username FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


# ── puzzles ───────────────────────────────────────────────────────────────────

def get_puzzles() -> list[dict]:
    """Return a summary list of all puzzles (no solution field exposed)."""
    with _connect() as con:
        rows = con.execute(
            "SELECT p.id, p.title, p.difficulty, p.size, "
            "       u.username AS author "
            "FROM puzzles p LEFT JOIN users u ON p.author_id = u.id "
            "ORDER BY p.id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_puzzle(puzzle_id: int) -> Optional[dict]:
    """Return a full puzzle row (including solution) or None if not found."""
    with _connect() as con:
        row = con.execute(
            "SELECT p.*, u.username AS author "
            "FROM puzzles p LEFT JOIN users u ON p.author_id = u.id "
            "WHERE p.id = ?",
            (puzzle_id,),
        ).fetchone()
    return dict(row) if row else None


def add_puzzle(
    title: str,
    author_id: int,
    initial_grid: str,
    solution: str,
    difficulty: str = "medium",
    size: int = 9,
) -> dict:
    """Insert a new puzzle.  Returns {"ok": True, "puzzle_id": int} or error dict."""
    expected = size * size
    if len(initial_grid) != expected or len(solution) != expected:
        return {
            "ok": False,
            "error": (
                f"Grid strings must each be {expected} characters "
                f"for a {size}×{size} puzzle"
            ),
        }
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO puzzles "
            "(title, author_id, initial_grid, solution, difficulty, size) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, author_id, initial_grid, solution, difficulty, size),
        )
        _append_feed(con, author_id, f'posted a new puzzle: "{title}"')
    return {"ok": True, "puzzle_id": cur.lastrowid}


# ── solving ───────────────────────────────────────────────────────────────────

def record_solve(user_id: int, puzzle_id: int, time_taken: float) -> None:
    """Persist a completed solve and write an activity-feed entry."""
    with _connect() as con:
        con.execute(
            "INSERT INTO solves (user_id, puzzle_id, time_taken) VALUES (?, ?, ?)",
            (user_id, puzzle_id, time_taken),
        )
        puzzle = con.execute(
            "SELECT title FROM puzzles WHERE id = ?", (puzzle_id,)
        ).fetchone()
        title = puzzle["title"] if puzzle else f"puzzle #{puzzle_id}"
        _append_feed(con, user_id, f'solved "{title}" in {time_taken:.1f}s')


def increment_hints(user_id: int) -> None:
    """Increment the hints-used counter for a user by one."""
    with _connect() as con:
        con.execute(
            "UPDATE users SET hints = hints + 1 WHERE id = ?", (user_id,)
        )


# ── statistics ────────────────────────────────────────────────────────────────

def get_user_stats(user_id: int) -> Optional[dict]:
    """Return a stats dict for one user, or None if the user does not exist."""
    with _connect() as con:
        user = con.execute(
            "SELECT id, username, hints FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        solves = con.execute(
            "SELECT COUNT(*) AS total, "
            "       MIN(time_taken) AS best, "
            "       AVG(time_taken) AS avg "
            "FROM solves WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        posted = con.execute(
            "SELECT COUNT(*) AS total FROM puzzles WHERE author_id = ?",
            (user_id,),
        ).fetchone()
    return {
        "user_id":        user["id"],
        "username":       user["username"],
        "hints_used":     user["hints"],
        "puzzles_solved": solves["total"],
        "best_time":      solves["best"],
        "avg_time":       solves["avg"],
        "puzzles_posted": posted["total"],
    }


def get_all_user_stats() -> list[dict]:
    """Return leaderboard rows ordered by puzzles solved, then average time."""
    with _connect() as con:
        rows = con.execute(
            "SELECT u.id, u.username, "
            "       COUNT(s.id)       AS puzzles_solved, "
            "       MIN(s.time_taken) AS best_time, "
            "       AVG(s.time_taken) AS avg_time "
            "FROM users u LEFT JOIN solves s ON u.id = s.user_id "
            "GROUP BY u.id "
            "ORDER BY puzzles_solved DESC, avg_time ASC"
        ).fetchall()
    return [dict(r) for r in rows]


# ── comments ──────────────────────────────────────────────────────────────────

def get_comments(puzzle_id: int) -> list[dict]:
    """Return all comments for a puzzle, oldest first."""
    with _connect() as con:
        rows = con.execute(
            "SELECT c.id, u.username, c.body, c.created_at "
            "FROM comments c JOIN users u ON c.user_id = u.id "
            "WHERE c.puzzle_id = ? ORDER BY c.created_at",
            (puzzle_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_comment(user_id: int, puzzle_id: int, body: str) -> dict:
    """Insert a comment.  Returns {"ok": True, "comment_id": int}."""
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO comments (user_id, puzzle_id, body) VALUES (?, ?, ?)",
            (user_id, puzzle_id, body),
        )
    return {"ok": True, "comment_id": cur.lastrowid}


# ── ratings ───────────────────────────────────────────────────────────────────

def rate_puzzle(user_id: int, puzzle_id: int, rating: int) -> dict:
    """Upsert a 1–5 star rating.  Returns {"ok": True} or error dict."""
    if not (1 <= rating <= 5):
        return {"ok": False, "error": "Rating must be between 1 and 5"}
    with _connect() as con:
        con.execute(
            "INSERT INTO ratings (user_id, puzzle_id, rating) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, puzzle_id) DO UPDATE SET rating = excluded.rating",
            (user_id, puzzle_id, rating),
        )
    return {"ok": True}


# ── friends ───────────────────────────────────────────────────────────────────

def get_friends(user_id: int) -> list[dict]:
    """Return list of {"id", "username"} dicts for all friends of user_id."""
    with _connect() as con:
        rows = con.execute(
            "SELECT u.id, u.username "
            "FROM friends f JOIN users u ON f.friend_id = u.id "
            "WHERE f.user_id = ?",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_friend(user_id: int, friend_id: int) -> dict:
    """Create a mutual friendship between two users."""
    if user_id == friend_id:
        return {"ok": False, "error": "Cannot add yourself as a friend"}
    try:
        with _connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)",
                (user_id, friend_id),
            )
            con.execute(
                "INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)",
                (friend_id, user_id),
            )
    except sqlite3.Error as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True}


# ── activity feed ─────────────────────────────────────────────────────────────

def _append_feed(con: sqlite3.Connection, user_id: int, message: str) -> None:
    """Internal helper — call inside an existing connection/transaction only."""
    con.execute(
        "INSERT INTO feed (user_id, message) VALUES (?, ?)", (user_id, message)
    )


def get_feed(user_id: int) -> list[dict]:
    """Return up to 50 recent activity items for a user and their friends."""
    with _connect() as con:
        rows = con.execute(
            "SELECT u.username, f.message, f.created_at "
            "FROM feed f JOIN users u ON f.user_id = u.id "
            "WHERE f.user_id = ? "
            "   OR f.user_id IN "
            "      (SELECT friend_id FROM friends WHERE user_id = ?) "
            "ORDER BY f.created_at DESC LIMIT 50",
            (user_id, user_id),
        ).fetchall()
    return [dict(r) for r in rows]