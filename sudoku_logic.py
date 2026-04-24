import random
import copy

### FUNCTIONS

def empty_grid():
    return [0] * 81


def get(grid, row, col):
    return grid[row * 9 + col]


def set_cell(grid, row, col, value):
    grid[row * 9 + col] = value


def is_valid(grid, row, col, value):
    # CHECKING ROWS
    for c in range(9):
        if c != col and get(grid, row, c) == value:
            return False
    # CHECKING COLUMNS
    for r in range(9):
        if r != row and get(grid, r, col) == value:
            return False
    # CHECKING 3x3 BOXES
    box_r = (row // 3) * 3
    box_c = (col // 3) * 3
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            if (r, c) != (row, col) and get(grid, r, c) == value:
                return False
    return True


def find_empty(grid):
    for i, val in enumerate(grid):
        if val == 0:
            return i // 9, i % 9
    return None

### SOLVE LOGIC AND BACKTRACKING


def solve(grid):
    cell = find_empty(grid)
    if cell is None:
        return True  # IF NO EMPTY (0) CELLS, SUDOKU = SOLVED

    row, col = cell
    for value in range(1, 10):
        if is_valid(grid, row, col, value):
            set_cell(grid, row, col, value)
            if solve(grid):
                return True
            set_cell(grid, row, col, 0)  # BACKTRACKING

    return False

### SUDOKU GENERATOR

# FILLING EMPTY GRID TO GENERATE A SOLVED GRID


def generate_solved_grid():
    grid = empty_grid()
    _fill(grid)
    return grid

# DEFINING GRID FILLING, FIND EMPTY CELL AND FILL WITH VALID NUMBER


def _fill(grid):
    cell = find_empty(grid)
    if cell is None:
        return True

    row, col = cell
    digits = list(range(1, 10))
    random.shuffle(digits)

    for value in digits:
        if is_valid(grid, row, col, value):
            set_cell(grid, row, col, value)
            if _fill(grid):
                return True
            set_cell(grid, row, col, 0)

    return False


def _count_solutions(grid, limit=2):
    count = [0]

    def recurse(g):
        if count[0] >= limit:
            return
        cell = find_empty(g)
        if cell is None:
            count[0] += 1
            return
        row, col = cell
        for v in range(1, 10):
            if is_valid(g, row, col, v):
                set_cell(g, row, col, v)
                recurse(g)
                set_cell(g, row, col, 0)
    recurse(copy.copy(grid))
    return count[0]

# GENERATE UNIQUE PUZZLE, DEFAULT CELLS EMPTY = 30
def generate_puzzle(clues=30):
    solution = generate_solved_grid()
    puzzle = copy.copy(solution)

    positions = list(range(81))
    random.shuffle(positions)

    removed = 0
    for i in positions:
        if removed >= 81 - clues:
            break
        saved = puzzle[i]
        puzzle[i] = 0
        if _count_solutions(puzzle) != 1:
            puzzle[i] = saved  # restore, removing this breaks uniqueness
        else:
            removed += 1

    return puzzle, solution



### GAME LOGIC

# RETURNS (PUZZLE, SOLUTION) AS LISTS OF 81 INTIGERS (0 MEANS CELL IS EMPTY). NEW GAME GENERATES A PUZZLE
def new_game():
    return generate_puzzle()

# PLAYER ABLE TO PLACE RECEIVED_NUMBER AT PLACE ON THE PUZZLE, RETURNS 'CORRECT' (MATCHES SOLUTION), 'INCORRECT' (DOES NOT MATCH SOLUTION), OR 'ALREADY FILLED' (CELL PRE-FILLED) AS RESPONSE
def place(puzzle, solution, index, received_number):
    if puzzle[index] != 0:
        return "already_filled"
    if solution[index] == received_number:
        puzzle[index] = received_number
        return "correct"
    return "incorrect"

# RETURNS TRUE IF NO ZEROES REMAIN IN PUZZLE
def is_complete(puzzle):
    return 0 not in puzzle


### These are the functions required by server2.py (kaylie's file)

def parse_grid(grid_str: str) -> list[list[int]]:
    """Parse a comma-separated or plain digit string into a 9x9 2D list."""
    grid_str = grid_str.strip()
    parts = grid_str.split(",") if "," in grid_str else list(grid_str)
    if len(parts) != 81:
        raise ValueError(f"Grid must have 81 values, got {len(parts)}")
    try:
        flat = [int(x) for x in parts]
    except ValueError:
        raise ValueError("Grid values must be integers")
    if any(v < 0 or v > 9 for v in flat):
        raise ValueError("Grid values must be 0-9")
    return [flat[i*9:(i+1)*9] for i in range(9)]


def is_valid_solution(current: list[list[int]], solution: list[list[int]]) -> bool:
    """Return True if current matches solution exactly with no zeros."""
    for r in range(9):
        for c in range(9):
            if current[r][c] == 0 or current[r][c] != solution[r][c]:
                return False
    return True


def has_unique_solution(initial: list[list[int]]) -> bool:
    """Return True if the puzzle has exactly one solution."""
    flat = [initial[r][c] for r in range(9) for c in range(9)]
    return _count_solutions(flat, limit=2) == 1


def get_hint(current: list[list[int]], solution: list[list[int]]) -> tuple | None:
    """Return (row, col, value) for the first empty cell, or None if complete."""
    for r in range(9):
        for c in range(9):
            if current[r][c] == 0:
                return r, c, solution[r][c]
    return None



### TESTING DEMO

if __name__ == "__main__":
    puzzle, solution = new_game()

    print("Puzzle (0 = empty):")
    for r in range(9):
        print(puzzle[r*9: r*9+9])

    print("\nSolution:")
    for r in range(9):
        print(solution[r*9: r*9+9])

    # SIMULATING PLAYER PLACING CORRECT NUMBER IN FIRST CELL
    index = puzzle.index(0)
    received_number = solution[index]
    result = place(puzzle, solution, index, received_number)
    print(f"\nPlaced {received_number} at index {index}: {result}")
    print(f"Complete: {is_complete(puzzle)}")