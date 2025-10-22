import sqlite3
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Path to the database file
DB_PATH = os.getenv("DB_PATH")
DB_NAME = os.path.join(DB_PATH, "bot.db")

os.makedirs(DB_PATH, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        data = None
        if fetchone:
            data = cursor.fetchone()
        elif fetchall:
            data = cursor.fetchall()

        if commit:
            conn.commit()

        return data
    except Exception as e:
        print(f"[DB ERROR] {e}")
    finally:
        conn.close()


execute_query("""
CREATE TABLE IF NOT EXISTS users (
    un_id INTEGER PRIMARY KEY AUTOINCREMENT,  
    user_id INTEGER NOT NULL UNIQUE,         
    joined DATE DEFAULT CURRENT_DATE,
    subscribed_status BOOLEAN DEFAULT 0,
    original_language TEXT
);
""", commit=True)


def add_user(user_id: int, subscribed_status: bool = False,
             original_language: str = "en"):
    joined = date.today().isoformat()  
    execute_query("""
        INSERT OR IGNORE INTO users (user_id, joined, subscribed_status, original_language)
        VALUES (?, ?, ?, ?)
    """, (user_id, joined, subscribed_status, original_language), commit=True)


def update_user(user_id: int, subscribed_status: bool = None, original_language: str = None):
   
    fields = []
    params = []

    if subscribed_status is not None:
        fields.append("subscribed_status = ?")
        params.append(subscribed_status)

    if original_language is not None:
        fields.append("original_language = ?")
        params.append(original_language)

    if not fields:
        return

    params.append(user_id)  

    query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
    execute_query(query, params=params, commit=True)


def get_user(user_id: int):
    query = "SELECT * FROM users WHERE user_id = ?"
    user = execute_query(query, params=(user_id,), fetchone=True)
    return user

# update_user(user_id=710680274, subscribed_status=True, original_language="de")



# users = execute_query("SELECT * FROM users", fetchall=True)
# print(users)