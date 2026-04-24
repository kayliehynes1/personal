from flask import Flask, request, jsonify
import sys 
import os 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SudokuDB
import sudoku_logic as logic 

app = Flask(__name__)
db = SudokuDB()

##Helper for request validation
def validate_json(required_fields):
    def decorator(f):
        def wrapper(*args,**kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Missing JSON body"}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400
            return f(data,*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper 
    return decorator

#Endpoint --> Register users
@app.route('/register', methods = ['POST'])
@validate_json(['username', 'password'])
def register(data):
    success = db.register_user(data['username'], data['password'])
    if success:
        return jsonify ({"status": "ok", "message": "User registered"})
    else:
        return jsonify({"status": "error", "message": "Username already exists"}), 409 

#Endpint --> Login users 
@app.route('/login', methods=['POST'])
@validate_json(['username', 'password'])
def login(data):
    user_id = db.login_user(data['username'], data['password'])
    if user_id:
        return jsonify({"status": "ok", "user_id": user_id, "username": data['username']})
    else:
        return jsonify({"status":"error", "message": "Invalid credentials"}), 401

#Endpoint --> Get all puzzles 
@app.route('/puzzles', methods=['GET'])
def get_puzzles():
    puzzles = db.get_all_puzzles()
    return jsonify({"status": "ok", "puzzles": puzzles})

#Endpoint --> Get a single puzzle 
@app.route('/puzzle/<int:puzzle_id>', methods=['GET'])
def get_puzzle(puzzle_id):
    puzzle = db.get_puzzle(puzzle_id)
    if puzzle:
        return jsonify({"status": "ok", "puzzle": puzzle})
    else:
        return jsonify({"status": "error", "message": "Puzzle not found"}), 404

#Endpoint --> Add a new puzzle 
@app.route('/puzzle', methods = ['POST'])
@validate_json(['user_id', 'initial_grid'])
def add_puzzle(data):
    try:
        initial = logic.parse_grid(data['initial_grid'])
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    # Auto-solve the puzzle
    flat_initial = [initial[r][c] for r in range(9) for c in range(9)]
    import copy
    flat_copy = copy.copy(flat_initial)
    solved = logic.solve(flat_copy)
    if not solved:
        return jsonify({"status": "error", "message": "This puzzle has no solution"}), 400
    # Verify unique solution
    if not logic.has_unique_solution(initial):
        return jsonify({"status": "error", "message": "Puzzle must have exactly one solution"}), 400
    # flat_copy is now solved - store as string
    solution_str = "".join(str(v) for v in flat_copy)
    difficulty = data.get('difficulty', 'medium')
    puzzle_id = db.add_puzzle(data['initial_grid'], solution_str, difficulty, data['user_id'])
    if puzzle_id:
        return jsonify({"status": "ok", "puzzle_id": puzzle_id})
    else:
        return jsonify({"status": "error", "message": "Database error"}), 500

#Solve (then record the solution)
@app.route('/solve', methods=['POST'])
@validate_json(['user_id', 'puzzle_id', 'current_grid', 'time_taken'])
def solve(data):
    puzzle = db.get_puzzle(data['puzzle_id'])
    if not puzzle:
        return jsonify({"status": "error", "message": "Puzzle not found"}), 404
    try:
        current = logic.parse_grid(data['current_grid'])
        solution = logic.parse_grid(puzzle['solution_grid'])
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    if not logic.is_valid_solution(current, solution):
        return jsonify({"status": "error", "message": "Solution is incorrect or incomplete"}), 400
    #if all of the cells are filled 
    if any(cell == 0 for row in current for cell in row):
        return jsonify({"status": "error", "message": "Puzzle isn't completed"}), 400
    db.record_solve(data['user_id'], data['puzzle_id'], data['time_taken'])
    return jsonify({"status": "ok", "message": "Solution recorded"})

#Hints 
@app.route('/hint', methods=['POST'])
@validate_json(['puzzle_id', 'current_grid'])
def hint(data):
    puzzle = db.get_puzzle(data['puzzle_id'])
    if not puzzle:
        return jsonify({"status": "error", "message": "Puzzle not found"}), 404
    try:
        current = logic.parse_grid(data['current_grid'])
        solution = logic.parse_grid(puzzle['solution_grid'])
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    hint = logic.get_hint(current,solution)
    if hint:
        row, col, val = hint
        return jsonify({"status": "ok", "row": row, "col": col, "value": val})
    else:
        return jsonify({"status": "error", "message": "No hint available for this puzzle"}), 400
    

#User statistics 
@app.route('/user_stats/<int:user_id>', methods=['GET'])
def user_stats(user_id):
    stats = db.get_user_stats(user_id)
    return jsonify({"status": "ok", "stats": stats})

#Puzzle statistics
@app.route('/puzzle_stats/<int:puzzle_id>', methods = ['GET'])
def puzzle_stats(puzzle_id):
    stats = db.get_puzzle_stats(puzzle_id)
    return jsonify({"status":"ok", "stats": stats})

#Leaderboard 
@app.route('/leaderboard', methods = ['GET'])
def leaderboard():
    limit = request.args.get('limit', 10, type=int)
    board = db.get_leaderboard(limit)
    return jsonify({"status": "ok", "leaderboard": board})

#Adding a comment 
@app.route ('/comment', methods = ['POST'])
@validate_json(['user_id', 'puzzle_id', 'comment_text'])
def add_comment(data):
    if not data['comment_text'].strip():
        return jsonify({"status": "error", "message": "Comment can't be empty"}), 400
    success = db.add_comment(data['user_id'], data['puzzle_id'], data['comment_text'])
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "error", "message": "Failed to add comment"}), 500
    
