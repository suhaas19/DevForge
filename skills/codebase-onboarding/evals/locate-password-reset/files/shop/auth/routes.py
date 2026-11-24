from flask import Blueprint, request, jsonify
from shop.auth.reset import start_password_reset

bp = Blueprint("auth", __name__)

@bp.post("/reset")
def reset():
    start_password_reset(request.json["email"])
    return jsonify(ok=True)
