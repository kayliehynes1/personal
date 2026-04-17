# sudoku_logic.py — Sudoku logic, validation and solver
# Teammate responsibility: Logic & Solver layer
#
# The server imports this as:
#     import sudoku_logic as logic
#
# Every function matches a logic.* call in the server exactly:
#
#   logic.parse_grid(grid_str)              → list[list[int]]   (raises ValueError if invalid)
#   logic.is_valid_solution(current, solution) → bool
#   logic.has_unique_solution(initial)      → bool
#   logic.get_hint(current, solution)       → tuple[int,int,int] | None   (row, col, value)

from __future__ import annotations
import random
from typing import Optional


# ── grid parsing ──────────────────────────────────────────────────────────────

def parse_grid(grid_str: str) -> list[list[int]]:
    """Parse a flat digit string into a 2-D list of ints.

    Accepts 9×9 (81 chars), 4×4 (16 chars) or 16×16 (256 chars) grids.
    Raises ValueError if the string length or contents are invalid.

    Args:
        grid_str: Flat digit string, e.g. "530070000600195000..."

    Returns:
        2-D list where 0 represents an empty cell.
    """
    grid_str = grid_str.strip()
    valid_sizes = {16: 4, 81: 9, 256: 16}
    if len(grid_str) not in valid_sizes:
        raise ValueError(
            f"Grid string must be 16, 81 or 256 characters long, got {len(grid_str)}"
        )
    if not grid_str.isdigit():
        raise ValueError("Grid string must contain digits only")

    size = valid_sizes[len(grid_str)]
    return [
        [int(grid_str[r * size + c]) for c in range(size)]
        for r in range(size)
    ]


# ── internal helpers ──────────────────────────────────────────────────────────

def _size(grid: list[list[int]]) -> int:
    return len(grid)


def _box_size(size: int) -> int:
    return int(size ** 0.5)


def _flatten(grid: list[list[int]]) -> str:
    return "".join(str(v) for row in grid for v in row)


def _candidates(grid: list[list[int]], r: int, c: int) -> set[int]:
    """Return the set of digits that can legally go in cell (r, c)."""
    size = _size(grid)
    box  = _box_size(size)
    used: set[int] = set()

    used.update(grid[r])                              # row
    used.update(grid[i][c] for i in range(size))      # column

    br, bc = (r // box) * box, (c // box) * box       # sub-box
    for dr in range(box):
        for dc in range(box):
            used.add(grid[br + dr][bc + dc])

    used.discard(0)
    return set(range(1, size + 1)) - used


def _group_ok(values: list[int], allow_zeros: bool) -> bool:
    """Return True if a row / column / box group has no duplicate non-zero digits."""
    filled = [v for v in values if v != 0]
    if not allow_zeros and len(filled) != len(values):
        return False
    return len(filled) == len(set(filled))


def _all_groups_ok(grid: list[list[int]], allow_zeros: bool) -> bool:
    size = _size(grid)
    box  = _box_size(size)

    for r in range(size):
        if not _group_ok(grid[r], allow_zeros):
            return False
    for c in range(size):
        if not _group_ok([grid[r][c] for r in range(size)], allow_zeros):
            return False
    for br in range(box):
        for bc in range(box):
            b = [
                grid[br * box + dr][bc * box + dc]
                for dr in range(box) for dc in range(box)
            ]
            if not _group_ok(b, allow_zeros):
                return False
    return True


# ── public API ────────────────────────────────────────────────────────────────

def is_valid_solution(
    current: list[list[int]],
    solution: list[list[int]],
) -> bool:
    """Return True if *current* matches *solution* and is a valid completed grid.

    The server calls this to check both the /solve and /puzzle (add) endpoints.

    Args:
        current:  2-D grid from parse_grid — the user's submitted answer.
        solution: 2-D grid from parse_grid — the stored correct solution.

    Returns:
        True only if every cell matches and the grid is a valid Sudoku solution.
    """
    if _flatten(current) != _flatten(solution):
        return False
    return _all_groups_ok(current, allow_zeros=False)


def has_unique_solution(initial: list[list[int]]) -> bool:
    """Return True if *initial* (with 0s for empty cells) has exactly one solution.

    Used by the /puzzle endpoint to validate user-submitted puzzles.

    Args:
        initial: 2-D grid from parse_grid with 0s for empty cells.
    """
    if not _all_groups_ok(initial, allow_zeros=True):
        return False
    solutions: list[str] = []
    _backtrack(initial, limit=2, solutions=solutions)
    return len(solutions) == 1


def get_hint(
    current: list[list[int]],
    solution: list[list[int]],
) -> Optional[tuple[int, int, int]]:
    """Return (row, col, value) for one empty cell that differs from the solution.

    Finds the first empty cell (value == 0) in *current* and returns the
    correct value from *solution*.  Returns None if there are no empty cells.

    Args:
        current:  2-D grid from parse_grid — the user's current board state.
        solution: 2-D grid from parse_grid — the correct solution.
    """
    size = _size(current)
    for r in range(size):
        for c in range(size):
            if current[r][c] == 0:
                return r, c, solution[r][c]
    return None


# ── solver (used internally by has_unique_solution) ───────────────────────────

def _backtrack(
    grid: list[list[int]],
    limit: int,
    solutions: list[str],
) -> None:
    """Backtracking solver with MRV heuristic.  Stops after *limit* solutions."""
    if len(solutions) >= limit:
        return

    size = _size(grid)
    best_pos: Optional[tuple[int, int]] = None
    best_cands: set[int] = set()

    # Pick the empty cell with the fewest legal candidates (MRV)
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                cands = _candidates(grid, r, c)
                if not cands:
                    return                         # Dead end
                if best_pos is None or len(cands) < len(best_cands):
                    best_pos, best_cands = (r, c), cands
                    if len(best_cands) == 1:
                        break
        if best_pos and len(best_cands) == 1:
            break

    if best_pos is None:
        solutions.append(_flatten(grid))           # Complete solution found
        return

    r, c = best_pos
    for digit in sorted(best_cands):
        grid[r][c] = digit
        _backtrack(grid, limit, solutions)
        if len(solutions) >= limit:
            grid[r][c] = 0
            return
        grid[r][c] = 0


# ── optional: auto-solve a puzzle ─────────────────────────────────────────────

def solve(initial: list[list[int]]) -> Optional[list[list[int]]]:
    """Return a solved copy of *initial*, or None if no solution exists.

    Not called directly by the server but useful for testing and for the
    client teammate if they want an auto-solve button.

    Args:
        initial: 2-D grid from parse_grid with 0s for empty cells.
    """
    import copy
    grid = copy.deepcopy(initial)
    solutions: list[str] = []
    _backtrack(grid, limit=1, solutions=solutions)
    if not solutions:
        return None
    size = _size(initial)
    flat = solutions[0]
    return [
        [int(flat[r * size + c]) for c in range(size)]
        for r in range(size)
    ]
