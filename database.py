# database.py — SQLite backend for the Sudoku platform

import sqlite3
import hashlib
import os
from typing import Optional, List, Tuple, Dict

SALT_SIZE       = 16
HASH_ITERATIONS = 100000


class SudokuDB:
    """All database access for the Sudoku platform.
    The server instantiates this as:  db = SudokuDB()
    """

    def __init__(self, db_path: str = 'sudoku.db') -> None:
        self.db_path = db_path
        self._create_schema()
        self._seed_demo_puzzles()

    # ── connection ────────────────────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── schema ────────────────────────────────────────────────────────────────

    def _create_schema(self) -> None:
        """Create all tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                salt          BLOB NOT NULL,
                join_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS puzzles (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                initial_grid  TEXT NOT NULL,
                solution_grid TEXT NOT NULL,
                difficulty    TEXT NOT NULL DEFAULT 'medium',
                creator_id    INTEGER,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solve_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                puzzle_id    INTEGER NOT NULL,
                time_taken   INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success      BOOLEAN,
                FOREIGN KEY (user_id)   REFERENCES users(id),
                FOREIGN KEY (puzzle_id) REFERENCES puzzles(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id         INTEGER PRIMARY KEY,
                puzzles_posted  INTEGER DEFAULT 0,
                puzzles_solved  INTEGER DEFAULT 0,
                total_time      INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS puzzle_stats (
                puzzle_id    INTEGER PRIMARY KEY,
                attempts     INTEGER DEFAULT 0,
                completions  INTEGER DEFAULT 0,
                average_time REAL    DEFAULT 0,
                FOREIGN KEY (puzzle_id) REFERENCES puzzles(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                puzzle_id  INTEGER NOT NULL,
                user_id    INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (puzzle_id) REFERENCES puzzles(id),
                FOREIGN KEY (user_id)   REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                puzzle_id INTEGER NOT NULL,
                user_id   INTEGER NOT NULL,
                rating    INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (puzzle_id) REFERENCES puzzles(id),
                FOREIGN KEY (user_id)   REFERENCES users(id),
                UNIQUE (puzzle_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                from_user INTEGER NOT NULL REFERENCES users(id),
                to_user   INTEGER NOT NULL REFERENCES users(id),
                status    TEXT    NOT NULL DEFAULT 'pending',
                PRIMARY KEY (from_user, to_user)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    def _seed_demo_puzzles(self) -> None:
        """Add one starter puzzle if the table is empty."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM puzzles")
        if cursor.fetchone()[0] == 0:
            initial = (
                "530070000600195000098000060"
                "800060003400803001700020006"
                "060000280000419005000080079"
            )
            solution = (
                "534678912672195348198342567"
                "859761423426853791713924856"
                "961537284287419635345286179"
            )
            cursor.execute(
                "INSERT INTO puzzles (initial_grid, solution_grid, difficulty, creator_id) "
                "VALUES (?, ?, 'easy', NULL)",
                (initial, solution),
            )
            conn.commit()
        conn.close()

    # ── password hashing ──────────────────────────────────────────────────────

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt, HASH_ITERATIONS
        )

    # ── users ─────────────────────────────────────────────────────────────────

    def register_user(self, username: str, password: str) -> bool:
        """Register a new user. Returns True on success, False if username taken."""
        salt = os.urandom(SALT_SIZE)
        pw_hash = self._hash_password(password, salt)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, pw_hash, salt),
            )
            # Create empty stats row
            cursor.execute(
                "INSERT INTO user_stats (user_id) VALUES (?)",
                (cursor.lastrowid,),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def login_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate a user. Returns user_id on success, None on failure."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        pw_hash = self._hash_password(password, row["salt"])
        if pw_hash == row["password_hash"]:
            return row["id"]
        return None

    # ── puzzles ───────────────────────────────────────────────────────────────

    def get_all_puzzles(self) -> List[Dict]:
        """Return summary list of all puzzles."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.id, p.difficulty, u.username AS author "
            "FROM puzzles p LEFT JOIN users u ON p.creator_id = u.id "
            "ORDER BY p.id"
        )
        puzzles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return puzzles

    def get_puzzle(self, puzzle_id: int) -> Optional[Dict]:
        """Return a full puzzle row including solution_grid, or None."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.*, u.username AS author "
            "FROM puzzles p LEFT JOIN users u ON p.creator_id = u.id "
            "WHERE p.id = ?",
            (puzzle_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_puzzle(self, initial_grid: str, solution_grid: str,
                   difficulty: str, user_id: int) -> Optional[int]:
        """Insert a new puzzle. Returns puzzle_id on success, None on failure."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO puzzles (initial_grid, solution_grid, difficulty, creator_id) "
                "VALUES (?, ?, ?, ?)",
                (initial_grid, solution_grid, difficulty, user_id),
            )
            puzzle_id = cursor.lastrowid
            # Create empty puzzle stats row
            cursor.execute(
                "INSERT INTO puzzle_stats (puzzle_id) VALUES (?)", (puzzle_id,)
            )
            # Update user's puzzles_posted count
            cursor.execute(
                "UPDATE user_stats SET puzzles_posted = puzzles_posted + 1 WHERE user_id = ?",
                (user_id,),
            )
            self._log_activity(cursor, user_id, "puzzle_posted", str(puzzle_id))
            conn.commit()
            return puzzle_id
        except sqlite3.Error:
            return None
        finally:
            conn.close()

    # ── solving ───────────────────────────────────────────────────────────────

    def record_solve(self, user_id: int, puzzle_id: int, time_taken: float) -> None:
        """Record a completed solve and update stats."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO solve_history (user_id, puzzle_id, time_taken, success) "
            "VALUES (?, ?, ?, 1)",
            (user_id, puzzle_id, time_taken),
        )
        # Update user stats
        cursor.execute(
            "UPDATE user_stats SET puzzles_solved = puzzles_solved + 1, "
            "total_time = total_time + ? WHERE user_id = ?",
            (time_taken, user_id),
        )
        # Update puzzle stats
        cursor.execute(
            "UPDATE puzzle_stats SET completions = completions + 1, "
            "average_time = (average_time * (completions - 1) + ?) / completions "
            "WHERE puzzle_id = ?",
            (time_taken, puzzle_id),
        )
        self._log_activity(cursor, user_id, "puzzle_solved", str(puzzle_id))
        conn.commit()
        conn.close()

    # ── statistics ────────────────────────────────────────────────────────────

    def get_user_stats(self, user_id: int) -> Dict:
        """Retrieve statistics for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT us.*, u.username FROM user_stats us "
            "JOIN users u ON us.user_id = u.id WHERE us.user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        # Also get best and avg time from solve_history
        cursor.execute(
            "SELECT MIN(time_taken) AS best_time, AVG(time_taken) AS avg_time "
            "FROM solve_history WHERE user_id = ? AND success = 1",
            (user_id,),
        )
        times = cursor.fetchone()
        conn.close()
        if row:
            result = dict(row)
            result["best_time"] = times["best_time"]
            result["avg_time"]  = times["avg_time"]
            return result
        return {}

    def get_puzzle_stats(self, puzzle_id: int) -> Dict:
        """Retrieve statistics for a puzzle."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM puzzle_stats WHERE puzzle_id = ?", (puzzle_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Return top users ranked by puzzles solved then average time."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.id, u.username, us.puzzles_solved, "
            "MIN(sh.time_taken) AS best_time, AVG(sh.time_taken) AS avg_time "
            "FROM users u "
            "JOIN user_stats us ON u.id = us.user_id "
            "LEFT JOIN solve_history sh ON u.id = sh.user_id AND sh.success = 1 "
            "GROUP BY u.id "
            "ORDER BY us.puzzles_solved DESC, avg_time ASC "
            "LIMIT ?",
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    # ── comments ──────────────────────────────────────────────────────────────

    def add_comment(self, user_id: int, puzzle_id: int, comment_text: str) -> bool:
        """Add a comment to a puzzle. Returns True on success."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO comments (puzzle_id, user_id, comment_text) VALUES (?, ?, ?)",
                (puzzle_id, user_id, comment_text),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_comments(self, puzzle_id: int) -> List[Dict]:
        """Get comments for a puzzle, newest first."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT c.comment_text, c.timestamp, u.username "
            "FROM comments c JOIN users u ON c.user_id = u.id "
            "WHERE c.puzzle_id = ? ORDER BY c.timestamp DESC",
            (puzzle_id,),
        )
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return comments

    # ── ratings ───────────────────────────────────────────────────────────────

    def set_rating(self, user_id: int, puzzle_id: int, rating: int = 0) -> bool:
        """Rate a puzzle 1-5. Returns True if successful."""
        if rating == 0:
            return False
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO ratings (puzzle_id, user_id, rating) VALUES (?, ?, ?)",
                (puzzle_id, user_id, rating),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_rating(self, user_id: int, puzzle_id: int) -> Optional[int]:
        """Get a user's rating for a puzzle."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rating FROM ratings WHERE user_id = ? AND puzzle_id = ?",
            (user_id, puzzle_id),
        )
        row = cursor.fetchone()
        conn.close()
        return row["rating"] if row else None

    # ── friends ───────────────────────────────────────────────────────────────

    def add_friend_request(self, user_id: int, friend_id: int) -> Tuple[bool, str]:
        """Send a friend request. Returns (success, message)."""
        if user_id == friend_id:
            return False, "Cannot add yourself as a friend"
        conn = self._get_connection()
        cursor = conn.cursor()
        # Check target exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (friend_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "User not found"
        # Check existing request or friendship
        cursor.execute(
            "SELECT status FROM friend_requests "
            "WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)",
            (user_id, friend_id, friend_id, user_id),
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, "Already friends" if existing["status"] == "accepted" else "Request already sent"
        try:
            cursor.execute(
                "INSERT INTO friend_requests (from_user, to_user) VALUES (?, ?)",
                (user_id, friend_id),
            )
            conn.commit()
            return True, "Friend request sent"
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def accept_friend_request(self, user_id: int, friend_id: int) -> bool:
        """Accept a pending friend request. Returns True on success."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM friend_requests "
            "WHERE from_user=? AND to_user=? AND status='pending'",
            (friend_id, user_id),
        )
        if not cursor.fetchone():
            conn.close()
            return False
        cursor.execute(
            "UPDATE friend_requests SET status='accepted' "
            "WHERE from_user=? AND to_user=?",
            (friend_id, user_id),
        )
        conn.commit()
        conn.close()
        return True

    def get_friends(self, user_id: int) -> List[Dict]:
        """Get list of accepted friends for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.id, u.username FROM friend_requests fr "
            "JOIN users u ON (CASE WHEN fr.from_user=? THEN fr.to_user ELSE fr.from_user END = u.id) "
            "WHERE (fr.from_user=? OR fr.to_user=?) AND fr.status='accepted'",
            (user_id, user_id, user_id),
        )
        friends = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return friends

    def get_pending_requests(self, user_id: int) -> List[Dict]:
        """Get pending friend requests sent TO this user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.id, u.username FROM friend_requests fr "
            "JOIN users u ON fr.from_user = u.id "
            "WHERE fr.to_user=? AND fr.status='pending'",
            (user_id,),
        )
        requests = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return requests

    # ── activity feed ─────────────────────────────────────────────────────────

    def _log_activity(self, cursor: sqlite3.Cursor, user_id: int,
                      activity_type: str, activity_data: str = '') -> None:
        """Internal helper — log an activity entry within an open transaction."""
        cursor.execute(
            "INSERT INTO activity (user_id, activity_type, activity_data) VALUES (?, ?, ?)",
            (user_id, activity_type, activity_data),
        )

    def get_activity_feed(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Return recent activity for a user and their accepted friends."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT a.activity_type, a.activity_data, a.timestamp, u.username "
            "FROM activity a LEFT JOIN users u ON a.user_id = u.id "
            "WHERE a.user_id = ? OR a.user_id IN ("
            "  SELECT CASE WHEN from_user=? THEN to_user ELSE from_user END "
            "  FROM friend_requests "
            "  WHERE (from_user=? OR to_user=?) AND status='accepted'"
            ") ORDER BY a.timestamp DESC LIMIT ?",
            (user_id, user_id, user_id, user_id, limit),
        )
        feed = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return feed


if __name__ == '__main__':
    db = SudokuDB()
    print("Database initialised and seeded.")
