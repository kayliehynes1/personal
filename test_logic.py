import sudoku_logic as logic 

init_str = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
sol_str  = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"

initial = logic.parse_grid(init_str)
solution = logic.parse_grid(sol_str)

print(logic.is_valid_solution(solution, solution)) #True 
print(logic.is_valid_solution(initial, solution)) #False - has 0s
print(logic.has_unique_solution(initial)) # True 
print(logic.get_hint(initial,solution)) # (row, col, value)

#Error handling 

try: 
    logic.parse_grid("tooshort")
except ValueError as e:
    print("Caught expected error:", e)
