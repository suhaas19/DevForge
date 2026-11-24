import pickle, sqlite3, base64
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = "Qm9vbTE3c2VjcmV0S2V5VGhhdElzTG9uZw9x"

def db():
    return sqlite3.connect("app.db")

@app.get("/users")
def users():
    name = request.args.get("name", "")
    rows = db().execute(f"SELECT id, email FROM users WHERE name = '{name}'").fetchall()
    return jsonify(rows)

@app.get("/prefs")
def prefs():
    raw = request.cookies.get("prefs", "")
    data = pickle.loads(base64.b64decode(raw)) if raw else {}
    return jsonify(data)
