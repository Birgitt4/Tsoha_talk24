from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import os

def login(username, password):
    sql = "SELECT password, id FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        return False
    else:
        if check_password_hash(user[0], password):
            session["user_id"] = user[1]
            session["loggedin"] = True
            session["csrf_token"] = os.urandom(16).hex()
            return True
        else:
            return False

def logout():
    del session["user_id"]
    del session["loggedin"]
    del session["csrf_token"]

def signup(username, password):
    hash_val = generate_password_hash(password)
    try:
        sql = "INSERT INTO users (username, password, status) VALUES (:username, :password, 'normal')"
        db.session.execute(sql, {"username":username, "password":hash_val})
        db.session.commit()
    except:
        return False
    return True

def username_taken(username):
    sql = "SELECT COUNT(*) FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    return result.first()[0] == 1

def user_id():
    return session.get("user_id", 0)

def logged():
    return session.get("loggedin", 0)

def is_admin():
    sql = "SELECT status FROM users WHERE id=:user_id"
    result = db.session.execute(sql, {"user_id":session.get("user_id")})
    return result.first()[0] == "admin"

def get_name(id):
    sql = "SELECT username FROM users WHERE id=:id"
    result = db.session.execute(sql, {"id":id})
    return result.first()[0]

def get_threads(user_id, privat):
    if privat == 0:
        sql = "SELECT title, id FROM threads WHERE user_id=:user_id AND privat=:privat"
        result = db.session.execute(sql, {"user_id":user_id, "privat":privat})
        return result.fetchall()
    else:
        sql = """SELECT T.title, T.id FROM threads T, privateThreads P WHERE 
                P.user_id=:user_id AND T.id=P.thread_id"""
        result = db.session.execute(sql, {"user_id":user_id})
        return result.fetchall()

def get_saved(user_id):
    sql = """SELECT T.title, T.id FROM threads T, saved S WHERE 
            S.user_id=:user_id AND T.id=S.thread_id"""
    result = db.session.execute(sql, {"user_id":user_id})
    return result.fetchall()

def save(thread_id):
    sql = "SELECT COUNT(*) FROM saved WHERE thread_id=:thread_id AND user_id=:user_id"
    result = db.session.execute(sql, {"thread_id":thread_id, "user_id":user_id()})
    if result.first()[0] == 1:
        return
    sql = "INSERT INTO saved (thread_id, user_id) VALUES (:thread_id, :user_id)"
    db.session.execute(sql, {"thread_id":thread_id, "user_id":user_id()})
    db.session.commit()

def add_friend(friend_id):
    sql = "SELECT COUNT(*) FROM friends WHERE user_id=:user_id AND friend_id=:friend_id"
    result = db.session.execute(sql, {"user_id":user_id(), "friend_id":friend_id})
    if result.first()[0] == 1:
        return
    sql = "INSERT INTO friends (user_id, friend_id) VALUES (:user_id, :friend_id)"
    db.session.execute(sql, {"user_id":user_id(), "friend_id":friend_id})
    db.session.commit()

def delete_friend(id):
    sql = "DELETE FROM friends WHERE user_id=:id AND friend_id=:user_id"
    db.session.execute(sql, {"id":id, "user_id":user_id()})
    db.session.commit()

#This will fetch friends of a logged in user who are not in the thread.
#Only "real" friends not friendrequests
def get_friends(thread_id):
    sql = """SELECT U.username, U.id FROM users U, friends F, friends X WHERE 
            U.id=F.friend_id AND F.user_id=:user_id AND F.user_id=X.friend_id AND 
            F.friend_id=X.user_id AND F.friend_id NOT IN (SELECT P.user_id FROM 
            privateThreads P WHERE P.thread_id=:thread_id) ORDER BY U.username"""
    result = db.session.execute(sql, {"user_id":user_id(), "thread_id":thread_id})
    return result.fetchall()

def get_friend_requests():
    sql = """SELECT U.username, U.id FROM users U, friends A WHERE U.id=A.user_id 
            AND A.friend_id=:user_id AND A.user_id NOT IN 
            (SELECT B.friend_id FROM friends B WHERE B.user_id=:user_id)"""
    result = db.session.execute(sql, {"user_id":user_id(), "user_id":user_id()})
    return result.fetchall()

def private_access(thread_id):
    sql = "SELECT COUNT(*) FROM privateThreads WHERE thread_id=:thread_id AND user_id=:user_id"
    result = db.session.execute(sql, {"thread_id":thread_id, "user_id":user_id()})
    return result.first()[0] == 1