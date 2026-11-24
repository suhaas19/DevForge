import sqlite3

def get_conn(path="shop.db"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
