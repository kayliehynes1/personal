# sudoku_logic.py — Sudoku logic, validation and solver
# Teammate responsibility: Logic & Solver layer
#
# Public API used by the rest of the project:
#
#   is_valid_solution(grid, size)      → bool
#   is_valid_partial(grid, size)       → bool
#   solve(grid, size)                  → str | None
#   has_unique_solution(grid, size)    → bool
#   generate_puzzle(size, difficulty)  → tuple[str, str]   (initial, solution)

from __future__ import annotations
import random
from typing import Optional


# ── helpers ───────────────────────────────────────────────────────────────────

def _box_size(size: int) -> int:
    """Return the sub-box side length for a given grid size (e.g. 3 for 9×9)."""
    return int(size ** 0.5)


def _grid_to_rows(grid: str, size: int) -> list[list[int]]:
    """Convert a flat digit string to a 2-D list of ints."""
    return [
        [int(grid[r * size + c]) for c in range(size)]
        for r in range(size)
    ]


def _rows_to_grid(rows: list[list[int]]) -> str:
    """Flatten a 2-D list back to a digit string."""
    return "".join(str(v) for row in rows for v in row)


def _candidates(rows: list[list[int]], r: int, c: int, size: int) -> set[int]:
    """Return the set of valid digits for cell (r, c) in the current board."""
    box = _box_size(size)
    used: set[int] = set()

    # Row and column
    used.update(rows[r])
    used.update(rows[i][c] for i in range(size))

    # Sub-box
    br, bc = (r // box) * box, (c // box) * box
    for dr in range(box):
        for dc in range(box):
            used.add(rows[br + dr][bc + dc])

    used.discard(0)
    return set(range(1, size + 1)) - used


# ── validation ────────────────────────────────────────────────────────────────

def _group_valid(values: list[int], size: int, allow_zeros: bool) -> bool:
    """Check that a row/col/box group is internally consistent."""
    filled = [v for v in values if v != 0]
    if not allow_zeros and len(filled) != size:
        return False
    if any(v < 1 or v > size for v in filled):
        return False
    return len(filled) == len(set(filled))


def _check_all_groups(rows: list[list[int]], size: int, allow_zeros: bool) -> bool:
    """Validate every row, column and sub-box."""
    box = _box_size(size)

    for r in range(size):
        if not _group_valid(rows[r], size, allow_zeros):
            return False

    for c in range(size):
        col = [rows[r][c] for r in range(size)]
        if not _group_valid(col, size, allow_zeros):
            return False

    for br in range(box):
        for bc in range(box):
            b = [
                rows[br * box + dr][bc * box + dc]
                for dr in range(box)
                for dc in range(box)
            ]
            if not _group_valid(b, size, allow_zeros):
                return False

    return True


def is_valid_solution(grid: str, size: int = 9) -> bool:
    """Return True if *grid* is a fully completed, valid Sudoku solution.

    Args:
        grid: Flat digit string of length size²; no zeros allowed.
        size: Side length of the grid (4, 9 or 16).
    """
    if len(grid) != size * size:
        return False
    if not grid.isdigit():
        return False
    rows = _grid_to_rows(grid, size)
    return _check_all_groups(rows, size, allow_zeros=False)


def is_valid_partial(grid: str, size: int = 9) -> bool:
    """Return True if *grid* (which may contain zeros) has no conflicts so far.

    Zeros represent empty cells and are ignored when checking for duplicates.

    Args:
        grid: Flat digit string of length size²; 0 means empty.
        size: Side length of the grid (4, 9 or 16).
    """
    if len(grid) != size * size:
        return False
    if not grid.isdigit():
        return False
    rows = _grid_to_rows(grid, size)
    return _check_all_groups(rows, size, allow_zeros=True)


# ── solver ────────────────────────────────────────────────────────────────────

def _solve_recursive(
    rows: list[list[int]],
    size: int,
    limit: int,
    solutions: list[str],
) -> None:
    """Backtracking solver; stops as soon as *limit* solutions are found."""
    if len(solutions) >= limit:
        return

    # Find the empty cell with the fewest candidates (MRV heuristic)
    best_pos: Optional[tuple[int, int]] = None
    best_cands: set[int] = set()
    for r in range(size):
        for c in range(size):
            if rows[r][c] == 0:
                cands = _candidates(rows, r, c, size)
                if not cands:
                    return          # Dead end — this branch has no solution
                if best_pos is None or len(cands) < len(best_cands):
                    best_pos, best_cands = (r, c), cands
                    if len(best_cands) == 1:
                        break       # Can't do better than one candidate
        if best_pos and len(best_cands) == 1:
            break

    if best_pos is None:
        # No empty cells remain — a complete solution has been found
        solutions.append(_rows_to_grid(rows))
        return

    r, c = best_pos
    for digit in sorted(best_cands):
        rows[r][c] = digit
        _solve_recursive(rows, size, limit, solutions)
        if len(solutions) >= limit:
            rows[r][c] = 0
            return
        rows[r][c] = 0


def solve(grid: str, size: int = 9) -> Optional[str]:
    """Return a solution string for *grid*, or None if no solution exists.

    Args:
        grid: Flat digit string of length size²; 0 means empty.
        size: Side length of the grid.
    """
    if not is_valid_partial(grid, size):
        return None
    rows = _grid_to_rows(grid, size)
    solutions: list[str] = []
    _solve_recursive(rows, size, limit=1, solutions=solutions)
    return solutions[0] if solutions else None


def has_unique_solution(grid: str, size: int = 9) -> bool:
    """Return True if *grid* has exactly one solution.

    Used when a user submits a new puzzle to verify it is well-formed.

    Args:
        grid: Flat digit string with 0s for empty cells.
        size: Side length of the grid.
    """
    if not is_valid_partial(grid, size):
        return False
    rows = _grid_to_rows(grid, size)
    solutions: list[str] = []
    _solve_recursive(rows, size, limit=2, solutions=solutions)
    return len(solutions) == 1


# ── puzzle generator ──────────────────────────────────────────────────────────

def _filled_grid(size: int) -> list[list[int]]:
    """Generate a complete, randomly filled valid Sudoku grid."""
    rows = [[0] * size for _ in range(size)]
    solutions: list[str] = []

    def fill(rows: list[list[int]]) -> bool:
        for r in range(size):
            for c in range(size):
                if rows[r][c] == 0:
                    cands = list(_candidates(rows, r, c, size))
                    random.shuffle(cands)
                    for digit in cands:
                        rows[r][c] = digit
                        if fill(rows):
                            return True
                        rows[r][c] = 0
                    return False
        return True

    fill(rows)
    return rows


_CLUES: dict[str, dict[int, int]] = {
    # Approximate number of clues to leave for each difficulty / grid size
    "easy":   {4: 12, 9: 36, 16: 120},
    "medium": {4: 10, 9: 30, 16: 100},
    "hard":   {4:  8, 9: 25, 16:  80},
}


def generate_puzzle(
    size: int = 9,
    difficulty: str = "medium",
) -> tuple[str, str]:
    """Generate a new Sudoku puzzle with a unique solution.

    Returns:
        (initial_grid, solution_grid) as flat digit strings.
        initial_grid contains 0s for empty cells.

    Args:
        size:       Grid side length (4, 9 or 16).
        difficulty: "easy", "medium" or "hard".
    """
    if size not in (4, 9, 16):
        raise ValueError(f"Unsupported grid size: {size}")

    rows      = _filled_grid(size)
    solution  = _rows_to_grid(rows)
    clues     = _CLUES.get(difficulty, _CLUES["medium"]).get(size, size * size // 3)

    total     = size * size
    positions = list(range(total))
    random.shuffle(positions)

    initial_digits = list(solution)

    # Remove cells one at a time, keeping the puzzle uniquely solvable
    removed = 0
    for pos in positions:
        if total - removed <= clues:
            break
        backup = initial_digits[pos]
        initial_digits[pos] = "0"
        candidate = "".join(initial_digits)
        if has_unique_solution(candidate, size):
            removed += 1
        else:
            initial_digits[pos] = backup   # Restore — removing this cell broke uniqueness

    return "".join(initial_digits), solution