#Get comments 
#Get comments 
@app.route('/comments/<int:puzzle_id>', methods = ['GET'])
def get_comments(puzzle_id):
    comments = db.get_comments(puzzle_id)
    return jsonify({'status': 'ok', 'comments': comments})

#Set rating 
@app.route('/rating', methods = ['POST'])
@validate_json(['user_id', 'puzzle_id', 'rating'])
def set_rating(data):
    rating = data['rating']
    if not (1 <= rating <=5):
        return jsonify({"status": "error", "message": "Rating must be 1-5"}), 400
    success = db.set_rating(data['user_id'], data['puzzle_id'], rating)
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "error", "message": "Failed to set rating"}), 500

#Getting users rating for a puzzle  
@app.route('/rating/<int:user_id>/<int:puzzle_id>', methods = ['GET'])
def get_rating(user_id, puzzle_id):
    rating = db.set_rating(user_id, puzzle_id)
    return jsonify({"status": "ok", "rating": rating})

#Sending a friend request 
@app.route('/friend_request', methods=['POST'])
@validate_json(['user_id', 'friend_id'])
def friend_request(data):
    success, msg = db.add_friend_request(data['user_id'], data['friend_id'])
    if success:
        return jsonify({"status": "ok", "message": msg})
    else:
        return jsonify({"status": "error", "message": msg}), 400 

#Accept friend requests 
@app.route('/accept_friend', methods = ['POST'])
@validate_json(['user_id', 'friend_id'])
def accept_friend(data):
    success = db.accept_friend_request(data['user_id'], data['friend_id'])
    if success:
        return jsonify({"status": "ok"})
    else: 
        return jsonify({"status": "error", "message": "Request not found"}), 400

#Extra code for friends list and activity feed
@app.route('/friends/<int:user_id>', methods = ['GET'])
def get_friends(user_id):
    friends = db.get_friends(user_id)
    return jsonify({"status": "ok", "friends": friends})

@app.route('/pending_requests/<int:user_id>', methods = ['GET'])
def pending_requests(user_id):
    requests = db.get_pending_requests(user_id)
    return jsonify({"status": "ok", "requests": requests})

@app.route('/activity/<int:user_id>', methods = ['GET'])
def activity_feed(user_id):
    limit = request.args.get('limit', 20, type=int)
    feed = db.get_activity_feed(user_id, limit)
    return jsonify({"status": "ok", "feed": feed})

@app.route('/find_user/<username>', methods=['GET'])
def find_user(username):
    user = db.get_user_by_username(username)
    if user:
        return jsonify({"status": "ok", "user": user})
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
