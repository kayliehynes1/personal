import os 
from database import SudokuDB

db = SudokuDB("test.db")

#Users
print(db.register_user("alice", "pass123")) #True 
print(db.register_user("alice", "pass123")) #False bc it's a duplicate
print(db.login_user("alice","pass123")) #1 
print(db.login_user("alice", "wrong")) #None 

#Puzzles
print(db.get_all_puzzles()) #seeded puzzle
print(db.get_puzzle(1)) #full puzzle dict
print(db.get_puzzle(999)) #None 

#Solving & Stats
db.record_solve(1,1,95.0)
print(db.get_user_stats(1)) #puzzles solved = 1
print(db.get_leaderboard(10)) #Alice at top

#Comments & Ratings
print(db.add_comment(1,1,"Great puzzle")) #True 
print(db.get_comments(1)) #list with one comment 
print(db.set_rating(1,1,5)) #True

#Friends
db.register_user("bob", "pass456")
ok, msg = db.add_friend_request(1,2)
print(ok, msg) #True, friend request sent
print(db.accept_friend_request(2,1)) #True 
print(db.get_friends(1)) #bob
print(db.get_pending_requests(2)) #empty list 
print(db.get_activity_feed(1,20)) #alice's actions

os.remove("test.db")
print("All done")
