import json 
import re 
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any 
from urllib.parse import urlparse, parse_qs

import database as db

HOST = "localhost"
PORT = 8080

def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
  body = json.dumps(payload).encode()
  handler.send_response(status)
  handler.send_header("Content-Type", "application/json")
  handler.send_header("Content-Length", str(len(body)))
  handler.end_headers()
  handler.wfile.write(body)

def _read_body(handler: BaseHTTPRequestHandler) -> dict:
  #Read and parse JSON request and return an empty dict if there is a failure 
  length = int(handler.headers.get("Content-Length", 0))
  if length == 0:
    return {}
  raw = handler.rfile.read(length)
  try:
    return json.loads(raw)
  except json.JSONDecodeError:
    return {}

def _require_fields(data:dict,fields: list[str]) -> str|None:
  #Return an error string if any required field is missing 
  missing = [f for f in fields if f not in data or data[f] == ""]
  if missing:
    return f"Missing required fields: {', '.join(missing)}"
  return None 

class SudokuHandler(BaseHTTPRequestHandler):
  def log_message(self, format_str: str, *args: Any) -> None:
    pass
  def do_GET(self) -> None:
    parsed = urlparse(self.path)
    path = parsed.path.rstrip("/")
    
    #List all puzzles
    if path == "/puzzles":
      puzzles = db.get_puzzles()
      _json_response(self, 200, {"ok": True, "puzzles": puzzles})
      return 
      
    #Get single puzzle
    m = re.fullmatch(r"/puzzle/(\d+)", path)
    if m:
      puzzle = db.get_puzzle(int(m.group(1)))
      if puzzle:
        _json_response(self,200, {"ok": True, "puzzle": puzzle})
      else:
        _json_response(self, 404, {"ok": False, "error": "Puzzle not found"})
      return
      
    #User stats
    m = re.fullmatch(r"/stats/(\d+)", path)
    if m:
      stats = db.get_user_stats(int(m.group(1)))
      if stats:
        _json_response(self, 200, {"ok": True, "stats": stats})
      else:
        _json_response(self, 404, {"ok": False, "error": "User not found"})
      return

    #Leaderboard for all users
    if path == "/leaderboard":
      all_stats = db.get_all_user_stats()
      _json_response(self, 200, {"ok": True, "leaderboard": all_stats})
      return 
      
    #Comments for a puzzle
    m = re.fullmatch(r"/comments/(\d+)", path)
    if m:
      comments = db.get_comments(int(m.group(1)))
      _json_response(self, 200, {"ok": True, "comments": comments})
      return 

    #Friends list
    m = re.fullmatch(r"/friends/(\d+)", path)
    if m:
      friends = db.get_friends(int(m.group(1)))
      _json_response(self, 200, {"ok": True, "friends": friends})
      return 

    #Activity feed
    m = re.fullmatch(r"/feed/(\d+)", path)
    if m:
      feed = db.get_feed(int(m.group(1)))
      _json_response(self, 200, {"ok": True, "feed": feed})
      return 
    _json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

def do_POST(self) -> None:
  parsed=urlparse(self.path)
  path = parsed.path.rstrip("/")
  data = _read_body(self)

  #Register
  if path == "/register":
    err= _require_fields(data, ["username", "password"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return
    result = db.register_user(data["username"], data["password"])
    _json_response(self, 201 if result["ok"] else 409, result)
    return
    
  #Login 
  if path == "/login":
    err = _require_fields(data, ["username", "password"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return 
    result = db.login_user(data["username"], data["password"])
    _json_response(self, 200 if result ["ok"] else 401, result)
    return
  if path == "/puzzle":
    err = _require_fields(
      data, ["title", "author_id", "initial_grid", "solution"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return
    size = int(data.get("size",9))
    if not isinstance(size,int) or size not in (4,9,16):
      _json_response(self, 400, {"ok": False, "error": "size must be 4, 9, or 16"})
      return
      
      #Validate grid strings 
    result = db.add_puzzle(
      title = data["title"],
      author_id = int(data["author_id"]),
      initial_grid = data["initial_grid"],
      solution = data["solution"],
      difficulty = data.get("difficulty", "medium"),
      size = size
      )
    _json_response(self, 201 if result["ok"] else 400, result)
    return 
  
  #=================================================Add rest on GitHub Repository ==============================================

  #Record a completed solution
  if path == "/solve":
    err = _require_fields(data, ["user_id", "puzzle_id", "time_taken"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return 
    db.record_solve(
      int(data["user_id"]),
      int(data["puzzle_id"]),
      float(data["time_taken"])
    )
    _json_response(self, 200, {"ok": True})
    return 
  
  #Hint --> return the correct value for one cell
  if path == "/hint":
    err = _require_fields(data, ["puzzle_id", "row", "col", "user_id"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return
    puzzle = db.get_puzzle(int(data["puzzle_id"]))
    if not puzzle:
      _json_response(self, 404, {"ok": False, "error": "Puzzle not found"})
      return
    size = puzzle["size"]
    row, col = int(data["row"]), int(data["col"])
    if not (0 <= row < size and 0 <= col<size):
      _json_response(self, 400, {"ok": False, "error": "Row or column is out of range"})
      return 
    idx = row * size + col
    hint_value = int(puzzle["solution"][idx])
    db.increment_hints(int(data["user_id"]))
    _json_response(self, 200, {"ok": True, "value": hint_value})
    return 
  
  #Validate a user-supplied full or partial grid
  if path == "/validate":
    err = _require_fields(data, ["puzzle_id", "grid"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return 
    puzzle = db.get_puzzle(int(data["puzzle_id"]))
    if not puzzle:
      _json_response(self, 404, {"ok": False, "error": "Puzzle not found"})
      return 
    user_grid: str = data["grid"]
    solution: str = puzzle["solution"]
    size = puzzle["size"]
    errors: list[str] = []
    for i, (u,s) in enumerate(zip(user_grid, solution)):
      if u != "0" and u != s:
        row, col = divmod(i, size)
        errors.append(f"({row},{col})")
    _json_response(self, 200, {
      "ok": True,
      "correct": len(errors) == 0,
      "wrong_cells": errors
    })
    return
  
  #Add comment
  if path == "/comment":
    err = _require_fields(data, ["user_id", "puzzle_id", "body"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return 
    result = db.add_comment(
      int(data["user_id"]), int(data["puzzle_id"]), data["body"]
    )
    _json_response(self, 201, result)
    return 
  
  #Rate a puzzle
  if path == "/rate":
    err = _require_fields(data, ["user_id", "puzzle_id", "rating"])
    if err: 
      _json_response(self, 400, {"ok": False, "error": err})
      return 
    result = db.rate_puzzle(
      int(data["user_id"]), int(data["puzzle_id"]), int(data["rating"])
    )
    _json_response(self, 200 if result ["ok"] else 400, result)
    return
  if path == "/friend":
    err = _require_fields(data, ["user_id", "friend_username"])
    if err:
      _json_response(self, 400, {"ok": False, "error": err})
      return
    friend = db.get_user_by_username(data["friend_username"])
    if not friend:
      _json_response(self, 404, {"ok": False, "error": "User not found"})
      return 
    result = db.add_friend(int(data["user_id"]), friend ["id"])
    _json_response(self, 200 if result ["ok"] else 400, result)
    return
   
  _json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

def run_server(host: str = HOST, port: int = PORT) -> None:
  db.init_db()
  server = HTTPServer((host, port), SudokuHandler)
  print(f"[Server] Sudoku server running on https://{host}:{port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    print("[Server] Shutting down")
    server.server_close()

if __name__ == "__main__":
  run_server()


  
  
  
  

      

      