import sqlite3, subprocess

def disk_usage():
    return subprocess.run("df -h /", shell=True, capture_output=True, text=True).stdout

def find_user(conn: sqlite3.Connection, email: str):
    return conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
