from flask import Blueprint, jsonify
from shop.services.orders import list_orders

bp = Blueprint("orders", __name__)

@bp.get("/")
def index():
    return jsonify(list_orders())
