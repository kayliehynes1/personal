MSG_LOGIN = "Login"
MSG_REGISTR = "Register"
MSG_LIST_PUZZLES = "List_Puzzles"
MSG_GET_PUZZLE = "Get_Puzzle"
MSG_SUBMIT_SOLUTION = "Submit_solution"
MSG_ADD_PUZZLE = "Add_Puzzle"
MSG_USER_STATS = "User_stats"
MSG_GLOBAL_STATS = "Global_stats"

# Response status
STATUS_OK = "Ok"
STATUS_ERROR = "Error"

def build_request(cmd, **kwargs):
    return {"command": cmd, **kwargs}

def parse_response(data):
    if isinstance(data, dict):
        status = data.get("status")
        if status == STATUS_OK:
            return STATUS_OK, data.get("data")
        else:
            return STATUS_ERROR, data.get("message","Unknown error")
    return STATUS_ERROR, "Invalid response format"